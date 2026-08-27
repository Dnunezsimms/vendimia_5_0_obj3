import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf
from sklearn.linear_model import HuberRegressor
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import chill models
from build_chill_indicators import calculate_dynamic_model

def block_bootstrap_residuals(residuals, block_size, n_simulations, target_length):
    """
    Generate bootstrap samples of residuals using moving blocks.
    """
    n_res = len(residuals)
    if n_res < block_size:
        raise ValueError("Block size cannot be larger than the number of residuals.")
        
    # Create all possible overlapping blocks
    blocks = [residuals[i:i + block_size] for i in range(n_res - block_size + 1)]
    blocks = np.array(blocks)
    
    n_blocks_needed = int(np.ceil(target_length / block_size))
    
    simulations = []
    for _ in range(n_simulations):
        # Sample blocks with replacement
        chosen_blocks = blocks[np.random.randint(0, len(blocks), size=n_blocks_needed)]
        # Flatten and truncate to target length
        sim_res = chosen_blocks.flatten()[:target_length]
        simulations.append(sim_res)
        
    return np.array(simulations)

def main():
    root_dir = Path(__file__).resolve().parent.parent
    target_path = root_dir / "data/processed/climate/hourly/inia_proxy_test/pencahue/climate_hourly.parquet"
    proxy_path = root_dir / "data/processed/climate/hourly/agromet_pencahue/climate_hourly.parquet"
    
    if not target_path.exists() or not proxy_path.exists():
        logging.error("Target or proxy parquet not found.")
        return

    df_target = pd.read_parquet(target_path)
    df_proxy = pd.read_parquet(proxy_path)

    df_target = df_target.set_index("fecha_hora")
    df_proxy = df_proxy.set_index("fecha_hora")

    # Rename to merge
    df_target = df_target.rename(columns={"tempMedia": "y_true"})
    df_proxy = df_proxy.rename(columns={"tempMedia": "X_proxy"})

    df = df_target[["y_true"]].join(df_proxy[["X_proxy"]], how="outer")

    # The period to reconstruct
    gap_start = pd.Timestamp("2024-05-01 00:00:00")
    gap_end = pd.Timestamp("2024-08-19 17:00:00")
    
    # Train data: periods where both exist, outside the gap
    mask_train = df["y_true"].notna() & df["X_proxy"].notna() & ((df.index < gap_start) | (df.index > gap_end))
    df_train = df[mask_train].copy()
    
    # Fit Huber
    huber = HuberRegressor(epsilon=1.35)
    X_train = df_train[["X_proxy"]].values
    y_train = df_train["y_true"].values
    huber.fit(X_train, y_train)
    
    # Calculate residuals on train
    df_train["y_pred"] = huber.predict(X_train)
    df_train["resid"] = df_train["y_true"] - df_train["y_pred"]
    
    # Analyze ACF to find block size
    # We want a block size where autocorrelation drops below e.g. 0.1 or we pick a physically meaningful block like 24h, 48h, 72h
    # Let's compute ACF
    res_acf = acf(df_train["resid"].dropna(), nlags=168, fft=True)
    
    # Let's test specific block sizes: 24, 48, 72
    block_sizes = [24, 48, 72, 168]
    logging.info(f"ACF at lags 24, 48, 72, 168: {res_acf[24]:.3f}, {res_acf[48]:.3f}, {res_acf[72]:.3f}, {res_acf[168]:.3f}")
    
    # Let's pick 72h as standard if ACF is still present, or 48h.
    chosen_block = 72
    logging.info(f"Chosen block size: {chosen_block} hours")

    # Extract the gap period for proxy
    df_gap = df[(df.index >= gap_start) & (df.index <= gap_end)].copy()
    
    if df_gap["X_proxy"].isna().sum() > 0:
        logging.warning("Proxy has NaNs in the gap period! Interpolating...")
        df_gap["X_proxy"] = df_gap["X_proxy"].interpolate()
        
    X_gap = df_gap[["X_proxy"]].values
    y_pred_gap = huber.predict(X_gap)
    
    # Simulations
    n_sims = 1000
    target_len = len(y_pred_gap)
    logging.info(f"Running {n_sims} bootstrap simulations for period of {target_len} hours...")
    
    # Get residuals array
    residuals = df_train["resid"].dropna().values
    sim_residuals = block_bootstrap_residuals(residuals, chosen_block, n_sims, target_len)
    
    # We will track accumulated CP at the end of the gap
    final_cp_list = []
    
    # We also keep track of the deterministic accumulation
    df_gap["temp_det"] = y_pred_gap
    det_res = calculate_dynamic_model(df_gap["temp_det"])
    det_cp_final = det_res["CP_acum"].iloc[-1]
    logging.info(f"Deterministic CP at end of gap: {det_cp_final:.1f}")
    
    for i in range(n_sims):
        sim_temp = y_pred_gap + sim_residuals[i]
        sim_series = pd.Series(sim_temp, index=df_gap.index)
        sim_res = calculate_dynamic_model(sim_series)
        final_cp_list.append(sim_res["CP_acum"].iloc[-1])
        
        if (i + 1) % 100 == 0:
            logging.info(f"Completed {i + 1} simulations...")
            
    final_cp_array = np.array(final_cp_list)
    p05 = np.percentile(final_cp_array, 5)
    p95 = np.percentile(final_cp_array, 95)
    mean_cp = np.mean(final_cp_array)
    std_cp = np.std(final_cp_array)
    
    logging.info(f"Bootstrap CP Stats (1000 sims):")
    logging.info(f"Mean: {mean_cp:.1f} CP")
    logging.info(f"Std:  {std_cp:.1f} CP")
    logging.info(f"90% CI: [{p05:.1f}, {p95:.1f}] CP")
    
    # Save results to a report
    out_path = root_dir / "reports/qa/validacion_incertidumbre_acumulada_frio.md"
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Validación de Incertidumbre en Acumulación de Frío\n\n")
        f.write("## Metodología\n")
        f.write("- **Método de Reconstrucción:** HuberRegressor (Agromet Pencahue -> INIA-333)\n")
        f.write(f"- **Simulaciones:** {n_sims} mediante Block Bootstrap\n")
        f.write(f"- **Tamaño de bloque:** {chosen_block} horas\n")
        f.write(f"- **Periodo reconstruido:** {gap_start.strftime('%Y-%m-%d')} a {gap_end.strftime('%Y-%m-%d')}\n")
        f.write(f"- **Modelo de Frío:** Modelo Dinámico (Fishman, implementation xclim/Luedeling)\n\n")
        
        f.write("## Resultados\n")
        f.write(f"- **CP Determinístico (sin error):** {det_cp_final:.1f} CP\n")
        f.write(f"- **CP Promedio (Bootstrap):** {mean_cp:.1f} CP\n")
        f.write(f"- **Intervalo Confianza 90%:** [{p05:.1f}, {p95:.1f}] CP\n")
        f.write(f"- **Desviación Estándar:** {std_cp:.1f} CP\n\n")
        
        f.write("## Análisis de Autocorrelación de Residuos (ACF)\n")
        f.write(f"- Lag 24h: {res_acf[24]:.3f}\n")
        f.write(f"- Lag 48h: {res_acf[48]:.3f}\n")
        f.write(f"- Lag 72h: {res_acf[72]:.3f}\n")
        f.write(f"- Lag 168h: {res_acf[168]:.3f}\n\n")
        
        f.write("## Conclusión\n")
        f.write("La incertidumbre generada por la imputación del modelo Huber se cuantifica a través del bootstrap. ")
        f.write("Esta banda de error es fundamental para reportar los indicadores fenológicos sin sobreestimar la precisión de los datos reconstruidos.\n")
        
    logging.info(f"Report saved to {out_path}")

if __name__ == '__main__':
    main()
