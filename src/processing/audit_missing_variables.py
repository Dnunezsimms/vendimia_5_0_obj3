import pandas as pd
import numpy as np
from pathlib import Path

def audit_variables():
    root_dir = Path(__file__).resolve().parent.parent.parent
    raw_hourly_dir = root_dir / "data" / "raw" / "climate" / "hourly"
    
    results = []
    
    # Expected core variables
    target_vars = {
        'TempMedia': ['tempmedia', 'temp_promedio', 'temp_mean', 'temperatura', 'air_temp'],
        'Precipitacion': ['precipitacion', 'lluvia', 'rain', 'precip'],
        'HumedadRelativa': ['humedadrelativa', 'hr', 'rh', 'relative_humidity'],
        'Radiacion': ['radiacion', 'rad_solar', 'solar_rad'],
        'Viento': ['velocidadpromedioviento', 'viento', 'wind_speed', 'vel_viento'],
        'HumedadSuelo': ['swc', 'soil_moisture', 'humedad_suelo', 'soil_water']
    }
    
    for network_dir in raw_hourly_dir.iterdir():
        if not network_dir.is_dir():
            continue
            
        for station_dir in network_dir.iterdir():
            if not station_dir.is_dir():
                continue
                
            parquet_path = station_dir / "climate_hourly.parquet"
            if not parquet_path.exists():
                continue
                
            try:
                df = pd.read_parquet(parquet_path)
                row_info = {
                    "Red": network_dir.name,
                    "Estacion_Fundo": station_dir.name,
                    "Total_Registros": len(df)
                }
                
                # Check for each target variable if it exists and what % is valid
                for var_name, possible_cols in target_vars.items():
                    # Find the column in df
                    col = next((c for c in df.columns if str(c).lower() in possible_cols), None)
                    
                    if col is None:
                        row_info[var_name] = "Falta Columna"
                    else:
                        valid_pct = 100 * df[col].notna().mean()
                        if valid_pct == 0:
                            row_info[var_name] = "0% (Todo NaN)"
                        elif valid_pct < 100:
                            row_info[var_name] = f"{valid_pct:.1f}% (Incompleto)"
                        else:
                            row_info[var_name] = "100% OK"
                            
                results.append(row_info)
            except Exception as e:
                print(f"Error processing {station_dir.name}: {e}")
                
    report_df = pd.DataFrame(results)
    if not report_df.empty:
        output_path = root_dir / "data" / "processed" / "climate" / "audit_variables_faltantes.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_df.to_csv(output_path, index=False)
        print("====== MATRIZ DE AUDITORÃA DE VARIABLES ======")
        print(f"Se procesaron {len(report_df)} estaciones.")
        print(f"Reporte completo guardado en: {output_path}\n")
        
        # Display stations with missing critical columns
        missing_temp = report_df[report_df['TempMedia'].str.contains('Falta Columna|^0%', regex=True)]
        missing_rad = report_df[report_df['Radiacion'].str.contains('Falta Columna|^0%', regex=True)]
        missing_suelo = report_df[report_df['HumedadSuelo'].str.contains('Falta Columna|^0%', regex=True)]
        
        print("--- ESTACIONES SIN TEMPERATURA ---")
        if not missing_temp.empty:
            print(missing_temp[['Red', 'Estacion_Fundo']].to_string(index=False))
        else:
            print("Ninguna. Todas tienen temperatura.")
            
        print("\n--- ESTACIONES SIN RADIACIÃ“N SOLAR ---")
        if not missing_rad.empty:
            print(missing_rad[['Red', 'Estacion_Fundo']].head(10).to_string(index=False))
            if len(missing_rad) > 10: print(f"...y {len(missing_rad)-10} mÃ¡s.")
        else:
            print("Ninguna. Todas tienen radiaciÃ³n.")
            
        print("\n--- ESTACIONES SIN HUMEDAD DE SUELO ---")
        if not missing_suelo.empty:
            print(f"Hay {len(missing_suelo)} estaciones sin sensor de Humedad de Suelo (incluyendo Datavid/INIA standard).")
        
    else:
        print("No valid data found.")

if __name__ == "__main__":
    audit_variables()

