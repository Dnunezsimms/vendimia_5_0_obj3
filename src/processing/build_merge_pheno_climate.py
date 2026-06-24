from pathlib import Path
import pandas as pd
import numpy as np
import re


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CLIMATE_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "climate"
)

PHENOLOGY_FILE = (
    BASE_DIR
    / "data"
    / "prepared"
    / "phenology"
    / "fenologia_limpia.xlsx"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "prepared"
    / "phenology_climate"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEASON = "2025_2026"


# =============================================================================
# FUNDO MAP
# =============================================================================

FOLDER_TO_FUNDO = {

    "keule": "keule",

    "quebrada_seca": "qba_seca",

    "lourdes": "lourdes",

    "los_acacios": "los_acacios",

    "idahue": "idahue",

    "nilahue": "nilahue",

    "ucuquer": "ucuquer",
}


# =============================================================================
# HELPERS
# =============================================================================

def normalize_columns(columns):

    out = []

    for c in columns:

        c = str(c)

        c = c.replace("\n", " ")
        c = c.replace("\r", " ")

        c = c.strip()

        out.append(c)

    return out


def find_col(columns, keywords):

    for col in columns:

        c = str(col).lower()

        for kw in keywords:

            if kw in c:
                return col

    return None


# =============================================================================
# ELP PARSER
# =============================================================================

def parse_elp(value):

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    if value == "":
        return np.nan

    # ranges like 19-25
    if "-" in value:

        nums = re.findall(r"\d+", value)

        if len(nums) == 2:

            avg = np.mean([
                float(nums[0]),
                float(nums[1])
            ])

            return int(avg)

    # values like 1,2
    if "," in value:

        nums = re.findall(r"\d+", value)

        if len(nums) >= 1:

            return int(float(nums[0]))

    try:
        return int(float(value))

    except:
        return np.nan


# =============================================================================
# PARSE ZENTRA
# =============================================================================

def parse_zentra(file_path):

    print(f"\nProcessing Zentra: {file_path.name}")

    raw = pd.read_csv(
        file_path,
        header=None,
        low_memory=False
    )

    header_row = None

    for i in range(min(15, len(raw))):

        row = (
            raw.iloc[i]
            .fillna("")
            .astype(str)
        )

        row_text = " ".join(
            row.tolist()
        ).lower()

        if (
            "timestamp" in row_text
            or "timestamps" in row_text
        ):

            header_row = i
            break

    if header_row is None:

        print(f"\n⚠ Skipping incompatible file: {file_path.name}")

        return None

    df = pd.read_csv(
        file_path,
        skiprows=header_row,
        low_memory=False
    )

    df.columns = normalize_columns(
        df.columns
    )

    time_col = find_col(
        df.columns,
        ["timestamp"]
    )

    temp_col = find_col(
        df.columns,
        ["air temperature"]
    )

    rain_col = find_col(
        df.columns,
        ["precipitation"]
    )

    rad_col = find_col(
        df.columns,
        ["solar radiation"]
    )

    rh_col = find_col(
        df.columns,
        ["relative humidity"]
    )

    if time_col is None:

        print(f"\n⚠ No timestamp column: {file_path.name}")

        return None

    df["timestamp"] = pd.to_datetime(
        df[time_col],
        format="mixed",
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp"]
    )

    out = pd.DataFrame()

    out["timestamp"] = df["timestamp"]

    out["temperature"] = pd.to_numeric(
        df[temp_col],
        errors="coerce"
    ) if temp_col else np.nan

    out["rain"] = pd.to_numeric(
        df[rain_col],
        errors="coerce"
    ) if rain_col else np.nan

    out["radiation"] = pd.to_numeric(
        df[rad_col],
        errors="coerce"
    ) if rad_col else np.nan

    out["rh"] = pd.to_numeric(
        df[rh_col],
        errors="coerce"
    ) if rh_col else np.nan

    out["Fecha"] = (
        out["timestamp"]
        .dt.normalize()
    )

    daily = (
        out
        .groupby("Fecha")
        .agg({

            "temperature": [
                "min",
                "max",
                "mean"
            ],

            "rain": "sum",

            "radiation": "mean",

            "rh": "mean"
        })
    )

    daily.columns = [

        "temp_min_grado_c",

        "temp_max_grado_c",

        "temp_media_grado_c",

        "precipitacion_mm",

        "radiacion_w_m2",

        "humedad_rel_%"
    ]

    daily = daily.reset_index()

    daily["radiacion_mj/m2"] = (
        daily["radiacion_w_m2"] * 0.0864
    )

    daily = daily.drop(
        columns=["radiacion_w_m2"]
    )

    return daily


# =============================================================================
# PARSE INIA
# =============================================================================

def parse_inia(file_path):

    print(f"\nProcessing INIA: {file_path.name}")

    raw = pd.read_csv(
        file_path,
        header=None,
        low_memory=False
    )

    header_row = None

    for i in range(min(20, len(raw))):

        row = (
            raw.iloc[i]
            .fillna("")
            .astype(str)
        )

        row_text = " ".join(
            row.tolist()
        ).lower()

        if (
            "temperatura" in row_text
            and "humedad" in row_text
        ):

            header_row = i
            break

    if header_row is None:

        raise ValueError(
            f"Could not detect INIA header row: {file_path.name}"
        )

    df = pd.read_csv(
        file_path,
        skiprows=header_row,
        low_memory=False
    )

    df.columns = normalize_columns(
        df.columns
    )

    date_col = find_col(
        df.columns,
        [
            "tiempo",
            "fecha",
            "date"
        ]
    )

    tmean_col = find_col(
        df.columns,
        [
            "temperatura del aire ºc"
        ]
    )

    tmin_col = find_col(
        df.columns,
        [
            "mínima"
        ]
    )

    tmax_col = find_col(
        df.columns,
        [
            "máxima"
        ]
    )

    rain_col = find_col(
        df.columns,
        [
            "precipitación"
        ]
    )

    rad_col = find_col(
        df.columns,
        [
            "radiación"
        ]
    )

    rh_col = find_col(
        df.columns,
        [
            "humedad relativa %"
        ]
    )

    out = pd.DataFrame()

    out["Fecha"] = pd.to_datetime(
        df[date_col],
        dayfirst=True,
        format="%d-%m-%Y",
        errors="coerce"
    )

    out["Fecha"] = (
        out["Fecha"]
        .dt.normalize()
    )

    out["humedad_rel_%"] = pd.to_numeric(
        df[rh_col],
        errors="coerce"
    ) if rh_col else np.nan

    out["temp_media_grado_c"] = pd.to_numeric(
        df[tmean_col],
        errors="coerce"
    ) if tmean_col else np.nan

    out["precipitacion_mm"] = pd.to_numeric(
        df[rain_col],
        errors="coerce"
    ) if rain_col else np.nan

    out["temp_min_grado_c"] = pd.to_numeric(
        df[tmin_col],
        errors="coerce"
    ) if tmin_col else np.nan

    out["temp_max_grado_c"] = pd.to_numeric(
        df[tmax_col],
        errors="coerce"
    ) if tmax_col else np.nan

    out["radiacion_mj/m2"] = pd.to_numeric(
        df[rad_col],
        errors="coerce"
    ) if rad_col else np.nan

    out = out.dropna(
        subset=["Fecha"]
    )

    out = out.sort_values(
        by="Fecha"
    )

    out = out.reset_index(
        drop=True
    )

    return out


# =============================================================================
# PHENOLOGY
# =============================================================================

def parse_phenology():

    xls = pd.ExcelFile(
        PHENOLOGY_FILE
    )

    all_data = []

    for sheet in xls.sheet_names:

        print(f"\nProcessing phenology: {sheet}")

        df = pd.read_excel(
            PHENOLOGY_FILE,
            sheet_name=sheet
        )

        df.columns = normalize_columns(
            df.columns
        )

        df["Fecha"] = pd.to_datetime(
            df["Fecha"],
            errors="coerce"
        )

        df["Fecha"] = (
            df["Fecha"]
            .dt.normalize()
        )

        df = df.dropna(
            subset=["Fecha"]
        )

        variety_cols = [

            c for c in df.columns

            if c != "Fecha"
        ]

        for variety in variety_cols:

            print(f"\nProcessing variety: {variety}")

            tmp = pd.DataFrame({

                "Fecha": df["Fecha"],

                "raw_elp": (
                    df[variety]
                    .astype(str)
                    .str.strip()
                )
            })

            tmp = tmp[
                tmp["raw_elp"].notna()
            ].copy()

            tmp = tmp[
                tmp["raw_elp"] != ""
            ].copy()

            tmp = tmp[
                tmp["raw_elp"].str.lower() != "nan"
            ].copy()

            tmp["ELP Observado"] = (
                tmp["raw_elp"]
                .apply(parse_elp)
            )

            tmp = tmp.dropna(
                subset=[
                    "Fecha",
                    "ELP Observado"
                ]
            )

            tmp["ELP Observado"] = pd.to_numeric(
                tmp["ELP Observado"],
                errors="coerce"
            )

            tmp["Fundo"] = (
                sheet.lower()
            )

            tmp["Variedad"] = (

                variety
                .lower()
                .replace(" ", "_")
            )

            tmp = tmp.sort_values(
                by="Fecha"
            )

            tmp = tmp.reset_index(
                drop=True
            )

            print(
                f"✓ {variety}: "
                f"{len(tmp)} observaciones válidas"
            )

            all_data.append(tmp)

    if len(all_data) == 0:

        raise ValueError(
            "No phenology data parsed."
        )

    final = pd.concat(
        all_data,
        ignore_index=True
    )

    final = final.sort_values(
        by=[
            "Fundo",
            "Variedad",
            "Fecha"
        ]
    )

    final = final.reset_index(
        drop=True
    )

    return final


# =============================================================================
# MAIN
# =============================================================================

def main():

    phenology = parse_phenology()

    expected_outputs = set()

    generated_outputs = set()

    for _, row in phenology.iterrows():

        expected_outputs.add(

            f"{row['Fundo']}_"
            f"{row['Variedad']}_"
            f"{SEASON}.xlsx"
        )

    climate_files = []

    for f in CLIMATE_DIR.rglob("*.csv"):

        fname = f.name.lower()

        skip_patterns = [

            "metadata",
            "catalog",
            "station",
            "estaciones",
            "listado",
            "summary",
            "diagnostic",
            "raw"
        ]

        if any(p in fname for p in skip_patterns):
            continue

        climate_files.append(f)

    for climate_file in climate_files:

        folder_name = (
            climate_file.parent.name
            .lower()
        )

        fundo = FOLDER_TO_FUNDO.get(
            folder_name,
            folder_name
        )

        print(f"\nDetected fundo: {fundo}")

        fname = climate_file.name.lower()

        if (
            "agrometeorologia" in fname
            or "inia" in fname
        ):

            climate = parse_inia(
                climate_file
            )

        else:

            climate = parse_zentra(
                climate_file
            )

        if climate is None:
            continue

        climate["Fecha"] = (
            climate["Fecha"]
            .dt.normalize()
        )

        pheno_fundo = phenology[
            phenology["Fundo"] == fundo
        ]

        if pheno_fundo.empty:

            print(f"No phenology for {fundo}")
            continue

        for variety in pheno_fundo[
            "Variedad"
        ].unique():

            pheno_var = pheno_fundo[
                pheno_fundo["Variedad"]
                == variety
            ].copy()

            pheno_var["Fecha"] = (
                pheno_var["Fecha"]
                .dt.normalize()
            )

            merged = pd.merge(

                climate,

                pheno_var[
                    ["Fecha", "ELP Observado"]
                ],

                on="Fecha",

                how="left"
            )

            merged = merged.sort_values(
                by="Fecha"
            )

            merged["ELP Observado"] = pd.to_numeric(
                merged["ELP Observado"],
                errors="coerce"
            )

            output_name = (

                f"{fundo}_"
                f"{variety}_"
                f"{SEASON}.xlsx"
            )

            output_path = (
                OUTPUT_DIR
                / output_name
            )

            merged.to_excel(
                output_path,
                index=False
            )

            generated_outputs.add(
                output_name
            )

            print(f"Saved: {output_name}")

    missing = (
        expected_outputs
        - generated_outputs
    )

    print("\n===================================")
    print("MISSING MERGE OUTPUTS")
    print("===================================")

    if len(missing) == 0:

        print("NONE")

    else:

        for m in sorted(missing):
            print(m)

    print("===================================")

    print("\nDONE")


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    main()