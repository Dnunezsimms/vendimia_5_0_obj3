import os
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def build_inventory():
    root_dir = Path(__file__).resolve().parent.parent
    raw_dir = root_dir / "data/raw/climate/hourly/datavid"
    
    # We will also map reconstructions. Let's hardcode the known one for Pencahue INIA-333 for now,
    # or scan `data/processed/climate/hourly/inia333_reconstructed`.
    # Wait, the observed datavid folder has 48 fundos.
    # Are we reconstructing all 48 fundos? The user says "Para cada fundo".
    # We will look for reconstructions in `data/processed/climate/hourly/reconstructed/<fundo>/`
    # Let's map what we have.
    
    fundos = [d.name for d in raw_dir.iterdir() if d.is_dir()]
    
    records = []
    
    for fundo in fundos:
        obs_file = raw_dir / fundo / "climate_hourly.parquet"
        rec_file = root_dir / f"data/processed/climate/hourly/reconstructed/{fundo}/climate_hourly.parquet"
        
        # Exception for Pencahue which we did as INIA-333
        if fundo == "pencahue_sur":
            # Wait, the user said the target station for Pencahue was INIA-333.
            # But the datavid folder has "pencahue_sur" and "pencahue_norte".
            # Which one gets the inia333 reconstruction?
            # Let's just map exactly what files exist.
            pass
            
        record = {
            "fundo": fundo,
            "archivo_observado": str(obs_file.relative_to(root_dir)) if obs_file.exists() else None,
            "archivo_reconstruido": str(rec_file.relative_to(root_dir)) if rec_file.exists() else None,
            "primera_fecha_observada": None,
            "ultima_fecha_observada": None,
            "primera_fecha_reconstruida": None,
            "ultima_fecha_reconstruida": None,
            "frecuencia_detectada": None,
            "unidad": "Celsius",
            "zona_horaria": "America/Santiago",
            "numero_registros": 0,
            "duplicados": 0,
            "porcentaje_nan": 100.0,
            "estado_disponibilidad": "No disponible"
        }
        
        # Analizar observado
        if obs_file.exists():
            df_obs = pd.read_parquet(obs_file)
            
            # Check schema
            time_col = None
            if "fecha_hora" in df_obs.columns:
                time_col = "fecha_hora"
            elif "time" in df_obs.columns:
                time_col = "time"
                
            temp_col = None
            if "tempMedia" in df_obs.columns:
                temp_col = "tempMedia"
            elif "temp_avg" in df_obs.columns:
                temp_col = "temp_avg"
            
            if time_col and temp_col:
                df_obs[time_col] = pd.to_datetime(df_obs[time_col])
                df_obs = df_obs.set_index(time_col)
                df_obs = df_obs.sort_index()
                
                # Check timezone
                if df_obs.index.tz is None:
                    # tz-naive
                    tz_str = "None (naive)"
                else:
                    tz_str = str(df_obs.index.tz)
                    
                record["zona_horaria"] = tz_str
                record["primera_fecha_observada"] = df_obs.index.min().isoformat()
                record["ultima_fecha_observada"] = df_obs.index.max().isoformat()
                record["numero_registros"] = len(df_obs)
                record["duplicados"] = df_obs.index.duplicated().sum()
                
                # Infer freq
                if len(df_obs) > 2:
                    diffs = df_obs.index.to_series().diff()
                    record["frecuencia_detectada"] = str(diffs.mode()[0])
                
                nan_count = df_obs[temp_col].isna().sum()
                record["porcentaje_nan"] = round((nan_count / len(df_obs)) * 100, 2)
                
                record["estado_disponibilidad"] = "Observado"
                
        # We will do the same for reconstructed if it exists
        # ...
        records.append(record)
        
    df_inv = pd.DataFrame(records)
    
    out_dir = root_dir / "reports/qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_inv.to_csv(out_dir / "inventario_fuentes_climaticas.csv", index=False)
    logging.info(f"Inventory saved to {out_dir / 'inventario_fuentes_climaticas.csv'}")

if __name__ == '__main__':
    build_inventory()
