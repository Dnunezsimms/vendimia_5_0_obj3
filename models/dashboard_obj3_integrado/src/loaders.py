from __future__ import annotations

import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import (
    CLIMATE_COVERAGE_DIR,
    CLIMATE_MASTER_PATH,
    GDD_DIR,
    LUIS_DASHBOARD_DIR,
    MATURITY_RAW_DIR,
    PHENOLOGY_PREPARED_DIR,
    PHENOLOGY_RAW_DIR,
)


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def read_table(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        if path.suffix.lower() == ".csv":
            for encoding in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
                try:
                    return pd.read_csv(path, encoding=encoding, **kwargs)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(path, **kwargs)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path, **kwargs)
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path, **kwargs)
    except Exception as exc:
        logging.warning("No se pudo leer %s: %s", path, exc)
    return pd.DataFrame()


def read_excel_workbook(path: Path, max_sheets: int | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    try:
        excel = pd.ExcelFile(path)
        for sheet in excel.sheet_names[: max_sheets or len(excel.sheet_names)]:
            df = pd.read_excel(path, sheet_name=sheet)
            if df.empty:
                continue
            df["source_file"] = str(path)
            df["sheet"] = sheet
            frames.append(df)
    except Exception as exc:
        logging.warning("No se pudo leer workbook %s: %s", path, exc)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_csv(name: str) -> pd.DataFrame:
    return read_table(CLIMATE_COVERAGE_DIR / name)


def freeze_climate_master() -> pd.DataFrame:
    resumen = load_csv("resumen_fundos.csv")
    asignacion = load_csv("asignacion_recomendada.csv")
    gaps = load_csv("gaps_por_fundo.csv")
    if resumen.empty:
        return pd.DataFrame()
    cols = [
        "fundo_normalizado",
        "estacion_recomendada",
        "red",
        "station_id",
        "cobertura_%",
        "calidad_global",
        "distancia_km",
        "estado",
        "comentario_tecnico",
    ]
    master = resumen[[c for c in cols if c in resumen.columns]].copy()
    master["temporada"] = "2025_2026"
    master["periodo_inicio"] = "2025-05-01"
    master["periodo_fin"] = "2026-05-31"
    master["fuente_tabla"] = "reports/climate/coverage/resumen_fundos.csv"
    if not asignacion.empty:
        keep = [
            "fundo_normalizado",
            "archivo",
            "criterio_asignacion",
            "origen_asignacion",
            "score_confianza_0_100",
            "requiere_validacion_manual",
        ]
        master = master.merge(asignacion[[c for c in keep if c in asignacion.columns]], on="fundo_normalizado", how="left")
    if not gaps.empty:
        g = gaps.groupby("fundo_normalizado", dropna=False).agg(
            n_gaps=("gap_inicio", "count"),
            gaps=("gap_inicio", lambda s: "; ".join(
                f"{a} a {b}" for a, b in zip(s.astype(str), gaps.loc[s.index, "gap_fin"].astype(str))
            )),
            gap_bloqueante=("bloqueante_dashboard_exploratorio", lambda s: "SI" if (s.astype(str).str.upper() == "SI").any() else "NO"),
        ).reset_index()
        master = master.merge(g, on="fundo_normalizado", how="left")
    CLIMATE_MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(CLIMATE_MASTER_PATH, index=False)
    logging.info("Tabla maestra climatica congelada en %s", CLIMATE_MASTER_PATH)
    return master


def load_climate_bundle() -> dict[str, pd.DataFrame]:
    master = freeze_climate_master()
    return {
        "master": master,
        "resumen": load_csv("resumen_fundos.csv"),
        "asignacion": load_csv("asignacion_recomendada.csv"),
        "gaps": load_csv("gaps_por_fundo.csv"),
        "faltantes": load_csv("faltantes.csv"),
        "equivalencias": load_csv("equivalencias_estaciones.csv"),
        "candidatos": load_csv("candidatos_secundarios.csv"),
    }


def load_gdd_outputs() -> dict[str, pd.DataFrame]:
    resumen_t0 = read_table(GDD_DIR / "method_pipeline_varietal_evaluation_by_fundo.csv")
    if not resumen_t0.empty:
        if "GDD Acumulado" in resumen_t0.columns:
            resumen_t0["GDD_alcanzado"] = resumen_t0["GDD Acumulado"]
        if "gdd_variedad_final" in resumen_t0.columns:
            resumen_t0["Error GDD"] = resumen_t0["GDD Acumulado"] - resumen_t0["gdd_variedad_final"]
        resumen_t0 = resumen_t0[[
            "Fundo", "Variedad", "t0 Cabernet usado", "Fecha Brotacion", 
            "GDD Acumulado", "gdd_variedad_base_crudo", "gdd_variedad_final", 
            "Error GDD", "metodo_gdd_variedad_final", "advertencia_gdd_varietal"
        ]]

    resultados_t0 = read_table(GDD_DIR / "method_pipeline_cs_t0_operativo_by_fundo.csv")
    if not resultados_t0.empty and "doy_t0_operativo" in resultados_t0.columns:
        resultados_t0["doy_brotacion"] = resultados_t0["doy_t0_operativo"]

    try:
        diagnostico_cs_reg = pd.read_excel(GDD_DIR / "method_pipeline_summary.xlsx", sheet_name="diagnostico_cs_reg")
    except Exception as exc:
        logging.warning("No se pudo leer diagnostico_cs_reg: %s", exc)
        diagnostico_cs_reg = pd.DataFrame()
        
    try:
        chill_dynamic = read_table(GDD_DIR / "chill_dynamic_diagnostics_by_fundo_temporada.csv")
    except Exception as exc:
        logging.warning("No se pudo leer chill_dynamic: %s", exc)
        chill_dynamic = pd.DataFrame()

    return {
        "resumen_t0": resumen_t0,
        "resultados_t0": resultados_t0,
        "diagnostico_cs_reg": diagnostico_cs_reg,
        "chill_dynamic": chill_dynamic,
        "inferencia_t0": read_table(GDD_DIR / "inferencia_t0_multisitio.csv"),
        "inferencia_t0_spatial": read_table(GDD_DIR / "inferencia_t0_multisitio_spatial.csv"),
        "qa_brotacion": read_table(GDD_DIR / "qa_brotacion.csv"),
        "qa_file_audit": read_table(GDD_DIR / "qa_file_audit.csv"),
    }


def load_phenology_tables() -> dict[str, pd.DataFrame]:
    raw_files = list(PHENOLOGY_RAW_DIR.glob("*.xlsx")) + list(PHENOLOGY_RAW_DIR.glob("*.csv"))
    raw_frames = []
    for path in raw_files:
        df = read_excel_workbook(path) if path.suffix.lower() in {".xlsx", ".xls"} else read_table(path)
        if not df.empty:
            df["source_file"] = str(path)
            raw_frames.append(df)
    prepared_files = list(PHENOLOGY_PREPARED_DIR.glob("*.xlsx"))
    prepared = pd.DataFrame(
        [
            {
                "source_file": str(path),
                "fundo_archivo": path.stem.split("_")[0],
                "variedad_archivo": "_".join(path.stem.split("_")[1:-2]),
                "temporada_archivo": "_".join(path.stem.split("_")[-2:]),
            }
            for path in prepared_files
        ]
    )
    return {
        "raw": pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame(),
        "prepared_manifest": prepared,
    }


def _load_many_csv(files: Iterable[Path]) -> pd.DataFrame:
    frames = []
    for path in files:
        df = read_table(path)
        if df.empty:
            continue
        df["source_file"] = str(path)
        meta = infer_model_metadata(path)
        for key, value in meta.items():
            if key not in df.columns or df[key].isna().all():
                df[key] = value
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def infer_model_metadata(path: Path) -> dict[str, str]:
    parts = list(path.parts)
    meta = {"target_key": "", "scheme": "", "predictors": "", "model_family": ""}
    if "outputs" not in parts:
        return meta
    i = parts.index("outputs")
    if len(parts) > i + 1:
        meta["target_key"] = parts[i + 1]
    if len(parts) > i + 2:
        meta["scheme"] = parts[i + 2]
    pred = next((p for p in parts if p.startswith("predictors__")), "")
    if pred:
        meta["predictors"] = pred.replace("predictors__", "", 1)
    if "rf" in parts:
        meta["model_family"] = "RF"
    elif "pysr" in parts:
        meta["model_family"] = "PySR/SR"
    return meta


def load_maturity_tables() -> dict[str, pd.DataFrame]:
    tintas = read_table(MATURITY_RAW_DIR / "consolidado_madurez_tintas.csv")
    raw_xlsx = []
    for path in MATURITY_RAW_DIR.glob("*.xlsx"):
        df = read_excel_workbook(path)
        if not df.empty:
            raw_xlsx.append(df)
    raw_current = pd.concat(raw_xlsx, ignore_index=True) if raw_xlsx else pd.DataFrame()
    combined = pd.concat([tintas, raw_current], ignore_index=True, sort=False)
    return {
        "tintas_historicas": tintas,
        "raw_2026": raw_current,
        "tecnica_canonica": prepare_maturity_technical(combined),
    }


def coalesce_by_names(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    result = pd.Series([pd.NA] * len(df), index=df.index, dtype="object")
    normalized = {normalize_text(c): c for c in df.columns}
    for cand in candidates:
        col = normalized.get(normalize_text(cand))
        if col is None:
            continue
        result = result.combine_first(df[col])
    return result


def coalesce_by_patterns(df: pd.DataFrame, patterns: list[str], exclude: list[str] | None = None) -> pd.Series:
    exclude = exclude or []
    result = pd.Series([pd.NA] * len(df), index=df.index, dtype="object")
    for col in df.columns:
        n = normalize_text(col)
        if any(x in n for x in exclude):
            continue
        if any(p in n for p in patterns):
            result = result.combine_first(df[col])
    return result


def infer_temporada(fecha: pd.Series) -> pd.Series:
    dates = pd.to_datetime(fecha, errors="coerce", dayfirst=True)
    start_year = dates.dt.year.where(dates.dt.month >= 7, dates.dt.year - 1)
    end_year = start_year + 1
    return start_year.astype("Int64").astype(str) + "_" + end_year.astype("Int64").astype(str)


def prepare_maturity_technical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=df.index)
    out["fecha"] = coalesce_by_names(df, ["fecha", "Fecha", "Fecha muestreo"])
    out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce", dayfirst=True)
    out["temporada"] = infer_temporada(out["fecha"])
    out["fundo"] = coalesce_by_names(df, ["fundo", "Fundo", "campo", "Campo"]).astype(str).str.strip()
    out["variedad"] = coalesce_by_names(df, ["variedad", "Variedad"]).astype(str).str.strip()
    out["cuartel"] = coalesce_by_names(df, ["cuartel", "Cuartel"]).astype(str).str.strip()
    out["muestra"] = coalesce_by_names(
        df,
        ["codigo_original_muestra", "Id. original muestra", "codigo_corto", "N° muestra", "N muestra"],
    ).astype(str).str.strip()
    out["brix"] = pd.to_numeric(coalesce_by_names(df, ["brix", "Brix"]), errors="coerce")
    out["pH"] = pd.to_numeric(coalesce_by_names(df, ["pH", "ph"]), errors="coerce")
    out["acidez_sulfurica"] = pd.to_numeric(coalesce_by_names(df, ["acidez_sulfurica", "Acidez Sulfúrica", "Acidez Sulfurica"]), errors="coerce")
    out["acidez_tartarica"] = pd.to_numeric(coalesce_by_names(df, ["acidez_tartarica", "Acidez Tartárica", "Acidez Tartarica"]), errors="coerce")
    out["peso_baya"] = pd.to_numeric(coalesce_by_names(df, ["peso_baya", "Peso baya", "Peso Baya"]), errors="coerce")
    out["azucar_real_baya_g"] = pd.to_numeric(coalesce_by_names(df, ["azucar_real_baya_g", "gramos_de_azucar_baya"]), errors="coerce")
    out["source_file"] = coalesce_by_names(df, ["source_file"]).astype(str)
    out = out.replace({"<NA>": pd.NA, "nan": pd.NA, "None": pd.NA, "": pd.NA})
    useful = ["brix", "pH", "acidez_sulfurica", "acidez_tartarica", "peso_baya", "azucar_real_baya_g"]
    out = out.dropna(subset=["fecha", "fundo", "variedad"], how="any")
    out = out.dropna(subset=useful, how="all")
    return out.reset_index(drop=True)


def _iter_files(base_dir: Path, suffixes: set[str]) -> list[Path]:
    files = []
    if not base_dir.exists():
        return files
    for root, _dirs, names in os.walk(base_dir):
        for name in names:
            path = Path(root) / name
            if path.suffix.lower() in suffixes:
                files.append(path)
    return files


def load_luis_artifacts() -> dict[str, pd.DataFrame]:
    outputs = LUIS_DASHBOARD_DIR / "outputs"
    metrics = _load_many_csv(outputs.glob("*/*/predictors__*/rf/*/metrics_per_split.csv"))
    pysr_metrics = _load_many_csv(outputs.glob("*/*/predictors__*/pysr/*/metrics_per_split.csv"))
    predictions = _load_many_csv(outputs.glob("*/*/predictors__*/rf/*/predictions.csv"))
    shap = _load_many_csv(outputs.glob("*/*/predictors__*/rf/*/shap_importance.csv"))
    perm = _load_many_csv(outputs.glob("*/*/predictors__*/rf/*/permutation_importance.csv"))
    original = _load_many_csv((LUIS_DASHBOARD_DIR / "data" / "prepared").glob("tintas_*.csv"))
    manifest = read_table(LUIS_DASHBOARD_DIR / "data" / "prepared" / "manifest.csv")
    return {
        "metrics_rf": metrics,
        "metrics_pysr": pysr_metrics,
        "predictions_rf": predictions,
        "shap": shap,
        "permutation": perm,
        "original_tintas": original,
        "manifest": manifest,
    }


def audit_artifacts() -> pd.DataFrame:
    rows = []
    checks = [
        ("clima", CLIMATE_COVERAGE_DIR, ["resumen_fundos.csv", "asignacion_recomendada.csv", "gaps_por_fundo.csv"]),
        ("fenologia_gdd", GDD_DIR, ["method_pipeline_varietal_evaluation_by_fundo.csv", "method_pipeline_cs_t0_operativo_by_fundo.csv"]),
        ("dashboard_luis", LUIS_DASHBOARD_DIR, ["app.py", "data/prepared/manifest.csv"]),
        ("madurez_raw", MATURITY_RAW_DIR, ["muestras_tintas_2026.xlsx", "muestras_blancas_2026.xlsx", "muestras_fenoles_2026.xlsx"]),
    ]
    for domain, base, rels in checks:
        for rel in rels:
            path = base / rel
            rows.append(
                {
                    "dominio": domain,
                    "archivo": str(path),
                    "existe": path.exists(),
                    "bytes": path.stat().st_size if path.exists() else 0,
                    "modificado": path.stat().st_mtime if path.exists() else None,
                }
            )
    output_counts = {
        "rf_metrics": len(list((LUIS_DASHBOARD_DIR / "outputs").glob("*/*/predictors__*/rf/*/metrics_per_split.csv"))),
        "pysr_metrics": len(list((LUIS_DASHBOARD_DIR / "outputs").glob("*/*/predictors__*/pysr/*/metrics_per_split.csv"))),
        "rf_predictions": len(list((LUIS_DASHBOARD_DIR / "outputs").glob("*/*/predictors__*/rf/*/predictions.csv"))),
        "shap": len(list((LUIS_DASHBOARD_DIR / "outputs").glob("*/*/predictors__*/rf/*/shap_importance.csv"))),
        "permutation": len(list((LUIS_DASHBOARD_DIR / "outputs").glob("*/*/predictors__*/rf/*/permutation_importance.csv"))),
    }
    for key, count in output_counts.items():
        rows.append({"dominio": "modelos_luis", "archivo": key, "existe": count > 0, "bytes": count, "modificado": None})
    return pd.DataFrame(rows)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def find_columns(df: pd.DataFrame, patterns: list[str]) -> list[str]:
    cols = []
    for col in df.columns:
        n = normalize_text(col)
        if any(p in n for p in patterns):
            cols.append(col)
    return cols


def load_state() -> dict[str, object]:
    climate = load_climate_bundle()
    gdd = load_gdd_outputs()
    phenology = load_phenology_tables()
    maturity = load_maturity_tables()
    luis = load_luis_artifacts()
    audit = audit_artifacts()
    return {
        "climate": climate,
        "gdd": gdd,
        "phenology": phenology,
        "maturity": maturity,
        "luis": luis,
        "audit": audit,
    }
