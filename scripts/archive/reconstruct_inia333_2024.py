import pandas as pd
import numpy as np
from pathlib import Path
import json
import joblib
import hashlib
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
MODELS_DIR = BASE_DIR / "reports" / "qa" / "models" / "inia333_agromet_huber_v1"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PARQUET = BASE_DIR / "data" / "processed" / "climate" / "hourly" / "inia333_reconstructed" / "climate_hourly_inia333_v1.parquet"
OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def norm_time(df, t_col, v_col, name):
    if df.empty: return pd.DataFrame(columns=['fecha_hora_utc', name])
    df[t_col] = pd.to_datetime(df[t_col], errors='coerce')
    df = df.dropna(subset=[t_col])
    if df[t_col].dt.tz is None:
        df[t_col] = df[t_col].dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[t_col].dt.tz_convert('UTC')
    df[name] = pd.to_numeric(df[v_col], errors='coerce')
    return df[['fecha_hora_utc', name]].drop_duplicates('fecha_hora_utc')

def main():
    inia_path = BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet"
    agro_path = BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet"
    
    hashes = {"inia333": hash_file(inia_path), "agromet": hash_file(agro_path)}
    
    t = norm_time(pd.read_parquet(inia_path), 'fecha_hora', 'tempMedia', 'INIA333')
    a = norm_time(pd.read_parquet(agro_path), 'fecha_hora', 'tempMedia', 'Agromet')
    
    df = t.merge(a, on='fecha_hora_utc', how='outer').sort_values('fecha_hora_utc').set_index('fecha_hora_utc')
    
    s_24 = pd.to_datetime('2024-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_24 = pd.to_datetime('2024-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    s_25 = pd.to_datetime('2025-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    e_25 = pd.to_datetime('2025-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    mask_gap24 = (df.index >= s_24) & (df.index <= e_24)
    mask_test25 = (df.index >= s_25) & (df.index <= e_25)
    
    train_audit_mask = ~mask_gap24 & ~mask_test25
    df_audit_train = df[train_audit_mask]
    
    best_l, best_c = 0, -1
    for l in range(-6, 7):
        s = df_audit_train['Agromet'].shift(l)
        m = df_audit_train['INIA333'].notna() & s.notna()
        if m.sum() > 10:
            corr = np.corrcoef(df_audit_train.loc[m, 'INIA333'], s[m])[0,1]
            if corr > best_c: best_c, best_l = corr, l
            
    X_tr_a = df_audit_train[['Agromet']].shift(best_l).dropna()
    y_tr_a = df_audit_train.loc[X_tr_a.index, 'INIA333'].dropna()
    idx_a = X_tr_a.index.intersection(y_tr_a.index)
    X_tr_a, y_tr_a = X_tr_a.loc[idx_a], y_tr_a.loc[idx_a]
    
    model_audit = HuberRegressor().fit(X_tr_a, y_tr_a)
    
    df_test = df[mask_test25]
    X_ts = df_test[['Agromet']].shift(best_l).dropna()
    y_ts = df_test.loc[X_ts.index, 'INIA333'].dropna()
    idx_ts = X_ts.index.intersection(y_ts.index)
    X_ts, y_ts = X_ts.loc[idx_ts], y_ts.loc[idx_ts]
    preds_audit = model_audit.predict(X_ts)
    
    mae_audit = mean_absolute_error(y_ts, preds_audit)
    
    resids = y_ts - preds_audit
    res_df = pd.DataFrame({'resid': resids, 'hour': resids.index.tz_convert('America/Santiago').hour})
    quantiles = res_df.groupby('hour')['resid'].quantile([0.05, 0.95]).unstack()
    
    train_final_mask = ~mask_gap24
    df_final_train = df[train_final_mask]
    X_tr_f = df_final_train[['Agromet']].shift(best_l).dropna()
    y_tr_f = df_final_train.loc[X_tr_f.index, 'INIA333'].dropna()
    idx_f = X_tr_f.index.intersection(y_tr_f.index)
    X_tr_f, y_tr_f = X_tr_f.loc[idx_f], y_tr_f.loc[idx_f]
    
    model_final = HuberRegressor().fit(X_tr_f, y_tr_f)
    
    cons_end = pd.to_datetime('2024-12-31 23:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    train_cons_mask = (df.index > e_24) & (df.index <= cons_end)
    df_cons_train = df[train_cons_mask]
    X_tr_c = df_cons_train[['Agromet']].shift(best_l).dropna()
    y_tr_c = df_cons_train.loc[X_tr_c.index, 'INIA333'].dropna()
    idx_c = X_tr_c.index.intersection(y_tr_c.index)
    X_tr_c, y_tr_c = X_tr_c.loc[idx_c], y_tr_c.loc[idx_c]
    
    model_cons = HuberRegressor().fit(X_tr_c, y_tr_c)
    
    meta = {
        "frozen_architecture": {
            "proxy": "Agromet_Pencahue",
            "target": "INIA_333",
            "model_type": "HuberRegressor",
            "lag": int(best_l)
        },
        "model_1_audit": {
            "description": "Validated model reproducing report metrics",
            "train_n": len(X_tr_a),
            "coef": float(model_audit.coef_[0]),
            "intercept": float(model_audit.intercept_),
            "mae_test_2025": float(mae_audit)
        },
        "model_2_final": {
            "description": "Final model used for reconstruction (retrospective)",
            "train_n": len(X_tr_f),
            "coef": float(model_final.coef_[0]),
            "intercept": float(model_final.intercept_)
        },
        "model_3_conservative": {
            "description": "Trained only on 2024 to avoid future data leakage",
            "train_n": len(X_tr_c),
            "coef": float(model_cons.coef_[0]),
            "intercept": float(model_cons.intercept_)
        }
    }
    with open(MODELS_DIR / "model_metadata.json", "w") as f:
        json.dump(meta, f, indent=4)
        
    with open(MODELS_DIR / "input_hashes.json", "w") as f:
        json.dump(hashes, f, indent=4)
        
    joblib.dump(model_final, MODELS_DIR / "huber_final.joblib")
    
    out_df = df.copy()
    out_df['local_time'] = out_df.index.tz_convert('America/Santiago')
    out_df['hour'] = out_df['local_time'].dt.hour
    
    X_all = out_df[['Agromet']].shift(best_l).fillna(0)
    raw_preds = model_final.predict(X_all)
    out_df['tempMedia_reconstruida'] = np.where(out_df['Agromet'].shift(best_l).notna(), raw_preds, np.nan)
    
    out_df['q05'] = out_df['hour'].map(quantiles[0.05])
    out_df['q95'] = out_df['hour'].map(quantiles[0.95])
    out_df['prediction_lower'] = out_df['tempMedia_reconstruida'] + out_df['q05']
    out_df['prediction_upper'] = out_df['tempMedia_reconstruida'] + out_df['q95']
    
    out_df['tempMedia'] = out_df['INIA333']
    out_df['data_source'] = 'INIA-333'
    out_df['is_observed'] = out_df['INIA333'].notna()
    out_df['is_reconstructed'] = False
    out_df['reconstruction_method'] = pd.Series(dtype='object')
    out_df['model_version'] = pd.Series(dtype='object')
    out_df['quality_flag'] = 'OK'
    
    reconstruct_mask = mask_gap24 & out_df['INIA333'].isna() & out_df['tempMedia_reconstruida'].notna()
    
    out_df.loc[reconstruct_mask, 'tempMedia'] = out_df.loc[reconstruct_mask, 'tempMedia_reconstruida']
    out_df.loc[reconstruct_mask, 'data_source'] = 'agromet_pencahue_calibrated'
    out_df.loc[reconstruct_mask, 'is_observed'] = False
    out_df.loc[reconstruct_mask, 'is_reconstructed'] = True
    out_df.loc[reconstruct_mask, 'reconstruction_method'] = 'HuberRegressor_retrospective'
    out_df.loc[reconstruct_mask, 'model_version'] = 'inia333_agromet_huber_v1'
    
    out_df.loc[~out_df['is_reconstructed'], ['prediction_lower', 'prediction_upper']] = np.nan
    
    missing_mask = out_df['tempMedia'].isna()
    out_df.loc[missing_mask, 'quality_flag'] = 'MISSING'
    out_df.loc[missing_mask, 'data_source'] = np.nan
    out_df.loc[missing_mask, 'is_observed'] = False
    
    out_df = out_df.reset_index().rename(columns={'fecha_hora_utc': 'fecha_hora', 'INIA333': 'tempMedia_original_inia333', 'Agromet': 'tempMedia_proxy_agromet'})
    
    final_cols = [
        'fecha_hora', 'local_time', 'tempMedia', 'tempMedia_original_inia333', 'tempMedia_proxy_agromet', 
        'tempMedia_reconstruida', 'data_source', 'is_observed', 'is_reconstructed', 
        'reconstruction_method', 'model_version', 'prediction_lower', 'prediction_upper', 'quality_flag'
    ]
    
    out_df[final_cols].to_parquet(OUT_PARQUET, index=False)
    out_df[final_cols].to_csv(OUT_PARQUET.with_suffix('.csv'), index=False)
    
    ranges = pd.DataFrame({
        "Model": ["Audit", "Final", "Conservative"],
        "Start": [df_audit_train.index.min(), df_final_train.index.min(), df_cons_train.index.min()],
        "End": [df_audit_train.index.max(), df_final_train.index.max(), df_cons_train.index.max()]
    })
    ranges.to_csv(MODELS_DIR / "training_data_ranges.csv", index=False)
    
    # Also save validation metrics
    pd.DataFrame({"Model": ["Audit"], "MAE_Test25": [mae_audit]}).to_csv(MODELS_DIR / "validation_metrics.csv", index=False)
    
    print(f"Reconstruction complete. Saved to {OUT_PARQUET}")

if __name__ == "__main__":
    main()
