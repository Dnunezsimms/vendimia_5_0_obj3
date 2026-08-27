import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy.stats import pearsonr, spearmanr
from pathlib import Path
import os
import pytz
from datetime import timedelta

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
OUT_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean\reports\qa")
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def get_metadata():
    return pd.DataFrame([
        {"nombre_usado": "Pencahue INIA (Antiguo Base)", "red": "INIA", "estacion_fisica": "Pencahue", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "tempMedia", "unidad": "°C", "resolucion": "Horaria", "archivo": "inia_proxy_test/pencahue/climate_hourly.parquet"},
        {"nombre_usado": "Lourdes (Pencahue Sur Datavid)", "red": "Datavid", "estacion_fisica": "Pencahue Sur", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "tempMedia", "unidad": "°C", "resolucion": "Horaria", "archivo": "datavid/pencahue_sur/climate_hourly.parquet"},
        {"nombre_usado": "San Clemente INIA", "red": "INIA", "estacion_fisica": "San Clemente", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "tempMedia", "unidad": "°C", "resolucion": "Horaria", "archivo": "inia_proxy_test/san_clemente/climate_hourly.parquet"},
        {"nombre_usado": "San Clemente Datavid", "red": "Datavid", "estacion_fisica": "San Clemente La Higuera", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "tempMedia", "unidad": "°C", "resolucion": "Horaria", "archivo": "datavid/san_clemente_la_higuera/climate_hourly.parquet"},
        {"nombre_usado": "Pencahue Agromet", "red": "Agromet", "estacion_fisica": "Pencahue", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "tempMedia", "unidad": "°C", "resolucion": "Horaria", "archivo": "agromet_pencahue/climate_hourly.parquet"},
        {"nombre_usado": "Panguilemo", "red": "INIA (Descarga CSV)", "estacion_fisica": "Panguilemo", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "Panguilemo", "unidad": "°C", "resolucion": "Horaria", "archivo": "inia_agromet/talca/agrometeorologia-20260722130118.csv"},
        {"nombre_usado": "Talca (Arauco)", "red": "INIA (Descarga CSV)", "estacion_fisica": "Talca", "coordenadas": "ND", "altitud": "ND", "sensor": "ND", "variable_original": "Talca", "unidad": "°C", "resolucion": "Horaria", "archivo": "inia_agromet/talca/agrometeorologia-20260722130118.csv"}
    ])

def normalize_time(df, time_col, tz_origin='America/Santiago'):
    df = df.copy()
    if df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize(tz_origin, ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[time_col].dt.tz_convert('UTC')
    df['fecha_hora_local'] = df['fecha_hora_utc'].dt.tz_convert('America/Santiago')
    return df

def calc_coverage(df, time_col, val_col, name, start_target, end_target):
    total = len(df)
    valid = df[val_col].notna().sum()
    
    # Filter for target period
    mask_target = (df[time_col] >= pd.to_datetime(start_target).tz_localize('UTC')) & (df[time_col] <= pd.to_datetime(end_target).tz_localize('UTC'))
    df_t = df[mask_target]
    pot_target = len(df_t)
    valid_target = df_t[val_col].notna().sum()
    
    # Find gaps
    df_sorted = df.sort_values(time_col).copy()
    df_sorted['gap'] = df_sorted[time_col].diff()
    gaps = df_sorted[df_sorted[val_col].isna()]['gap']
    
    return {
        "Estacion": name,
        "Total_Obs_File": total,
        "Validas_File": valid,
        "Obs_Periodo_Objetivo": pot_target,
        "Validas_Periodo_Objetivo": valid_target,
        "Gaps_Mayores_6h": sum(gaps > timedelta(hours=6)),
        "Gaps_Mayores_24h": sum(gaps > timedelta(hours=24))
    }

def compute_detailed_metrics(y_true, y_pred, name):
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    y_t = y_true[mask]
    y_p = y_pred[mask]
    n = len(y_t)
    
    if n < 2:
        return {"Name": name, "N": n, "MAE": np.nan, "RMSE": np.nan, "Bias": np.nan, "R2": np.nan, "Pearson": np.nan}
        
    mae = mean_absolute_error(y_t, y_p)
    rmse = np.sqrt(mean_squared_error(y_t, y_p))
    bias = np.mean(y_p - y_t)
    r2 = r2_score(y_t, y_p)
    pearson = pearsonr(y_t, y_p)[0]
    
    return {"Name": name, "N": n, "MAE": mae, "RMSE": rmse, "Bias": bias, "R2": r2, "Pearson": pearson}

def run_audit():
    print("Generating Metadata...")
    meta_df = get_metadata()
    meta_df.to_csv(OUT_DIR / "auditoria_proxy_lourdes_metadata_fuentes.csv", index=False)
    
    # Load Datasets
    print("Loading datasets...")
    # 1. Pencahue INIA
    df_pinia = pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet")
    df_pinia['fecha_hora'] = pd.to_datetime(df_pinia['fecha_hora'])
    df_pinia = normalize_time(df_pinia, 'fecha_hora')
    
    # 2. Pencahue Sur Datavid
    df_pdatavid = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_sur/climate_hourly.parquet")
    df_pdatavid['fecha_hora'] = pd.to_datetime(df_pdatavid['fecha'])
    df_pdatavid['tempMedia'] = pd.to_numeric(df_pdatavid['tempMedia'], errors='coerce')
    df_pdatavid = normalize_time(df_pdatavid, 'fecha_hora')
    
    # 3. San Clemente INIA
    df_scinia = pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/san_clemente/climate_hourly.parquet")
    df_scinia['fecha_hora'] = pd.to_datetime(df_scinia['fecha_hora'])
    df_scinia = normalize_time(df_scinia, 'fecha_hora')
    
    # 4. San Clemente Datavid
    df_scdatavid = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/san_clemente_la_higuera/climate_hourly.parquet")
    df_scdatavid['fecha_hora'] = pd.to_datetime(df_scdatavid['fecha'])
    df_scdatavid['tempMedia'] = pd.to_numeric(df_scdatavid['tempMedia'], errors='coerce')
    df_scdatavid = normalize_time(df_scdatavid, 'fecha_hora')
    
    # 5. Pencahue Agromet
    df_pagro = pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet")
    df_pagro['fecha_hora'] = pd.to_datetime(df_pagro['fecha_hora'])
    df_pagro = normalize_time(df_pagro, 'fecha_hora')
    
    # 6. CSV Panguilemo / Talca
    csv_path = BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv"
    df_csv = pd.read_csv(csv_path, skiprows=5)
    df_csv['fecha_hora'] = pd.to_datetime(df_csv["Tiempo UTC-4"], format="%d-%m-%Y %H:%M", errors="coerce")
    df_csv = df_csv.dropna(subset=['fecha_hora'])
    df_csv = normalize_time(df_csv, 'fecha_hora')
    df_csv["Panguilemo"] = pd.to_numeric(df_csv["Panguilemo"], errors='coerce')
    df_csv["Talca"] = pd.to_numeric(df_csv["Talca"], errors='coerce')

    # Calculate Coverage for Winter 2024 (May 1 2024 to Aug 31 2024)
    print("Calculating Coverage...")
    start_target = '2024-05-01'
    end_target = '2024-08-31'
    cov = []
    cov.append(calc_coverage(df_pinia, 'fecha_hora_utc', 'tempMedia', 'Pencahue INIA', start_target, end_target))
    cov.append(calc_coverage(df_pdatavid, 'fecha_hora_utc', 'tempMedia', 'Pencahue Sur Datavid', start_target, end_target))
    cov.append(calc_coverage(df_scinia, 'fecha_hora_utc', 'tempMedia', 'San Clemente INIA', start_target, end_target))
    cov.append(calc_coverage(df_scdatavid, 'fecha_hora_utc', 'tempMedia', 'San Clemente Datavid', start_target, end_target))
    cov.append(calc_coverage(df_pagro, 'fecha_hora_utc', 'tempMedia', 'Pencahue Agromet', start_target, end_target))
    cov.append(calc_coverage(df_csv, 'fecha_hora_utc', 'Panguilemo', 'Panguilemo', start_target, end_target))
    cov.append(calc_coverage(df_csv, 'fecha_hora_utc', 'Talca', 'Talca', start_target, end_target))
    pd.DataFrame(cov).to_csv(OUT_DIR / "auditoria_proxy_lourdes_cobertura.csv", index=False)
    
    print("Merging for Experiment 1 (Old Analysis)...")
    df1 = df_pinia[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Target'})
    df1 = df1.merge(df_scinia[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Cand_SC_INIA'}), on='fecha_hora_utc', how='inner')
    df1 = df1.merge(df_pagro[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Cand_PAgro'}), on='fecha_hora_utc', how='inner')
    
    res1 = []
    res1.append(compute_detailed_metrics(df1['Target'], df1['Cand_SC_INIA'], "Exp1: San Clemente INIA vs Pencahue INIA"))
    res1.append(compute_detailed_metrics(df1['Target'], df1['Cand_PAgro'], "Exp1: Pencahue Agromet vs Pencahue INIA"))
    
    print("Merging for Experiment 2 (New Analysis)...")
    df2 = df_pdatavid[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Target'})
    df2 = df2.merge(df_scdatavid[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Cand_SC_Datavid'}), on='fecha_hora_utc', how='inner')
    df2 = df2.merge(df_pagro[['fecha_hora_utc', 'tempMedia']].rename(columns={'tempMedia': 'Cand_PAgro'}), on='fecha_hora_utc', how='inner')
    df2 = df2.merge(df_csv[['fecha_hora_utc', 'Panguilemo', 'Talca']], on='fecha_hora_utc', how='inner')
    
    res2 = []
    res2.append(compute_detailed_metrics(df2['Target'], df2['Cand_SC_Datavid'], "Exp2: San Clemente Datavid vs Lourdes Datavid"))
    res2.append(compute_detailed_metrics(df2['Target'], df2['Cand_PAgro'], "Exp2: Pencahue Agromet vs Lourdes Datavid"))
    res2.append(compute_detailed_metrics(df2['Target'], df2['Panguilemo'], "Exp2: Panguilemo vs Lourdes Datavid"))
    res2.append(compute_detailed_metrics(df2['Target'], df2['Talca'], "Exp2: Talca vs Lourdes Datavid"))
    
    pd.DataFrame(res1 + res2).to_csv(OUT_DIR / "auditoria_proxy_lourdes_metricas.csv", index=False)
    print("Completed Base Scripts.")

if __name__ == "__main__":
    run_audit()
