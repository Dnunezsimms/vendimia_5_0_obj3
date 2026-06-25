"""
Script reproducible: Construcción canónica de series temporales GDD por candidato de Biofix.
Genera:
  - models/indicador_biologico/outputs_multisite_gdd/gdd_acumulado_por_biofix.csv
  - models/indicador_biologico/outputs_multisite_gdd/gdd_acumulado_por_biofix_summary.csv

Parámetros térmicos canónicos adoptados:
  - Método: Seno simple (single sine)
  - Tb (Umbral base): 10.0 °C
  - Tu (Corte superior): 35.0 °C
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.dashboard_obj3_integrado.src.loaders import load_gdd_latitudinal

OUTPUT_DIR = REPO_ROOT / "models" / "indicador_biologico" / "outputs_multisite_gdd"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROC_CLIMA_DIR = REPO_ROOT / "data" / "processed" / "phenology_climate"

CS_T0_PATH = OUTPUT_DIR / "method_pipeline_cs_t0_operativo_by_fundo.csv"
VAR_EVAL_PATH = OUTPUT_DIR / "method_pipeline_varietal_evaluation_by_fundo.csv"

# Mapeo de nombres de display y fuentes climáticas canónicas por fundo
FUNDO_DISPLAY_MAP = {
    "qba_seca": "Quebrada Seca",
    "los_acacios": "Los Acacios",
    "ucuquer": "Ucuquer",
    "idahue": "Idahue",
    "nilahue": "Nilahue",
    "lourdes": "Lourdes",
    "keule": "Keule",
}

FUENTE_CLIMA_MAP = {
    "qba_seca": "Datavid",
    "los_acacios": "INIA/Agromet",
    "ucuquer": "Datavid",
    "idahue": "Zentra",
    "nilahue": "Zentra",
    "lourdes": "INIA/Agromet",
    "keule": "Zentra",
}

def gdd_seno_simple(tmax, tmin, tb=10.0, tu=35.0):
    """
    Fórmula canónica de Seno Simple (Single Sine) con umbral base Tb=10 y tope Tu=35.
    """
    if pd.isna(tmax) or pd.isna(tmin):
        return np.nan
    tmean = (tmax + tmin) / 2.0
    alpha = (tmax - tmin) / 2.0
    if alpha == 0:
        return max(0.0, min(tmean, tu) - tb)
    if tmax <= tb:
        return 0.0
    if tmin >= tu:
        return tu - tb
    if tmin >= tb and tmax <= tu:
        return tmean - tb
    if tmin < tb and tmax <= tu:
        theta = np.arcsin((tb - tmean) / alpha)
        return (((tmean - tb) * (np.pi / 2.0 - theta)) + (alpha * np.cos(theta))) / np.pi
    if tmin >= tb and tmax > tu:
        theta = np.arcsin((tu - tmean) / alpha)
        return (((tmean - tb) * (theta + np.pi / 2.0)) + (alpha * np.cos(theta)) + ((tu - tb) * (np.pi / 2.0 - theta))) / np.pi
    if tmin < tb and tmax > tu:
        theta1 = np.arcsin((tb - tmean) / alpha)
        theta2 = np.arcsin((tu - tmean) / alpha)
        return (((tmean - tb) * (theta2 - theta1)) + (alpha * (np.cos(theta1) - np.cos(theta2))) + ((tu - tb) * (np.pi / 2.0 - theta2))) / np.pi
    return np.nan

def build_canonical_outputs():
    print("=== INICIANDO CONSTRUCCIÓN CANÓNICA GDD POR BIOFIX ===")
    
    cs_df = pd.read_csv(CS_T0_PATH)
    var_df = pd.read_csv(VAR_EVAL_PATH)
    
    # Cargar diagnóstico de regresión latitudinal
    lat_data = load_gdd_latitudinal()
    lat_diag = lat_data["diagnostico"]
    
    # Construir mapa de t0 latitudinal por fundo
    t0_lat_map = {}
    for _, r in lat_diag.iterrows():
        f_id = str(r["fundo"]).strip().lower()
        doy = r.get("doy_t0_pred_reg_lat", np.nan)
        if pd.notna(doy):
            # En temporada 2025_2026, DOY 1 es 2025-01-01
            t0_lat_date = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(round(float(doy))) - 1)
            t0_lat_map[f_id] = t0_lat_date.strftime("%Y-%m-%d")
        else:
            t0_lat_map[f_id] = np.nan

    # Unificar lista maestro de los 28 combinaciones fundos x variedades
    cases = []
    
    # 1. Casos Cabernet Sauvignon (7 fundos)
    for _, r in cs_df.iterrows():
        f_id = str(r["fundo_id"]).strip().lower()
        cases.append({
            "fundo": f_id,
            "Fundo": FUNDO_DISPLAY_MAP.get(f_id, r.get("Fundo", f_id)),
            "temporada": str(r["temporada_representativa"]),
            "variedad": "cabernet_sauvignon",
            "t0_operativo": str(r["t0 Estimado"]) if pd.notna(r["t0 Estimado"]) else np.nan,
            "t0_latitudinal": t0_lat_map.get(f_id, np.nan),
            "fecha_brotacion_ELP4": str(r["Fecha Brotacion"]) if pd.notna(r["Fecha Brotacion"]) else np.nan,
            "threshold_GDD_usado": float(r["GDD Acumulado"]) if pd.notna(r["GDD Acumulado"]) else 70.0,
        })
        
    # 2. Casos otras variedades (21 combinaciones)
    for _, r in var_df.iterrows():
        f_id = str(r["fundo_id"]).strip().lower()
        v_id = str(r["variedad_id"]).strip().lower()
        cs_match = cs_df[cs_df["fundo_id"].astype(str).str.strip().str.lower() == f_id]
        t0_op = str(cs_match.iloc[0]["t0 Estimado"]) if not cs_match.empty and pd.notna(cs_match.iloc[0]["t0 Estimado"]) else np.nan
        
        cases.append({
            "fundo": f_id,
            "Fundo": FUNDO_DISPLAY_MAP.get(f_id, r.get("Fundo", f_id)),
            "temporada": str(r["temporada"]),
            "variedad": v_id,
            "t0_operativo": t0_op,
            "t0_latitudinal": t0_lat_map.get(f_id, np.nan),
            "fecha_brotacion_ELP4": str(r["Fecha Brotacion"]) if pd.notna(r["Fecha Brotacion"]) else np.nan,
            "threshold_GDD_usado": float(r["gdd_variedad_final"]) if pd.notna(r["gdd_variedad_final"]) else np.nan,
        })

    timeseries_rows = []
    summary_rows = []

    fixed_biofixes = [
        ("1_julio", "2025-07-01"),
        ("1_agosto", "2025-08-01"),
        ("15_agosto", "2025-08-15"),
        ("1_septiembre", "2025-09-01"),
    ]

    print(f"Total casos maestro a procesar: {len(cases)}")

    for case in cases:
        fundo = case["fundo"]
        Fundo = case["Fundo"]
        temporada = case["temporada"]
        variedad = case["variedad"]
        t0_op = case["t0_operativo"]
        t0_lat = case["t0_latitudinal"]
        brot_elp4 = case["fecha_brotacion_ELP4"]
        threshold = case["threshold_GDD_usado"]
        
        fuente_clima = FUENTE_CLIMA_MAP.get(fundo, "Desconocido")
        archivo_origen = f"data/processed/phenology_climate/{fundo}_{variedad}_{temporada}.xlsx"
        xlsx_path = REPO_ROOT / archivo_origen
        
        clima_df = pd.DataFrame()
        if xlsx_path.exists():
            try:
                clima_df = pd.read_excel(xlsx_path)
                clima_df["Fecha"] = pd.to_datetime(clima_df["Fecha"], errors="coerce")
                clima_df = clima_df.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)
            except Exception as e:
                print(f"Advertencia: Error leyendo {archivo_origen}: {e}")
        else:
            print(f"Advertencia: Archivo climático no encontrado: {archivo_origen}")

        case_biofixes = list(fixed_biofixes)
        case_biofixes.append(("t0_operativo", t0_op))
        case_biofixes.append(("t0_latitudinal", t0_lat))

        t0_ref = t0_op if pd.notna(t0_op) and str(t0_op) != "nan" else t0_lat

        for b_tipo, b_fecha in case_biofixes:
            is_missing_insumo = pd.isna(b_fecha) or str(b_fecha).strip().lower() == "nan"
            
            if is_missing_insumo or clima_df.empty:
                alerta_msg = "NA: Insumo faltante (sin biofix definido o sin archivo climático)"
                diag_code = "sin_t0_operativo" if b_tipo == "t0_operativo" else "revisar"
                
                timeseries_rows.append({
                    "fundo": fundo,
                    "Fundo": Fundo,
                    "temporada": temporada,
                    "variedad": variedad,
                    "fecha": np.nan,
                    "biofix_tipo": b_tipo,
                    "biofix_fecha": np.nan,
                    "t0_operativo": t0_op,
                    "t0_latitudinal": t0_lat,
                    "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_diario": np.nan,
                    "gdd_acumulado": np.nan,
                    "gdd_acumulado_previo_t0": np.nan,
                    "threshold_GDD_usado": threshold,
                    "fuente_clima": fuente_clima,
                    "archivo_origen": archivo_origen,
                    "alerta_temporada_anterior": alerta_msg,
                    "diagnostico_biofix": diag_code,
                })
                summary_rows.append({
                    "fundo": fundo,
                    "temporada": temporada,
                    "variedad": variedad,
                    "biofix_tipo": b_tipo,
                    "biofix_fecha": np.nan,
                    "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_acumulado_a_brotacion": np.nan,
                    "gdd_acumulado_previo_t0": np.nan,
                    "threshold_GDD_usado": threshold,
                    "alerta_temporada_anterior": alerta_msg,
                    "diagnostico_biofix": diag_code,
                })
                continue

            b_dt = pd.Timestamp(b_fecha)
            end_dt = pd.Timestamp("2025-11-30")
            
            sub_clima = clima_df[(clima_df["Fecha"] >= b_dt) & (clima_df["Fecha"] <= end_dt)].copy()
            
            if sub_clima.empty:
                alerta_msg = "NA: Serie climática vacía en ventana posterior a biofix"
                diag_code = "revisar"
                summary_rows.append({
                    "fundo": fundo,
                    "temporada": temporada,
                    "variedad": variedad,
                    "biofix_tipo": b_tipo,
                    "biofix_fecha": b_fecha,
                    "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_acumulado_a_brotacion": np.nan,
                    "gdd_acumulado_previo_t0": np.nan,
                    "threshold_GDD_usado": threshold,
                    "alerta_temporada_anterior": alerta_msg,
                    "diagnostico_biofix": diag_code,
                })
                continue

            gdd_daily_vals = []
            for _, cr in sub_clima.iterrows():
                gdd_daily_vals.append(gdd_seno_simple(cr.get("temp_max_grado_c"), cr.get("temp_min_grado_c")))
            sub_clima["gdd_diario"] = gdd_daily_vals
            sub_clima["gdd_acumulado"] = sub_clima["gdd_diario"].fillna(0.0).cumsum()

            gdd_previo_t0 = 0.0
            if pd.notna(t0_ref) and str(t0_ref) != "nan":
                t0_ref_dt = pd.Timestamp(t0_ref)
                if b_dt < t0_ref_dt:
                    prev_sub = sub_clima[sub_clima["Fecha"] < t0_ref_dt]
                    gdd_previo_t0 = float(prev_sub["gdd_diario"].fillna(0.0).sum())

            has_brot = pd.notna(brot_elp4) and str(brot_elp4).strip().lower() != "nan"
            
            alerta_msg = "NO"
            diag_code = "OK"
            
            if gdd_previo_t0 > 0.1:
                alerta_msg = f"SI: Acumulación térmica previa a t0 ({gdd_previo_t0:.1f} GDD acumulados invernales)"
                diag_code = "acumulacion_termica_previa_a_t0"
            elif has_brot and b_dt > pd.Timestamp(brot_elp4):
                alerta_msg = "SI: Biofix posterior a fecha de brotación observada"
                diag_code = "biofix_posterior_a_brotacion"
            elif not has_brot:
                diag_code = "sin_brotacion"

            gdd_a_brot = np.nan
            if has_brot:
                brot_dt = pd.Timestamp(brot_elp4)
                brot_match = sub_clima[sub_clima["Fecha"] == brot_dt]
                if not brot_match.empty:
                    gdd_a_brot = float(brot_match.iloc[0]["gdd_acumulado"])
                else:
                    prev_matches = sub_clima[sub_clima["Fecha"] <= brot_dt]
                    if not prev_matches.empty:
                        gdd_a_brot = float(prev_matches.iloc[-1]["gdd_acumulado"])

            summary_rows.append({
                "fundo": fundo,
                "temporada": temporada,
                "variedad": variedad,
                "biofix_tipo": b_tipo,
                "biofix_fecha": b_fecha,
                "fecha_brotacion_ELP4": brot_elp4,
                "gdd_acumulado_a_brotacion": gdd_a_brot,
                "gdd_acumulado_previo_t0": gdd_previo_t0,
                "threshold_GDD_usado": threshold,
                "alerta_temporada_anterior": alerta_msg,
                "diagnostico_biofix": diag_code,
            })

            for _, cr in sub_clima.iterrows():
                timeseries_rows.append({
                    "fundo": fundo,
                    "Fundo": Fundo,
                    "temporada": temporada,
                    "variedad": variedad,
                    "fecha": cr["Fecha"].strftime("%Y-%m-%d"),
                    "biofix_tipo": b_tipo,
                    "biofix_fecha": b_fecha,
                    "t0_operativo": t0_op,
                    "t0_latitudinal": t0_lat,
                    "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_diario": float(cr["gdd_diario"]) if pd.notna(cr["gdd_diario"]) else np.nan,
                    "gdd_acumulado": float(cr["gdd_acumulado"]) if pd.notna(cr["gdd_acumulado"]) else np.nan,
                    "gdd_acumulado_previo_t0": gdd_previo_t0,
                    "threshold_GDD_usado": threshold,
                    "fuente_clima": fuente_clima,
                    "archivo_origen": archivo_origen,
                    "alerta_temporada_anterior": alerta_msg,
                    "diagnostico_biofix": diag_code,
                })

    out_ts = pd.DataFrame(timeseries_rows)
    out_sum = pd.DataFrame(summary_rows)

    csv_ts_path = OUTPUT_DIR / "gdd_acumulado_por_biofix.csv"
    csv_sum_path = OUTPUT_DIR / "gdd_acumulado_por_biofix_summary.csv"

    out_ts.to_csv(csv_ts_path, index=False)
    out_sum.to_csv(csv_sum_path, index=False)

    print(f"=== GENERADO ÉXITOSAMENTE ===")
    print(f"  -> {csv_ts_path} (Shape: {out_ts.shape})")
    print(f"  -> {csv_sum_path} (Shape: {out_sum.shape})")

if __name__ == "__main__":
    build_canonical_outputs()
