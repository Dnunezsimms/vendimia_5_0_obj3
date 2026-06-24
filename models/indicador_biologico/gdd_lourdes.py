# =============================================================================
# GDD CABERNET SAUVIGNON - LOURDES
# Método del PDF
# Comparando ambas temporadas y obteniendo promedio
# =============================================================================

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (12,5)
plt.rcParams["axes.grid"] = True


# =============================================================================
# FILE
# =============================================================================

FILE_PATH = Path(
    r"C:\projects\vendimia_5_0_obj3\models\pheno_modeling-main\data\cabernet_sauvignon\clima_lourdes_cs.xlsx"
)

# =============================================================================
# LOAD
# =============================================================================

xls = pd.ExcelFile(FILE_PATH)

print(xls.sheet_names)

# =============================================================================
# PARAMETERS
# =============================================================================

Tb = 10
Tu = 35

# =============================================================================
# GDD FUNCTION
# =============================================================================

def gdd_simple(tmax, tmin, tb, tu):

    if pd.isna(tmax) or pd.isna(tmin):
        return np.nan

    tmean = (tmax + tmin) / 2
    alpha = (tmax - tmin) / 2

    if alpha == 0:
        return max(0, min(tmean, tu) - tb)

    # Caso 1
    if tmax <= tb:
        return 0.0

    # Caso 2
    if tmin >= tu:
        return tu - tb

    # Caso 3
    if tmin >= tb and tmax <= tu:
        return tmean - tb

    # Caso 4
    if tmin < tb and tmax <= tu:

        theta = np.arcsin((tb - tmean) / alpha)

        return (
            (
                (tmean - tb)
                * (np.pi/2 - theta)
            )
            +
            (
                alpha
                * np.cos(theta)
            )
        ) / np.pi

    # Caso 5
    if tmin >= tb and tmax > tu:

        theta = np.arcsin((tu - tmean) / alpha)

        return (
            (
                (tmean - tb)
                * (theta + np.pi/2)
            )
            +
            (
                alpha
                * np.cos(theta)
            )
            +
            (
                (tu - tb)
                * (np.pi/2 - theta)
            )
        ) / np.pi

    # Caso 6
    if tmin < tb and tmax > tu:

        theta1 = np.arcsin((tb - tmean) / alpha)
        theta2 = np.arcsin((tu - tmean) / alpha)

        return (
            (
                (tmean - tb)
                * (theta2 - theta1)
            )
            +
            (
                alpha
                * (
                    np.cos(theta1)
                    -
                    np.cos(theta2)
                )
            )
            +
            (
                (tu - tb)
                * (np.pi/2 - theta2)
            )
        ) / np.pi

    return np.nan

# =============================================================================
# STORAGE
# =============================================================================

results = []

all_curves = []

# =============================================================================
# PROCESS ALL SEASONS
# =============================================================================

for sheet in xls.sheet_names:

    print("\n================================================")
    print(sheet)
    print("================================================")

    df = pd.read_excel(
        FILE_PATH,
        sheet_name=sheet
    )

    # =========================================================================
    # DATE
    # =========================================================================

    df["Fecha"] = pd.to_datetime(
        df["Fecha"]
    )

    df = df.sort_values("Fecha")

    # =========================================================================
    # FIND ELP4
    # =========================================================================

    mask_elp4 = (
        df["ELP Observado"] == 4
    )

    if not mask_elp4.any():

        print("⚠ No ELP 4")
        continue

    fecha_brotacion = df.loc[
        mask_elp4,
        "Fecha"
    ].iloc[0]

    print(f"ELP4: {fecha_brotacion}")

    # =========================================================================
    # DEFINE T0
    # =========================================================================

    t0 = pd.Timestamp(
        year=fecha_brotacion.year,
        month=9,
        day=1
    )

    # =========================================================================
    # FILTER PERIOD
    # =========================================================================

    df_period = df[
        (df["Fecha"] >= t0)
        &
        (df["Fecha"] <= fecha_brotacion)
    ].copy()

    # =========================================================================
    # GDD
    # =========================================================================

    df_period["gdd"] = df_period.apply(

        lambda row: gdd_simple(
            row["temp_max_grado_c"],
            row["temp_min_grado_c"],
            Tb,
            Tu
        ),

        axis=1
    )

    df_period["gdd_acumulado"] = (
        df_period["gdd"]
        .cumsum()
    )

    gdd_total = (
        df_period["gdd_acumulado"]
        .iloc[-1]
    )

    dias = (
        df_period["Fecha"].max()
        -
        df_period["Fecha"].min()
    ).days

    print(f"GDD total: {round(gdd_total,2)}")

    # =========================================================================
    # SAVE RESULTS
    # =========================================================================

    results.append({

        "season": sheet,

        "fecha_brotacion": fecha_brotacion,

        "dias": dias,

        "gdd_total": round(gdd_total,2)
    })

    curve = df_period[[
        "Fecha",
        "gdd_acumulado"
    ]].copy()

    curve["season"] = sheet

    all_curves.append(curve)

# =============================================================================
# RESULTS
# =============================================================================

results_df = pd.DataFrame(results)

print("\n================================================")
print("RESULTADOS")
print("================================================")

print(results_df)

# =============================================================================
# AVERAGE
# =============================================================================

gdd_promedio = (
    results_df["gdd_total"]
    .mean()
)

dias_promedio = (
    results_df["dias"]
    .mean()
)

print("\n================================================")
print("PROMEDIO MULTI-TEMPORADA")
print("================================================")

print(f"GDD promedio : {round(gdd_promedio,2)}")
print(f"Días promedio: {round(dias_promedio,2)}")

# =============================================================================
# STATS
# =============================================================================

print("\n================================================")
print("ESTADISTICAS MULTI-TEMPORADA")
print("================================================")

print(results_df)

print("\nResumen:")

print(
    results_df[
        [
            "gdd_total",
            "dias"
        ]
    ].describe()
)

gdd_promedio = (
    results_df["gdd_total"]
    .mean()
)

gdd_std = (
    results_df["gdd_total"]
    .std()
)

gdd_cv = (
    gdd_std
    /
    gdd_promedio
) * 100

print(f"\nGDD promedio : {round(gdd_promedio,2)}")
print(f"GDD std      : {round(gdd_std,2)}")
print(f"GDD CV (%)   : {round(gdd_cv,2)}")


# =============================================================================
# NORMALIZED DAY INDEX
# =============================================================================

for curve in all_curves:

    curve["dia_relativo"] = np.arange(
        len(curve)
    )


# =============================================================================
# PLOT COMPARABLE
# =============================================================================

fig, ax = plt.subplots(figsize=(14,6))

for curve in all_curves:

    season = curve["season"].iloc[0]

    fechas = pd.to_datetime(
        curve["Fecha"]
    )

    labels = fechas.dt.strftime("%b")

    ax.plot(
        curve["dia_relativo"],
        curve["gdd_acumulado"],
        linewidth=2,
        label=season
    )

# =============================================================================
# MONTH TICKS
# =============================================================================

reference_curve = all_curves[0]

reference_dates = pd.to_datetime(
    reference_curve["Fecha"]
)

reference_months = (
    reference_dates.dt.strftime("%b")
)

month_positions = []

month_labels = []

last_month = None

for i, month in enumerate(reference_months):

    if month != last_month:

        month_positions.append(i)
        month_labels.append(month)

        last_month = month

ax.set_xticks(month_positions)

ax.set_xticklabels(
    month_labels,
    fontsize=11
)

# =============================================================================
# FINAL STYLE
# =============================================================================

ax.set_title(
    "Curvas acumuladas GDD\nCabernet Sauvignon - Lourdes",
    fontsize=15
)

ax.set_xlabel(
    "Mes fenológico",
    fontsize=12
)

ax.set_ylabel(
    "GDD acumulado",
    fontsize=12
)

ax.legend()

plt.tight_layout()

plt.show()