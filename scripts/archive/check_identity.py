import pandas as pd
from pathlib import Path
import numpy as np

BASE_DIR = Path(r"C:\projects\vendimia_5_0_obj3_clean")

def check_identity():
    p_inia333 = BASE_DIR / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet"
    p_agromet = BASE_DIR / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet"
    
    df1 = pd.read_parquet(p_inia333)
    df2 = pd.read_parquet(p_agromet)
    
    df1['fecha_hora'] = pd.to_datetime(df1['fecha_hora'])
    df2['fecha_hora'] = pd.to_datetime(df2['fecha_hora'])
    
    df1 = df1.rename(columns={'tempMedia': 't1'})
    df2 = df2.rename(columns={'tempMedia': 't2'})
    
    # Merge on exact timestamp
    df = df1[['fecha_hora', 't1']].merge(df2[['fecha_hora', 't2']], on='fecha_hora', how='inner')
    
    df = df.dropna(subset=['t1', 't2'], how='all')
    
    if len(df) == 0:
        print("No overlapping data!")
        return
        
    mask_both = df['t1'].notna() & df['t2'].notna()
    df_valid = df[mask_both]
    
    exact_matches = (df_valid['t1'] == df_valid['t2']).sum()
    total_valid = len(df_valid)
    
    mean_diff = (df_valid['t1'] - df_valid['t2']).mean()
    max_diff = (df_valid['t1'] - df_valid['t2']).abs().max()
    
    if total_valid > 1:
        corr = np.corrcoef(df_valid['t1'], df_valid['t2'])[0,1]
    else:
        corr = np.nan
        
    print(f"Overlap Start: {df['fecha_hora'].min()}")
    print(f"Overlap End: {df['fecha_hora'].max()}")
    print(f"Total overlapping timestamps: {len(df)}")
    print(f"Total with valid temp in both: {total_valid}")
    print(f"Exact matches (t1 == t2): {exact_matches}")
    if total_valid > 0:
        print(f"Percentage of exact matches: {exact_matches / total_valid * 100:.2f}%")
    print(f"Mean Difference: {mean_diff:.4f}")
    print(f"Max Absolute Difference: {max_diff:.4f}")
    print(f"Correlation: {corr:.6f}")
    
    # Check for shifted timestamps
    df2_shifted = df2.copy()
    df2_shifted['fecha_hora'] = df2_shifted['fecha_hora'] + pd.Timedelta(hours=1)
    df_shift = df1[['fecha_hora', 't1']].merge(df2_shifted[['fecha_hora', 't2']], on='fecha_hora', how='inner')
    df_shift_valid = df_shift.dropna()
    shift_exact = (df_shift_valid['t1'] == df_shift_valid['t2']).sum()
    print(f"Exact matches with +1h shift: {shift_exact} / {len(df_shift_valid)}")

if __name__ == "__main__":
    check_identity()
