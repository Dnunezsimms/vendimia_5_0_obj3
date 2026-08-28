from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .luis_config import BASE_DIR, COMBO_ORDER_HUMAN
from .luis_utils import first_existing, human_combo, normalize_name, safe_read_table, to_datetime_if_exists


@dataclass
class ArtifactRow:
    path: str
    ext: str
    kind: str
    target: str
    scheme: str
    combo: str


def _infer_from_path(path: Path) -> tuple[str, str, str, str]:
    s = str(path)
    parts = path.parts
    target = ""
    scheme = ""
    combo = ""
    kind = "other"

    if "outputs" in parts:
        i = parts.index("outputs")
        if len(parts) > i + 1:
            target = parts[i + 1]
        if len(parts) > i + 2:
            scheme = parts[i + 2]

        combo_part = next((p for p in parts if p.startswith("predictors__")), "")
        if combo_part:
            combo = combo_part.replace("predictors__", "", 1)

        low = s.lower()
        if low.endswith("metrics_per_split.csv"):
            kind = "metrics"
        elif low.endswith("predictions.csv"):
            kind = "predictions"
        elif low.endswith("shap_importance.csv"):
            kind = "shap"
        elif low.endswith("permutation_importance.csv"):
            kind = "permutation"

    if "data" in parts and "prepared" in parts and path.name.startswith("tintas_"):
        kind = "original_data"
        target = path.stem.replace("tintas_", "")

    if any(x in s for x in ["monitoring", "plots"]):
        if path.suffix.lower() in {".png", ".pdf", ".html"}:
            kind = "plot"

    return kind, target, scheme, combo


def _data_dir(base_dir: Path) -> Path:
    return base_dir / "data" / "prepared"


def _empty_artifacts() -> pd.DataFrame:
    return pd.DataFrame(columns=["path", "ext", "kind", "target", "scheme", "combo"])


def _iter_files(base_dir: Path):
    if not base_dir.exists():
        logging.warning("Artifacts directory does not exist: %s", base_dir)
        return
    def _onerror(error):
        logging.debug("Skipping unreadable path during artifact scan: %s", error)

    for root, _dirs, files in os.walk(base_dir, onerror=_onerror):
        root_path = Path(root)
        for name in files:
            yield root_path / name


def discover_artifacts(base_dir: Path = BASE_DIR) -> pd.DataFrame:
    exts = {".csv", ".tsv", ".parquet", ".json", ".pkl", ".png", ".pdf", ".html"}
    rows: list[dict[str, str]] = []
    for p in _iter_files(base_dir):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        kind, target, scheme, combo = _infer_from_path(p)
        rows.append(
            {
                "path": str(p),
                "ext": p.suffix.lower(),
                "kind": str(kind),
                "target": str(target),
                "scheme": str(scheme),
                "combo": str(combo),
            }
        )
    if not rows:
        return _empty_artifacts()
    logging.info("Discovered %s artifact files under %s", len(rows), base_dir)
    return pd.DataFrame.from_records(rows, columns=["path", "ext", "kind", "target", "scheme", "combo"])


def load_metrics(base_dir: Path = BASE_DIR) -> pd.DataFrame:
    try:
        files = list(base_dir.glob("outputs/*/*/predictors__*/rf/*/metrics_per_split.csv"))
    except OSError as e:
        logging.warning("No se pudieron buscar archivos metrics (ruta muy larga?): %s", e)
        files = []
    logging.info("Found %s metrics_per_split.csv files under %s", len(files), base_dir / "outputs")
    dfs = []
    for f in files:
        try:
            d = safe_read_table(f)
            d["file_path"] = str(f)
            d["output_tag"] = f.parent.name
            d["combo_human"] = d.get("predictors", "").astype(str).map(human_combo)
            dfs.append(d)
        except Exception as e:
            logging.warning("Could not read metrics %s: %s", f, e)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_predictions(base_dir: Path = BASE_DIR) -> pd.DataFrame:
    try:
        files = list(base_dir.glob("outputs/*/*/predictors__*/rf/*/predictions.csv"))
    except OSError as e:
        logging.warning("No se pudieron buscar archivos predictions (ruta muy larga?): %s", e)
        files = []
    logging.info("Found %s predictions.csv files under %s", len(files), base_dir / "outputs")
    dfs = []
    for f in files:
        try:
            d = safe_read_table(f)
            d["file_path"] = str(f)
            d["output_tag"] = f.parent.name
            d = to_datetime_if_exists(d, first_existing(d.columns, ["fecha", "date"]))
            dfs.append(d)
        except Exception as e:
            logging.warning("Could not read predictions %s: %s", f, e)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_importance(base_dir: Path = BASE_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        shap_files = list(base_dir.glob("outputs/*/*/predictors__*/rf/*/shap_importance.csv"))
        perm_files = list(base_dir.glob("outputs/*/*/predictors__*/rf/*/permutation_importance.csv"))
    except OSError as e:
        logging.warning("No se pudieron buscar archivos importance (ruta muy larga?): %s", e)
        shap_files, perm_files = [], []
    logging.info(
        "Found %s permutation_importance.csv and %s shap_importance.csv files under %s",
        len(perm_files),
        len(shap_files),
        base_dir / "outputs",
    )

    def load_many(files: list[Path]) -> pd.DataFrame:
        out = []
        for f in files:
            try:
                d = safe_read_table(f)
                d["file_path"] = str(f)
                d["output_tag"] = f.parent.name
                out.append(d)
            except Exception as e:
                logging.warning("Could not read importance %s: %s", f, e)
        return pd.concat(out, ignore_index=True) if out else pd.DataFrame()

    return load_many(perm_files), load_many(shap_files)


def load_original_data(target_key: str, base_dir: Path = BASE_DIR) -> pd.DataFrame:
    if not target_key:
        return pd.DataFrame()
    p = _data_dir(base_dir) / f"tintas_{target_key}.csv"
    if not p.exists():
        logging.warning("Original data file not found for target '%s': %s", target_key, p)
        return pd.DataFrame()
    df = safe_read_table(p)
    date_col = first_existing(df.columns, ["fecha", "date"])
    df = to_datetime_if_exists(df, date_col)
    return df


def available_targets(metrics_df: pd.DataFrame, base_dir: Path = BASE_DIR) -> list[str]:
    t_from_metrics = sorted(metrics_df.get("target_key", pd.Series([], dtype=str)).dropna().astype(str).unique().tolist())
    data_dir = _data_dir(base_dir)
    t_from_data = sorted([p.stem.replace("tintas_", "") for p in data_dir.glob("tintas_*.csv")]) if data_dir.exists() else []
    targets = sorted(set(t_from_metrics + t_from_data))
    logging.info(
        "Available targets: %s from metrics, %s from %s, %s total",
        len(t_from_metrics),
        len(t_from_data),
        data_dir,
        len(targets),
    )
    return targets


def available_schemes(metrics_df: pd.DataFrame, target: str) -> list[str]:
    if metrics_df.empty or not target or "target_key" not in metrics_df.columns:
        return []
    d = metrics_df[metrics_df["target_key"] == target]
    return sorted(d.get("scheme", pd.Series([], dtype=str)).dropna().astype(str).unique().tolist())


def available_combos(metrics_df: pd.DataFrame, target: str, scheme: str) -> pd.DataFrame:
    if metrics_df.empty or not target or not scheme:
        return pd.DataFrame(columns=["predictors", "combo_human"])
    d = metrics_df[(metrics_df["target_key"] == target) & (metrics_df["scheme"] == scheme)]
    if d.empty:
        return pd.DataFrame(columns=["predictors", "combo_human"])
    c = d[["predictors", "combo_human"]].drop_duplicates()
    present = set(c["combo_human"].astype(str).tolist())
    ordered = [x for x in COMBO_ORDER_HUMAN if x in present]
    rank = {k: i for i, k in enumerate(ordered)}
    c = c.copy()
    c["_ord"] = c["combo_human"].map(rank).fillna(len(COMBO_ORDER_HUMAN) + 1)
    c = c.sort_values(["_ord", "combo_human"]).drop(columns=["_ord"])
    return c.reset_index(drop=True)


def detect_target_col(pred_df: pd.DataFrame) -> str | None:
    candidates = [
        "y_true",
        "observed",
        "real",
        "valor_real",
        "antocianinas(mg/baya)",
        "taninos(mg/baya)",
    ]
    col = first_existing(pred_df.columns, candidates)
    if col:
        return col
    # fallback: first numeric column not known metadata/prediction
    excluded = {normalize_name(x) for x in ["prediction", "seed", "n_predictors", "split_id"]}
    for c in pred_df.columns:
        if normalize_name(c) in excluded:
            continue
        if pd.api.types.is_numeric_dtype(pred_df[c]):
            return c
    return None


def detect_predictor_columns(original_df: pd.DataFrame, target_col: str | None) -> list[str]:
    meta = {normalize_name(x) for x in ["fecha", "variedad", "fundo", "codigo_original_muestra", "codigo_corto", "muestreo"]}
    out = []
    for c in original_df.columns:
        if target_col and c == target_col:
            continue
        if normalize_name(c) in meta:
            continue
        if pd.api.types.is_numeric_dtype(original_df[c]):
            out.append(c)
    return out


def load_experiment_config(base_dir: Path = BASE_DIR) -> dict:
    cfg_path = base_dir / "config" / "experiment_config.json"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)
