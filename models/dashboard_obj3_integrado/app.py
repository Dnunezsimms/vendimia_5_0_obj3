from __future__ import annotations

import argparse
import logging
from pathlib import Path

import gradio as gr
import pandas as pd

try:
    from .src.config import HOST, LOG_DIR, PORT, REPO_ROOT
    from .src.loaders import find_columns, get_climate_station_variables, load_climate_station_series, load_state, numeric_columns, setup_logging
    from .src.plots import (
        baseline_comparison_plot,
        cabernet_diagnostic_table,
        climate_status_bar,
        climate_timeseries_plot,
        coverage_bar,
        empty_figure,
        gdd_progress_bar,
        importance_bar,
        latitudinal_regression_plot,
        maturity_curve,
        maturity_curve_grouped,
        prepare_maturity_traceability_table,
        metric_ranking,
        observed_vs_pred,
        panel_a_operativo_plot,
        panel_b_diagnostico_plot,
        panel_d_chill_plot,
        panel_d_chill_table,
        gdd_biofix_timeseries_plot,
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src.config import HOST, LOG_DIR, PORT, REPO_ROOT
    from src.loaders import find_columns, get_climate_station_variables, load_climate_station_series, load_state, numeric_columns, setup_logging
    from src.plots import (
        baseline_comparison_plot,
        cabernet_diagnostic_table,
        climate_status_bar,
        climate_timeseries_plot,
        coverage_bar,
        empty_figure,
        gdd_progress_bar,
        importance_bar,
        latitudinal_regression_plot,
        maturity_curve,
        maturity_curve_grouped,
        prepare_maturity_traceability_table,
        metric_ranking,
        observed_vs_pred,
        panel_a_operativo_plot,
        panel_b_diagnostico_plot,
        panel_d_chill_plot,
        panel_d_chill_table,
        gdd_biofix_timeseries_plot,
    )
try:
    from .src.luis_config import BASE_DIR as LUIS_BASE_DIR, CACHE_DIR as LUIS_CACHE_DIR
    from .src.luis_data_loader import (
        available_combos, available_schemes, available_targets, detect_predictor_columns,
        discover_artifacts, load_experiment_config, load_importance, load_metrics,
        load_original_data, load_predictions
    )
    from .src.luis_metrics import aggregate_metrics, attach_deltas, combine_shap_mae, executive_summary, lofo_fundo_table
    from .src.luis_plots import (
        box_target_by_fundo, box_target_by_variety, combo_compare_bars,
        importance_bar as luis_importance_bar, lofo_ranking_bar, observed_vs_pred as luis_observed_vs_pred,
        performance_scatter as luis_performance_scatter, predictor_timeseries, residual_plots, timeseries_target
    )
    from .src.luis_utils import setup_logging as luis_setup_logging
except ImportError:
    from src.luis_config import BASE_DIR as LUIS_BASE_DIR, CACHE_DIR as LUIS_CACHE_DIR
    from src.luis_data_loader import (
        available_combos, available_schemes, available_targets, detect_predictor_columns,
        discover_artifacts, load_experiment_config, load_importance, load_metrics,
        load_original_data, load_predictions
    )
    from src.luis_metrics import aggregate_metrics, attach_deltas, combine_shap_mae, executive_summary, lofo_fundo_table
    from src.luis_plots import (
        box_target_by_fundo, box_target_by_variety, combo_compare_bars,
        importance_bar as luis_importance_bar, lofo_ranking_bar, observed_vs_pred as luis_observed_vs_pred,
        performance_scatter as luis_performance_scatter, predictor_timeseries, residual_plots, timeseries_target
    )
    from src.luis_utils import setup_logging as luis_setup_logging



def _safe(df: pd.DataFrame | None) -> pd.DataFrame:
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def _markdown_status(state: dict) -> str:
    climate = state["climate"]
    luis = state["luis"]
    audit = state["audit"]
    resumen = climate["resumen"]
    n_ok = int((resumen.get("estado", pd.Series(dtype=str)) == "OK").sum()) if "estado" in resumen.columns else 0
    n_val = int((resumen.get("estado", pd.Series(dtype=str)) == "PENDIENTE_VALIDACION_MANUAL").sum()) if "estado" in resumen.columns else 0

    return (
        "### 🏛️ Matriz General de Dependencias e Ingesta\n\n"
        "| Componente | Estado Operacional | Archivo Canónico / Fuente |\n"
        "|---|---|---|\n"
        "| **Clima** | 🟢 CERRADO | `consolidado_fenologia_ELP_OBJ3_INDICES_BIOCLIMATICOS.csv` |\n"
        "| **Fenología** | 🟢 CERRADO | `consolidado_fenologia_ELP_MODELABLE_FULL_v1.csv` |\n"
        "| **Madurez Técnica** | 🟢 CERRADO | `madurez_tecnica_2025_2026_train_test_CANONICO_V5_INDICES_ORIGINALES.csv` |\n"
        "| **Madurez Fenólica** | 🟡 EN PROGRESO | Bloqueado por resultados lab 2026 |\n"
        "| **Modelos (Baseline)** | 🟢 CERRADO | `run_pipeline_v2.py` ejecutado y métricas consolidadas |\n"
        "| **Export INRIA** | 🟡 EN ESPERA | `paquete_luis_inria_fenologia_ELP_OBJ3_CLEAN_2.zip` |\n\n"
        "### 🔎 Auditoría de Orígenes de Datos\n"
        f"- **Repositorio Base:** `{REPO_ROOT}`\n"
        f"- **Red Climática:** `{n_ok}` fundos consolidados OK, `{n_val}` en verificación manual.\n"
        f"- **Métricas RF (Luis):** `{len(luis['metrics_rf'])}` registros.\n"
        f"- **Métricas PySR / Regresión Simbólica:** `{len(luis['metrics_pysr'])}` fórmulas evaluadas.\n"
        f"- **Predicciones RF Espaciales:** `{len(luis['predictions_rf'])}` puntos.\n"
        f"- **Control de Integridad (SHA/Path):** `{len(audit)}` archivos verificados.\n"
    )


def _filter_table(df: pd.DataFrame, fundo: str, variedad: str) -> pd.DataFrame:
    d = df.copy()
    if fundo != "Todos":
        col = next((c for c in d.columns if "fundo" in c.lower()), None)
        if col:
            d = d[d[col].astype(str).str.contains(fundo, case=False, na=False)]
    if variedad != "Todas":
        col = next((c for c in d.columns if "variedad" in c.lower()), None)
        if col:
            d = d[d[col].astype(str).str.contains(variedad, case=False, na=False)]
    return d


def _choices(df: pd.DataFrame, col: str, all_label: str) -> list[str]:
    if df.empty or col not in df.columns:
        return [all_label]
    values = sorted(df[col].dropna().astype(str).unique().tolist())
    return [all_label] + values


def _filter_maturity(df: pd.DataFrame, variedad: str, fundo: str, temporada: str) -> pd.DataFrame:
    d = df.copy()
    filters = {
        "variedad": variedad,
        "fundo": fundo,
        "temporada": temporada,
    }
    for col, value in filters.items():
        if value not in {"Todas", "Todos", "Todas las temporadas"} and col in d.columns:
            d = d[d[col].astype(str) == str(value)]
    return d


CUSTOM_CSS = """
.gradio-container {
    max-width: 1450px !important;
    margin: auto;
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
}
h1, h2, h3 {
    color: #6b1d2f !important;
    font-weight: 700;
}
.prose {
    color: #2d3748 !important;
}
"""

def _safe_dropdown_value(default_value, choices):
    choices = list(choices or [])
    if default_value in choices:
        return default_value
    return choices[0] if choices else None


def _load_or_empty(label: str, loader, *args) -> pd.DataFrame:
    try:
        return loader(*args)
    except Exception as e:
        logging.exception("%s failed; using an empty table: %s", label, e)
        return pd.DataFrame()


def _export_csv(df: pd.DataFrame, prefix: str) -> str:
    LUIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = LUIS_CACHE_DIR / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(p, index=False)
    return str(p)


def _export_md(text: str, prefix: str) -> str:
    LUIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = LUIS_CACHE_DIR / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    p.write_text(text, encoding="utf-8")
    return str(p)


def build_state() -> dict:
    logging.info("Loading artifacts from %s", LUIS_BASE_DIR)
    logging.info("Artifacts directory exists: %s", LUIS_BASE_DIR.exists())
    logging.info("Outputs directory: %s | exists=%s", LUIS_BASE_DIR / "outputs", (LUIS_BASE_DIR / "outputs").exists())
    logging.info("Prepared data directory: %s | exists=%s", LUIS_BASE_DIR / "data" / "prepared", (LUIS_BASE_DIR / "data" / "prepared").exists())
    logging.info("Config file: %s | exists=%s", LUIS_BASE_DIR / "config" / "experiment_config.json", (LUIS_BASE_DIR / "config" / "experiment_config.json").exists())
    try:
        artifacts = discover_artifacts(LUIS_BASE_DIR)
    except Exception as e:
        logging.exception("discover_artifacts failed, using empty table: %s", e)
        artifacts = pd.DataFrame()
    metrics = _load_or_empty("load_metrics", load_metrics, LUIS_BASE_DIR)
    preds = _load_or_empty("load_predictions", load_predictions, LUIS_BASE_DIR)
    try:
        perm_df, shap_df = load_importance(LUIS_BASE_DIR)
    except Exception as e:
        logging.exception("load_importance failed; using empty tables: %s", e)
        perm_df, shap_df = pd.DataFrame(), pd.DataFrame()
    summary = attach_deltas(aggregate_metrics(metrics))
    lofo_table = lofo_fundo_table(metrics)
    try:
        cfg = load_experiment_config(LUIS_BASE_DIR)
    except Exception as e:
        logging.exception("load_experiment_config failed; using empty config: %s", e)
        cfg = {}
    ratios = combine_shap_mae(shap_df, metrics)
    logging.info(
        "Loaded dashboard tables: artifacts=%s metrics_rows=%s predictions_rows=%s permutation_rows=%s shap_rows=%s summary_rows=%s",
        len(artifacts),
        len(metrics),
        len(preds),
        len(perm_df),
        len(shap_df),
        len(summary),
    )

    return {
        "artifacts": artifacts,
        "metrics": metrics,
        "predictions": preds,
        "perm": perm_df,
        "shap": shap_df,
        "summary": summary,
        "lofo": lofo_table,
        "cfg": cfg,
        "ratios": ratios,
    }


def filtered_summary(state: dict, target: str, scheme: str) -> pd.DataFrame:
    s = state["summary"]
    if s.empty or not {"target_key", "scheme"}.issubset(s.columns) or not target or not scheme:
        return s
    return s[(s["target_key"] == target) & (s["scheme"] == scheme)].copy()


def filtered_metrics(state: dict, target: str, scheme: str, combo: str | None) -> pd.DataFrame:
    m = state["metrics"]
    if m.empty or not {"target_key", "scheme"}.issubset(m.columns) or not target or not scheme:
        return m
    d = m[(m["target_key"] == target) & (m["scheme"] == scheme)].copy()
    if combo and combo != "Todos":
        d = d[d["predictors"] == combo]
    return d


def filtered_predictions(state: dict, target: str, scheme: str, combo: str | None, variedad: str, fundo: str) -> pd.DataFrame:
    p = state["predictions"]
    if p.empty or not target or not scheme:
        return p
    d = p[(p["target_key"] == target) & (p["scheme"] == scheme)].copy() if "target_key" in p.columns else p.copy()
    if combo and combo != "Todos" and "predictors" in d.columns:
        d = d[d["predictors"] == combo]
    if variedad != "Todas" and "variedad" in d.columns:
        d = d[d["variedad"] == variedad]
    if fundo != "Todos" and "fundo" in d.columns:
        d = d[d["fundo"] == fundo]
    return d


def filtered_importance(df: pd.DataFrame, target: str, scheme: str, combo: str | None) -> pd.DataFrame:
    if df.empty or not {"target_key", "scheme"}.issubset(df.columns) or not target or not scheme:
        return df
    d = df[(df["target_key"] == target) & (df["scheme"] == scheme)].copy()
    if combo and combo != "Todos":
        d = d[d["predictors"] == combo]
    return d


def _performance_boxplot_image(target: str, scheme: str) -> tuple[str | None, str]:
    """Return path + status for precomputed RF boxplot image in monitoring."""
    box_dir = LUIS_BASE_DIR / "monitoring" / "rf_diego_latest_target_combo_boxplots"
    cand = [
        box_dir / f"rf_boxplot_wanted_combos_{target}_{scheme}_version2.png",
        box_dir / f"rf_boxplot_wanted_combos_{target}_{scheme}.png",
    ]
    for c in cand:
        if c.exists():
            return str(c), f"Mostrando boxplot precomputado: `{c.name}`"
    return None, "No hay boxplot precomputado para este target/esquema en monitoring."


def refresh_options(state: dict, target: str, scheme: str):
    targets = available_targets(state["metrics"], LUIS_BASE_DIR)
    target = _safe_dropdown_value(target, targets)

    schemes = available_schemes(state["metrics"], target)
    scheme = _safe_dropdown_value(scheme, schemes)

    combos_df = available_combos(state["metrics"], target, scheme)
    combos = ["Todos"] + combos_df["predictors"].tolist() if not combos_df.empty else ["Todos"]
    combos_h = ["Todos"] + combos_df["combo_human"].tolist() if not combos_df.empty else ["Todos"]

    orig = load_original_data(target, LUIS_BASE_DIR)
    variedades = ["Todas"] + sorted(orig["variedad"].dropna().astype(str).unique().tolist()) if "variedad" in orig.columns else ["Todas"]
    fundos = ["Todos"] + sorted(orig["fundo"].dropna().astype(str).unique().tolist()) if "fundo" in orig.columns else ["Todos"]

    return (
        gr.update(choices=targets, value=target),
        gr.update(choices=schemes, value=scheme),
        gr.update(choices=combos, value=_safe_dropdown_value("Todos", combos)),
        gr.update(choices=variedades, value=_safe_dropdown_value("Todas", variedades)),
        gr.update(choices=fundos, value=_safe_dropdown_value("Todos", fundos)),
        gr.update(choices=combos_h, value=_safe_dropdown_value("Todos", combos_h)),
    )


def update_resumen(state: dict, target: str, scheme: str):
    if not target or not scheme:
        md = (
            "### Estado de carga\n"
            "No hay targets/esquemas disponibles. Revisa que existan archivos bajo "
            f"`{LUIS_BASE_DIR / 'outputs'}` con el patron "
            "`outputs/<target>/<scheme>/predictors__*/rf/<run>/metrics_per_split.csv` "
            f"o datos originales en `{LUIS_BASE_DIR / 'data' / 'prepared'}`."
        )
        return md, pd.DataFrame(), luis_performance_scatter(pd.DataFrame())

    orig = load_original_data(target, LUIS_BASE_DIR)
    fs = filtered_summary(state, target, scheme)
    ex = executive_summary(target, scheme, fs, orig)

    md = f"""
### Resumen ejecutivo
- **Target:** `{target}`
- **Validación:** `{scheme}`
- **Mejor combinación (MAE):** {ex.get('best_mae', 'N/A')}
- **Mejor combinación (R2):** {ex.get('best_r2', 'N/A')}
- **Delta MAE (best vs base):** `{ex.get('delta_mae_best', float('nan')):.4f}`
- **Mejora MAE % (best vs base):** `{ex.get('mejora_mae_pct_best', float('nan')):.2f}`
- **Delta R2 (best vs base):** `{ex.get('delta_r2_best', float('nan')):.4f}`
- **N combinaciones:** `{ex.get('n_combos', 0)}`
- **N fundos:** `{ex.get('n_fundos', 0)}`
- **N variedades:** `{ex.get('n_variedades', 0)}`
- **N observaciones:** `{ex.get('n_obs', 0)}`

Fórmulas:
`deltaMAE = MAE_modelo - MAE_base`
`mejora_MAE_% = (MAE_base - MAE_modelo) / MAE_base * 100`
`deltaR2 = R2_modelo - R2_base`
"""
    return md, fs, luis_performance_scatter(fs)


def update_datos_originales(target: str, variedad: str, fundo: str, predictor: str):
    orig = load_original_data(target, LUIS_BASE_DIR)
    if orig.empty:
        return "No se encontró información suficiente para esta visualización con los filtros actuales.", None, None, None, None, gr.update(choices=[""], value="")

    target_col = None
    cfg = load_experiment_config(LUIS_BASE_DIR)
    if target in cfg.get("targets", {}):
        target_col = cfg["targets"][target].get("column")
    if target_col not in orig.columns:
        cands = [c for c in orig.columns if "mg/baya" in c or "mgEqMv" in c or "mg/Kg" in c]
        target_col = cands[-1] if cands else None
    if target_col is None:
        return "No se encontró información suficiente para esta visualización con los filtros actuales.", None, None, None, None, gr.update(choices=[""], value="")

    d = orig.copy()
    if variedad != "Todas" and "variedad" in d.columns:
        d = d[d["variedad"] == variedad]
    if fundo != "Todos" and "fundo" in d.columns:
        d = d[d["fundo"] == fundo]

    pred_cols = detect_predictor_columns(orig, target_col)
    if predictor not in pred_cols:
        predictor = pred_cols[0] if pred_cols else ""

    msg = f"Target original: `{target_col}` | Filas: {len(d)}"
    return (
        msg,
        box_target_by_variety(d, target_col),
        timeseries_target(d, target_col),
        box_target_by_fundo(d, target_col),
        predictor_timeseries(d, predictor) if predictor else predictor_timeseries(pd.DataFrame(), ""),
        gr.update(choices=pred_cols, value=predictor),
    )


def update_lofo(state: dict, target: str, combo: str):
    lo = state["lofo"]
    if lo.empty:
        return lo, lofo_ranking_bar(lo)
    d = lo[lo["target_key"] == target].copy()
    if combo != "Todos":
        d = d[d["predictors"] == combo]
    return d, lofo_ranking_bar(d)


def update_predicciones(state: dict, target: str, scheme: str, combo: str, variedad: str, fundo: str):
    d = filtered_predictions(state, target, scheme, combo, variedad, fundo)
    fig_obs_pred = luis_observed_vs_pred(d)
    h, rvp = residual_plots(d)
    if d.empty or "fecha" not in d.columns:
        ts = timeseries_target(pd.DataFrame(), "")
    else:
        y_col = [c for c in d.columns if c not in ["prediction", "subset", "split_id", "method", "predictors", "n_predictors", "seed", "file_path", "output_tag", "fecha", "variedad", "fundo"] and pd.api.types.is_numeric_dtype(d[c])]
        y = y_col[0] if y_col else None
        if y:
            long = d[["fecha", y, "prediction"]].copy().rename(columns={y: "observed"})
            long = long.melt(id_vars=["fecha"], value_vars=["observed", "prediction"], var_name="serie", value_name="valor")
            ts = px.line(long.sort_values("fecha"), x="fecha", y="valor", color="serie", template="plotly_white")
        else:
            ts = timeseries_target(pd.DataFrame(), "")
    return d, fig_obs_pred, ts, h, rvp


def update_importancia(state: dict, target: str, scheme: str, combo: str, tipo: str):
    perm = filtered_importance(state["perm"], target, scheme, combo)
    shap = filtered_importance(state["shap"], target, scheme, combo)
    ratio = state["ratios"]
    ratio = filtered_importance(ratio, target, scheme, combo) if not ratio.empty else ratio

    if tipo == "permutation":
        fig = luis_importance_bar(perm, "perm_importance_mean", "Importancia por permutación")
        table = perm
    elif tipo == "shap":
        fig = luis_importance_bar(shap, "shap_mean_abs", "Importancia SHAP")
        table = shap
    else:
        fig = luis_importance_bar(ratio, "shap_over_mae", "Cociente SHAP/MAE")
        table = ratio

    if table.empty:
        msg = "No se encontraron archivos SHAP/permutation para esta combinación."
    else:
        msg = f"Filas disponibles: {len(table)}"
    return msg, fig, table


def update_comparador(state: dict, target: str, scheme: str, combos: list[str]):
    fs = filtered_summary(state, target, scheme)
    if combos:
        fs = fs[fs["predictors"].isin(combos)]
    a, b, c = combo_compare_bars(fs)
    return fs, a, b, c


def update_explorer(state: dict):
    art = state["artifacts"]
    if art.empty:
        return art
    return art.sort_values(["kind", "target", "scheme"]).reset_index(drop=True)


def export_tables(state: dict, target: str, scheme: str, combo: str, variedad: str, fundo: str):
    fs = filtered_summary(state, target, scheme)
    fm = filtered_metrics(state, target, scheme, combo)
    fp = filtered_predictions(state, target, scheme, combo, variedad, fundo)

    metrics_csv = _export_csv(fm if not fm.empty else fs, "metrics_filtered")
    preds_csv = _export_csv(fp, "predictions_filtered")

    imp = filtered_importance(state["perm"], target, scheme, combo)
    if imp.empty:
        imp = filtered_importance(state["shap"], target, scheme, combo)
    imp_csv = _export_csv(imp, "importance_filtered") if not imp.empty else _export_csv(pd.DataFrame(), "importance_filtered_empty")

    md = (
        f"# Resumen ejecutivo\n\n"
        f"- Target: `{target}`\n"
        f"- Validación: `{scheme}`\n"
        f"- Combinación: `{combo}`\n"
        f"- Variedad: `{variedad}`\n"
        f"- Fundo: `{fundo}`\n"
        f"- Fecha generación: `{datetime.now().isoformat()}`\n"
    )
    md_file = _export_md(md, "resumen_ejecutivo")
    return metrics_csv, preds_csv, imp_csv, md_file



def build_app() -> gr.Blocks:
    state = load_state()
    logging.info("Estado inicial cargado")

    climate = state["climate"]
    gdd = state["gdd"]
    phenology = state["phenology"]
    maturity = state["maturity"]
    luis = state["luis"]
    climate_catalog = state["climate_catalog"]
    gdd_latitudinal = state["gdd_latitudinal"]

    # Selectores de clima
    _catalog_stations = climate_catalog["stations"]  # dict source->list
    _sources = list(_catalog_stations.keys()) or ["Datavid"]
    _first_source = _sources[0]
    _first_stations = _catalog_stations.get(_first_source, [])
    _first_station = _first_stations[0] if _first_stations else ""
    _first_vars = get_climate_station_variables(_first_source, _first_station) if _first_station else []
    _first_var = _first_vars[0] if _first_vars else "Temp. Media [°C]"

    fundos = ["Todos"] + sorted(climate["resumen"].get("fundo_normalizado", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    gdd_var_col = "Variedad" if "Variedad" in gdd["resumen_t0"].columns else "variedad" if "variedad" in gdd["resumen_t0"].columns else None
    variedades = ["Todas"] + sorted(gdd["resumen_t0"].get(gdd_var_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) if gdd_var_col else ["Todas"]
    maturity_df = pd.concat([maturity["tintas_historicas"], maturity["raw_2026"]], ignore_index=True, sort=False)
    maturity_technical = maturity.get("tecnica_canonica", pd.DataFrame())
    maturity_vars = [c for c in ["brix", "pH", "acidez_sulfurica", "acidez_tartarica", "peso_baya", "azucar_real_baya_g"] if c in maturity_technical.columns]
    if not maturity_vars:
        maturity_vars = find_columns(maturity_df, ["brix", "ph", "acidez", "peso", "azucar"]) or numeric_columns(maturity_df)
    phenolic_df = pd.concat([luis["original_tintas"], maturity["raw_2026"]], ignore_index=True, sort=False)
    phenolic_vars = find_columns(phenolic_df, ["antoc", "tanino", "fenol", "hplc", "uv"]) or numeric_columns(phenolic_df)
    model_metrics = pd.concat([luis["metrics_rf"], luis["metrics_pysr"]], ignore_index=True, sort=False)
    model_targets = ["Todos"] + sorted(model_metrics.get("target_key", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    schemes = ["Todos"] + sorted(model_metrics.get("scheme", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())

    with gr.Blocks(title="Vendimia 5.0 — Plataforma Exploratoria Objetivo 3") as demo:
        gr.Markdown(
            """
            # 🍇 Vendimia 5.0 — Explorador Técnico Objetivo 3
            **Flujo Técnico de Análisis y Trazabilidad:** *Clima Fisiológico → Modelación Fenológica → Madurez Técnica/Fenólica → Modelos IA/RF/PySR → Referencia de Cosecha*

            📬 Contacto técnico: **Diego Núñez** — Análisis de datos, modelamiento y trazabilidad del Objetivo 3.
            """  
        )

        with gr.Tab("📊 Estado del sistema"):
            gr.Markdown(_markdown_status(state))

            # --- Panel principal: series temporales climáticas ---
            gr.Markdown("### 🌡️ Series Temporales Climáticas — Explorador Horario/Diario")
            gr.Markdown("> Selecciona fuente, estación y variable. La frecuencia diaria se calcula como promedio en memoria (sin guardar archivos nuevos).")
            with gr.Row():
                ts_source = gr.Dropdown(_sources, value=_first_source, label="Fuente", scale=1)
                ts_station = gr.Dropdown(_first_stations or [""], value=_first_station, label="Estación / Fuente Climática", scale=2)
                ts_var = gr.Dropdown(_first_vars or [_first_var], value=_first_var, label="Variable Climática", scale=2)
                _init_freq_choices = ["diaria"] if _first_source == "INIA/Agromet" else ["horaria", "diaria"]
                _init_freq_val = "diaria" if _first_source == "INIA/Agromet" else "horaria"
                ts_freq = gr.Radio(_init_freq_choices, value=_init_freq_val, label="Frecuencia de visualización", scale=1)

            _init_df = load_climate_station_series(_first_source, _first_station, "hourly" if _init_freq_val == "horaria" else "daily") if _first_station else pd.DataFrame()
            ts_plot = gr.Plot(value=climate_timeseries_plot(_init_df, _first_var, _first_station, _first_source, _init_freq_val))

            def on_ts_source_change(source, freq):
                stations = _catalog_stations.get(source, [])
                st = stations[0] if stations else ""
                vars_avail = get_climate_station_variables(source, st) if st else []
                var = vars_avail[0] if vars_avail else ""
                if source == "INIA/Agromet":
                    freq_choices = ["diaria"]
                    freq = "diaria"
                else:
                    freq_choices = ["horaria", "diaria"]
                    if freq not in freq_choices:
                        freq = "horaria"
                freq_key = "daily" if freq == "diaria" else "hourly"
                df = load_climate_station_series(source, st, freq_key) if st else pd.DataFrame()
                fig = climate_timeseries_plot(df, var, st, source, freq)
                return gr.update(choices=stations, value=st), gr.update(choices=vars_avail, value=var), gr.update(choices=freq_choices, value=freq), fig

            def on_ts_station_change(source, station, freq):
                vars_avail = get_climate_station_variables(source, station) if station else []
                var = vars_avail[0] if vars_avail else ""
                if source == "INIA/Agromet":
                    freq_choices = ["diaria"]
                    freq = "diaria"
                else:
                    freq_choices = ["horaria", "diaria"]
                    if freq not in freq_choices:
                        freq = "horaria"
                freq_key = "daily" if freq == "diaria" else "hourly"
                df = load_climate_station_series(source, station, freq_key) if station else pd.DataFrame()
                fig = climate_timeseries_plot(df, var, station, source, freq)
                return gr.update(choices=vars_avail, value=var), gr.update(choices=freq_choices, value=freq), fig

            def on_ts_var_or_freq_change(source, station, var, freq):
                if not station:
                    return empty_figure("Selecciona una estación.")
                if source == "INIA/Agromet":
                    freq = "diaria"
                freq_key = "daily" if freq == "diaria" else "hourly"
                df = load_climate_station_series(source, station, freq_key)
                return climate_timeseries_plot(df, var, station, source, freq)

            ts_source.change(on_ts_source_change, [ts_source, ts_freq], [ts_station, ts_var, ts_freq, ts_plot])
            ts_station.change(on_ts_station_change, [ts_source, ts_station, ts_freq], [ts_var, ts_freq, ts_plot])
            ts_var.change(on_ts_var_or_freq_change, [ts_source, ts_station, ts_var, ts_freq], ts_plot)
            ts_freq.change(on_ts_var_or_freq_change, [ts_source, ts_station, ts_var, ts_freq], ts_plot)

            # --- Panel secundario: auditoría de cobertura ---
            gr.Markdown("### 🗂️ Auditoría de Cobertura Climática por Fundo")
            gr.Markdown("> **📌 COBERTURA:** Ingesta climática operacional consolidada hasta Octubre 2025. *Los sensores horarios de frío invernal cortan en Junio 2025.*")
            with gr.Row():
                gr.Plot(value=climate_status_bar(climate["resumen"]))
                gr.Plot(value=coverage_bar(climate["resumen"]))
            gr.Markdown("### 🗃️ Catálogo Maestro Regional (Fundo - Estación - Fuente - Temporada)")
            gr.Dataframe(value=_safe(climate["master"]), interactive=False, wrap=True)
            gr.Markdown("### 🕳️ Detección de Gaps Horarios por Fundo")
            gr.Dataframe(value=_safe(climate["gaps"]), interactive=False, wrap=True)
            gr.Markdown("### 🔄 Equivalencias Homologadas")
            with gr.Row():
                gr.Dataframe(value=_safe(climate["equivalencias"]), interactive=False, wrap=True)
                gr.Dataframe(value=_safe(state["audit"]), interactive=False, wrap=True)

        with gr.Tab("🌱 Fenología & GDD"):
            gr.Markdown("> **⚠️ CRITERIO METODOLÓGICO:** El **T0 Cerrado** es un indicador de diagnóstico retrospectivo (*leakage* histórico); el **T0 Latitudinal** es el biofix predictivo operacional candidato a producción.")
            with gr.Tabs():
                with gr.Tab("A. Curva Latitudinal T0 / Brotación"):
                    gr.Markdown(
                        "**Auditoría espacial del gradiente fenológico.** "
                        "Muestra cómo el DOY de brotación y T0 (biofix Cabernet) varían con la latitud en los fundos monitoreados. "
                        "Los Acacios se excluye de la regresión por inconsistencias en la cobertura de datos."
                    )
                    gr.Plot(value=latitudinal_regression_plot(
                        gdd_latitudinal["diagnostico"],
                        gdd_latitudinal["regresiones"],
                    ))
                    gr.Markdown("### 📋 Tabla de Diagnóstico por Fundo (Cabernet Sauvignon 2025–2026)")
                    gr.Dataframe(value=_safe(gdd_latitudinal["diagnostico"][[c for c in [
                        "Fundo", "lat", "t0_operativo", "doy_t0_operativo",
                        "fecha_brotacion", "doy_brotacion",
                        "doy_brotacion_pred_reg_lat", "residuo_brotacion_latitud",
                        "doy_t0_pred_reg_lat", "residuo_t0_latitud",
                        "incluido_en_regresion", "motivo_exclusion",
                    ] if c in gdd_latitudinal["diagnostico"].columns]]), interactive=False, wrap=True)

                with gr.Tab("B. Valle Térmico y Auditoría de Fecha de Inicio"):
                    gr.Markdown(
                        "**Auditoría fisiológica de inicio de conteo térmico (Fecha candidata vs Fondo del Valle).**\n\n"
                        "El valle térmico se audita con GDD diario y una curva móvil de actividad térmica. La temperatura media puede mostrarse solo como apoyo. "
                        "El GDD acumulado no sirve para encontrar el valle porque siempre aumenta; se usa solo para evaluar cuánto se acumula desde la fecha candidata auditada.\n\n"
                        "Este panel audita térmicamente la fecha candidata de inicio. No reconstruye todavía el indicador biológico completo Lourdes → umbral GDD → T0 → latitud. Esa sensibilidad queda pendiente para Sprint 2.5C.\n\n"
                        "> ❓ **Pregunta clave que resuelve este panel:** *¿La fecha de inicio de acumulación cae cerca del valle de actividad térmica diaria, o está metida en el monte térmico anterior/posterior?*"
                    )
                    bf_df = gdd.get("biofix_timeseries", pd.DataFrame())
                    bf_sum = gdd.get("biofix_summary", pd.DataFrame())
                    tv_df = gdd.get("thermal_valley", pd.DataFrame())

                    bf_fundos = sorted(bf_df["fundo"].dropna().unique().tolist()) if not bf_df.empty else ["qba_seca"]
                    bf_temps = sorted(bf_df["temporada"].dropna().unique().tolist()) if not bf_df.empty else ["2025_2026"]
                    bf_vars = sorted(bf_df["variedad"].dropna().unique().tolist()) if not bf_df.empty else ["cabernet_sauvignon"]
                    bf_tipos = sorted(bf_df["biofix_tipo"].dropna().unique().tolist()) if not bf_df.empty else ["1_agosto"]

                    with gr.Row():
                        bf_fundo_dd = gr.Dropdown(bf_fundos, value=bf_fundos[0] if bf_fundos else "", label="Fundo / Viñedo")
                        bf_temp_dd = gr.Dropdown(bf_temps, value=bf_temps[0] if bf_temps else "", label="Temporada")
                        bf_var_dd = gr.Dropdown(bf_vars, value=bf_vars[0] if bf_vars else "", label="Variedad")
                        bf_tipo_dd = gr.Dropdown(bf_tipos, value="1_agosto" if "1_agosto" in bf_tipos else (bf_tipos[0] if bf_tipos else ""), label="Fecha candidata auditada")

                    init_bf_fig = gdd_biofix_timeseries_plot(
                        bf_df,
                        bf_fundos[0] if bf_fundos else "",
                        bf_temps[0] if bf_temps else "",
                        bf_vars[0] if bf_vars else "",
                        "1_agosto" if "1_agosto" in bf_tipos else (bf_tipos[0] if bf_tipos else ""),
                    )
                    bf_plot = gr.Plot(value=init_bf_fig)

                    gr.Markdown("### 📋 Resumen Canónico de Valle Térmico y Alertas por Fecha candidata")
                    bf_table = gr.Dataframe(value=_safe(bf_sum), interactive=False, wrap=True)

                    gr.Markdown("### 🏔️ Matriz de Diagnóstico Detallado de Valle Térmico (`thermal_valley_diagnostics_by_biofix.csv`)")
                    tv_table = gr.Dataframe(value=_safe(tv_df), interactive=False, wrap=True)

                    def update_bf_panel(f, t, v, b):
                        fig = gdd_biofix_timeseries_plot(bf_df, f, t, v, b)
                        sub_sum = pd.DataFrame()
                        if not bf_sum.empty:
                            sub_sum = bf_sum[
                                (bf_sum["fundo"].astype(str).str.strip().str.lower() == str(f).strip().lower())
                                & (bf_sum["temporada"].astype(str) == str(t))
                                & (bf_sum["variedad"].astype(str).str.strip().str.lower() == str(v).strip().lower())
                            ].copy()
                        sub_tv = pd.DataFrame()
                        if not tv_df.empty:
                            sub_tv = tv_df[
                                (tv_df["fundo"].astype(str).str.strip().str.lower() == str(f).strip().lower())
                                & (tv_df["temporada"].astype(str) == str(t))
                                & (tv_df["variedad"].astype(str).str.strip().str.lower() == str(v).strip().lower())
                            ].copy()
                        return fig, _safe(sub_sum), _safe(sub_tv)

                    for dd in [bf_fundo_dd, bf_temp_dd, bf_var_dd, bf_tipo_dd]:
                        dd.change(update_bf_panel, [bf_fundo_dd, bf_temp_dd, bf_var_dd, bf_tipo_dd], [bf_plot, bf_table, tv_table])

                with gr.Tab("C. Evaluación Operacional (Residuo T0 Latitudinal)"):
                    f_lat_error_plot = gr.Plot(value=panel_a_operativo_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))

                with gr.Tab("D. Diagnóstico de Leakage (T0 Cerrado vs Latitudinal)"):
                    gr.Markdown(
                        "> **🔍 EVALUACIÓN METODOLÓGICA DE LEAKAGE:** El **T0 Cerrado** se infirió retrospectivamente ajustando el umbral a la fecha de brotación observada (*data leakage*). "
                        "El **T0 Latitudinal** es un candidato predictivo operacional legítimo, ciego a brotación observada."
                    )
                    with gr.Row():
                        f_t0_comparison_plot = gr.Plot(value=panel_b_diagnostico_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                        f_baseline_plot = gr.Plot(value=baseline_comparison_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                    gr.Markdown("### 📋 Matriz de Diagnóstico y Alertas de Leakage (Cabernet Sauvignon)")
                    f_alert_table = gr.Dataframe(value=_safe(cabernet_diagnostic_table(gdd.get("diagnostico_cs_reg", pd.DataFrame()))), interactive=False, wrap=True)

                with gr.Tab("E. Auditoría Varietal"):
                    gr.Markdown("### 📂 Comportamiento por Variedad en Pipeline Histórico\n*(Nota: Módulo configurado sobre T0 retrospectivo de referencia).*")
                    with gr.Row():
                        f_fundo = gr.Dropdown(fundos, value="Todos", label="Fundo / Viñedo")
                        f_var = gr.Dropdown(variedades, value="Todas", label="Variedad")
                    f_table = gr.Dataframe(value=_safe(gdd["resumen_t0"]), interactive=False, wrap=True)
                    gr.Markdown("### 🧬 Registro de Matrices Emparejadas (Fenología + Clima)")
                    gr.Dataframe(value=_safe(phenology["prepared_manifest"]), interactive=False, wrap=True)

                    def update_fenologia(fundo, variedad):
                        d = _filter_table(gdd["resumen_t0"], fundo, variedad)
                        return _safe(d)

                    f_fundo.change(update_fenologia, [f_fundo, f_var], [f_table])
                    f_var.change(update_fenologia, [f_fundo, f_var], [f_table])

                with gr.Tab("F. Plausibilidad Fisiológica (Frío Invernal)"):
                    gr.Markdown("> **🧪 NOTA DE INVESTIGACIÓN:** Evaluación exploratoria de balance bioclimático previo a brotación.")
                    gr.Markdown("> **💡 DESGLOSE HORARIO VS DIARIO:** El cálculo de **Frío Invernal (Chill Portions)** requiere integración horaria continua (disponible hasta Junio 2025). La **Acumulación Térmica (GDD)** se integra desde registros diarios completos con alta precisión operacional.")
                    
                    with gr.Row():
                        f_chill_plot = gr.Plot(value=panel_d_chill_plot(gdd.get("chill_dynamic", pd.DataFrame())))
                    
                    gr.Markdown("### 🏷️ Semáforo de Plausibilidad Bioclimática por Fundo")
                    f_chill_table = gr.Dataframe(value=_safe(panel_d_chill_table(gdd.get("chill_dynamic", pd.DataFrame()))), interactive=False, wrap=True)
                    
                    gr.Markdown("### 📑 Detalle Analítico de Calor Disponible (GDD Mayo — Septiembre)")
                    f_chill_full_table = gr.Dataframe(value=_safe(gdd.get("chill_dynamic", pd.DataFrame())), interactive=False, wrap=True)

        with gr.Tab("📈 Madurez técnica"):
            gr.Markdown(
                "> **🍇 SEGUIMIENTO ENOLÓGICO TEMPORAL:** Curvas de madurez técnica por viñedo, variedad y temporada. "
                "Los registros por cuartel y muestra se integran espacialmente como promedio simple por fecha/fundo/variedad/temporada "
                "en el gráfico principal y se detallan explícitamente en la tabla secundaria."
            )
            maturity_vars_choices = [
                (label, col)
                for label, col in [
                    ("Brix [°Bx]", "brix"),
                    ("pH", "pH"),
                    ("Acidez Sulfúrica [g/L eq.]", "acidez_sulfurica"),
                    ("Acidez Tartárica [g/L eq.]", "acidez_tartarica"),
                    ("Peso de Baya [g]", "peso_baya"),
                    ("Azúcar Real en Baya [g/baya]", "azucar_real_baya_g"),
                ]
                if col in maturity_technical.columns
            ]
            init_var = maturity_vars_choices[0][1] if maturity_vars_choices else "brix"

            with gr.Row():
                m_var = gr.Dropdown(maturity_vars_choices or [("Brix", "brix")], value=init_var, label="Parámetro Enológico / Target", scale=2)
                m_fundo = gr.Dropdown(_choices(maturity_technical, "fundo", "Todos"), value="Todos", label="Viñedo / Fundo", scale=2)
                m_variedad = gr.Dropdown(_choices(maturity_technical, "variedad", "Todas"), value="Todas", label="Variedad", scale=2)
                m_temporada = gr.Dropdown(_choices(maturity_technical, "temporada", "Todas las temporadas"), value="Todas las temporadas", label="Temporada", scale=2)

            initial_m = _filter_maturity(maturity_technical, "Todas", "Todos", "Todas las temporadas")
            m_plot = gr.Plot(value=maturity_curve_grouped(initial_m, init_var))
            gr.Markdown("### 📑 Trazabilidad Analítica de Controles (Cuartel y Muestras)")
            m_table = gr.Dataframe(value=_safe(prepare_maturity_traceability_table(initial_m, init_var)), interactive=False, wrap=True)

            def update_maturity(var, fundo, variedad, temporada):
                d = _filter_maturity(maturity_technical, variedad, fundo, temporada)
                return maturity_curve_grouped(d, var), _safe(prepare_maturity_traceability_table(d, var))

            for control in [m_var, m_fundo, m_variedad, m_temporada]:
                control.change(
                    update_maturity,
                    [m_var, m_fundo, m_variedad, m_temporada],
                    [m_plot, m_table],
                )


        state = build_state()
        targets = available_targets(state["metrics"], LUIS_BASE_DIR)
        target0 = _safe_dropdown_value("antocianinas_mg_baya", targets)
        schemes0 = available_schemes(state["metrics"], target0)
        scheme0 = _safe_dropdown_value("cv5_mixed", schemes0)
        combos_df = available_combos(state["metrics"], target0, scheme0)
        combo_opts = ["Todos"] + combos_df["predictors"].tolist() if not combos_df.empty else ["Todos"]
        combo_h_opts = ["Todos"] + combos_df["combo_human"].tolist() if not combos_df.empty else ["Todos"]
        logging.info("Dropdown target choices: %s", targets)
        logging.info("Dropdown target value: %s", target0)
        logging.info("Dropdown scheme choices for target '%s': %s", target0, schemes0)
        logging.info("Dropdown scheme value: %s", scheme0)
        logging.info("Dropdown combo choices count: %s", len(combo_opts))
        logging.info("Dropdown readable combo choices count: %s", len(combo_h_opts))
    
        orig0 = load_original_data(target0, LUIS_BASE_DIR)
        var_opts = ["Todas"] + sorted(orig0["variedad"].dropna().astype(str).unique().tolist()) if "variedad" in orig0.columns else ["Todas"]
        fundo_opts = ["Todos"] + sorted(orig0["fundo"].dropna().astype(str).unique().tolist()) if "fundo" in orig0.columns else ["Todos"]
        logging.info("Dropdown variedad choices count: %s", len(var_opts))
        logging.info("Dropdown fundo choices count: %s", len(fundo_opts))
    
        startup_status = (
            "### Estado de carga\n"
            f"- Directorio de artefactos: `{LUIS_BASE_DIR}`\n"
            f"- Archivos detectados: `{len(state['artifacts'])}`\n"
            f"- Filas de metricas: `{len(state['metrics'])}`\n"
            f"- Filas de predicciones: `{len(state['predictions'])}`\n"
            f"- Targets detectados: `{len(targets)}`\n"
            f"- Esquemas para target inicial: `{', '.join(schemes0) if schemes0 else 'ninguno'}`"
        )
        if not targets or not schemes0:
            startup_status += (
                "\n\nNo se encontraron artefactos suficientes para poblar todos los filtros. "
                f"Verifica `{LUIS_BASE_DIR / 'outputs'}` y `{LUIS_BASE_DIR / 'data' / 'prepared'}`."
            )
    
    
        with gr.Tab("🤖 Modelos de Madurez Fenólica (IA/RF)"):
            with gr.Row():
                with gr.Column(scale=1):
                    target_dd = gr.Dropdown(label="Target", choices=targets, value=target0)
                    scheme_dd = gr.Dropdown(label="Estrategia de validación", choices=schemes0, value=scheme0)
                    variedad_dd = gr.Dropdown(label="Variedad", choices=var_opts, value="Todas", visible=False, interactive=False)
                    fundo_dd = gr.Dropdown(label="Fundo", choices=fundo_opts, value="Todos")
                    combo_dd = gr.Dropdown(label="Combinación (raw)", choices=combo_opts, value="Todos")
                    combo_h_dd = gr.Dropdown(label="Combinación legible", choices=combo_h_opts, value="Todos")
                    viz_type_dd = gr.Dropdown(
                        label="Tipo de visualización",
                        choices=[
                            "resumen general",
                            "distribución por variedad",
                            "series temporales",
                            "boxplots por fundo",
                            "predicho vs observado",
                            "residuos",
                            "ranking de fundos por MAE",
                            "importancia por permutación",
                            "importancia SHAP",
                            "comparación MAE/SHAP",
                            "tabla de métricas",
                            "tabla de mejores combinaciones",
                        ],
                        value="resumen general",
                    )
                    refresh_btn = gr.Button("Recargar y actualizar filtros")
    
                with gr.Column(scale=3):
                    with gr.Tabs():
                        with gr.Tab("Resumen general"):
                            resumen_md = gr.Markdown()
                            resumen_table = gr.Dataframe(label="Tabla de métricas agregadas")
                            resumen_scatter = gr.Plot(label="MAE vs R2")
    
                        with gr.Tab("Datos originales"):
                            orig_msg = gr.Markdown()
                            fig_box_var = gr.Plot(label="Boxplot target por variedad")
                            fig_ts_target = gr.Plot(label="Serie temporal target")
                            fig_box_fundo = gr.Plot(label="Boxplot target por fundo")
                            predictor_dd = gr.Dropdown(label="Variable original / predictor", choices=[], value=None)
                            fig_ts_pred = gr.Plot(label="Serie temporal predictor")
    
                        with gr.Tab("Desempeño modelos"):
                            perf_table = gr.Dataframe(label="Métricas por combinación")
                            perf_scatter = gr.Plot(label="Scatter MAE vs R2")
                            perf_boxplot_msg = gr.Markdown()
                            perf_boxplot_img = gr.Image(label="Boxplot global por combinación (precomputado)", type="filepath")
    
                        with gr.Tab("LOFO por fundo"):
                            lofo_table = gr.Dataframe(label="Tabla LOFO")
                            lofo_rank = gr.Plot(label="Ranking de fundos por MAE")
    
    
                        with gr.Tab("Importancia"):
                            tipo_imp_dd = gr.Dropdown(label="tipo_importancia", choices=["permutation", "shap", "mae_shap"], value="permutation")
                            imp_msg = gr.Markdown()
                            imp_plot = gr.Plot(label="Importancia")
                            imp_table = gr.Dataframe(label="Tabla importancia")
    
                        with gr.Tab("Comparador de combinaciones"):
                            combo_mult = gr.Dropdown(label="Selecciona 2+ combinaciones", multiselect=True, choices=combo_opts, value=[])
                            cmp_table = gr.Dataframe(label="Tabla comparativa")
                            cmp_mae = gr.Plot(label="MAE")
                            cmp_r2 = gr.Plot(label="R2")
                            cmp_mej = gr.Plot(label="Mejora MAE %")
    
                        with gr.Tab("Explorador archivos"):
                            explorer_table = gr.Dataframe(label="Archivos detectados")
    
                        with gr.Tab("Exportación"):
                            export_btn = gr.Button("Exportar tablas filtradas")
                            out_metrics_file = gr.File(label="Descargar métricas CSV")
                            out_preds_file = gr.File(label="Descargar predicciones CSV")
                            out_imp_file = gr.File(label="Descargar importancia CSV")
                            out_md_file = gr.File(label="Descargar resumen Markdown")
    
            def _sync_filters(state, target, scheme):
                return refresh_options(state, target, scheme)
    
            refresh_btn.click(
                _sync_filters,
                inputs=[app_state, target_dd, scheme_dd],
                outputs=[target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd, combo_h_dd],
            )
            target_dd.change(
                _sync_filters,
                inputs=[app_state, target_dd, scheme_dd],
                outputs=[target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd, combo_h_dd],
            )
            scheme_dd.change(
                _sync_filters,
                inputs=[app_state, target_dd, scheme_dd],
                outputs=[target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd, combo_h_dd],
            )
    
            def _combo_from_human(state, target, scheme, combo_h):
                combos_df = available_combos(state["metrics"], target, scheme)
                if combo_h == "Todos" or combos_df.empty:
                    return "Todos"
                m = combos_df[combos_df["combo_human"] == combo_h]
                return m["predictors"].iloc[0] if not m.empty else "Todos"
    
            combo_h_dd.change(_combo_from_human, inputs=[app_state, target_dd, scheme_dd, combo_h_dd], outputs=[combo_dd])
    
            def _update_all_main(state, target, scheme, combo, variedad, fundo):
                r_md, r_tbl, r_sc = update_resumen(state, target, scheme)
                o_msg, b1, t1, b2, t2, pred_dd_new = update_datos_originales(target, variedad, fundo, "")
                fs = filtered_summary(state, target, scheme)
                perf_img, perf_msg = _performance_boxplot_image(target, scheme)
                lo_tbl, lo_fig = update_lofo(state, target, combo)
                return r_md, r_tbl, r_sc, o_msg, b1, t1, b2, t2, pred_dd_new, fs, r_sc, perf_msg, perf_img, lo_tbl, lo_fig
    
            refresh_btn.click(
                _update_all_main,
                inputs=[app_state, target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd],
                outputs=[
                    resumen_md,
                    resumen_table,
                    resumen_scatter,
                    orig_msg,
                    fig_box_var,
                    fig_ts_target,
                    fig_box_fundo,
                    fig_ts_pred,
                    predictor_dd,
                    perf_table,
                    perf_scatter,
                    perf_boxplot_msg,
                    perf_boxplot_img,
                    lofo_table,
                    lofo_rank,
                ],
            )
    
            predictor_dd.change(
                lambda t, v, f, p: update_datos_originales(t, v, f, p)[4],
                inputs=[target_dd, variedad_dd, fundo_dd, predictor_dd],
                outputs=[fig_ts_pred],
            )
    
            for trigger in [target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd]:
                trigger.change(
                    _update_all_main,
                    inputs=[app_state, target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd],
                    outputs=[
                        resumen_md,
                        resumen_table,
                        resumen_scatter,
                        orig_msg,
                        fig_box_var,
                        fig_ts_target,
                        fig_box_fundo,
                        fig_ts_pred,
                        predictor_dd,
                        perf_table,
                        perf_scatter,
                        perf_boxplot_msg,
                        perf_boxplot_img,
                        lofo_table,
                        lofo_rank,
                    ],
                )
    
            tipo_imp_dd.change(
                update_importancia,
                inputs=[app_state, target_dd, scheme_dd, combo_dd, tipo_imp_dd],
                outputs=[imp_msg, imp_plot, imp_table],
            )
            for trigger in [target_dd, scheme_dd, combo_dd]:
                trigger.change(
                    update_importancia,
                    inputs=[app_state, target_dd, scheme_dd, combo_dd, tipo_imp_dd],
                    outputs=[imp_msg, imp_plot, imp_table],
                )
    
            def _update_combo_mult(state, target, scheme):
                combos_df = available_combos(state["metrics"], target, scheme)
                opts = combos_df["predictors"].tolist() if not combos_df.empty else []
                return gr.Dropdown(choices=["Todos"] + opts, value=[])
    
            def _expand_combo_todos(state, target, scheme, selected):
                combos_df = available_combos(state["metrics"], target, scheme)
                all_opts = combos_df["predictors"].tolist() if not combos_df.empty else []
                selected = selected or []
                if "Todos" in selected:
                    return all_opts
                return [x for x in selected if x in all_opts]
    
            refresh_btn.click(_update_combo_mult, inputs=[app_state, target_dd, scheme_dd], outputs=[combo_mult])
            target_dd.change(_update_combo_mult, inputs=[app_state, target_dd, scheme_dd], outputs=[combo_mult])
            scheme_dd.change(_update_combo_mult, inputs=[app_state, target_dd, scheme_dd], outputs=[combo_mult])
    
            combo_mult.change(
                _expand_combo_todos,
                inputs=[app_state, target_dd, scheme_dd, combo_mult],
                outputs=[combo_mult],
            ).then(
                update_comparador,
                inputs=[app_state, target_dd, scheme_dd, combo_mult],
                outputs=[cmp_table, cmp_mae, cmp_r2, cmp_mej],
            )
    
            refresh_btn.click(update_explorer, inputs=[app_state], outputs=[explorer_table])
            demo.load(update_explorer, inputs=[app_state], outputs=[explorer_table])
    
            export_btn.click(
                export_tables,
                inputs=[app_state, target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd],
                outputs=[out_metrics_file, out_preds_file, out_imp_file, out_md_file],
            )

            # initial render
            demo.load(
                _update_all_main,
                inputs=[app_state, target_dd, scheme_dd, combo_dd, variedad_dd, fundo_dd],
                outputs=[
                    resumen_md,
                    resumen_table,
                    resumen_scatter,
                    orig_msg,
                    fig_box_var,
                    fig_ts_target,
                    fig_box_fundo,
                    fig_ts_pred,
                    predictor_dd,
                    perf_table,
                    perf_scatter,
                    perf_boxplot_msg,
                    perf_boxplot_img,
                    lofo_table,
                    lofo_rank,
                ],
            )

            demo.load(
                update_importancia,
                inputs=[app_state, target_dd, scheme_dd, combo_dd, tipo_imp_dd],
                outputs=[imp_msg, imp_plot, imp_table],
            )
    
    
        
        with gr.Tab("🔗 Integración conceptual"):
            gr.Markdown(
                """
                ### 🔄 Cadena de Valor del Proyecto CORFO (Objetivo 3)

                1. **⛅ Clima Fisiológico:** Consolidación horaria e interpolación de estaciones meteorológicas en viñedos.
                2. **🌿 Fenología Dinámica:** Biofix de brotación fisiológica e integración térmica en Grados Día (GDD).
                3. **📈 Madurez Técnica:** Monitoreo secuencial de sólidos solubles, pH, AT y peso de baya.
                4. **🍷 Madurez Fenólica:** Extracción y especiación de taninos y antocianinas monoméricas.
                5. **🧠 Predictor Enológico:** Modelos de bosque aleatorio e IA simbólica con validación espacial cruzada.
                6. **🎯 Soporte a la Decisión:** QA científico y agrometeorológico previo al corte comercial en bodega.
                """
            )
            gr.Markdown("### 🗃️ Matriz Consolidada Multi-Origen")
            gr.Dataframe(value=_safe(climate["master"]), interactive=False, wrap=True)


        with gr.Tab("📑 Trazabilidad CORFO"):
            gr.Markdown(
                """
                ### 🏛️ Seguimiento Curricular de Hitos y Entregables CORFO

                | Actividad | Entregable Técnico | Estado Actual | Bloqueo o Próximo Hito |
                |---|---|---|---|
                | **Act. 16** | Proyecciones Agrometeorológicas | 🟡 PARCIAL | Operacional con clima histórico. Pendiente acoplar pronósticos GFS a 15 días. |
                | **Act. 17** | Modelo Fenológico ELP | 🟢 CERRADO | Dataset FULL_v1 validado. Esperando modelo final INRIA para evaluación LOFO. |
                | **Act. 18/19**| Monitoreo de Madurez en Viñedo | 🟡 EN PROGRESO | Curvas técnicas 25/26 OK. Fenólica histórica OK, esperando laboratorio 2026. |
                | **Act. 20** | IA Predictiva de Cosecha | 🟢 CERRADO | Pipeline `v2` empaquetado y verificado con métricas satisfactorias. |
                | **Act. 21** | Optimización Multiobjetivo Bodega| 🔴 NO INICIADO | Requiere parametrizar función de costos con dirección enológica. |
                | **Act. 22** | Validación Sensorial en Bodega | ⚪ PENDIENTE | Subordinado a ventanas de cosecha resultantes de Act. 21. |
                """
            )

        with gr.Tab("ℹ️ Ayuda & Documentación"):
            gr.Markdown(
                """
                ### 📘 Manual Operativo del Repositorio Limpio

                1. **Inmutabilidad de SharePoint (`data/all_project/`):** **🚫 INTOCABLE.** Directorio espejo en modo lectura estricta.
                2. **Ejecución de Pipeline:** Para re-entrenar modelos base, invoca `python src/modeling/internal_baseline_v2/run_pipeline_v2.py`.
                3. **Lanzador Local:** Abre `ABRIR_DASHBOARD.bat` o navega a `ACCESO_DASHBOARD.html`.
                4. **Marco Técnico del Proyecto (CORFO):** Consulta `docs/objetivo_3_vendimia_5_0.md` para entender el flujo científico completo del Objetivo 3.
                5. **Contacto técnico:** Diego Núñez — análisis de datos, modelamiento y trazabilidad del Objetivo 3.
                """
            )

    return demo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-name", default=HOST)
    parser.add_argument("--server-port", type=int, default=PORT)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    setup_logging(LOG_DIR / "dashboard_obj3_integrado.log")
    app = build_app()
    app.queue().launch(server_name=args.server_name, server_port=args.server_port, share=args.share, theme=gr.themes.Soft(primary_hue="rose", neutral_hue="slate"), css=CUSTOM_CSS)


if __name__ == "__main__":
    main()
