import requests
import pandas as pd
import time
from pathlib import Path

def download_inia_station(station_id, station_name, start_date, end_date):
    """
    Downloads hourly temperature data from INIA API for a given station in chunks.
    """
    api_key = "108e6ad380def67c9c34e84a4a126b3732f3cf5e"
    var_temp = "2002" # Temperatura del Aire Media
    
    print(f"Downloading {station_name} ({station_id}) from {start_date} to {end_date}...")
    
    # Generate 7-day chunks to respect API limits
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    all_data = []
    
    current_start = start_dt
    while current_start <= end_dt:
        current_end = min(current_start + pd.Timedelta(days=6), end_dt) # API limit is 7 days
        
        chunk_start = current_start.strftime('%Y-%m-%d')
        chunk_end = current_end.strftime('%Y-%m-%d')
            
        url = f"http://agromet.inia.cl/api/v2/muestras/?estacion={station_id}&variable={var_temp}&desde={chunk_start}&hasta={chunk_end}&key={api_key}"
        print(f"  Fetching chunk {chunk_start} to {chunk_end}...")
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if isinstance(data, list):
                all_data.extend(data)
            elif isinstance(data, dict) and 'response' in data:
                # If 'response' is a list, it's the actual data
                if isinstance(data['response'], list):
                    all_data.extend(data['response'])
                else:
                    print(f"  API Error: {data['response']}")
            time.sleep(0.5) # Be nice to the API
        except Exception as e:
            print(f"  Error fetching chunk: {e}")
            
        current_start = current_end + pd.Timedelta(days=1)
            
    if not all_data:
        print(f"No data returned for {station_name}.")
        return None
        
    df = pd.DataFrame(all_data)
    df['fecha_hora'] = pd.to_datetime(df['tiempo'])
    df['tempMedia'] = pd.to_numeric(df['valor'])
    df = df[['fecha_hora', 'tempMedia']].set_index('fecha_hora').sort_index()
    
    # Resample to hourly mean and export
    df_hourly = df.resample('h').mean()
    
    out_dir = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly\inia_proxy_test") / station_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "climate_hourly.parquet"
    
    df_hourly.reset_index().to_parquet(out_path, index=False)
    print(f"Saved {len(df_hourly)} hourly records for {station_name} at {out_path}\n")
    return df_hourly

if __name__ == "__main__":
    # 1. Los Acacios (Fill the Winter Gap)
    download_inia_station("INIA-319", "los_acacios", "2024-05-01", "2025-12-31")
    
    # 2. Pencahue (Lourdes) - Ground Truth for Proxy Test
    download_inia_station("INIA-333", "pencahue", "2024-05-01", "2025-12-31")
    
    # 3. San Clemente - Candidate Proxy for Pencahue
    download_inia_station("INIA-135", "san_clemente", "2024-05-01", "2025-12-31")
    
    print("INIA API downloads completed.")

