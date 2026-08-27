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
FIG_DIR = OUT_DIR / "figures" / "inia333"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_and_normalize(path, time_col, val_col):
    if not path.exists(): return pd.DataFrame(columns=['fecha_hora_utc'])
    if path.suffix == '.parquet': df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        try: df = pd.read_csv(path, skiprows=5)
        except: df = pd.read_csv(path)
    else: return pd.DataFrame(columns=['fecha_hora_utc'])
    
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    if df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[time_col].dt.tz_convert('UTC')
    df['temp'] = pd.to_numeric(df[val_col], errors='coerce')
    return df[['fecha_hora_utc', 'temp']]

def find_best_lag(df_train, target_col, cand_col):
    best_lag = 0
    best_corr = -1
    for lag in range(-6, 7):
        shifted = df_train[cand_col].shift(lag)
        mask = df_train[target_col].notna() & shifted.notna()
        if mask.sum() > 10:
            corr = np.corrcoef(df_train.loc[mask, target_col], shifted[mask])[0,1]
            if corr > best_corr:
                best_corr = corr
                best_lag = lag
    return best_lag, best_corr

def compute_hourly_metrics(y_true, y_pred, name):
    mask = y_true.notna() & y_pred.notna()
    y_t, y_p = y_true[mask], y_pred[mask]
    n = len(y_t)
    if n < 2: return {"Method": name, "N": n}
    
    diff = y_p - y_t
    return {
        "Method": name, "N": n, "MAE": mean_absolute_error(y_t, y_p), 
        "RMSE": np.sqrt(mean_squared_error(y_t, y_p)), "Bias": diff.mean(),
        "Median_Err": diff.median(), "Std_Resid": diff.std(),
        "R2": r2_score(y_t, y_p), "Pearson": pearsonr(y_t, y_p)[0], "Spearman": spearmanr(y_t, y_p)[0]
    }

def compute_daily_metrics(df, true_col, pred_col, name):
    df = df.copy()
    df['local_date'] = df['fecha_hora_utc'].dt.tz_convert('America/Santiago').dt.date
    
    daily = df.groupby('local_date').agg(
        true_min=(true_col, 'min'), pred_min=(pred_col, 'min'),
        true_max=(true_col, 'max'), pred_max=(pred_col, 'max'),
        true_mean=(true_col, 'mean'), pred_mean=(pred_col, 'mean')
    ).dropna()
    
    if len(daily) < 2: return {"Method": name}
    
    return {
        "Method": name,
        "N_days": len(daily),
        "Tmin_MAE": mean_absolute_error(daily['true_min'], daily['pred_min']),
        "Tmax_MAE": mean_absolute_error(daily['true_max'], daily['pred_max']),
        "Tmean_MAE": mean_absolute_error(daily['true_mean'], daily['pred_mean'])
    }

def compute_chill_metrics(y_true, y_pred, name, threshold=7.2):
    mask = y_true.notna() & y_pred.notna()
    y_t, y_p = y_true[mask], y_pred[mask]
    
    true_chill = (y_t <= threshold).sum()
    pred_chill = (y_p <= threshold).sum()
    
    if true_chill == 0: return {"Method": name}
    
    y_t_bin = (y_t <= threshold).astype(int)
    y_p_bin = (y_p <= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_t_bin, y_p_bin, labels=[0, 1]).ravel()
    
    sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    
    return {
        "Method": name, "True_Chill": true_chill, "Pred_Chill": pred_chill,
        "Abs_Diff": pred_chill - true_chill, "Err_%": (pred_chill - true_chill)/true_chill * 100,
        "FP": fp, "FN": fn, "Sensitivity": sens, "Specificity": spec
    }

def run_phase_2():
    print("Loading data...")
    target = load_and_normalize(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet", 'fecha_hora', 'tempMedia')
    target = target.rename(columns={'temp': 'INIA333'})
    
    cands = {
        "Agromet": load_and_normalize(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet", 'fecha_hora', 'tempMedia'),
        "PencahueNorte": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet", 'fecha', 'tempMinima'), # Assuming tempMinima or tempMedia
        "SanClemente_INIA": load_and_normalize(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/san_clemente/climate_hourly.parquet", 'fecha_hora', 'tempMedia'),
        "Panguilemo": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv", 'Tiempo UTC-4', 'Panguilemo')
    }
    
    # Check pencahue norte variable
    df_pn = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet")
    val_col_pn = 'tempMedia' if 'tempMedia' in df_pn.columns else ('tempMinima' if 'tempMinima' in df_pn.columns else df_pn.columns[1])
    cands['PencahueNorte'] = load_and_normalize(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet", 'fecha', val_col_pn)
    
    df_merged = target.copy()
    for name, df in cands.items():
        df_c = df.rename(columns={'temp': name})
        df_merged = df_merged.merge(df_c, on='fecha_hora_utc', how='outer')
        
    df_merged = df_merged.sort_values('fecha_hora_utc')
    
    test_start = pd.to_datetime('2025-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    test_end = pd.to_datetime('2025-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    mask_test = (df_merged['fecha_hora_utc'] >= test_start) & (df_merged['fecha_hora_utc'] <= test_end)
    df_train = df_merged[~mask_test].copy()
    df_test = df_merged[mask_test].copy()
    
    results_hourly = []
    results_daily = []
    results_chill = []
    
    for cand in ['Agromet', 'PencahueNorte', 'SanClemente_INIA', 'Panguilemo']:
        best_lag, best_corr = find_best_lag(df_train, 'INIA333', cand)
        
        df_train[f'{cand}_lag'] = df_train[cand].shift(best_lag)
        df_test[f'{cand}_lag'] = df_test[cand].shift(best_lag)
        
        train_clean = df_train[['INIA333', f'{cand}_lag']].dropna()
        if len(train_clean) < 100: continue
        
        X_tr = train_clean[[f'{cand}_lag']]
        y_tr = train_clean['INIA333']
        
        bias = np.mean(y_tr - X_tr[f'{cand}_lag'])
        
        ols = LinearRegression()
        ols.fit(X_tr, y_tr)
        
        huber = HuberRegressor()
        huber.fit(X_tr, y_tr)
        
        df_test['Direct'] = df_test[f'{cand}_lag']
        df_test['Bias'] = df_test[f'{cand}_lag'] + bias
        df_test['OLS'] = np.nan
        df_test['Huber'] = np.nan
        
        mask_valid = df_test[f'{cand}_lag'].notna()
        if mask_valid.sum() > 0:
            X_ts = df_test.loc[mask_valid, [f'{cand}_lag']]
            df_test.loc[mask_valid, 'OLS'] = ols.predict(X_ts)
            df_test.loc[mask_valid, 'Huber'] = huber.predict(X_ts)
            
        for method in ['Direct', 'Bias', 'OLS', 'Huber']:
            name_full = f"{cand}_{method}"
            h_metrics = compute_hourly_metrics(df_test['INIA333'], df_test[method], name_full)
            h_metrics['Lag_Aplicado'] = best_lag
            results_hourly.append(h_metrics)
            
            d_metrics = compute_daily_metrics(df_test, 'INIA333', method, name_full)
            results_daily.append(d_metrics)
            
            c_metrics = compute_chill_metrics(df_test['INIA333'], df_test[method], name_full)
            results_chill.append(c_metrics)
            
    pd.DataFrame(results_hourly).to_csv(OUT_DIR / "auditoria_proxy_inia333_metricas_horarias.csv", index=False)
    pd.DataFrame(results_daily).to_csv(OUT_DIR / "auditoria_proxy_inia333_metricas_diarias.csv", index=False)
    pd.DataFrame(results_chill).to_csv(OUT_DIR / "auditoria_proxy_inia333_frio.csv", index=False)
    print("Phase 2 complete. Validation metrics generated.")

if __name__ == "__main__":
    run_phase_2()
