import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize

# =============================================================================
# PATH
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "models" / "pheno_modeling-main" / "data" / "cabernet_sauvignon"

# =============================================================================
# CONFIG
# =============================================================================
Tb = 10.0
Tu = 35.0
fecha_inicio = 243  # 1 septiembre
ELP_f = 38.0

# =============================================================================
# GDD SENO SIMPLE
# =============================================================================
def gdd_single_sine(Tmin, Tmax, Tb, Tu):
    alpha = (Tmax + Tmin) / 2
    beta = (Tmax - Tmin) / 2

    if Tmax <= Tb:
        return 0
    elif Tmin >= Tu:
        return Tu - Tb
    elif Tmin >= Tb and Tmax <= Tu:
        return alpha - Tb
    elif Tmin < Tb and Tmax <= Tu:
        theta = np.arcsin((Tb - alpha) / beta)
        return (1/np.pi) * ((alpha - Tb)*(np.pi/2 - theta) + beta*np.cos(theta))
    elif Tmin >= Tb and Tmax > Tu:
        theta = np.arcsin((Tu - alpha) / beta)
        return (1/np.pi) * ((alpha - Tb)*(theta + np.pi/2) - beta*np.cos(theta) + (Tu - Tb)*(np.pi/2 - theta))
    elif Tmin < Tb and Tmax > Tu:
        theta1 = np.arcsin((Tb - alpha) / beta)
        theta2 = np.arcsin((Tu - alpha) / beta)
        return (1/np.pi) * ((alpha - Tb)*(theta2 - theta1) + beta*(np.cos(theta1) - np.cos(theta2)) + (Tu - Tb)*(np.pi/2 - theta2))
    else:
        return 0

# =============================================================================
# CALCULO GDD ACUMULADO
# =============================================================================
def calc_gdd(df):
    df = df.copy()
    gdd_list = []

    for tmin, tmax in zip(df["temp_min_grado_c"], df["temp_max_grado_c"]):
        gdd = gdd_single_sine(tmin, tmax, Tb, Tu)
        gdd_list.append(gdd)

    df["GDD"] = gdd_list
    df["GDD_acum"] = df["GDD"].cumsum()

    return df

# =============================================================================
# MODELO ELP
# =============================================================================
def elp_model(gdd, delta, beta):
    return ELP_f - delta * np.exp(-beta * gdd)

# =============================================================================
# COSTO GLOBAL
# =============================================================================
def objective(params, datasets):
    delta, beta = params
    errors = []

    for df in datasets:
        df_valid = df.dropna(subset=["ELP Observado"])

        gdd = df_valid["GDD_acum"].values
        elp_obs = df_valid["ELP Observado"].values

        elp_pred = elp_model(gdd, delta, beta)
        errors.append(np.mean((elp_obs - elp_pred) ** 2))

    return np.mean(errors)

# =============================================================================
# CARGA DATOS
# =============================================================================
files = [
    ("clima_los_sauces_cs.xlsx", "2023-2024"),
    ("clima_los_sauces_cs.xlsx", "2024-2025"),

    ("clima_los_indios_cs.xlsx", "2023-2024"),
    ("clima_los_indios_cs.xlsx", "2024-2025"),

    ("clima_los_ponchos_cs.xlsx", "2023-2024"),
    ("clima_los_ponchos_cs.xlsx", "2024-2025"),

    ("clima_cruz_del_alto_cs.xlsx", "2023-2024"),
    ("clima_cruz_del_alto_cs.xlsx", "2024-2025"),

    ("clima_los_zorros_cs.xlsx", "2023-2024"),
    ("clima_los_zorros_cs.xlsx", "2024-2025"),

    # Lourdes (validación)
    ("clima_lourdes_cs.xlsx", "2024-2025"),
    ("clima_lourdes_cs.xlsx", "2025-2026"),
]

datasets = []
labels = []

for file, sheet in files:

    df = pd.read_excel(DATA_PATH / file, sheet_name=sheet)

    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

    cols = ["temp_min_grado_c", "temp_max_grado_c", "ELP Observado"]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Fecha", "temp_min_grado_c", "temp_max_grado_c"])

    df = df[df["Fecha"].dt.dayofyear >= fecha_inicio]

    df = calc_gdd(df)

    datasets.append(df)
    labels.append(f"{file}-{sheet}")

# =============================================================================
# SEPARAR TRAIN / LOURDES
# =============================================================================
datasets_train = []
datasets_lourdes = []

for df, label in zip(datasets, labels):
    if "lourdes" in label:
        datasets_lourdes.append(df)
    else:
        datasets_train.append(df)

# =============================================================================
# AJUSTE GLOBAL
# =============================================================================
res = minimize(
    objective,
    x0=[30, 0.005],
    bounds=[(10, 80), (1e-3, 1e-2)],
    args=(datasets_train,),
)

delta_opt, beta_opt = res.x

print("\nPARAMETROS GLOBALES")
print("delta:", round(delta_opt, 4))
print("beta:", round(beta_opt, 6))

# =============================================================================
# GDD PARA BROTACION
# =============================================================================
def gdd_brotacion(delta, beta):
    return -(1 / beta) * np.log((ELP_f - 4) / delta)

gdd_global = gdd_brotacion(delta_opt, beta_opt)

print("\nGDD GLOBAL (brotación):", round(gdd_global, 2))

# =============================================================================
# EVALUAR LOURDES
# =============================================================================
gdd_lourdes_list = []

for df in datasets_lourdes:

    df_valid = df.dropna(subset=["ELP Observado"]).sort_values("Fecha")

    elp = df_valid["ELP Observado"]
    gdd = df_valid["GDD_acum"]

    idx = np.where((elp.shift(1) < 4) & (elp >= 4))[0]

    if len(idx) > 0:
        gdd_obs = gdd.iloc[idx[0]]
    else:
        idx2 = (elp - 4).abs().idxmin()
        gdd_obs = gdd.loc[idx2]

    gdd_lourdes_list.append(gdd_obs)

gdd_lourdes_mean = np.mean(gdd_lourdes_list)

print("\nDEBUG LOURDES:")
for val in gdd_lourdes_list:
    print("GDD:", round(val, 2))

# =============================================================================
# RESULTADOS
# =============================================================================
error = abs(gdd_lourdes_mean - gdd_global)

print("\n================ RESULTADOS ================")

print("\n--- MODELO GLOBAL ---")
print("GDD esperado:", round(gdd_global, 2))

print("\n--- LOURDES ---")
print("GDD Lourdes:", round(gdd_lourdes_mean, 2))

print("\n--- EVALUACION ---")
print("Diferencia:", round(error, 2))

if error < 10:
    print("✅ Lourdes consistente")
else:
    print("⚠️ Lourdes NO consistente")

print("===========================================")