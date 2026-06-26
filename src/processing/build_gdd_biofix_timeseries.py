"""
Script reproducible: Construcción canónica de series temporales GDD y Diagnóstico de Valle Térmico por candidato de Biofix.
Genera:
  - models/indicador_biologico/outputs_multisite_gdd/gdd_acumulado_por_biofix.csv
  - models/indicador_biologico/outputs_multisite_gdd/gdd_acumulado_por_biofix_summary.csv
  - models/indicador_biologico/outputs_multisite_gdd/thermal_valley_diagnostics_by_biofix.csv

Parámetros térmicos canónicos adoptados:
  - Método: Seno simple (single sine)
  - Tb (Umbral base): 10.0 °C
  - Tu (Corte superior): 35.0 °C
  - Valle térmico: Promedio móvil 14 días de Temperatura Media diaria (Tmax + Tmin)/2
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
    """Fórmula canónica de Seno Simple (Single Sine) con umbral base Tb=10 y tope Tu=35."""
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
    print("=== INICIANDO CONSTRUCCIÓN CANÓNICA GDD POR BIOFIX Y VALLE TÉRMICO ===")
    
    cs_df = pd.read_csv(CS_T0_PATH)
    var_df = pd.read_csv(VAR_EVAL_PATH)
    
    lat_data = load_gdd_latitudinal()
    lat_diag = lat_data["diagnostico"]
    
    t0_lat_map = {}
    for _, r in lat_diag.iterrows():
        f_id = str(r["fundo"]).strip().lower()
        doy = r.get("doy_t0_pred_reg_lat", np.nan)
        if pd.notna(doy):
            t0_lat_date = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(round(float(doy))) - 1)
            t0_lat_map[f_id] = t0_lat_date.strftime("%Y-%m-%d")
        else:
            t0_lat_map[f_id] = np.nan

    cases = []
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
    diag_rows = []

    fixed_biofixes = [
        ("15_julio", "2025-07-15"),
        ("1_agosto", "2025-08-01"),
        ("15_agosto", "2025-08-15"),
        ("1_septiembre", "2025-09-01"),
    ]

    print(f"Total combinaciones fundo x variedad a procesar: {len(cases)}")

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

        case_biofixes = list(fixed_biofixes)

        t0_ref = t0_op if pd.notna(t0_op) and str(t0_op) != "nan" else t0_lat

        # Diagnóstico de valle térmico base del viñedo
        fecha_fondo_valle = np.nan
        valor_minimo_valle = np.nan
        metrica_valle = "promedio_movil_14d_temp_media"
        start_win_str = np.nan
        end_win_str = np.nan
        gdd_previo_a_t0 = np.nan

        if not clima_df.empty:
            clima_df["temp_media"] = (clima_df["temp_max_grado_c"] + clima_df["temp_min_grado_c"]) / 2.0
            clima_df["gdd_diario_real"] = [gdd_seno_simple(r["temp_max_grado_c"], r["temp_min_grado_c"]) for _, r in clima_df.iterrows()]
            clima_df["rolling_tmean_14"] = clima_df["temp_media"].rolling(14, center=True, min_periods=7).mean()
            clima_df["rolling_gdd_14"] = clima_df["gdd_diario_real"].rolling(14, center=True, min_periods=7).mean()
            
            start_win_str = clima_df["Fecha"].min().strftime("%Y-%m-%d")
            end_win_str = clima_df["Fecha"].max().strftime("%Y-%m-%d")

            winter_sub = clima_df[(clima_df["Fecha"] >= "2025-05-01") & (clima_df["Fecha"] <= "2025-08-31")]
            if not winter_sub.empty and not winter_sub["rolling_gdd_14"].isna().all():
                min_val = float(winter_sub["rolling_gdd_14"].min())
                flat_rows = winter_sub[winter_sub["rolling_gdd_14"] <= min_val + 0.05]
                mid_idx = flat_rows.index[len(flat_rows) // 2]
                valle_row = clima_df.loc[mid_idx]
                fecha_fondo_valle = valle_row["Fecha"].strftime("%Y-%m-%d")
                valor_minimo_valle = float(valle_row["rolling_gdd_14"])
                if len(flat_rows) > 7:
                    metrica_valle = f"valle_termico_extendido_{len(flat_rows)}d"
                else:
                    metrica_valle = "promedio_movil_14d_gdd_diario"

            if pd.notna(t0_ref) and str(t0_ref) != "nan":
                t0_dt_ref = pd.Timestamp(t0_ref)
                gdd_previo_a_t0 = float(clima_df[clima_df["Fecha"] < t0_dt_ref]["gdd_diario_real"].fillna(0.0).sum())

        for b_tipo, b_fecha in case_biofixes:
            is_missing_insumo = pd.isna(b_fecha) or str(b_fecha).strip().lower() == "nan"
            
            if is_missing_insumo or clima_df.empty:
                alerta_msg = "NA: Insumo faltante (sin biofix definido o sin archivo climático)"
                diag_code = "sin_t0_operativo" if b_tipo == "t0_operativo" else "revisar"
                
                timeseries_rows.append({
                    "fundo": fundo, "Fundo": Fundo, "temporada": temporada, "variedad": variedad,
                    "fecha": np.nan, "biofix_tipo": b_tipo, "biofix_fecha": np.nan,
                    "t0_operativo": t0_op, "t0_latitudinal": t0_lat, "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_diario": np.nan, "gdd_acumulado": np.nan, "gdd_acumulado_previo_t0": np.nan,
                    "gdd_entre_biofix_y_t0": np.nan,
                    "temp_media": np.nan, "rolling_tmean_14": np.nan, "rolling_gdd_14": np.nan, "fecha_fondo_valle": np.nan,
                    "valor_minimo_valle": np.nan, "dias_biofix_vs_valle": np.nan, "diagnostico_valle": "revisar",
                    "comentario_metodologico": alerta_msg, "threshold_GDD_usado": threshold,
                    "fuente_clima": fuente_clima, "archivo_origen": archivo_origen,
                    "alerta_temporada_anterior": alerta_msg, "diagnostico_biofix": diag_code,
                })
                summary_rows.append({
                    "fundo": fundo, "temporada": temporada, "variedad": variedad, "biofix_tipo": b_tipo,
                    "biofix_fecha": np.nan, "fecha_brotacion_ELP4": brot_elp4, "gdd_acumulado_a_brotacion": np.nan,
                    "gdd_acumulado_previo_t0": np.nan, "gdd_entre_biofix_y_t0": np.nan, "dias_biofix_vs_valle": np.nan,
                    "diagnostico_valle": "revisar", "threshold_GDD_usado": threshold,
                    "alerta_temporada_anterior": alerta_msg, "diagnostico_biofix": diag_code,
                })
                diag_rows.append({
                    "fundo": fundo, "Fundo": Fundo, "temporada": temporada, "variedad": variedad,
                    "biofix_tipo": b_tipo, "biofix_fecha": np.nan, "t0_operativo": t0_op, "t0_latitudinal": t0_lat,
                    "fecha_brotacion_ELP4": brot_elp4, "fecha_inicio_ventana": start_win_str, "fecha_fin_ventana": end_win_str,
                    "fecha_fondo_valle": np.nan, "metrica_valle": metrica_valle, "valor_minimo_valle": np.nan,
                    "dias_biofix_vs_valle": np.nan, "gdd_entre_biofix_y_t0": np.nan, "gdd_entre_biofix_y_brotacion": np.nan,
                    "gdd_previo_a_t0_desde_inicio_ventana": np.nan, "actividad_termica_en_biofix": np.nan,
                    "diagnostico_valle": "revisar", "comentario_metodologico": alerta_msg,
                    "fuente_clima": fuente_clima, "archivo_origen": archivo_origen,
                })
                continue

            b_dt = pd.Timestamp(b_fecha)
            end_plot_dt = pd.Timestamp("2025-11-30")
            
            sub_clima = clima_df[clima_df["Fecha"] <= end_plot_dt].copy()
            
            sub_clima["post_mask"] = sub_clima["Fecha"] >= b_dt
            sub_clima["gdd_diario"] = sub_clima["gdd_diario_real"]
            sub_clima["gdd_acumulado"] = sub_clima["gdd_diario_real"].where(sub_clima["post_mask"], 0.0).cumsum()
            sub_clima["gdd_acumulado"] = sub_clima["gdd_acumulado"].where(sub_clima["post_mask"], np.nan)

            dias_bf_valle = np.nan
            if pd.notna(fecha_fondo_valle):
                dias_bf_valle = int((b_dt - pd.Timestamp(fecha_fondo_valle)).days)

            gdd_entre_bf_y_t0 = 0.0
            if pd.notna(t0_ref) and str(t0_ref) != "nan":
                t0_ref_dt = pd.Timestamp(t0_ref)
                if b_dt < t0_ref_dt:
                    gdd_entre_bf_y_t0 = float(clima_df[(clima_df["Fecha"] >= b_dt) & (clima_df["Fecha"] < t0_ref_dt)]["gdd_diario_real"].fillna(0.0).sum())
                elif b_dt > t0_ref_dt:
                    gdd_entre_bf_y_t0 = -float(clima_df[(clima_df["Fecha"] >= t0_ref_dt) & (clima_df["Fecha"] < b_dt)]["gdd_diario_real"].fillna(0.0).sum())

            has_brot = pd.notna(brot_elp4) and str(brot_elp4).strip().lower() != "nan"
            gdd_entre_bf_y_brot = np.nan
            gdd_a_brot = np.nan
            if has_brot:
                brot_dt = pd.Timestamp(brot_elp4)
                if b_dt <= brot_dt:
                    gdd_entre_bf_y_brot = float(clima_df[(clima_df["Fecha"] >= b_dt) & (clima_df["Fecha"] <= brot_dt)]["gdd_diario_real"].fillna(0.0).sum())
                b_match = sub_clima[sub_clima["Fecha"] <= brot_dt]
                if not b_match.empty and pd.notna(b_match.iloc[-1]["gdd_acumulado"]):
                    gdd_a_brot = float(b_match.iloc[-1]["gdd_acumulado"])

            act_bf = np.nan
            bf_match = clima_df[clima_df["Fecha"] == b_dt]
            if not bf_match.empty:
                act_bf = float(bf_match.iloc[0]["rolling_tmean_14"]) if pd.notna(bf_match.iloc[0]["rolling_tmean_14"]) else float(bf_match.iloc[0]["temp_media"])

            if clima_df["Fecha"].min() > pd.Timestamp("2025-06-30"):
                diag_valle = "sin_datos_suficientes"
            elif pd.isna(dias_bf_valle):
                diag_valle = "revisar"
            elif dias_bf_valle < -21:
                diag_valle = "anterior_al_valle"
            elif dias_bf_valle > 21:
                diag_valle = "posterior_al_valle"
            else:
                diag_valle = "cercano_al_valle"

            if diag_valle == "anterior_al_valle":
                comentario = f"Biofix ({b_fecha}) precede al fondo invernal ({fecha_fondo_valle}) en {abs(dias_bf_valle)} días; arrastra {gdd_entre_bf_y_t0:.1f} GDD de calor otoñal previo a T0."
            elif diag_valle == "posterior_al_valle":
                comentario = f"Biofix ({b_fecha}) posterior al fondo invernal ({fecha_fondo_valle}) en {dias_bf_valle} días; omite calentamiento temprano."
            elif diag_valle == "cercano_al_valle":
                comentario = f"Biofix ({b_fecha}) cae en la ventana fisiológica del fondo térmico invernal ({fecha_fondo_valle}, {dias_bf_valle:+}d)."
            else:
                comentario = "Serie climática incompleta antes de julio."

            alerta_msg = "NO"
            diag_code = "OK"
            if (gdd_previo_a_t0 or 0) > 0.1 and b_dt < pd.Timestamp(t0_ref if pd.notna(t0_ref) else "2025-12-31"):
                alerta_msg = f"SI: Acumulación térmica previa a t0 ({gdd_entre_bf_y_t0:.1f} GDD acumulados desde biofix)"
                diag_code = "acumulacion_termica_previa_a_t0"
            elif has_brot and b_dt > pd.Timestamp(brot_elp4):
                alerta_msg = "SI: Biofix posterior a fecha de brotación observada"
                diag_code = "biofix_posterior_a_brotacion"

            diag_rows.append({
                "fundo": fundo, "Fundo": Fundo, "temporada": temporada, "variedad": variedad,
                "biofix_tipo": b_tipo, "biofix_fecha": b_fecha, "t0_operativo": t0_op, "t0_latitudinal": t0_lat,
                "fecha_brotacion_ELP4": brot_elp4, "fecha_inicio_ventana": start_win_str, "fecha_fin_ventana": end_win_str,
                "fecha_fondo_valle": fecha_fondo_valle, "metrica_valle": metrica_valle,
                "valor_minimo_valle": round(valor_minimo_valle, 2) if pd.notna(valor_minimo_valle) else np.nan,
                "dias_biofix_vs_valle": dias_bf_valle,
                "gdd_entre_biofix_y_t0": round(gdd_entre_bf_y_t0, 2),
                "gdd_entre_biofix_y_brotacion": round(gdd_entre_bf_y_brot, 2) if pd.notna(gdd_entre_bf_y_brot) else np.nan,
                "gdd_previo_a_t0_desde_inicio_ventana": round(gdd_previo_a_t0, 2) if pd.notna(gdd_previo_a_t0) else np.nan,
                "actividad_termica_en_biofix": round(act_bf, 2) if pd.notna(act_bf) else np.nan,
                "diagnostico_valle": diag_valle, "comentario_metodologico": comentario,
                "fuente_clima": fuente_clima, "archivo_origen": archivo_origen,
            })

            summary_rows.append({
                "fundo": fundo, "temporada": temporada, "variedad": variedad, "biofix_tipo": b_tipo,
                "biofix_fecha": b_fecha, "fecha_brotacion_ELP4": brot_elp4, "gdd_acumulado_a_brotacion": gdd_a_brot,
                "gdd_acumulado_previo_t0": gdd_previo_a_t0, "gdd_entre_biofix_y_t0": gdd_entre_bf_y_t0,
                "dias_biofix_vs_valle": dias_bf_valle, "diagnostico_valle": diag_valle,
                "threshold_GDD_usado": threshold, "alerta_temporada_anterior": alerta_msg, "diagnostico_biofix": diag_code,
            })

            for _, cr in sub_clima.iterrows():
                timeseries_rows.append({
                    "fundo": fundo, "Fundo": Fundo, "temporada": temporada, "variedad": variedad,
                    "fecha": cr["Fecha"].strftime("%Y-%m-%d"), "biofix_tipo": b_tipo, "biofix_fecha": b_fecha,
                    "t0_operativo": t0_op, "t0_latitudinal": t0_lat, "fecha_brotacion_ELP4": brot_elp4,
                    "gdd_diario": float(cr["gdd_diario"]) if pd.notna(cr["gdd_diario"]) else np.nan,
                    "gdd_acumulado": float(cr["gdd_acumulado"]) if pd.notna(cr["gdd_acumulado"]) else np.nan,
                    "gdd_acumulado_previo_t0": gdd_previo_a_t0,
                    "gdd_entre_biofix_y_t0": gdd_entre_bf_y_t0,
                    "temp_media": float(cr["temp_media"]) if pd.notna(cr["temp_media"]) else np.nan,
                    "rolling_tmean_14": float(cr["rolling_tmean_14"]) if pd.notna(cr["rolling_tmean_14"]) else np.nan,
                    "rolling_gdd_14": float(cr["rolling_gdd_14"]) if pd.notna(cr["rolling_gdd_14"]) else np.nan,
                    "fecha_fondo_valle": fecha_fondo_valle, "valor_minimo_valle": valor_minimo_valle,
                    "dias_biofix_vs_valle": dias_bf_valle, "diagnostico_valle": diag_valle,
                    "comentario_metodologico": comentario, "threshold_GDD_usado": threshold,
                    "fuente_clima": fuente_clima, "archivo_origen": archivo_origen,
                    "alerta_temporada_anterior": alerta_msg, "diagnostico_biofix": diag_code,
                })

    out_ts = pd.DataFrame(timeseries_rows)
    out_sum = pd.DataFrame(summary_rows)
    out_diag = pd.DataFrame(diag_rows)

    csv_ts_path = OUTPUT_DIR / "gdd_acumulado_por_biofix.csv"
    csv_sum_path = OUTPUT_DIR / "gdd_acumulado_por_biofix_summary.csv"
    csv_diag_path = OUTPUT_DIR / "thermal_valley_diagnostics_by_biofix.csv"

    out_ts.to_csv(csv_ts_path, index=False)
    out_sum.to_csv(csv_sum_path, index=False)
    out_diag.to_csv(csv_diag_path, index=False)

    print(f"=== GENERADO ÉXITOSAMENTE ===")
    print(f"  -> {csv_ts_path} (Shape: {out_ts.shape})")
    print(f"  -> {csv_sum_path} (Shape: {out_sum.shape})")
    print(f"  -> {csv_diag_path} (Shape: {out_diag.shape})")

if __name__ == "__main__":
    build_canonical_outputs()
