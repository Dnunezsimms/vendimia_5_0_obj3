import pandas as pd
import numpy as np
from pathlib import Path

def audit_gaps():
    root_dir = Path(__file__).resolve().parent.parent.parent
    raw_hourly_dir = root_dir / "data" / "raw" / "climate" / "hourly"
    
    results = []
    
    # Iterate over all networks (datavid, inia_agromet, zentra)
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
                
                # Identify time column
                time_col = next((c for c in df.columns if 'time' in c.lower() or 'fecha' in c.lower() or 'date' in c.lower()), None)
                # Identify temp column
                temp_col = next((c for c in df.columns if 'temp' in c.lower() and 'min' not in c.lower() and 'max' not in c.lower()), None)
                
                if not time_col or not temp_col:
                    continue
                    
                df[time_col] = pd.to_datetime(df[time_col])
                df = df.set_index(time_col).sort_index()
                
                # Filter for winter/spring of the two seasons (May to Dec)
                df = df[(df.index >= '2024-05-01') & (df.index <= '2025-12-31')]
                
                if df.empty:
                    continue
                
                # Reindex to full hourly frequency
                full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='h')
                df_reindexed = df.reindex(full_range)
                
                # Calculate gaps
                is_nan = df_reindexed[temp_col].isna()
                # Create groups for consecutive NaNs
                gap_groups = (~is_nan).cumsum()[is_nan]
                gap_sizes = gap_groups.value_counts()
                
                total_missing = is_nan.sum()
                max_gap = gap_sizes.max() if not gap_sizes.empty else 0
                gaps_gt_3h = (gap_sizes > 3).sum()
                
                results.append({
                    "Network": network_dir.name,
                    "Station": station_dir.name,
                    "Start": df.index.min().strftime('%Y-%m-%d'),
                    "End": df.index.max().strftime('%Y-%m-%d'),
                    "Total Hours": len(full_range),
                    "Missing Hours": total_missing,
                    "Max Gap (Hours)": max_gap,
                    "Gaps > 3h (Count)": gaps_gt_3h,
                    "Completeness (%)": round(100 * (len(full_range) - total_missing) / len(full_range), 2) if len(full_range) > 0 else 0
                })
            except Exception as e:
                print(f"Error processing {station_dir.name}: {e}")
                
    report_df = pd.DataFrame(results)
    if not report_df.empty:
        report_df = report_df.sort_values(by="Gaps > 3h (Count)", ascending=False)
        output_path = root_dir / "data" / "processed" / "climate" / "hourly_gaps_audit_report.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_df.to_csv(output_path, index=False)
        print(f"Audit completed. Found {len(report_df)} stations.")
        print(f"Report saved to {output_path}")
        print("\nTop 10 stations with most gaps > 3 hours:")
        print(report_df.head(10).to_string(index=False))
    else:
        print("No valid data found.")

if __name__ == "__main__":
    audit_gaps()

