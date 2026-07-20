from __future__ import annotations

import numpy as np
import pandas as pd

from .luis_config import BASE_COMBO_LABEL, COMBO_ORDER_HUMAN


def _apply_combo_order(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "combo_human" not in df.columns:
        return df
    order_map = {k: i for i, k in enumerate(COMBO_ORDER_HUMAN)}
    out = df.copy()
    out["_combo_order"] = out["combo_human"].map(order_map).fillna(10_000)
    return out.sort_values(["_combo_order", "combo_human"]).drop(columns=["_combo_order"])


def aggregate_metrics(metrics_df: pd.DataFrame) -> pd.DataFrame:
    if metrics_df.empty:
        return pd.DataFrame()
    g = (
        metrics_df.groupby(["target_key", "scheme", "predictors", "combo_human"], dropna=False)
        .agg(
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            r2_mean=("r2", "mean"),
            r2_std=("r2", "std"),
            n_eval=("split_id", "count"),
            n_fundos=("split_id", lambda s: s.astype(str).nunique()),
        )
        .reset_index()
    )
    g["rank_mae"] = g.groupby(["target_key", "scheme"])["mae_mean"].rank(method="dense", ascending=True)
    g["rank_r2"] = g.groupby(["target_key", "scheme"])["r2_mean"].rank(method="dense", ascending=False)
    g = _apply_combo_order(g)
    return g.sort_values(["target_key", "scheme"]).reset_index(drop=True)


def attach_deltas(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    out = summary_df.copy()
    out["delta_mae"] = np.nan
    out["mejora_mae_pct"] = np.nan
    out["delta_r2"] = np.nan

    for (target, scheme), idx in out.groupby(["target_key", "scheme"]).groups.items():
        sub = out.loc[idx]
        base = sub[sub["combo_human"] == BASE_COMBO_LABEL]
        if base.empty:
            base = sub[sub["predictors"].astype(str).str.contains("GDA") & sub["predictors"].astype(str).str.contains("VPD")].head(1)
        if base.empty:
            continue
        b_mae = float(base["mae_mean"].iloc[0])
        b_r2 = float(base["r2_mean"].iloc[0])
        out.loc[idx, "delta_mae"] = out.loc[idx, "mae_mean"] - b_mae
        out.loc[idx, "mejora_mae_pct"] = (b_mae - out.loc[idx, "mae_mean"]) / b_mae * 100.0
        out.loc[idx, "delta_r2"] = out.loc[idx, "r2_mean"] - b_r2

    return out


def lofo_fundo_table(metrics_df: pd.DataFrame) -> pd.DataFrame:
    if metrics_df.empty:
        return pd.DataFrame()
    d = metrics_df[metrics_df["scheme"] == "lofo_mixed"].copy()
    if d.empty:
        return pd.DataFrame()
    g = (
        d.groupby(["target_key", "predictors", "combo_human", "split_id"], dropna=False)
        .agg(mae=("mae", "mean"), r2=("r2", "mean"), n_eval=("mae", "count"))
        .reset_index()
        .rename(columns={"split_id": "fundo_testeado"})
    )
    g = _apply_combo_order(g)
    return g.sort_values(["target_key", "combo_human", "mae"]).reset_index(drop=True)


def executive_summary(
    target: str,
    scheme: str,
    summary_df: pd.DataFrame,
    original_df: pd.DataFrame,
) -> dict:
    if summary_df.empty or not {"target_key", "scheme"}.issubset(summary_df.columns):
        return {
            "best_mae": "N/A",
            "best_r2": "N/A",
            "n_combos": 0,
            "n_obs": int(len(original_df)) if len(original_df) else 0,
            "n_variedades": int(original_df["variedad"].nunique()) if "variedad" in original_df.columns else 0,
            "n_fundos": int(original_df["fundo"].nunique()) if "fundo" in original_df.columns else 0,
        }

    subset = summary_df[(summary_df["target_key"] == target) & (summary_df["scheme"] == scheme)]
    if subset.empty:
        return {
            "best_mae": "N/A",
            "best_r2": "N/A",
            "n_combos": 0,
            "n_obs": int(len(original_df)) if len(original_df) else 0,
            "n_variedades": int(original_df["variedad"].nunique()) if "variedad" in original_df.columns else 0,
            "n_fundos": int(original_df["fundo"].nunique()) if "fundo" in original_df.columns else 0,
        }

    best_mae_row = subset.sort_values("mae_mean", ascending=True).iloc[0]
    best_r2_row = subset.sort_values("r2_mean", ascending=False).iloc[0]

    return {
        "best_mae": f"{best_mae_row['combo_human']} (MAE={best_mae_row['mae_mean']:.3f})",
        "best_r2": f"{best_r2_row['combo_human']} (R2={best_r2_row['r2_mean']:.3f})",
        "n_combos": int(subset["predictors"].nunique()),
        "n_obs": int(len(original_df)) if len(original_df) else 0,
        "n_variedades": int(original_df["variedad"].nunique()) if "variedad" in original_df.columns else 0,
        "n_fundos": int(original_df["fundo"].nunique()) if "fundo" in original_df.columns else 0,
        "delta_mae_best": float(best_mae_row.get("delta_mae", np.nan)),
        "mejora_mae_pct_best": float(best_mae_row.get("mejora_mae_pct", np.nan)),
        "delta_r2_best": float(best_mae_row.get("delta_r2", np.nan)),
    }


def combine_shap_mae(shap_df: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    if shap_df.empty or metrics_df.empty:
        return pd.DataFrame()
    keys = ["target_key", "scheme", "subset", "split_id", "method", "predictors", "seed"]
    m = metrics_df[keys + ["mae"]].copy()
    j = shap_df.merge(m, on=keys, how="left")
    eps = 1e-12
    j["shap_over_mae"] = np.where(j["mae"].abs() > eps, j["shap_mean_abs"] / j["mae"], np.nan)
    j["mae_over_shap"] = np.where(j["shap_mean_abs"].abs() > eps, j["mae"] / j["shap_mean_abs"], np.nan)
    return j
