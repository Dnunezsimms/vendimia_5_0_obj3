import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")
OUT_DIR = BASE_DIR / "reports" / "qa"

def calc_chill_metrics(temp_series):
    hf = (temp_series <= 7.2).sum()
    
    utah = pd.cut(temp_series, bins=[-np.inf, 1.4, 2.4, 9.1, 12.4, 15.9, 18.0, np.inf], 
                  labels=[0, 0.5, 1.0, 0.5, 0, -0.5, -1.0]).astype(float).sum()
    
    return hf, utah, np.nan

def main():
    pheno_path = BASE_DIR / "data" / "processed" / "phenology_climate" / "consolidado_fenologia_ELP_MODELABLE_FULL_v1.csv"
    if pheno_path.exists():
        ph = pd.read_csv(pheno_path)
    else:
        print(f"Warning: {pheno_path} not found.")
        ph = pd.DataFrame()
    
    if not ph.empty:
        ph['fecha_brotacion_ELP4'] = pd.to_datetime(ph['fecha_brotacion_ELP4'], errors='coerce')
        ph = ph.dropna(subset=['fecha_brotacion_ELP4'])
        
        ph['invierno_year'] = ph['Temporada'].str.extract(r'^(\d{4})').astype(float)
        ph['inicio_frio'] = pd.to_datetime(ph['invierno_year'].astype(int).astype(str) + '-05-01')
        ph['fin_frio'] = ph['fecha_brotacion_ELP4']
    
    stations = {
        'INIA-333 (Lourdes)': BASE_DIR / "data" / "processed" / "climate" / "hourly" / "inia333_reconstructed" / "climate_hourly_inia333_v1.parquet",
        'Pencahue Sur Datavid': BASE_DIR / "data" / "processed" / "climate" / "hourly" / "pencahue_sur_datavid" / "climate_hourly.parquet",
        'San Clemente Datavid': BASE_DIR / "data" / "processed" / "climate" / "hourly" / "san_clemente_datavid" / "climate_hourly.parquet"
    }
    
    cov_rows = []
    ind_rows = []
    
    for st_name, st_path in stations.items():
        if not st_path.exists(): continue
        
        df = pd.read_parquet(st_path)
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        if df['fecha_hora'].dt.tz is None:
            df['fecha_hora'] = df['fecha_hora'].dt.tz_localize('UTC')
            
        df = df.set_index('fecha_hora').sort_index()
        
        for y in [2024, 2025]:
            s_date = pd.to_datetime(f"{y}-05-01").tz_localize('America/Santiago').tz_convert('UTC')
            e_date = pd.to_datetime(f"{y}-09-30").tz_localize('America/Santiago').tz_convert('UTC')
            
            mask = (df.index >= s_date) & (df.index <= e_date)
            w_df = df[mask]
            
            total_h = int((e_date - s_date).total_seconds() / 3600) + 1
            obs_h = w_df['is_observed'].sum() if 'is_observed' in w_df.columns else w_df['tempMedia'].notna().sum()
            rec_h = w_df['is_reconstructed'].sum() if 'is_reconstructed' in w_df.columns else 0
            
            cov_rows.append({
                'estacion': st_name,
                'invierno': y,
                'inicio_teorico': s_date.date(),
                'fin_teorico': e_date.date(),
                'total_esperado': total_h,
                'observado': obs_h,
                'reconstruido': rec_h,
                'faltante': total_h - obs_h - rec_h,
                'calidad': 'Apta con reconstruccion' if rec_h > 0 else ('Apta' if (obs_h/total_h)>0.95 else 'No apta')
            })
            
        if not ph.empty:
            if 'INIA' in st_name: map_fundos = ['Lourdes']
            elif 'Pencahue' in st_name: map_fundos = ['Pencahue Sur']
            elif 'Clemente' in st_name: map_fundos = ['San Clemente']
            else: map_fundos = []
            
            ph_f = ph[ph['Fundo'].isin(map_fundos)]
            
            for _, row in ph_f.iterrows():
                s = row['inicio_frio'].tz_localize('America/Santiago').tz_convert('UTC')
                e = row['fin_frio'].tz_localize('America/Santiago').tz_convert('UTC')
                
                mask = (df.index >= s) & (df.index <= e)
                w_df = df[mask]
                
                if len(w_df) == 0: continue
                
                hf, utah, dyn = calc_chill_metrics(w_df['tempMedia'])
                
                ind_rows.append({
                    'fundo': row['Fundo'],
                    'estacion_climatica': st_name,
                    'temporada': row['Temporada'],
                    'variedad': row['Variedad'],
                    'inicio_frio': s.date(),
                    'fin_frio_brotacion': e.date(),
                    'horas_frio_7.2': hf,
                    'utah_units': utah,
                    'cobertura_obs': w_df['is_observed'].sum() if 'is_observed' in w_df.columns else w_df['tempMedia'].notna().sum(),
                    'cobertura_rec': w_df['is_reconstructed'].sum() if 'is_reconstructed' in w_df.columns else 0
                })
    
    pd.DataFrame(cov_rows).to_csv(OUT_DIR / "cobertura_frio_por_estacion_temporada.csv", index=False)
    pd.DataFrame(ind_rows).to_csv(OUT_DIR / "indicadores_frio_por_fundo_temporada.csv", index=False)
    
    scripts_inv = [
        {'script': 'audit_temporal_gaps.py', 'rol': 'Auditoría inicial de huecos', 'estado': 'Inactivo/Incompleto'},
        {'script': 'build_gdd_biofix_timeseries.py', 'rol': 'Genera predictores para RF', 'estado': 'GDD y Biofix OK, Frío NO IMPLEMENTADO'}
    ]
    pd.DataFrame(scripts_inv).to_csv(OUT_DIR / "inventario_scripts_modelacion_frio.csv", index=False)
    
    # Calculate Uncertainty of INIA333 specifically
    df_inia = pd.read_parquet(BASE_DIR / "data" / "processed" / "climate" / "hourly" / "inia333_reconstructed" / "climate_hourly_inia333_v1.parquet")
    df_inia['fecha_hora'] = pd.to_datetime(df_inia['fecha_hora'])
    df_inia = df_inia.set_index('fecha_hora').sort_index()
    mask24 = (df_inia.index >= pd.to_datetime('2024-05-01').tz_localize('UTC')) & (df_inia.index <= pd.to_datetime('2024-08-31 23:59:59').tz_localize('UTC'))
    
    w_df = df_inia[mask24]
    
    # Central chill
    hf_central = (w_df['tempMedia'] <= 7.2).sum()
    
    # Uncertainty chill
    hf_upper = (np.where(w_df['is_reconstructed'], w_df['prediction_lower'] <= 7.2, w_df['tempMedia'] <= 7.2)).sum()
    hf_lower = (np.where(w_df['is_reconstructed'], w_df['prediction_upper'] <= 7.2, w_df['tempMedia'] <= 7.2)).sum()
    
    uncert = [{
        'metrica': 'Horas_Frio_7.2',
        'estacion': 'INIA-333 (Lourdes)',
        'periodo': 'Invierno 2024',
        'estimacion_central': hf_central,
        'intervalo_inferior_90': hf_lower,
        'intervalo_superior_90': hf_upper,
        'amplitud_incertidumbre': hf_upper - hf_lower,
        'proporcion_error_max': (hf_upper - hf_central) / hf_central if hf_central > 0 else 0
    }]
    pd.DataFrame(uncert).to_csv(OUT_DIR / "incertidumbre_frio_inia333.csv", index=False)
    
    print("Audit Phase 2 data extraction complete.")

if __name__ == "__main__":
    main()
