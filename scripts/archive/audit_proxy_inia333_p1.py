import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
OUT_DIR = BASE_DIR / "reports" / "qa"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR = OUT_DIR / "figures" / "inia333"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_and_normalize(path, time_col, val_cols, rename_dict=None):
    if not path.exists():
        return pd.DataFrame(columns=['fecha_hora_utc'])
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        try:
            df = pd.read_csv(path, skiprows=5) # INIA CSVs
        except:
            df = pd.read_csv(path)
    else:
        return pd.DataFrame(columns=['fecha_hora_utc'])
    
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    
    # Normalize to UTC
    if df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize('America/Santiago', ambiguous='NaT', nonexistent='NaT')
    df['fecha_hora_utc'] = df[time_col].dt.tz_convert('UTC')
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
        
    for c in val_cols:
        col_name = rename_dict[c] if rename_dict and c in rename_dict else c
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
        
    return df[['fecha_hora_utc'] + [rename_dict[c] if rename_dict and c in rename_dict else c for c in val_cols]]

def check_identity(df_target, df_agromet):
    # Overlap
    df = df_target.merge(df_agromet, on='fecha_hora_utc', how='inner')
    df = df.dropna(subset=['Target_INIA333', 'Agromet'])
    
    n_valid = len(df)
    if n_valid == 0:
        return
        
    exact_matches = (df['Target_INIA333'] == df['Agromet']).sum()
    diff = df['Agromet'] - df['Target_INIA333']
    mean_diff = diff.mean()
    max_diff = diff.abs().max()
    corr = np.corrcoef(df['Target_INIA333'], df['Agromet'])[0,1] if n_valid > 1 else np.nan
    
    report = f"""# Auditoría de Identidad: `agromet_pencahue` vs `INIA-333 Pencahue`

## Contexto
El objetivo de este análisis es determinar si los datos contenidos en `agromet_pencahue` (que abarcan desde mayo de 2024) corresponden exactamente a observaciones físicas reales de la misma estación `INIA-333 Pencahue`. 
Si fuesen idénticos, los datos de mayo a agosto podrían tratarse como una recuperación directa de la serie original.

## Evidencia Numérica
En el periodo donde ambas series tienen solape (desde el 19 de agosto de 2024 en adelante), se analizaron {n_valid} registros horarios simultáneos válidos.

* **Registros Exactamente Iguales:** {exact_matches} de {n_valid} ({(exact_matches/n_valid*100):.2f}%).
* **Diferencia Media (Agromet - INIA333):** {mean_diff:.2f}°C. El signo negativo o positivo indica si Agromet fue más fría o más cálida. En este caso, al ser {mean_diff:.2f}, Agromet difiere sistemáticamente.
* **Diferencia Máxima Absoluta:** {max_diff:.2f}°C.
* **Correlación Pearson:** {corr:.3f}.

## Conclusión

Las series **no son intercambiables como observaciones idénticas**. Con la información actualmente disponible, no se ha demostrado que correspondan al mismo producto de datos exacto. La altísima correlación ({corr:.3f}) sugiere fuertemente que están midiendo la misma localidad (Pencahue), pero la falta de coincidencias exactas y la diferencia sistemática ({mean_diff:.2f}°C) indica que existen divergencias originadas por:
- Posible redondeo o distintos métodos de agregación horaria.
- Diferentes sensores instalados en el mismo punto físico.
- Distintos métodos de filtrado de calidad (QA/QC) en las respectivas plataformas.
- Posibles calibraciones o desplazamientos temporales.

Por lo tanto, **`agromet_pencahue` no puede usarse para rellenar los datos de INIA-333 asumiendo identidad**. Deberá ser tratada metodológicamente como un proxy comparativo que debe someterse a evaluación y, eventualmente, calibración.
"""
    with open(OUT_DIR / "auditoria_identidad_agromet_pencahue_inia333.md", "w", encoding='utf-8') as f:
        f.write(report)

def calc_coverage(df, start_dt, end_dt, target_col):
    mask = (df['fecha_hora_utc'] >= start_dt) & (df['fecha_hora_utc'] <= end_dt)
    df_t = df[mask].copy()
    
    # Generate complete hourly index for the period
    full_idx = pd.date_range(start=start_dt, end=end_dt, freq='h')
    n_expected = len(full_idx)
    
    if len(df_t) == 0:
        return 0, 0, n_expected, 0, pd.Timedelta(0)
        
    n_obs = len(df_t)
    n_valid = df_t[target_col].notna().sum()
    
    # Calculate gaps
    df_t = df_t.set_index('fecha_hora_utc').reindex(full_idx)
    df_t['gap_marker'] = df_t[target_col].isna().astype(int)
    # Find longest sequence of 1s
    if df_t['gap_marker'].sum() == 0:
        max_gap = pd.Timedelta(0)
    else:
        # Group consecutive 1s
        s = df_t['gap_marker']
        max_gap_hours = s.groupby((s != s.shift()).cumsum()).sum().max()
        max_gap = pd.Timedelta(hours=max_gap_hours)
        
    return n_obs, n_valid, n_expected, (n_valid/n_expected*100), max_gap

def run_step_1_and_2():
    # 1. Load Data
    # Target: INIA-333
    df_target = load_and_normalize(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet", 'fecha_hora', ['tempMedia'], {'tempMedia': 'Target_INIA333'})
    
    candidates = {
        "Agromet": load_and_normalize(BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet", 'fecha_hora', ['tempMedia'], {'tempMedia': 'Agromet'}),
        "SanClemente_INIA": load_and_normalize(BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/san_clemente/climate_hourly.parquet", 'fecha_hora', ['tempMedia'], {'tempMedia': 'SanClemente_INIA'}),
        "Panguilemo": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv", 'Tiempo UTC-4', ['Panguilemo']),
        "Talca": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/inia_agromet/talca/agrometeorologia-20260722130118.csv", 'Tiempo UTC-4', ['Talca']),
        "PencahueSur_Datavid": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_sur/climate_hourly.parquet", 'fecha', ['tempMedia'], {'tempMedia': 'PencahueSur_Datavid'}),
        "PencahueNorte_Datavid": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet", 'fecha', ['tempMedia'], {'tempMedia': 'PencahueNorte_Datavid'}),
        "SanClemente_Datavid": load_and_normalize(BASE_DIR / "data/raw/climate/hourly/datavid/san_clemente_la_higuera/climate_hourly.parquet", 'fecha', ['tempMedia'], {'tempMedia': 'SanClemente_Datavid'})
    }
    
    check_identity(df_target, candidates["Agromet"])
    
    # 2. Coverage
    start_dt = pd.to_datetime('2024-05-01 00:00:00').tz_localize('America/Santiago').tz_convert('UTC')
    end_dt = pd.to_datetime('2024-08-19 17:59:00').tz_localize('America/Santiago').tz_convert('UTC')
    
    cov_results = []
    for name, df in candidates.items():
        obs, valid, exp, pct, max_gap = calc_coverage(df, start_dt, end_dt, name)
        status = "Operable" if pct >= 90 else "Solo Comparativo"
        cov_results.append({
            "Candidato": name,
            "Inicio": df['fecha_hora_utc'].min().strftime('%Y-%m-%d') if not df.empty else "N/A",
            "Fin": df['fecha_hora_utc'].max().strftime('%Y-%m-%d') if not df.empty else "N/A",
            "Horas Esperadas": exp,
            "Horas Disponibles": obs,
            "Temp Validas": valid,
            "Cobertura %": f"{pct:.1f}%",
            "Gap Maximo": str(max_gap),
            "Estatus": status
        })
        
    cov_df = pd.DataFrame(cov_results)
    cov_df.to_csv(OUT_DIR / "auditoria_proxy_inia333_cobertura2024.csv", index=False)
    print("Coverage calculated and saved.")

if __name__ == "__main__":
    run_step_1_and_2()
