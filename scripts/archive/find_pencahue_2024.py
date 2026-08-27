import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")

candidates = [
    BASE_DIR / "data/raw/climate/hourly/inia_agromet/lourdes/agrometeorologia-20260527125953.xlsx",
    BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet",
    BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet",
    BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_norte/climate_hourly.parquet",
    BASE_DIR / "data/raw/climate/hourly/datavid/pencahue_sur/climate_hourly.parquet",
    BASE_DIR / "data/raw/climate/hourly/zentra/pencahue/Pencahue(A4100677)-1779288356.xlsx"
]

results = []

for path in candidates:
    if not path.exists():
        continue
    
    file_name = path.name
    try:
        if path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(path)
            # Try to infer time col
            time_cols = [c for c in df.columns if 'fecha' in str(c).lower() or 'tiempo' in str(c).lower() or 'time' in str(c).lower() or 'date' in str(c).lower()]
            temp_cols = [c for c in df.columns if 'temp' in str(c).lower()]
            if not time_cols or not temp_cols:
                # Might need to skip rows
                df = pd.read_excel(path, skiprows=5)
                time_cols = [c for c in df.columns if 'fecha' in str(c).lower() or 'tiempo' in str(c).lower() or 'time' in str(c).lower() or 'date' in str(c).lower()]
                temp_cols = [c for c in df.columns if 'temp' in str(c).lower() or 'pencahue' in str(c).lower() or 'lourdes' in str(c).lower()]
            
            if not time_cols:
                results.append({"archivo": file_name, "estacion": "Unknown", "rango temporal": "N/A", "cobertura 2024 (obs)": "N/A", "observacion": "Could not parse excel"})
                continue
            
            time_col = time_cols[0]
            temp_col = temp_cols[0] if temp_cols else df.columns[1]
            
        elif path.suffix == '.parquet':
            df = pd.read_parquet(path)
            time_cols = [c for c in df.columns if 'fecha' in str(c).lower() or 'tiempo' in str(c).lower() or 'time' in str(c).lower() or 'date' in str(c).lower()]
            temp_cols = [c for c in df.columns if 'temp' in str(c).lower()]
            if not time_cols:
                results.append({"archivo": file_name, "estacion": "Unknown", "rango temporal": "N/A", "cobertura 2024 (obs)": "N/A", "observacion": "Could not parse parquet"})
                continue
            
            time_col = time_cols[0]
            temp_col = temp_cols[0] if temp_cols else df.columns[1]
            
        else:
            continue
            
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col])
        
        start = df[time_col].min()
        end = df[time_col].max()
        
        df_2024 = df[df[time_col].dt.year == 2024]
        
        df_2024[temp_col] = pd.to_numeric(df_2024[temp_col], errors='coerce')
        valid_2024 = df_2024.dropna(subset=[temp_col])
        first_valid_2024 = valid_2024[time_col].min() if not valid_2024.empty else pd.NaT
        
        obs_2024 = len(valid_2024)
        
        estacion = "Unknown"
        if "agrometeorologia" in file_name:
            estacion = str(temp_col)
        elif "datavid" in str(path):
            estacion = path.parent.name
        elif "zentra" in str(path):
            estacion = "Zentra Pencahue"
        elif "agromet" in str(path) or "inia" in str(path):
            estacion = "INIA/Agromet Pencahue"
            
        results.append({
            "archivo": path.parent.name + "/" + file_name,
            "estacion": estacion,
            "rango temporal": f"{start.strftime('%Y-%m-%d')} a {end.strftime('%Y-%m-%d')}",
            "primera_temp_2024": first_valid_2024.strftime('%Y-%m-%d %H:%M') if pd.notnull(first_valid_2024) else "N/A",
            "cobertura 2024 (obs)": obs_2024,
            "observacion": f"Temp col: {temp_col}"
        })
        
    except Exception as e:
        results.append({"archivo": file_name, "estacion": "Error", "rango temporal": "N/A", "cobertura 2024 (obs)": "N/A", "observacion": str(e)})

res_df = pd.DataFrame(results)
print(res_df.to_string(index=False))
