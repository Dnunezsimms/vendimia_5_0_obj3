from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def strip_accents(text: str) -> str:
    if text is None:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(c))


def normalize_name(text: str) -> str:
    s = strip_accents(str(text)).lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def human_combo(combo: str) -> str:
    if combo is None:
        return ""
    tokens = str(combo).split("|")
    pretty = []
    rep = {
        "VPD_medio_acum": "VPD",
        "IFTT_acum": "IFTT",
        "IFN_acum": "IFN",
        "IFs_acum": "IFs",
        "Hef_acum": "Hef",
        "HEP_acum": "HEP",
        "IE_acum": "IE",
        "STa_acum": "STa",
        "azucar_real_baya_g": "azucar",
        "gramos_de_azucar_baya": "azucar",
        "peso_baya": "peso",
        "rendimientoton_ha": "rendimiento",
        "rendimiento(ton/ha)": "rendimiento",
    }
    for t in tokens:
        pretty.append(rep.get(t, t))
    return " + ".join(pretty)


def safe_read_table(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    readers = []
    if ext == ".csv":
        readers = [lambda p: pd.read_csv(p), lambda p: pd.read_csv(p, sep=";"), lambda p: pd.read_csv(p, encoding="latin-1")]
    elif ext == ".tsv":
        readers = [lambda p: pd.read_csv(p, sep="\t")]
    elif ext == ".parquet":
        readers = [pd.read_parquet]
    elif ext == ".json":
        readers = [pd.read_json]
    else:
        raise ValueError(f"Unsupported format: {path}")

    last_err = None
    for r in readers:
        try:
            return r(path)
        except Exception as e:  # pragma: no cover
            last_err = e
    raise RuntimeError(f"Could not read {path}: {last_err}")


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cols_norm = {normalize_name(c): c for c in columns}
    for cand in candidates:
        n = normalize_name(cand)
        if n in cols_norm:
            return cols_norm[n]
    return None


def to_datetime_if_exists(df: pd.DataFrame, col: str | None) -> pd.DataFrame:
    if col and col in df.columns:
        df = df.copy()
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
