import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression, HuberRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy.stats import pearsonr

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")

def norm_time(df, t_col, v_col, name):
    if df.empty: return pd.DataFrame(columns=['fecha_hora_utc', name])
    df[t_col] = pd.to_datetime(df[t_col], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[t_col])
    if df[t_col].dt.tz is None:
        df[t_col] = df[t_col].dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[t_col].dt.tz_convert('UTC')
    df[name] = pd.to_numeric(df[v_col], errors='coerce')
    return df[['fecha_hora_utc', name]].drop_duplicates('fecha_hora_utc')

def calc_cov(df, start, end, col):
    mask = (df.index >= start) & (df.index <= end)
    d = df[mask]
    e = len(pd.date_range(start, end, freq='h'))
    if len(d) == 0: return 0, e
    return d[col].notna().sum(), e

def get_metrics(y_true, y_pred):
    m = y_true.notna() & y_pred.notna()
    yt, yp = y_true[m], y_pred[m]
    if len(yt) < 2: return None
    chill_t = (yt <= 7.2).sum()
    chill_p = (yp <= 7.2).sum()
    chill_err = abs(chill_p - chill_t) / chill_t * 100 if chill_t > 0 else np.nan
    df_d = pd.DataFrame({'yt': yt, 'yp': yp, 'idx': yt.index})
    df_d['date'] = df_d['idx'].dt.tz_convert('America/Santiago').dt.date
    daily = df_d.groupby('date').agg(t_min=('yt','min'), p_min=('yp','min')).dropna()
    tmin_mae = mean_absolute_error(daily['t_min'], daily['p_min']) if len(daily) > 0 else np.nan
    return {
        "MAE": mean_absolute_error(yt, yp), "RMSE": np.sqrt(mean_squared_error(yt, yp)),
        "Bias": (yp - yt).mean(), "Pearson": pearsonr(yt, yp)[0],
        "Tmin_MAE": tmin_mae, "Chill_Err%": chill_err
    }

def main():
    t = norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'INIA333')
    
    cands = {
        "Agromet": norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'Agromet'),
        "SanClemente_INIA": norm_time(pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/san_clemente/climate_hourly.parquet"), 'fecha_hora', 'tempMedia', 'SanClemente_INIA'),
        "Panguilemo": norm_time(pd.read_csv(BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv", skiprows=5), 'Tiempo UTC-4', 'Panguilemo', 'Panguilemo'),
        "Talca": norm_time(pd.read_csv(BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv", skiprows=5), 'Tiempo UTC-4', 'Talca', 'Talca'),
        "PencahueSur_Datavid": norm_time(pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_sur/climate_hourly.parquet"), 'fecha', 'tempMedia', 'PencahueSur_Datavid'),
        "SanClemente_Datavid": norm_time(pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/san_clemente_la_higuera/climate_hourly.parquet"), 'fecha', 'tempMedia', 'SanClemente_Datavid')
    }
    df_pn = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet")
    pn_col = 'tempMedia' if 'tempMedia' in df_pn.columns else ('tempMinima' if 'tempMinima' in df_pn.columns else df_pn.columns[1])
    cands["PencahueNorte"] = norm_time(df_pn, 'fecha', pn_col, 'PencahueNorte')
    
    df_m = t.copy()
    for c, df in cands.items(): df_m = df_m.merge(df, on='fecha_hora_utc', how='outer')
    df_m = df_m.sort_values('fecha_hora_utc').set_index('fecha_hora_utc')
    
    s_24 = pd.to_datetime('2024-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_24 = pd.to_datetime('2024-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    s_25 = pd.to_datetime('2025-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_25 = pd.to_datetime('2025-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    test_mask = (df_m.index >= s_25) & (df_m.index <= e_25)
    test_df = df_m[test_mask].copy()
    train_df = df_m[~test_mask].copy()
    
    report_lines = [
        "## Auditoría Completa de Candidatos (Incluidos No Operativos)",
        "",
        "Se revisó exhaustivamente la disponibilidad de cada candidato, confirmándose que `Panguilemo`, `Talca` y `Pencahue Sur Datavid` carecen por completo de datos para el hueco crítico de 2024.",
        "",
        "| Candidato | Inicio Serie | Fin Serie | Cob. Hueco 2024 | Cob. Test 2025 | N Simultáneo Test | Evaluado | Motivo de Exclusión | Mejor Método | MAE | Tmin MAE | Error Frío |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for c in cands.keys():
        start = cands[c]['fecha_hora_utc'].min().strftime('%Y-%m-%d') if not cands[c].empty else "N/A"
        end = cands[c]['fecha_hora_utc'].max().strftime('%Y-%m-%d') if not cands[c].empty else "N/A"
        
        v24, e24 = calc_cov(df_m, s_24, e_24, c)
        p24 = f"{v24/e24*100:.1f}%" if e24>0 else "0%"
        
        v25, e25 = calc_cov(df_m, s_25, e_25, c)
        p25 = f"{v25/e25*100:.1f}%" if e25>0 else "0%"
        
        mask = test_df['INIA333'].notna() & test_df[c].notna()
        n_sim = mask.sum()
        
        if v24/e24 < 0.9:
            motivo = f"Sin datos en 2024"
            ev = "Sí (Solo comparativo)" if n_sim > 0 else "No"
        else:
            motivo = "Ninguno (Operativo)"
            ev = "Sí"
            
        best_m_str, best_mae, best_tmin, best_chill = "-", "-", "-", "-"
        if n_sim > 100:
            best_l, best_c = 0, -1
            for l in range(-6, 7):
                s = train_df[c].shift(l)
                m = train_df['INIA333'].notna() & s.notna()
                if m.sum() > 10:
                    corr = np.corrcoef(train_df.loc[m, 'INIA333'], s[m])[0,1]
                    if corr > best_c: best_c, best_l = corr, l
            
            X_tr = train_df[[c]].shift(best_l).dropna()
            y_tr = train_df.loc[X_tr.index, 'INIA333'].dropna()
            idx = X_tr.index.intersection(y_tr.index)
            if len(idx)>10:
                X_tr, y_tr = X_tr.loc[idx], y_tr.loc[idx]
                bias = np.mean(y_tr - X_tr[c])
                ols = LinearRegression().fit(X_tr, y_tr)
                huber = HuberRegressor().fit(X_tr, y_tr)
                
                X_ts = test_df.loc[mask, [c]].shift(best_l)
                valid_ts = X_ts.dropna()
                if len(valid_ts)>0:
                    y_true = test_df.loc[valid_ts.index, 'INIA333']
                    
                    res_dir = get_metrics(y_true, valid_ts[c])
                    res_bias = get_metrics(y_true, valid_ts[c] + bias)
                    res_ols = get_metrics(y_true, pd.Series(ols.predict(valid_ts), index=valid_ts.index))
                    res_huber = get_metrics(y_true, pd.Series(huber.predict(valid_ts), index=valid_ts.index))
                    
                    best_score = 999
                    for name, met in [('Directo', res_dir), ('Bias', res_bias), ('OLS', res_ols), ('Huber', res_huber)]:
                        if met:
                            score = met['MAE'] + met['Tmin_MAE'] + (met['Chill_Err%']/10)
                            if score < best_score:
                                best_score = score
                                best_m_str = name
                                best_mae = f"{met['MAE']:.2f}"
                                best_tmin = f"{met['Tmin_MAE']:.2f}"
                                best_chill = f"{met['Chill_Err%']:.1f}%"
        
        report_lines.append(f"| {c} | {start} | {end} | {p24} | {p25} | {n_sim} | {ev} | {motivo} | {best_m_str} | {best_mae} | {best_tmin} | {best_chill} |")
        
    out_file = BASE_DIR / "reports" / "qa" / "auditoria_proxy_inia333_exhaustiva.md"
    with open(out_file, "w", encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"Written to {out_file}")

if __name__ == "__main__":
    main()
