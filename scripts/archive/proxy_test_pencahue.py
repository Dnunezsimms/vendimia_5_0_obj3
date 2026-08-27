import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from pathlib import Path

def compute_metrics(y_true, y_pred, name):
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    if len(y_true) == 0:
        return {"Name": name, "N": 0, "RMSE": np.nan, "MAE": np.nan, "R2": np.nan, "Bias": np.nan}
        
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    bias = np.mean(y_pred - y_true)
    
    return {"Name": name, "N": len(y_true), "RMSE": rmse, "MAE": mae, "R2": r2, "Bias": bias}

def run_proxy_test():
    base_dir = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly")
    
    # Paths
    path_pencahue_inia = base_dir / "inia_proxy_test" / "pencahue" / "climate_hourly.parquet"
    path_san_clemente_inia = base_dir / "inia_proxy_test" / "san_clemente" / "climate_hourly.parquet"
    path_pencahue_era5 = base_dir / "era5" / "pencahue" / "climate_hourly.parquet"
    
    path_pencahue_agromet = base_dir / "agromet_pencahue" / "climate_hourly.parquet"
    
    # Load
    df_pencahue = pd.read_parquet(path_pencahue_inia).rename(columns={'tempMedia': 'Pencahue_INIA'})
    df_sc = pd.read_parquet(path_san_clemente_inia).rename(columns={'tempMedia': 'SanClemente_INIA'})
    df_era5 = pd.read_parquet(path_pencahue_era5).rename(columns={'tempMedia': 'Pencahue_ERA5'})
    df_agro = pd.read_parquet(path_pencahue_agromet).rename(columns={'tempMedia': 'Pencahue_Agromet'})
    
    # Ensure timezone-naive for joining if needed, but they should all be naive
    for df in [df_pencahue, df_sc, df_era5, df_agro]:
        if df['fecha_hora'].dt.tz is not None:
            df['fecha_hora'] = df['fecha_hora'].dt.tz_localize(None)
            
    # Merge
    df_merged = df_pencahue.merge(df_sc, on='fecha_hora', how='inner')
    df_merged = df_merged.merge(df_era5, on='fecha_hora', how='inner')
    df_merged = df_merged.merge(df_agro, on='fecha_hora', how='inner')
    
    # Compute metrics against Pencahue INIA
    metrics_sc = compute_metrics(df_merged['Pencahue_INIA'], df_merged['SanClemente_INIA'], "San Clemente INIA")
    metrics_era5 = compute_metrics(df_merged['Pencahue_INIA'], df_merged['Pencahue_ERA5'], "Pencahue ERA5-Land")
    metrics_agro = compute_metrics(df_merged['Pencahue_INIA'], df_merged['Pencahue_Agromet'], "Pencahue Agromet (Manual)")
    
    results = pd.DataFrame([metrics_sc, metrics_era5, metrics_agro])
    
    out_path = Path(r"C:\projects\vendimia_5_0_obj3_clean\reports\proxy_test_pencahue_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    
    print("Proxy Test Results:")
    print(results.to_string(index=False))
    
if __name__ == "__main__":
    run_proxy_test()
