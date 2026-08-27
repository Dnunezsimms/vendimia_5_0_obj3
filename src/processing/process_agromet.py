import pandas as pd
from pathlib import Path
import glob

def process_agromet():
    raw_dir = Path(r"C:\projects\vendimia_5_0_obj3\data\raw\climate\agromet\Pencahue")
    files = glob.glob(str(raw_dir / "*.csv"))
    
    dfs = []
    for f in files:
        df = pd.read_csv(f, sep=',', quotechar='"', decimal=',')
        dfs.append(df)
        
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Clean up column names just in case there are trailing spaces
    df_all.columns = df_all.columns.str.strip()
    
    # Parse date
    df_all['fecha_hora'] = pd.to_datetime(df_all['Fecha Hora'], format='%d-%m-%Y %H:%M')
    
    # Rename Temp column
    df_all = df_all.rename(columns={'Temp. promedio aire': 'tempMedia'})
    
    # Clean '--' and convert to numeric
    df_all['tempMedia'] = pd.to_numeric(df_all['tempMedia'].astype(str).str.replace(',', '.').replace('--', 'NaN'), errors='coerce')
    
    # Select cols
    df_out = df_all[['fecha_hora', 'tempMedia']].copy()
    
    # Sort and drop duplicates
    df_out = df_out.sort_values('fecha_hora').drop_duplicates('fecha_hora')
    
    # Save to clean dir
    out_dir = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly\agromet_pencahue")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "climate_hourly.parquet"
    
    df_out.to_parquet(out_path, index=False)
    print(f"Processed {len(df_out)} rows. Saved to {out_path}")
    print(f"Date range: {df_out['fecha_hora'].min()} to {df_out['fecha_hora'].max()}")
    print(f"Missing values: {df_out['tempMedia'].isna().sum()}")

if __name__ == "__main__":
    process_agromet()

