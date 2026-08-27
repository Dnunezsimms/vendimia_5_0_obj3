import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
OUT_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean\reports\qa")
FIG_DIR = OUT_DIR / "figures"

def calculate_chill_hours(temp_series, threshold=7.2):
    return (temp_series <= threshold).sum()

def run_chill_validation():
    # Load normalized datasets
    df_lourdes = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_sur/climate_hourly.parquet")
    df_lourdes['fecha_hora_utc'] = pd.to_datetime(df_lourdes['fecha']).dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    df_lourdes = df_lourdes.rename(columns={'tempMedia': 'Target'})
    df_lourdes['Target'] = pd.to_numeric(df_lourdes['Target'], errors='coerce')

    df_pagro = pd.read_parquet(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet")
    df_pagro['fecha_hora_utc'] = pd.to_datetime(df_pagro['fecha_hora']).dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    df_pagro = df_pagro.rename(columns={'tempMedia': 'Pencahue_Agromet'})
    df_pagro['Pencahue_Agromet'] = pd.to_numeric(df_pagro['Pencahue_Agromet'], errors='coerce')

    csv_path = BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv"
    df_csv = pd.read_csv(csv_path, skiprows=5)
    df_csv['fecha_hora_utc'] = pd.to_datetime(df_csv["Tiempo UTC-4"], format="%d-%m-%Y %H:%M", errors="coerce").dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    df_csv = df_csv.dropna(subset=['fecha_hora_utc'])
    df_csv["Panguilemo"] = pd.to_numeric(df_csv["Panguilemo"], errors='coerce')

    df_sc = pd.read_parquet(BASE_DIR / "data/raw/climate/hourly/datavid/san_clemente_la_higuera/climate_hourly.parquet")
    df_sc['fecha_hora_utc'] = pd.to_datetime(df_sc['fecha']).dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    df_sc = df_sc.rename(columns={'tempMedia': 'San_Clemente'})
    df_sc['San_Clemente'] = pd.to_numeric(df_sc['San_Clemente'], errors='coerce')

    df_merged = df_lourdes[['fecha_hora_utc', 'Target']].merge(df_pagro[['fecha_hora_utc', 'Pencahue_Agromet']], on='fecha_hora_utc', how='inner')
    df_merged = df_merged.merge(df_csv[['fecha_hora_utc', 'Panguilemo']], on='fecha_hora_utc', how='inner')
    df_merged = df_merged.merge(df_sc[['fecha_hora_utc', 'San_Clemente']], on='fecha_hora_utc', how='inner')

    df_merged = df_merged[df_merged['fecha_hora_utc'] >= pd.to_datetime('2025-05-01').tz_localize('UTC')]
    
    mask_june = (df_merged['fecha_hora_utc'].dt.month == 6) & (df_merged['fecha_hora_utc'].dt.year == 2025)
    
    train_df = df_merged[~mask_june].dropna()
    test_df = df_merged[mask_june].dropna()
    
    if len(test_df) == 0:
        print("No test data available for June 2025.")
        return
        
    true_chill = calculate_chill_hours(test_df['Target'])
    
    results = []
    
    for cand in ['Pencahue_Agromet', 'Panguilemo', 'San_Clemente']:
        chill_direct = calculate_chill_hours(test_df[cand])
        
        lr = LinearRegression()
        lr.fit(train_df[[cand]], train_df['Target'])
        pred_lr = lr.predict(test_df[[cand]])
        chill_lr = calculate_chill_hours(pd.Series(pred_lr))
        
        bias = np.mean(train_df['Target'] - train_df[cand])
        pred_bias = test_df[cand] + bias
        chill_bias = calculate_chill_hours(pred_bias)
        
        results.append({
            "Candidate": cand,
            "True_Chill": true_chill,
            "Direct_Chill": chill_direct,
            "LR_Chill": chill_lr,
            "Bias_Chill": chill_bias,
            "Direct_Err_%": (chill_direct - true_chill)/true_chill * 100 if true_chill else np.nan,
            "LR_Err_%": (chill_lr - true_chill)/true_chill * 100 if true_chill else np.nan,
            "Bias_Err_%": (chill_bias - true_chill)/true_chill * 100 if true_chill else np.nan
        })
        
        plt.figure(figsize=(15,5))
        test_week = test_df.head(168)
        plt.plot(test_week['fecha_hora_utc'], test_week['Target'], label='Lourdes (Real)', color='black', linewidth=2)
        plt.plot(test_week['fecha_hora_utc'], test_week[cand], label=f'{cand} (Directo)', alpha=0.7)
        plt.plot(test_week['fecha_hora_utc'], pred_lr[:len(test_week)], label=f'{cand} (Corregido LR)', linestyle='--')
        plt.title(f"Reconstrucción de Hueco Simulado (1era Sem. Junio 2025) - {cand}")
        plt.legend()
        plt.savefig(FIG_DIR / f"gap_sim_ts_{cand}.png")
        plt.close()

    pd.DataFrame(results).to_csv(OUT_DIR / "auditoria_proxy_lourdes_chill_eval.csv", index=False)
    print("Chill Validation Completed.")

if __name__ == "__main__":
    run_chill_validation()
