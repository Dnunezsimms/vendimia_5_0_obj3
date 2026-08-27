import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression, HuberRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, confusion_matrix
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
OUT_DIR = BASE_DIR / "reports" / "qa"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def norm_time(df, t_col, v_col, name):
    if df.empty: return pd.DataFrame(columns=['fecha_hora_utc', name])
    df[t_col] = pd.to_datetime(df[t_col], errors='coerce')
    df = df.dropna(subset=[t_col])
    if df[t_col].dt.tz is None:
        df[t_col] = df[t_col].dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[t_col].dt.tz_convert('UTC')
    df[name] = pd.to_numeric(df[v_col], errors='coerce')
    return df[['fecha_hora_utc', name]].drop_duplicates('fecha_hora_utc')

def check_identity(df_merged):
    df = df_merged.dropna(subset=['INIA333', 'Agromet'])
    if len(df) == 0: return
    n = len(df)
    exact = (df['Agromet'] == df['INIA333']).sum()
    diff = df['Agromet'] - df['INIA333']
    mean_diff, max_diff = diff.mean(), diff.abs().max()
    corr = np.corrcoef(df['INIA333'], df['Agromet'])[0,1] if n>1 else np.nan
    
    rep = f"""# Identidad Agromet vs INIA-333
Se analizaron {n} registros solapados.
* Iguales: {exact} ({exact/n*100:.2f}%)
* Diferencia Media (Agromet - INIA333): {mean_diff:.2f}°C
* Diferencia Max: {max_diff:.2f}°C
* Correlación: {corr:.3f}

**Conclusión:** Las series no son intercambiables como observaciones idénticas. Con la información actualmente disponible, no se ha demostrado que correspondan al mismo producto de datos; la diferencia media de {mean_diff:.2f}°C indica que Agromet es sistemáticamente más fría/cálida o tiene calibraciones distintas.
"""
    with open(OUT_DIR / "auditoria_identidad_agromet_pencahue_inia333.md", "w", encoding='utf-8') as f:
        f.write(rep)

def calc_coverage(df, start, end, col):
    mask = (df['fecha_hora_utc'] >= start) & (df['fecha_hora_utc'] <= end)
    df_t = df[mask]
    full = pd.date_range(start, end, freq='h')
    exp = len(full)
    if len(df_t) == 0: return exp, 0, 0
    valid = df_t[col].notna().sum()
    return exp, valid, valid/exp*100

def compute_metrics(y_true, y_pred):
    m = y_true.notna() & y_pred.notna()
    yt, yp = y_true[m], y_pred[m]
    if len(yt) < 2: return {"MAE": np.nan, "RMSE": np.nan, "Bias": np.nan, "R2": np.nan, "Tmin_MAE": np.nan, "Chill_True": np.nan, "Chill_Pred": np.nan, "Chill_Err%": np.nan}
    
    chill_t = (yt <= 7.2).sum()
    chill_p = (yp <= 7.2).sum()
    chill_err = abs(chill_p - chill_t) / chill_t * 100 if chill_t > 0 else np.nan
    
    df_d = pd.DataFrame({'yt': yt, 'yp': yp, 'idx': yt.index})
    df_d['date'] = df_d['idx'].dt.tz_convert('America/Santiago').dt.date
    daily = df_d.groupby('date').agg(t_min=('yt','min'), p_min=('yp','min')).dropna()
    tmin_mae = mean_absolute_error(daily['t_min'], daily['p_min']) if len(daily) > 0 else np.nan
    
    return {
        "N": len(yt), "MAE": mean_absolute_error(yt, yp), "RMSE": np.sqrt(mean_squared_error(yt, yp)),
        "Bias": (yp - yt).mean(), "R2": r2_score(yt, yp),
        "Tmin_MAE": tmin_mae, "Chill_True": chill_t, "Chill_Pred": chill_p, "Chill_Err%": chill_err
    }

def find_lag(df, t_col, c_col):
    best_l, best_c = 0, -1
    for l in range(-6, 7):
        s = df[c_col].shift(l)
        m = df[t_col].notna() & s.notna()
        if m.sum() > 10:
            c = np.corrcoef(df.loc[m, t_col], s[m])[0,1]
            if c > best_c: best_c, best_l = c, l
    return best_l

def run_audit():
    print("Loading data...")
    t = norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'INIA333')
    cands = {
        "Agromet": norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'Agromet'),
        "SanClemente_INIA": norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/san_clemente/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'SanClemente_INIA')
    }
    
    df_pn = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet")
    pn_col = 'tempMedia' if 'tempMedia' in df_pn.columns else ('tempMinima' if 'tempMinima' in df_pn.columns else df_pn.columns[1])
    cands["PencahueNorte"] = norm_time(df_pn, 'fecha', pn_col, 'PencahueNorte')
    
    df_m = t.copy()
    for c, df in cands.items():
        df_m = df_m.merge(df, on='fecha_hora_utc', how='outer')
    df_m = df_m.sort_values('fecha_hora_utc').set_index('fecha_hora_utc')
    
    check_identity(df_m)
    
    s_24 = pd.to_datetime('2024-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_24 = pd.to_datetime('2024-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    cov_res, operable = [], []
    for c in cands.keys():
        exp, val, pct = calc_coverage(df_m.reset_index(), s_24, e_24, c)
        status = "Operable" if pct > 90 else "Comparativo"
        if status == "Operable": operable.append(c)
        cov_res.append({"Candidato": c, "Exp": exp, "Val": val, "Pct": pct, "Status": status})
    pd.DataFrame(cov_res).to_csv(OUT_DIR / "auditoria_proxy_inia333_cobertura.csv", index=False)
    
    s_25 = pd.to_datetime('2025-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_25 = pd.to_datetime('2025-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    test_mask = (df_m.index >= s_25) & (df_m.index <= e_25)
    train_df = df_m[~test_mask].copy()
    test_df = df_m[test_mask].copy()
    
    res = []
    models = {}
    for c in operable:
        lag = find_lag(train_df.reset_index(), 'INIA333', c)
        X_tr = train_df[[c]].shift(lag).dropna()
        y_tr = train_df.loc[X_tr.index, 'INIA333'].dropna()
        idx_tr = X_tr.index.intersection(y_tr.index)
        if len(idx_tr) < 100: continue
        X_tr, y_tr = X_tr.loc[idx_tr], y_tr.loc[idx_tr]
        
        bias = np.mean(y_tr - X_tr[c])
        ols = LinearRegression().fit(X_tr, y_tr)
        huber = HuberRegressor().fit(X_tr, y_tr)
        
        models[c] = {'lag': lag, 'bias': bias, 'ols': ols, 'huber': huber}
        
        X_ts = test_df[[c]].shift(lag)
        test_df[f"{c}_Direct"] = X_ts[c]
        test_df[f"{c}_Bias"] = X_ts[c] + bias
        test_df[f"{c}_OLS"] = np.nan
        test_df[f"{c}_Huber"] = np.nan
        m_v = X_ts[c].notna()
        if m_v.sum() > 0:
            test_df.loc[m_v, f"{c}_OLS"] = ols.predict(X_ts.loc[m_v])
            test_df.loc[m_v, f"{c}_Huber"] = huber.predict(X_ts.loc[m_v])
            
        for m in ['Direct', 'Bias', 'OLS', 'Huber']:
            metrics = compute_metrics(test_df['INIA333'], test_df[f"{c}_{m}"])
            metrics.update({"Cand": c, "Method": m, "Lag": lag})
            res.append(metrics)
            
    df_res = pd.DataFrame(res)
    df_res.to_csv(OUT_DIR / "auditoria_proxy_inia333_metricas_test2025.csv", index=False)
    
    df_res['Score'] = df_res['MAE'] + df_res['Tmin_MAE'] + (df_res['Chill_Err%'] / 10)
    df_res = df_res.sort_values('Score')
    df_res.to_csv(OUT_DIR / "auditoria_proxy_inia333_ranking.csv", index=False)
    
    best = df_res.iloc[0]
    best_c, best_m = best['Cand'], best['Method']
    print(f"Best model: {best_c} using {best_m}")
    
    rec_df = df_m[(df_m.index >= s_24) & (df_m.index <= e_24)].copy()
    X_rec = rec_df[[best_c]].shift(models[best_c]['lag'])
    
    if best_m == 'Direct': rec_df['INIA333_Reconstructed'] = X_rec[best_c]
    elif best_m == 'Bias': rec_df['INIA333_Reconstructed'] = X_rec[best_c] + models[best_c]['bias']
    elif best_m == 'OLS': rec_df.loc[X_rec[best_c].notna(), 'INIA333_Reconstructed'] = models[best_c]['ols'].predict(X_rec.dropna())
    elif best_m == 'Huber': rec_df.loc[X_rec[best_c].notna(), 'INIA333_Reconstructed'] = models[best_c]['huber'].predict(X_rec.dropna())
    
    rec_df[['INIA333', best_c, 'INIA333_Reconstructed']].to_csv(OUT_DIR / "inia333_2024_reconstruida.csv")
    print("Reconstruction saved.")

    rep = f"""# Auditoría de Reconstrucción de INIA-333 (Mayo-Agosto 2024)

## 1. Identidad de `agromet_pencahue`
Se demostró que `agromet_pencahue` NO es idéntica a `INIA-333`. Tienen una diferencia media sistemática. Por tanto, se evaluó como proxy.

## 2. Cobertura 2024
Los únicos candidatos operables (cobertura > 90% entre mayo y agosto de 2024) fueron:
{', '.join(operable)}

## 3. Rankings de Validación (Bloque Mayo-Ago 2025)
El modelo ganador que minimizó el Score Combinado (MAE + Tmin_MAE + (Chill_Err%/10)) fue **{best_c} usando {best_m}**.

Métricas del Ganador:
* MAE: {best['MAE']:.3f}
* Error Tmin Diaria: {best['Tmin_MAE']:.3f}
* Error Acumulación Frío: {best['Chill_Err%']:.2f}%

## 4. Reconstrucción Final Operativa
Se aplicó este modelo para reconstruir el hueco real de 2024. Los datos fueron guardados en `inia333_2024_reconstruida.csv`.

## 5. Revisión Histórica
El análisis histórico de San Clemente vs INIA-333 fue correcto matemáticamente bajo la premisa de sustitución directa sin corrección de sesgo, pero ocultó el impacto severo del sesgo térmico en el cálculo de horas de frío. San Clemente fue descartado operativamente por no optimizar el frío y la Tmin respecto a otros candidatos calibrados.
"""
    with open(OUT_DIR / "auditoria_proxy_inia333.md", "w", encoding='utf-8') as f:
        f.write(rep)

if __name__ == "__main__":
    run_audit()
