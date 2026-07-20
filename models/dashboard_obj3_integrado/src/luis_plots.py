from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .luis_config import COMBO_ORDER_HUMAN
from .luis_data_loader import detect_target_col


def empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper", font=dict(size=16))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(template="plotly_white", height=500)
    return fig


def box_target_by_variety(df: pd.DataFrame, target_col: str) -> go.Figure:
    if df.empty or target_col not in df.columns or "variedad" not in df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    return px.box(df, x="variedad", y=target_col, points="all", color="variedad", template="plotly_white")


def timeseries_target(df: pd.DataFrame, target_col: str) -> go.Figure:
    if df.empty or target_col not in df.columns or "fecha" not in df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    color_col = "fundo" if "fundo" in df.columns else None
    symbol_col = "variedad" if "variedad" in df.columns else None
    fig = px.scatter(df.sort_values("fecha"), x="fecha", y=target_col, color=color_col, symbol=symbol_col, template="plotly_white")
    if color_col:
        for fundo, g in df.sort_values("fecha").groupby(color_col):
            fig.add_trace(go.Scatter(x=g["fecha"], y=g[target_col], mode="lines", name=f"{fundo} (line)", showlegend=False))
    return fig


def box_target_by_fundo(df: pd.DataFrame, target_col: str) -> go.Figure:
    if df.empty or target_col not in df.columns or "fundo" not in df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    return px.box(df, x="fundo", y=target_col, points="all", color="fundo", template="plotly_white")


def predictor_timeseries(df: pd.DataFrame, predictor: str) -> go.Figure:
    if df.empty or predictor not in df.columns or "fecha" not in df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    color_col = "fundo" if "fundo" in df.columns else None
    return px.line(df.sort_values("fecha"), x="fecha", y=predictor, color=color_col, template="plotly_white")


def performance_scatter(summary_df: pd.DataFrame) -> go.Figure:
    if summary_df.empty:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    return px.scatter(summary_df, x="mae_mean", y="r2_mean", color="scheme", hover_data=["combo_human", "target_key"], template="plotly_white")


def lofo_ranking_bar(lofo_df: pd.DataFrame) -> go.Figure:
    if lofo_df.empty:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    g = lofo_df.groupby("fundo_testeado", as_index=False)["mae"].mean().sort_values("mae", ascending=False)
    return px.bar(g, x="fundo_testeado", y="mae", template="plotly_white", title="Ranking de fundos por MAE (LOFO)")


def observed_vs_pred(pred_df: pd.DataFrame) -> go.Figure:
    if pred_df.empty:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    y_col = detect_target_col(pred_df)
    if not y_col or "prediction" not in pred_df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    c = "fundo" if "fundo" in pred_df.columns else ("variedad" if "variedad" in pred_df.columns else None)
    fig = px.scatter(pred_df, x=y_col, y="prediction", color=c, template="plotly_white")
    vmin = min(pred_df[y_col].min(), pred_df["prediction"].min())
    vmax = max(pred_df[y_col].max(), pred_df["prediction"].max())
    fig.add_trace(go.Scatter(x=[vmin, vmax], y=[vmin, vmax], mode="lines", name="y=x"))
    return fig


def residual_plots(pred_df: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    if pred_df.empty:
        em = empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
        return em, em
    y_col = detect_target_col(pred_df)
    if not y_col or "prediction" not in pred_df.columns:
        em = empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
        return em, em
    d = pred_df.copy()
    d["residuo"] = d[y_col] - d["prediction"]
    h = px.histogram(d, x="residuo", nbins=30, template="plotly_white")
    s = px.scatter(d, x="prediction", y="residuo", color=("fundo" if "fundo" in d.columns else None), template="plotly_white")
    return h, s


def importance_bar(df: pd.DataFrame, value_col: str, title: str) -> go.Figure:
    if df.empty or value_col not in df.columns or "feature" not in df.columns:
        return empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
    g = (
        df.groupby("feature", as_index=False)
        .agg(mean_value=(value_col, "mean"), std_value=(value_col, "std"))
        .sort_values("mean_value", ascending=True)
    )
    fig = px.bar(g, x="mean_value", y="feature", orientation="h", error_x="std_value", template="plotly_white", title=title)
    return fig


def combo_compare_bars(df: pd.DataFrame) -> tuple[go.Figure, go.Figure, go.Figure]:
    if df.empty:
        em = empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
        return em, em, em
    d = df.copy()
    present = set(d["combo_human"].astype(str).tolist())
    ordered = [x for x in COMBO_ORDER_HUMAN if x in present]
    if not ordered:
        em = empty_figure("No se encontró información suficiente para esta visualización con los filtros actuales.")
        return em, em, em
    d = d[d["combo_human"].isin(ordered)].copy()
    category_orders = {"combo_human": ordered}
    a = px.bar(d, x="combo_human", y="mae_mean", category_orders=category_orders, template="plotly_white", title="MAE medio por combinación")
    b = px.bar(d, x="combo_human", y="r2_mean", category_orders=category_orders, template="plotly_white", title="R2 medio por combinación")
    c = px.bar(d, x="combo_human", y="mejora_mae_pct", category_orders=category_orders, template="plotly_white", title="Mejora MAE (%) vs base")
    for f in (a, b, c):
        f.update_xaxes(tickangle=-35, categoryorder="array", categoryarray=ordered)
    return a, b, c
