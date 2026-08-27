import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def calculate_hf_72(temp_series, mode="CH_LE_7_2"):
    """
    Calculate Chill Hours.
    mode='CH_LE_7_2': sum of hours where T <= 7.2
    mode='CH_0_7_2': sum of hours where 0 <= T <= 7.2
    """
    if mode == "CH_LE_7_2":
        return (temp_series <= 7.2).astype(float)
    elif mode == "CH_0_7_2":
        return ((temp_series >= 0) & (temp_series <= 7.2)).astype(float)
    else:
        raise ValueError("Invalid mode for calculate_hf_72")

def calculate_utah(temp_series):
    """
    Calculate Utah Chill Units.
    """
    bins = [-np.inf, 1.3999, 2.4999, 9.1001, 12.4001, 15.9001, 18.0001, np.inf]
    labels = [0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0]
    return pd.cut(temp_series, bins=bins, labels=labels, ordered=False).astype(float).fillna(0)

def calculate_dynamic_model(temp_series, initial_state=None):
    """
    Dynamic Model (Fishman et al., 1987) for Chill Portions.
    """
    E0 = 4153.5
    E1 = 12888.8
    A0 = 139500.0
    A1 = 2.567e18
    SLP = 1.6
    TETMLT = 277.0
    AA = A0 / A1
    EE = E1 - E0
    
    x = initial_state['x'] if initial_state else 0.0
    y_total = initial_state['y'] if initial_state else 0.0
    prev_xi = initial_state['prev_xi'] if (initial_state and 'prev_xi' in initial_state) else 0.0
    
    xs_arr = np.zeros(len(temp_series))
    ys_arr = np.zeros(len(temp_series))
    y_acums = np.zeros(len(temp_series))
    prev_xi_arr = np.zeros(len(temp_series))
    
    for i, t_c in enumerate(temp_series):
        if np.isnan(t_c):
            xs_arr[i] = x
            ys_arr[i] = 0.0
            y_acums[i] = y_total
            prev_xi_arr[i] = prev_xi
            continue
            
        t_k = t_c + 273.15
        
        ftmprt = SLP * TETMLT * (t_k - TETMLT) / t_k
        sr = np.exp(ftmprt)
        xi = sr / (1.0 + sr)
        
        xs = AA * np.exp(EE / t_k)
        ak1 = A1 * np.exp(-E1 / t_k)
        
        if x >= 1.0:
            curr_s = x - x * prev_xi
        else:
            curr_s = x
            
        x = xs - (xs - curr_s) * np.exp(-ak1)
        
        if x >= 1.0:
            y_inc = x * xi
        else:
            y_inc = 0.0
        
        y_total += y_inc
        xs_arr[i] = x
        ys_arr[i] = y_inc
        y_acums[i] = y_total
        prev_xi_arr[i] = xi
        prev_xi = xi
        
    return pd.DataFrame({
        'x_state': xs_arr,
        'CP_hourly': ys_arr,
        'CP_acum': y_acums,
        'prev_xi': prev_xi_arr
    }, index=temp_series.index)


def process_fundo_chill(file_path):
    df = pd.read_parquet(file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    
    fundo_name = df["fundo"].iloc[0] if len(df) > 0 else "unknown"
    
    # Calcular métricas base
    expected_hours = len(df)
    obs_count = (df["origen_temp"] == "observado").sum()
    rec_count = (df["origen_temp"] == "reconstruido").sum()
    gap_count = (df["origen_temp"] == "gap").sum()
    
    temp_series = df["temperature_c"]
    
    # Gap analysis
    is_gap = temp_series.isna()
    gap_groups = (is_gap != is_gap.shift()).cumsum()
    gap_sizes = is_gap.groupby(gap_groups).sum()
    gap_sizes = gap_sizes[gap_sizes > 0]
    
    number_of_gaps = len(gap_sizes)
    maximum_gap_hours = int(gap_sizes.max()) if number_of_gaps > 0 else 0
    
    # Calculate HF and Utah
    # Para los NA, astype float -> NaN or False, then fillna 0
    hf_le_7_2_series = calculate_hf_72(temp_series, mode="CH_LE_7_2").fillna(0)
    hf_0_7_2_series = calculate_hf_72(temp_series, mode="CH_0_7_2").fillna(0)
    utah_series = calculate_utah(temp_series).fillna(0)
    
    # Calculate Dynamic Model
    dyn_res = calculate_dynamic_model(temp_series)
    cp_hourly_series = dyn_res["CP_hourly"].fillna(0)
    
    # Aggregate into hourly output
    df_hourly = pd.DataFrame({
        "fundo": fundo_name,
        "temperature_c": temp_series,
        "hf_le_7_2": hf_le_7_2_series,
        "hf_0_to_7_2": hf_0_7_2_series,
        "utah_chill_units": utah_series,
        "dynamic_chill_portions": cp_hourly_series,
        "dynamic_x_state": dyn_res["x_state"]
    }, index=df.index).reset_index()
    
    # Resumen diario
    # Como el index era temporal
    df_daily = df.copy()
    df_daily["hf_le_7_2"] = hf_le_7_2_series
    df_daily["hf_0_to_7_2"] = hf_0_7_2_series
    df_daily["utah_chill_units"] = utah_series
    df_daily["dynamic_chill_portions"] = cp_hourly_series
    
    # Acumular a nivel diario
    daily_agg = df_daily.resample('D').agg({
        "hf_le_7_2": "sum",
        "hf_0_to_7_2": "sum",
        "utah_chill_units": "sum",
        "dynamic_chill_portions": "sum",
        "origen_temp": lambda x: (x == "gap").sum() # gap hours
    })
    daily_agg = daily_agg.rename(columns={"origen_temp": "missing_hours"})
    daily_agg["fundo"] = fundo_name
    daily_agg = daily_agg.reset_index()
    
    # Quality status según gaps
    if maximum_gap_hours > 72 or gap_count > (expected_hours * 0.15):
        quality_status = "insuficiente"
        notes = "Demasiados gaps o gap muy prolongado"
    elif maximum_gap_hours > 24 or gap_count > 0:
        quality_status = "valido_con_advertencia"
        notes = "Presenta gaps menores"
    else:
        quality_status = "valido"
        notes = "OK"
        
    start_ts = df.index.min().isoformat() if len(df) > 0 else ""
    end_ts = df.index.max().isoformat() if len(df) > 0 else ""
    
    # Summary record
    summary = {
        "fundo": fundo_name,
        "season": "2024",
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "expected_hours": expected_hours,
        "observed_hours": obs_count,
        "reconstructed_hours": rec_count,
        "missing_hours": gap_count,
        "observed_percentage": round(obs_count / max(1, expected_hours) * 100, 2),
        "reconstructed_percentage": round(rec_count / max(1, expected_hours) * 100, 2),
        "missing_percentage": round(gap_count / max(1, expected_hours) * 100, 2),
        "number_of_gaps": number_of_gaps,
        "maximum_gap_hours": maximum_gap_hours,
        "hf_le_7_2": round(hf_le_7_2_series.sum(), 2),
        "hf_0_to_7_2": round(hf_0_7_2_series.sum(), 2),
        "utah_chill_units": round(utah_series.sum(), 2),
        "dynamic_chill_portions": round(cp_hourly_series.sum(), 2),
        "quality_status": quality_status,
        "notes": notes
    }
    
    return df_hourly, daily_agg, summary

def main():
    root_dir = Path(__file__).resolve().parent.parent
    consolidated_dir = root_dir / "data/processed/climate/hourly/consolidated"
    
    if not consolidated_dir.exists():
        logging.error("Directorio de consolidados no existe.")
        return
        
    files = list(consolidated_dir.glob("*.parquet"))
    
    out_hourly_dir = root_dir / "data/processed/chill/hourly"
    out_daily_dir = root_dir / "data/processed/chill/daily"
    out_summary_dir = root_dir / "data/processed/chill"
    
    out_hourly_dir.mkdir(parents=True, exist_ok=True)
    out_daily_dir.mkdir(parents=True, exist_ok=True)
    out_summary_dir.mkdir(parents=True, exist_ok=True)
    
    all_daily = []
    summaries = []
    
    for f in files:
        logging.info(f"Calculando indicadores para {f.stem}...")
        df_hourly, df_daily, summary = process_fundo_chill(f)
        
        fundo_name = summary["fundo"]
        
        # Save hourly
        df_hourly.to_parquet(out_hourly_dir / f"{fundo_name}_chill_hourly.parquet", index=False)
        
        all_daily.append(df_daily)
        summaries.append(summary)
        
    # Combine daily
    if all_daily:
        combined_daily = pd.concat(all_daily, ignore_index=True)
        # reorder columns
        cols = ["fundo", "timestamp", "missing_hours", "hf_le_7_2", "hf_0_to_7_2", "utah_chill_units", "dynamic_chill_portions"]
        combined_daily = combined_daily[cols]
        combined_daily.to_csv(out_daily_dir / "chill_daily_accumulation_by_fundo.csv", index=False)
        
    # Combine summaries
    if summaries:
        df_summaries = pd.DataFrame(summaries)
        df_summaries.to_csv(out_summary_dir / "chill_indicators_by_fundo.csv", index=False)
        
        # Generar reporte de auditoría MD
        report_path = root_dir / "reports/qa/auditoria_indicadores_frio_por_fundo.md"
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("# Auditoría de Indicadores de Frío por Fundo\n\n")
            rf.write("## 1. Resumen de Ejecución\n")
            rf.write("Se ejecutaron los cálculos de frío (HF, HF [0-7.2], Utah, Dynamic) para todas las series consolidadas.\n\n")
            rf.write("## 2. Resumen por Fundo\n")
            rf.write(df_summaries.to_markdown(index=False))
            
    logging.info("Procesamiento de frío completado.")

if __name__ == '__main__':
    main()
