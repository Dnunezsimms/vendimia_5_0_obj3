from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import gradio as gr
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import HOST, LOG_DIR, PORT, REPO_ROOT  # noqa: E402
from src.loaders import find_columns, load_state, numeric_columns, read_table, setup_logging  # noqa: E402
from src.plots import (  # noqa: E402
    climate_status_bar,
    coverage_bar,
    empty_figure,
    gdd_progress_bar,
    panel_a_operativo_plot,
    panel_b_diagnostico_plot,
    baseline_comparison_plot,
    cabernet_diagnostic_table,
    panel_d_chill_table,
    panel_d_chill_plot,
    importance_bar,
    maturity_curve,
    maturity_curve_grouped,
    metric_ranking,
    observed_vs_pred,
)


def _safe(df: pd.DataFrame, max_rows: int = 500) -> pd.DataFrame:
    return df.head(max_rows).copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()


def _markdown_status(state: dict) -> str:
    resumen = state["climate"]["resumen"]
    audit = state["audit"]
    luis = state["luis"]
    n_ok = int((resumen.get("estado", pd.Series(dtype=str)) == "OK").sum()) if not resumen.empty else 0
    n_val = int((resumen.get("estado", pd.Series(dtype=str)) == "REQUIERE_VALIDACION_MANUAL").sum()) if not resumen.empty else 0
    return (
        "### Resumen Ejecutivo Obj3\n\n"
        "**Estado General:** Consolidación de línea base técnica completada. Transición hacia validación fenólica y optimización.\n\n"
        "| Módulo | Estado | Dataset Vigente / Base |\n"
        "|---|---|---|\n"
        "| **Clima** | 🟢 CERRADO | `consolidado_fenologia_ELP_OBJ3_INDICES_BIOCLIMATICOS.csv` |\n"
        "| **Fenología** | 🟢 CERRADO | `consolidado_fenologia_ELP_MODELABLE_FULL_v1.csv` |\n"
        "| **Madurez Técnica** | 🟢 CERRADO | `madurez_tecnica_2025_2026_train_test_CANONICO_V5_INDICES_ORIGINALES.csv` |\n"
        "| **Madurez Fenólica** | 🟡 EN PROGRESO | Bloqueado por resultados lab 2026 |\n"
        "| **Modelos (Baseline)** | 🟢 CERRADO | `run_pipeline_v2.py` ejecutado y métricas listas |\n"
        "| **Export INRIA** | 🟡 ESPERANDO RESPUESTA | `paquete_luis_inria_fenologia_ELP_OBJ3_CLEAN_2.zip` |\n\n"
        "### Auditoría de carga\n"
        f"- Repo: `{REPO_ROOT}`\n"
        f"- Clima: `{n_ok}` fundos OK, `{n_val}` en validación manual.\n"
        f"- RF metrics Luis: `{len(luis['metrics_rf'])}` filas.\n"
        f"- PySR/SR metrics Luis: `{len(luis['metrics_pysr'])}` filas.\n"
        f"- Predicciones RF: `{len(luis['predictions_rf'])}` filas.\n"
        f"- Artefactos auditados: `{len(audit)}` entradas.\n"
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


def _filter_maturity(df: pd.DataFrame, variedad: str, fundo: str, temporada: str, cuartel: str) -> pd.DataFrame:
    d = df.copy()
    filters = {
        "variedad": variedad,
        "fundo": fundo,
        "temporada": temporada,
        "cuartel": cuartel,
    }
    for col, value in filters.items():
        if value not in {"Todas", "Todos", "Todas las temporadas", "Todos los cuarteles"} and col in d.columns:
            d = d[d[col].astype(str) == str(value)]
    return d


def build_app() -> gr.Blocks:
    state = load_state()
    logging.info("Estado inicial cargado")

    climate = state["climate"]
    gdd = state["gdd"]
    phenology = state["phenology"]
    maturity = state["maturity"]
    luis = state["luis"]
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

    with gr.Blocks(title="Obj.3 Vendimia 5.0 - Dashboard exploratorio") as demo:
        gr.Markdown("# Dashboard exploratorio integrado Obj.3")
        gr.Markdown("Clima -> fenologia -> madurez tecnica -> madurez fenolica -> modelos -> decision de cosecha")

        with gr.Tab("Estado del sistema"):
            gr.Markdown(_markdown_status(state))
            with gr.Row():
                gr.Plot(value=climate_status_bar(climate["resumen"]))
                gr.Plot(value=coverage_bar(climate["resumen"]))
            gr.Markdown("Tabla maestra fundo-estacion-fuente-temporada")
            gr.Dataframe(value=_safe(climate["master"]), interactive=False, wrap=True)
            gr.Markdown("Gaps por fundo")
            gr.Dataframe(value=_safe(climate["gaps"]), interactive=False, wrap=True)
            gr.Markdown("Equivalencias y auditoria de artefactos")
            with gr.Row():
                gr.Dataframe(value=_safe(climate["equivalencias"]), interactive=False, wrap=True)
                gr.Dataframe(value=_safe(state["audit"]), interactive=False, wrap=True)

        with gr.Tab("Fenología"):
            gr.Markdown("> **⚠️ ADVERTENCIA:** El t0 cerrado es diagnóstico retrospectivo; el t0 latitudinal es el candidato operativo/predictivo. La validación formal requiere leave-one-fundo-out espacial.")
            with gr.Tabs():
                with gr.Tab("Evaluación operacional preliminar del t0 latitudinal"):
                    f_lat_error_plot = gr.Plot(value=panel_a_operativo_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                    
                with gr.Tab("Panel B: Diagnóstico T0 y Alertas"):
                    gr.Markdown("Comparación retrospectiva del t0 cerrado vs latitudinal y evaluación del *leakage*.")
                    with gr.Row():
                        f_t0_comparison_plot = gr.Plot(value=panel_b_diagnostico_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                        f_baseline_plot = gr.Plot(value=baseline_comparison_plot(gdd.get("diagnostico_cs_reg", pd.DataFrame())))
                    gr.Markdown("**Cabernet Sauvignon: Tabla Diagnóstica Base (T0 y Leakage)**")
                    f_alert_table = gr.Dataframe(value=_safe(cabernet_diagnostic_table(gdd.get("diagnostico_cs_reg", pd.DataFrame()))), interactive=False, wrap=True)
                    
                with gr.Tab("Panel C: Calidad y Evaluación Varietal Heredada"):
                    gr.Markdown("**Evaluación varietal heredada del pipeline actual — usa t0 Cabernet cerrado**\n*(Nota: A futuro el pipeline debe exportar la evaluación varietal recalculada desde `t0_regresion_latitudinal`).*")
                    with gr.Row():
                        f_fundo = gr.Dropdown(fundos, value="Todos", label="Fundo")
                        f_var = gr.Dropdown(variedades, value="Todas", label="Variedad")
                    f_table = gr.Dataframe(value=_safe(gdd["resumen_t0"]), interactive=False, wrap=True)
                    gr.Markdown("Merges fenología-clima detectados")
                    gr.Dataframe(value=_safe(phenology["prepared_manifest"]), interactive=False, wrap=True)

                    def update_fenologia(fundo, variedad):
                        d = _filter_table(gdd["resumen_t0"], fundo, variedad)
                        return _safe(d)

                    f_fundo.change(update_fenologia, [f_fundo, f_var], [f_table])
                    f_var.change(update_fenologia, [f_fundo, f_var], [f_table])

                with gr.Tab("Panel D: Plausibilidad fisiológica del biofix (Frío + Calor)"):
                    gr.Markdown("> **NOTA METODOLÓGICA:** Esta sección es una auditoría de plausibilidad fisiológica, **no una validación completa del biofix**. Se encuentra pendiente de completitud con los datos horarios de Jul-Sep 2025.")
                    gr.Markdown("> **SEPARACIÓN DE COBERTURAS:** El **Frío Dinámico** está incompleto porque depende estrictamente de datos horarios (que cortan en junio 2025). El **Calor (GDD)** mostrado es 'calor diario disponible' calculado desde sets diarios completos, por lo que tiene alta confiabilidad, distinta a la del frío horario.")
                    
                    with gr.Row():
                        f_chill_plot = gr.Plot(value=panel_d_chill_plot(gdd.get("chill_dynamic", pd.DataFrame())))
                    
                    gr.Markdown("**Diagnóstico Acumulado y Semáforo de Confianza (Frío Horario)**")
                    f_chill_table = gr.Dataframe(value=_safe(panel_d_chill_table(gdd.get("chill_dynamic", pd.DataFrame()))), interactive=False, wrap=True)
                    
                    gr.Markdown("**Detalle Calor Diario Disponible (GDD Mensual Mayo - Septiembre)**")
                    f_chill_full_table = gr.Dataframe(value=_safe(gdd.get("chill_dynamic", pd.DataFrame())), interactive=False, wrap=True)

        with gr.Tab("Madurez tecnica"):
            with gr.Row():
                m_var = gr.Dropdown(maturity_vars or [""], value=(maturity_vars[0] if maturity_vars else ""), label="Variable")
                m_variedad = gr.Dropdown(_choices(maturity_technical, "variedad", "Todas"), value="Todas", label="Variedad")
                m_fundo = gr.Dropdown(_choices(maturity_technical, "fundo", "Todos"), value="Todos", label="Fundo")
            with gr.Row():
                m_temporada = gr.Dropdown(_choices(maturity_technical, "temporada", "Todas las temporadas"), value="Todas las temporadas", label="Temporada")
                m_cuartel = gr.Dropdown(_choices(maturity_technical, "cuartel", "Todos los cuarteles"), value="Todos los cuarteles", label="Cuartel")
                m_group_cuartel = gr.Checkbox(value=False, label="Agrupar por cuartel")
            initial_m = _filter_maturity(maturity_technical, "Todas", "Todos", "Todas las temporadas", "Todos los cuarteles")
            m_plot = gr.Plot(value=maturity_curve_grouped(initial_m, maturity_vars[0] if maturity_vars else "", False))
            m_table = gr.Dataframe(value=_safe(initial_m), interactive=False, wrap=True)

            def update_maturity(var, variedad, fundo, temporada, cuartel, group_cuartel):
                d = _filter_maturity(maturity_technical, variedad, fundo, temporada, cuartel)
                return maturity_curve_grouped(d, var, bool(group_cuartel)), _safe(d)

            for control in [m_var, m_variedad, m_fundo, m_temporada, m_cuartel, m_group_cuartel]:
                control.change(
                    update_maturity,
                    [m_var, m_variedad, m_fundo, m_temporada, m_cuartel, m_group_cuartel],
                    [m_plot, m_table],
                )

        with gr.Tab("Madurez fenolica"):
            p_var = gr.Dropdown(phenolic_vars or [""], value=(phenolic_vars[0] if phenolic_vars else ""), label="Variable")
            p_plot = gr.Plot(value=maturity_curve(phenolic_df, phenolic_vars[0] if phenolic_vars else "", "Curva de madurez fenolica"))
            gr.Dataframe(value=_safe(phenolic_df), interactive=False, wrap=True)
            p_var.change(lambda v: maturity_curve(phenolic_df, v, "Curva de madurez fenolica"), p_var, p_plot)

        with gr.Tab("Modelos"):
            with gr.Row():
                target = gr.Dropdown(model_targets, value=model_targets[0], label="Target")
                scheme = gr.Dropdown(schemes, value=schemes[0], label="Validacion")
            model_table = gr.Dataframe(value=_safe(model_metrics), interactive=False, wrap=True)
            model_plot = gr.Plot(value=metric_ranking(model_metrics))
            pred_plot = gr.Plot(value=observed_vs_pred(luis["predictions_rf"]))

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

        with gr.Tab("Interpretabilidad agronomica"):
            gr.Markdown(
                "Brix se interpreta junto a acumulacion termica/GDD. pH y acidez se revisan contra temperatura y "
                "respiracion/degradacion de acidos. Antocianinas y taninos se tratan como respuestas complejas a GDD, "
                "VPD, IFN, IFs, IFTT y variables productivas."
            )
            with gr.Row():
                gr.Plot(value=importance_bar(luis["shap"], "shap_mean_abs"))
                gr.Plot(value=importance_bar(luis["permutation"], "perm_importance_mean"))
            gr.Markdown("Metricas PySR/SR disponibles")
            gr.Dataframe(value=_safe(luis["metrics_pysr"]), interactive=False, wrap=True)

        with gr.Tab("Integracion conceptual"):
            gr.Markdown(
                """
### Cadena Obj.3

1. **Clima:** tabla maestra por fundo, estacion, fuente, gaps y calidad.
2. **Fenologia:** brotacion, ELP observado, DOY, t0 estimado y GDD acumulado.
3. **Madurez tecnica:** Brix, pH, acidez y peso de baya cuando existan.
4. **Madurez fenolica:** antocianinas, taninos y compuestos HPLC/UV-Vis cuando existan.
5. **Modelos:** RF y PySR/SR con CV5, LOFO, prediccion vs observado e interpretabilidad.
6. **Decision de cosecha:** aun no operacional; este dashboard sirve para QA cientifico-tecnico previo.
                """
            )
            gr.Dataframe(value=_safe(climate["master"]), interactive=False, wrap=True)

        with gr.Tab("Trazabilidad CORFO"):
            gr.Markdown(
                """
### Seguimiento del Plan de Trabajo (Obj. 3)

| Actividad | Nombre Corto | Estado | Bloqueo / Siguiente Paso |
|---|---|---|---|
| **Act. 16** | Predicciones climáticas | 🟡 PARCIAL | Funciona con clima histórico. Falta explorar caída de rendimiento usando forecast a 15 días. |
| **Act. 17** | Modelo fenológico ELP | 🟢 CERRADO (Data) | Dataset FULL_v1 listo. Falta modelo final de INRIA para evaluar generalización espacial. |
| **Act. 18/19** | Monitoreo madurez | 🟡 EN PROGRESO | Técnica 25/26 OK. Fenólica 25 OK, bloqueado esperando lab 2026. |
| **Act. 20** | Modelos madurez | 🟢 CERRADO (Técnica) | Pipeline `v2` demostró predictibilidad técnica. Modelos empaquetados. |
| **Act. 21** | Optimización multiobjetivo | 🔴 NO INICIADO | Requiere definición de pesos de la función objetivo por equipo de enología/dirección. |
| **Act. 22** | Validación enológica | ⚪ PENDIENTE | Depende de las fechas que sugiera Act. 21. |
                """
            )

        with gr.Tab("Export / INRIA"):
            gr.Markdown(
                """
### Estado de Envío a INRIA (Subcontrato)

**Último paquete oficial cerrado:**
`exports/inria/paquete_luis_inria_fenologia_ELP_OBJ3_CLEAN_2.zip`

**Estado actual:** 🟡 ENVIADO / ESPERANDO RESPUESTA

> **⚠️ ADVERTENCIA:**
> **NO** generar ni enviar nuevos datasets exploratorios a Luis hasta obtener confirmación y resultados del paquete vigente, para evitar desincronización de versiones.

**Datasets de reemplazo cuando se solicite:**
- Técnica: `madurez_tecnica_2025_2026_train_test_CANONICO_V5_INDICES_ORIGINALES.csv`
- Fenología: `consolidado_fenologia_ELP_MODELABLE_FULL_v1.csv`
                """
            )

        with gr.Tab("Cómo usar este repo"):
            gr.Markdown(
                """
### Guía de Supervivencia Obj. 3

1. **Datos Raw (`data/all_project/`):** **NO TOCAR.** Son réplicas de SharePoint en modo lectura.
2. **Pipeline Vigente:** Si necesitas re-correr modelos, usa `src/modeling/internal_baseline_v2/run_pipeline_v2.py`.
3. **Dashboard Maestro:** Ejecuta `python -m models.dashboard_obj3_integrado.app` para ver este mismo dashboard.
4. **Contexto Formal:** Lee `docs/objetivo_3_vendimia_5_0.md` para entender la arquitectura y exigencias del proyecto CORFO.
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
    app.queue().launch(server_name=args.server_name, server_port=args.server_port, share=args.share)


if __name__ == "__main__":
    main()
