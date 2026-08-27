import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_and_normalize(file_path, tz="America/Santiago"):
    """Carga y normaliza un archivo parquet horario."""
    df = pd.read_parquet(file_path)
    
    time_col = "fecha_hora" if "fecha_hora" in df.columns else (
        "fecha" if "fecha" in df.columns else (
        "time" if "time" in df.columns else None))
    temp_col = "tempMedia" if "tempMedia" in df.columns else ("temp_avg" if "temp_avg" in df.columns else ("temperature" if "temperature" in df.columns else None))
    
    if not time_col or not temp_col:
        raise ValueError(f"No se encontraron columnas esperadas en {file_path}")
        
    df = df.rename(columns={time_col: "timestamp", temp_col: "temperature"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    
    # Manejo de duplicados: promediamos en caso de haber duplicados exactos en el timestamp
    if df.index.duplicated().any():
        logging.warning(f"  Encontrados duplicados en {file_path}, colapsando por media.")
        df = df.groupby(level=0).mean()
        
    # Zona horaria
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(tz)
    else:
        df.index = df.index.tz_convert(tz)
        
    # Resample estricto a 1H para rellenar gaps intermedios con NaN y alinear
    # En caso de cambios de hora, pandas maneja el resample.
    df = df.resample('1h').asfreq()
    
    return df[["temperature"]]

def is_valid_temperature(val):
    """Criterio de observación válida."""
    if pd.isna(val):
        return False
    if not isinstance(val, (int, float, np.floating, np.integer)):
        return False
    if val == -9999 or val == 999:
        return False
    if val < -15.0 or val > 50.0:
        return False
    return True

def consolidate_fundo(fundo, obs_path, rec_path, out_dir, start_date="2024-05-01 00:00:00", end_date="2024-08-31 23:00:00", tz="America/Santiago"):
    logging.info(f"Consolidando {fundo}...")
    
    try:
        df_obs = load_and_normalize(obs_path, tz)
        df_obs = df_obs.rename(columns={"temperature": "temperature_observed_c"})
    except Exception as e:
        logging.error(f"  Error cargando observado: {e}")
        return
        
    if rec_path and Path(rec_path).exists():
        df_rec = load_and_normalize(rec_path, tz)
        df_rec = df_rec.rename(columns={"temperature": "temperature_reconstructed_c"})
    else:
        df_rec = pd.DataFrame(columns=["temperature_reconstructed_c"], index=df_obs.index)
        df_rec.index.name = "timestamp"
        
    # Crear un índice base continuo desde start_date hasta end_date
    start_ts = pd.Timestamp(start_date).tz_localize(tz)
    end_ts = pd.Timestamp(end_date).tz_localize(tz)
    full_idx = pd.date_range(start=start_ts, end=end_ts, freq='1h', name="timestamp")
    
    # Unir ambas fuentes en el índice completo
    df = pd.DataFrame(index=full_idx)
    df = df.join(df_obs, how='left')
    df = df.join(df_rec, how='left')
    
    # Calcular flags de validez
    df["observed_valid"] = df["temperature_observed_c"].apply(is_valid_temperature)
    df["reconstructed_valid"] = df["temperature_reconstructed_c"].apply(is_valid_temperature)
    
    # Lógica de Hard Cut (Coalesce estricto)
    temp_final = []
    origen = []
    flags = []
    
    for idx, row in df.iterrows():
        flag_notes = []
        
        if not row["observed_valid"] and pd.notna(row["temperature_observed_c"]):
            flag_notes.append("obs_invalid")
            
        if not row["reconstructed_valid"] and pd.notna(row["temperature_reconstructed_c"]):
            flag_notes.append("rec_invalid")
            
        if row["observed_valid"]:
            t = row["temperature_observed_c"]
            o = "observado"
        elif row["reconstructed_valid"]:
            t = row["temperature_reconstructed_c"]
            o = "reconstruido"
        else:
            t = np.nan
            o = "gap"
            
        temp_final.append(t)
        origen.append(o)
        flags.append("|".join(flag_notes) if flag_notes else "")
        
    df["temperature_c"] = temp_final
    df["origen_temp"] = origen
    df["quality_flag"] = flags
    df["fundo"] = fundo
    
    df = df.reset_index()
    
    # Reordenar columnas según el esquema mínimo
    cols = [
        "fundo", "timestamp", "temperature_observed_c", "temperature_reconstructed_c", 
        "temperature_c", "origen_temp", "observed_valid", "reconstructed_valid", "quality_flag"
    ]
    df = df[cols]
    
    # Guardar
    out_dir_fundo = Path(out_dir)
    out_dir_fundo.mkdir(parents=True, exist_ok=True)
    
    parquet_path = out_dir_fundo / f"{fundo}_climate_hourly_consolidated.parquet"
    csv_path = out_dir_fundo / f"{fundo}_climate_hourly_consolidated.csv"
    
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    
    obs_pct = (df["origen_temp"] == "observado").mean() * 100
    rec_pct = (df["origen_temp"] == "reconstruido").mean() * 100
    gap_pct = (df["origen_temp"] == "gap").mean() * 100
    logging.info(f"  -> Guardado. Obs: {obs_pct:.1f}%, Rec: {rec_pct:.1f}%, Gap: {gap_pct:.1f}%")

def main():
    root_dir = Path(__file__).resolve().parent.parent
    raw_dir = root_dir / "data/raw/climate/hourly/datavid"
    out_dir = root_dir / "data/processed/climate/hourly/consolidated"
    
    # Mapeo manual de reconstrucciones conocidas
    reconstructions_map = {
        "pencahue_sur": root_dir / "data/processed/climate/hourly/inia333_reconstructed/climate_hourly_inia333_v1.parquet",
        "pencahue_norte": root_dir / "data/processed/climate/hourly/inia333_reconstructed/climate_hourly_inia333_v1.parquet"
    }
    
    # Para la prueba, consolidaremos todos los fundos disponibles en datavid
    # (la gran mayoría solo tendrá observado y gap)
    fundos = [d.name for d in raw_dir.iterdir() if d.is_dir()]
    
    for fundo in fundos:
        obs_path = raw_dir / fundo / "climate_hourly.parquet"
        rec_path = reconstructions_map.get(fundo, None)
        
        if obs_path.exists():
            # Fijamos fecha límite al 19 de agosto como hito del proyecto
            consolidate_fundo(fundo, obs_path, rec_path, out_dir, start_date="2024-05-01 00:00:00", end_date="2024-08-31 23:00:00")

if __name__ == '__main__':
    main()
