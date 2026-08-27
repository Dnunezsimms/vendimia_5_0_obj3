import pandas as pd
import numpy as np
from pathlib import Path

def audit_temporal_gaps():
    root_dir = Path(__file__).resolve().parent.parent.parent
    raw_hourly_dir = root_dir / "data" / "raw" / "climate" / "hourly"
    
    # The fundos of interest for phenology (based on chill_dynamic.py and Obj3 scope)
    fundos_interes = [
        "san_vicente_idahue", "cauquenes_keule", "ovalle_quebrada_seca", 
        "lolol_nilahue", "navidad_ucuquer", "lourdes", "los_acacios"
    ]
    
    results = []
    
    for network_dir in raw_hourly_dir.iterdir():
        if not network_dir.is_dir():
            continue
            
        for station_dir in network_dir.iterdir():
            if not station_dir.is_dir():
                continue
                
            # Check if this station matches our fundos of interest
            if not any(fundo in station_dir.name.lower() for fundo in fundos_interes):
                continue
                
            parquet_path = station_dir / "climate_hourly.parquet"
            if not parquet_path.exists():
                print(f"No parquet data for {station_dir.name}")
                continue
                
            try:
                df = pd.read_parquet(parquet_path)
                
                # Identify time and temp columns
                time_col = next((c for c in df.columns if 'time' in c.lower() or 'fecha' in c.lower() or 'date' in c.lower()), None)
                temp_col = next((c for c in df.columns if 'temp' in c.lower() and 'min' not in c.lower() and 'max' not in c.lower()), None)
                
                if not time_col or not temp_col:
                    continue
                    
                df[time_col] = pd.to_datetime(df[time_col])
                df = df.set_index(time_col).sort_index()
                
                # Filter for the relevant winter/spring window for Chill Portions (May 1st to Nov 1st) for 2024 and 2025
                for year in [2024, 2025]:
                    start_date = f"{year}-05-01"
                    end_date = f"{year}-11-01"
                    
                    df_season = df[(df.index >= start_date) & (df.index <= end_date)]
                    
                    if df_season.empty:
                        results.append({
                            "Fundo": station_dir.name,
                            "Temporada": year,
                            "Tipo_Gap": "Temporada Completa Ausente",
                            "Inicio_Gap": start_date,
                            "Fin_Gap": end_date,
                            "Horas_Perdidas": pd.date_range(start_date, end_date, freq='h').size
                        })
                        continue
                        
                    # Reindex to strict hourly freq to find missing hours
                    full_range = pd.date_range(start=start_date, end=end_date, freq='h')
                    df_reindexed = df_season.reindex(full_range)
                    
                    is_nan = df_reindexed[temp_col].isna()
                    
                    if not is_nan.any():
                        continue
                        
                    # Find consecutive gaps > 3 hours
                    gap_mask = is_nan.copy()
                    
                    # Group consecutive NaNs
                    gap_groups = (~gap_mask).cumsum()[gap_mask]
                    
                    for group_id, group_df in gap_groups.groupby(gap_groups):
                        gap_size = len(group_df)
                        if gap_size > 3:
                            gap_dates = group_df.index
                            results.append({
                                "Fundo": station_dir.name,
                                "Temporada": year,
                                "Tipo_Gap": "VacÃ­o Prolongado (>3h)",
                                "Inicio_Gap": gap_dates.min().strftime('%Y-%m-%d %H:%M'),
                                "Fin_Gap": gap_dates.max().strftime('%Y-%m-%d %H:%M'),
                                "Horas_Perdidas": gap_size
                            })
                            
            except Exception as e:
                print(f"Error processing {station_dir.name}: {e}")
                
    report_df = pd.DataFrame(results)
    if not report_df.empty:
        # Sort by Fundo, then Date
        report_df = report_df.sort_values(by=["Fundo", "Inicio_Gap"])
        output_path = root_dir / "data" / "processed" / "climate" / "audit_temporal_gaps_frio.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_df.to_csv(output_path, index=False)
        print("====== AUDITORÃA DE GAPS TEMPORALES PARA FRÃO ======")
        print(f"Reporte completo guardado en: {output_path}\n")
        print(report_df.to_string(index=False))
    else:
        print("====== AUDITORÃA DE GAPS TEMPORALES PARA FRÃO ======")
        print("Â¡Excelentes noticias! No hay gaps > 3 horas en las ventanas de invierno (mayo-nov) para los fundos de interÃ©s.")

if __name__ == "__main__":
    audit_temporal_gaps()

