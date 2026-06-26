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

                with gr.Tab("B. Evaluación Operacional (Residuo T0 Latitudinal)"):
                    f_lat_error_plot = gr.Plot(value=panel_a_operativo_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))

                with gr.Tab("C. Diagnóstico de Leakage (T0 Cerrado vs Latitudinal)"):
                    gr.Markdown("> ⚠️ El T0 cerrado es retrospectivo. No usar como predictor operativo.")
                    with gr.Row():
                        f_t0_comparison_plot = gr.Plot(value=panel_b_diagnostico_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                        f_baseline_plot = gr.Plot(value=baseline_comparison_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                    gr.Markdown("### 📋 Matriz de Diagnóstico y Alertas de Leakage (Cabernet Sauvignon)")
                    f_alert_table = gr.Dataframe(value=_safe(cabernet_diagnostic_table(gdd.get("diagnostico_cs_reg", pd.DataFrame()))), interactive=False, wrap=True)

                with gr.Tab("D. Auditoría Varietal"):
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

                with gr.Tab("E. Auditoría GDD por Biofix"):
                    gr.Markdown(
                        "**Evaluación fisiológica del inicio de conteo térmico (Biofix).** "
                        "Permite contrastar cómo cambia la curva de GDD acumulado y detectar posibles "
                        "arrastres de calor invernal de la temporada anterior.\n\n"
                        "> ℹ️ **Nota metodológica:** El selector de biofix audita acumulación GDD; "
                        "no recalcula todavía el t0 operativo ni reconstruye el indicador biológico. "
                        "*(Propuesta futura de análisis de sensibilidad: `t0_sensitivity_by_biofix.csv`)*."
                    )
                    bf_df = gdd.get("biofix_timeseries", pd.DataFrame())
                    bf_sum = gdd.get("biofix_summary", pd.DataFrame())

                    bf_fundos = sorted(bf_df["fundo"].dropna().unique().tolist()) if not bf_df.empty else ["qba_seca"]
                    bf_temps = sorted(bf_df["temporada"].dropna().unique().tolist()) if not bf_df.empty else ["2025_2026"]
                    bf_vars = sorted(bf_df["variedad"].dropna().unique().tolist()) if not bf_df.empty else ["cabernet_sauvignon"]
                    bf_tipos = sorted(bf_df["biofix_tipo"].dropna().unique().tolist()) if not bf_df.empty else ["t0_operativo"]

                    with gr.Row():
                        bf_fundo_dd = gr.Dropdown(bf_fundos, value=bf_fundos[0] if bf_fundos else "", label="Fundo / Viñedo")
                        bf_temp_dd = gr.Dropdown(bf_temps, value=bf_temps[0] if bf_temps else "", label="Temporada")
                        bf_var_dd = gr.Dropdown(bf_vars, value=bf_vars[0] if bf_vars else "", label="Variedad")
                        bf_tipo_dd = gr.Dropdown(bf_tipos, value="t0_operativo" if "t0_operativo" in bf_tipos else (bf_tipos[0] if bf_tipos else ""), label="Candidato Biofix")

                    init_bf_fig = gdd_biofix_timeseries_plot(
                        bf_df,
                        bf_fundos[0] if bf_fundos else "",
                        bf_temps[0] if bf_temps else "",
                        bf_vars[0] if bf_vars else "",
                        "t0_operativo" if "t0_operativo" in bf_tipos else (bf_tipos[0] if bf_tipos else ""),
                    )
                    bf_plot = gr.Plot(value=init_bf_fig)

                    gr.Markdown("### 📋 Resumen Comparativo de Acumulación y Alertas por Biofix")
                    bf_table = gr.Dataframe(value=_safe(bf_sum), interactive=False, wrap=True)

                    def update_bf_panel(f, t, v, b):
                        fig = gdd_biofix_timeseries_plot(bf_df, f, t, v, b)
                        sub_sum = pd.DataFrame()
                        if not bf_sum.empty:
                            sub_sum = bf_sum[
                                (bf_sum["fundo"].astype(str).str.strip().str.lower() == str(f).strip().lower())
                                & (bf_sum["temporada"].astype(str) == str(t))
                                & (bf_sum["variedad"].astype(str).str.strip().str.lower() == str(v).strip().lower())
                            ].copy()
                        return fig, _safe(sub_sum)

                    for dd in [bf_fundo_dd, bf_temp_dd, bf_var_dd, bf_tipo_dd]:
                        dd.change(update_bf_panel, [bf_fundo_dd, bf_temp_dd, bf_var_dd, bf_tipo_dd], [bf_plot, bf_table])

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

        with gr.Tab("🍷 Madurez fenólica"):
            gr.Markdown("> **🔬 RECEPCIÓN DE MUESTRAS 2026:** Las curvas desplegadas representan las temporadas históricas consolidadas. Las muestras analíticas 2026 están pendientes de titulación en laboratorio de especialidad.")
            p_var = gr.Dropdown(phenolic_vars or [""], value=(phenolic_vars[0] if phenolic_vars else ""), label="Compuesto Fenólico")
            p_plot = gr.Plot(value=maturity_curve(phenolic_df, phenolic_vars[0] if phenolic_vars else "", "Curva de Madurez Fenólica"))
            gr.Markdown("### 🧪 Base de Mediciones de HPLC y Espectrofotometría")
            gr.Dataframe(value=_safe(phenolic_df), interactive=False, wrap=True)
            p_var.change(lambda v: maturity_curve(phenolic_df, v, "Curva de Madurez Fenólica"), p_var, p_plot)

        with gr.Tab("🤖 Modelos IA / RF / PySR"):
            gr.Markdown("> **📌 REFERENCIA PREDICTIVA:** Evaluación técnica de modelos Random Forest (RF) y fórmulas explícitas obtenidas por Regresión Simbólica (PySR).")
            with gr.Row():
                target = gr.Dropdown(model_targets, value=model_targets[0], label="Variable Objetivo (Target)")
                scheme = gr.Dropdown(schemes, value=schemes[0], label="Esquema de Validación")
            model_plot = gr.Plot(value=metric_ranking(model_metrics))
            pred_plot = gr.Plot(value=observed_vs_pred(luis["predictions_rf"]))
            gr.Markdown("### 📊 Tabla de Desempeño Multimodelo (MAE / R²)")
            model_table = gr.Dataframe(value=_safe(model_metrics), interactive=False, wrap=True)

            def update_models(t, s):
                d = model_metrics.copy()
                if t != "Todos" and "target_key" in d.columns:
                    d = d[d["target_key"] == t]
                if s != "Todos" and "scheme" in d.columns:
                    d = d[d["scheme"] == s]
                preds = luis["predictions_rf"].copy()
                if t != "Todos" and "target_key" in preds.columns:
                    preds = preds[preds["target_key"] == t]
                return _safe(d), metric_ranking(d), observed_vs_pred(preds)

            target.change(update_models, [target, scheme], [model_table, model_plot, pred_plot])
            scheme.change(update_models, [target, scheme], [model_table, model_plot, pred_plot])

        with gr.Tab("💡 Interpretabilidad agronómica"):
            gr.Markdown(
                "> **🌱 GUÍA AGRONÓMICA SHAP:** Los sólidos solubles (°Brix) acoplan su evolución a la acumulación térmica (GDD). El pH y la acidez total responden a temperaturas máximas e índices nocturnos de degradación del ácido málico. La síntesis de antocianinas y taninos actúa como respuesta multivariada no lineal a estrés térmico y déficit de presión de vapor (VPD)."
            )
            with gr.Row():
                gr.Plot(value=importance_bar(luis["shap"], "shap_mean_abs"))
                gr.Plot(value=importance_bar(luis["permutation"], "perm_importance_mean"))
            gr.Markdown("### 📜 Ecuaciones Explícitas Descubiertas por Regresión Simbólica (PySR)")
            gr.Dataframe(value=_safe(luis["metrics_pysr"]), interactive=False, wrap=True)

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
