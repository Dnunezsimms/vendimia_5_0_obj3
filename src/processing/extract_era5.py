import xarray as xr
import pandas as pd
from pathlib import Path
import glob

def combine_era5land_files(station_name, nc_dir, out_path):
    print(f"Combining ERA5-Land files for {station_name} from {nc_dir}...")
    
    # Use ONLY the .extracted.nc files
    pattern = f"{nc_dir}/*{station_name}*era5land.extracted.nc"
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found for {station_name}")
        return
        
    print(f"Found {len(files)} files. Loading...")
    
    dfs = []
    for f in files:
        try:
            ds = xr.open_dataset(f, engine='netcdf4')
            df_part = ds.to_dataframe().reset_index()
            dfs.append(df_part)
            ds.close()
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    if not dfs:
        print("No valid data loaded.")
        return
        
    df = pd.concat(dfs, ignore_index=True)
    
    # T2M in ERA5-Land is in Kelvin
    if 't2m' in df.columns:
        df['tempMedia'] = df['t2m'] - 273.15
        
    df = df[['valid_time', 'tempMedia']].rename(columns={'valid_time': 'fecha_hora'})
    df = df.sort_values('fecha_hora').drop_duplicates('fecha_hora')
    
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"Saved {len(df)} ERA5-Land records to {out_path}\n")

if __name__ == "__main__":
    nc_dir = r"C:\projects\plataforma-rs\data\external\era5land\raw"
    
    # 1. Pencahue (Lourdes)
    pencahue_out = r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly\era5\pencahue\climate_hourly.parquet"
    combine_era5land_files("lourdes", nc_dir, pencahue_out)
    
    # 2. San Clemente (Mariposas)
    san_clemente_out = r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly\era5\san_clemente\climate_hourly.parquet"
    combine_era5land_files("mariposas", nc_dir, san_clemente_out)

