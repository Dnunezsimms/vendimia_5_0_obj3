from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .loaders import find_columns, normalize_text


def empty_figure(message: str = "Sin datos disponibles") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    fig.update_layout(height=360, template="plotly_white")
    return fig


def climate_status_bar(resumen: pd.DataFrame) -> go.Figure:
    if resumen.empty or "estado" not in resumen.columns:
        return empty_figure("Sin resumen climatico")
    d = resumen.groupby("estado", dropna=False).size().reset_index(name="fundos")
    fig = px.bar(d, x="estado", y="fundos", color="estado", text="fundos", template="plotly_white")
    fig.update_layout(height=320, showlegend=False, xaxis_title="", yaxis_title="Fundos")
    return fig


def coverage_bar(resumen: pd.DataFrame) -> go.Figure:
    if resumen.empty or "cobertura_%" not in resumen.columns:
        return empty_figure("Sin cobertura climatica")
    d = resumen.copy()
    d["cobertura_%"] = pd.to_numeric(d["cobertura_%"], errors="coerce")
    d = d.sort_values("cobertura_%")
    fig = px.bar(
        d,
        x="cobertura_%",
        y="fundo_normalizado",
        color="estado",
        orientation="h",
        template="plotly_white",
        hover_data=["estacion_recomendada", "red", "station_id"],
    )
    fig.update_layout(height=560, xaxis_title="Cobertura %", yaxis_title="")
    return fig


def gdd_progress_bar(gdd: pd.DataFrame) -> go.Figure:
    if gdd.empty:
        return empty_figure("Sin salidas GDD")
    d = gdd.copy()
    if "GDD_alcanzado" not in d.columns or "GDD Lourdes Variedad" not in d.columns:
        return empty_figure("No se detectaron columnas de GDD acumulado/umbral")
        
    d["GDD_alcanzado"] = pd.to_numeric(d["GDD_alcanzado"], errors="coerce")
    d["GDD Lourdes Variedad"] = pd.to_numeric(d["GDD Lourdes Variedad"], errors="coerce")
    d = d.dropna(subset=["GDD_alcanzado", "GDD Lourdes Variedad"])
    if d.empty:
        return empty_figure("Sin valores numericos para GDD")
        
    d["Avance %"] = (d["GDD_alcanzado"] / d["GDD Lourdes Variedad"] * 100).clip(upper=100)
    
    fundo = "Fundo" if "Fundo" in d.columns else "fundo" if "fundo" in d.columns else None
    variedad = "Variedad" if "Variedad" in d.columns else "variedad" if "variedad" in d.columns else None
    
    if fundo and variedad:
        d["serie"] = d[fundo].astype(str) + " - " + d[variedad].astype(str)
    elif fundo:
        d["serie"] = d[fundo].astype(str)
    elif variedad:
        d["serie"] = d[variedad].astype(str)
    else:
        d["serie"] = "Serie"
    
    fig = px.bar(
        d.sort_values("Avance %"),
        x="Avance %",
        y="serie",
        color=variedad,
        orientation="h",
        template="plotly_white",
        title="Avance GDD hacia Umbral de Brotacion",
        hover_data={"GDD_alcanzado": ":.1f", "GDD Lourdes Variedad": ":.1f"}
    )
    fig.update_layout(height=440, xaxis_title="Avance % hacia Umbral GDD", yaxis_title="")
    return fig


def phenology_error_plot(gdd: pd.DataFrame) -> go.Figure:
    # Este era el plot antiguo, lo reemplazamos por el panel A operativo.
    pass

def panel_a_operativo_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "residuo_brotacion_latitud" not in diagnostico.columns:
        return empty_figure("Sin datos de T0 Latitudinal")
    
    d = diagnostico.copy()
    d["error_dias_lat"] = pd.to_numeric(d["residuo_brotacion_latitud"], errors="coerce")
    d = d.dropna(subset=["error_dias_lat"])
    
    if d.empty:
        return empty_figure("Sin errores validos para T0 Latitudinal")
        
    fig = px.bar(
        d.sort_values("error_dias_lat"),
        x="Fundo" if "Fundo" in d.columns else "fundo",
        y="error_dias_lat",
        color="error_dias_lat",
        color_continuous_scale="RdBu",
        template="plotly_white",
        title="Desempeño preliminar del t0 latitudinal para brotación Cabernet",
        hover_data={"doy_t0_pred_reg_lat": True}
    )
    
    mae = d["error_dias_lat"].abs().mean()
    bias = d["error_dias_lat"].mean()
    
    fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text=f"Predicción exacta | MAE: {mae:.1f} | Sesgo: {bias:.1f}")
    
    # Nota metodologica: el MAE es sobre los mismos datos de ajuste
    fig.add_annotation(
        text="<b>Nota:</b> El MAE puede ser optimista (evaluado sobre set de ajuste). Idealmente requeriría CV espacial.",
        xref="paper", yref="paper", x=0.5, y=-0.2, showarrow=False, font=dict(size=10, color="gray")
    )
    
    fig.update_layout(height=450, xaxis_title="Fundo", yaxis_title="Error (Días adelantado/atrasado)", margin=dict(b=80))
    return fig


def panel_b_diagnostico_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "doy_t0_pred_reg_lat" not in diagnostico.columns:
        return empty_figure("Sin datos para diagnóstico")
        
    d = diagnostico.copy()
    
    fig = px.scatter(
        d,
        x="doy_t0_pred_reg_lat",
        y="doy_t0_operativo",
        color="Fundo" if "Fundo" in d.columns else "fundo",
        template="plotly_white",
        title="Panel B - Diagnóstico: T0 Latitudinal vs T0 Cerrado (DOY)",
        hover_data={"ventana_dias_t0_brotacion": True}
    )
    
    min_val = min(d["doy_t0_pred_reg_lat"].min(), d["doy_t0_operativo"].min()) - 5
    max_val = max(d["doy_t0_pred_reg_lat"].max(), d["doy_t0_operativo"].max()) + 5
    fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", name="1:1 (Concordancia)", line=dict(dash="dash", color="black")))
    
    fig.update_layout(height=450, xaxis_title="DOY T0 Latitudinal (Predictivo)", yaxis_title="DOY T0 Cerrado (Leakage retrospectivo)")
    return fig


def baseline_comparison_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "residuo_brotacion_latitud" not in diagnostico.columns:
        return empty_figure("Sin datos para comparación")
        
    d = diagnostico.copy()
    d["doy_brotacion"] = pd.to_numeric(d["doy_brotacion"], errors="coerce")
    
    mae_lat = d["residuo_brotacion_latitud"].abs().mean()
    mae_cerrado = d["error_dias"].abs().mean()
    
    # Baseline Fijo: Predecir brotación con el promedio de brotación (equivalente a un T0 y ventana fijos)
    mean_brot = d["doy_brotacion"].mean()
    mae_fijo = (d["doy_brotacion"] - mean_brot).abs().mean()
    
    comp = pd.DataFrame({
        "Esquema": ["A. T0 Cerrado (Leakage)", "B. T0 Latitudinal (Predictivo)", "C. Fijo (Baseline ingenuo)"],
        "MAE (días)": [mae_cerrado, mae_lat, mae_fijo],
        "Tipo": ["Diagnóstico", "Operativo", "Baseline"]
    })
    
    fig = px.bar(
        comp,
        x="Esquema",
        y="MAE (días)",
        color="Tipo",
        text_auto=".1f",
        template="plotly_white",
        title="Comparación de Modelos de Predicción (MAE)"
    )
    fig.update_layout(height=400, yaxis_title="MAE en días vs Observado")
    return fig


def cabernet_diagnostic_table(diagnostico: pd.DataFrame) -> pd.DataFrame:
    if diagnostico.empty:
        return pd.DataFrame()
    
    d = diagnostico.copy()
    
    # Derivar t0 latitudinal fecha real (aproximada, dado el doy)
    if "t0_operativo" in d.columns and "doy_t0_pred_reg_lat" in d.columns:
        d["t0_operativo"] = pd.to_datetime(d["t0_operativo"], errors="coerce")
        # Sumamos el doy - 1 al inicio del año para reconstruir la fecha del t0 latitudinal
        d["t0_latitudinal"] = d["t0_operativo"].dt.year.apply(lambda y: pd.Timestamp(f"{int(y) if pd.notna(y) else 2025}-01-01")) + pd.to_timedelta(d["doy_t0_pred_reg_lat"].fillna(0) - 1, unit="D")
        d["t0_latitudinal"] = d["t0_latitudinal"].dt.strftime("%Y-%m-%d")
        d["t0_operativo"] = d["t0_operativo"].dt.strftime("%Y-%m-%d")
        
    if "fecha_brotacion" in d.columns:
        d["fecha_brotacion"] = pd.to_datetime(d["fecha_brotacion"], errors="coerce").dt.strftime("%Y-%m-%d")
        
    out = pd.DataFrame()
    out["Fundo"] = d.get("Fundo", d.get("fundo", pd.Series(dtype=str)))
    out["T0 Cerrado"] = d.get("t0_operativo", pd.Series(dtype=str))
    out["T0 Latitudinal"] = d.get("t0_latitudinal", pd.Series(dtype=str))
    out["Fecha Brotación"] = d.get("fecha_brotacion", pd.Series(dtype=str))
    out["Error T0 Lat. (Días)"] = d.get("residuo_brotacion_latitud", pd.Series(dtype=float)).round(1)
    out["Ventana T0 Cerrado - Brotación"] = d.get("ventana_dias_t0_brotacion", pd.Series(dtype=float))
    
    # Consideramos critico si la ventana es menor a 22 días
    if "Ventana T0 Cerrado - Brotación" in out.columns:
        out["Estado / Alerta Leakage"] = ["🔴 CRÍTICO (Leakage excesivo)" if pd.notna(v) and v < 22 else "🟡 SOSPECHOSO (T0 tardío)" if pd.notna(v) else "" for v in out["Ventana T0 Cerrado - Brotación"]]
    
    return out.sort_values("Ventana T0 Cerrado - Brotación")


def panel_d_chill_table(chill: pd.DataFrame) -> pd.DataFrame:
    if chill.empty:
        return pd.DataFrame()
    d = chill.copy()
    
    out = pd.DataFrame()
    out["Fundo"] = d.get("Fundo", pd.Series(dtype=str))
    out["T0 Latitudinal"] = d.get("t0_latitudinal", pd.Series(dtype=str))
    out["Brotación"] = d.get("fecha_brotacion", pd.Series(dtype=str))
    out["Frío (CP) hasta T0 Lat."] = d.get("chill_hasta_t0_lat", pd.Series(dtype=float))
    out["GDD Previos al T0 Lat."] = d.get("gdd_jul1_a_t0_lat", pd.Series(dtype=float))
    out["GDD T0 a Brotación"] = d.get("gdd_t0_lat_a_brotacion", pd.Series(dtype=float))
    out["Estado Cobertura"] = d.get("estado_cobertura_horaria", pd.Series(dtype=str))
    
    # Semaforización
    def eval_status(row):
        cov = str(row.get("estado_cobertura_horaria", ""))
        cp = row.get("chill_hasta_t0_lat")
        gdd = row.get("gdd_jul1_a_t0_lat")
        
        if "INCOMPLETA" in cov:
            return "🔴 INCOMPLETO (Faltan datos Jul-Sep)"
        if pd.notna(cp) and pd.notna(gdd):
            # Criterio arbitrario de plausibilidad para diagnostico
            if cp < 20 and gdd > 80:
                return "🔴 CRITICO (Bajo frío, alto calor previo)"
            elif cp < 30:
                return "🟡 SOSPECHOSO (Bajo frío)"
            return "🟢 PLAUSIBLE"
        return "⚪ SIN DATOS"
        
    out["Alerta Plausibilidad"] = [eval_status(r) for _, r in d.iterrows()]
    return out

def panel_d_chill_plot(chill: pd.DataFrame) -> go.Figure:
    if chill.empty or "chill_hasta_t0_lat" not in chill.columns:
        return empty_figure("No hay cobertura horaria suficiente para calcular frío dinámico.")
        
    d = chill.copy()
    # Solo mostrar los completos
    d = d[~d["estado_cobertura_horaria"].str.contains("INCOMPLETA", na=False)]
    if d.empty:
        return empty_figure("No hay cobertura horaria suficiente para calcular frío dinámico en la temporada 2025_2026.")
        
    fig = px.bar(
        d,
        x="Fundo",
        y=["chill_hasta_t0_lat", "chill_hasta_t0_cerrado", "chill_hasta_brotacion"],
        barmode="group",
        template="plotly_white",
        title="Acumulación de Frío (Chill Portions) por Hito"
    )
    fig.update_layout(height=450, yaxis_title="Chill Portions Acumuladas", legend_title="Hito")
    return fig


def maturity_curve(df: pd.DataFrame, variable: str, title: str) -> go.Figure:
    if df.empty or not variable:
        return empty_figure("Sin datos para curva")
    d = df.copy()
    date_col = next((c for c in d.columns if normalize_text(c) in {"fecha", "date"} or "fecha" in normalize_text(c)), None)
    if date_col:
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    else:
        d["_row"] = range(len(d))
        date_col = "_row"
    color = next((c for c in d.columns if normalize_text(c) in {"fundo", "campo"} or "fundo" in normalize_text(c)), None)
    line_dash = next((c for c in d.columns if "variedad" in normalize_text(c)), None)
    fig = px.line(
        d.sort_values(date_col),
        x=date_col,
        y=variable,
        color=color,
        line_dash=line_dash,
        markers=True,
        template="plotly_white",
        title=title,
    )
    fig.update_layout(height=460, xaxis_title="Fecha", yaxis_title=variable)
    return fig


def maturity_curve_grouped(df: pd.DataFrame, variable: str, group_by_cuartel: bool = False) -> go.Figure:
    if df.empty or not variable or variable not in df.columns:
        return empty_figure("Sin datos de madurez tecnica para los filtros seleccionados")
    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    d[variable] = pd.to_numeric(d[variable], errors="coerce")
    d = d.dropna(subset=["fecha", "fundo", "variedad", variable])
    if d.empty:
        return empty_figure("Sin valores numericos para la variable seleccionada")

    group_cols = ["fecha", "temporada", "fundo", "variedad"]
    if group_by_cuartel and "cuartel" in d.columns:
        group_cols.append("cuartel")

    agg = (
        d.groupby(group_cols, dropna=False)
        .agg(
            valor=(variable, "mean"),
            n_muestras=(variable, "count"),
            cuarteles=("cuartel", lambda s: ", ".join(sorted({str(x) for x in s.dropna().unique()})[:5])),
            muestras=("muestra", lambda s: ", ".join(sorted({str(x) for x in s.dropna().unique()})[:5])),
        )
        .reset_index()
    )
    agg["serie"] = agg["fundo"].astype(str).str.title() + " - " + agg["variedad"].astype(str).str.title()
    if group_by_cuartel and "cuartel" in agg.columns:
        agg["serie"] = agg["serie"] + " - C" + agg["cuartel"].astype(str)

    fig = px.line(
        agg.sort_values("fecha"),
        x="fecha",
        y="valor",
        color="serie",
        markers=True,
        template="plotly_white",
        title=f"Progreso temporal de {variable}",
        hover_data={
            "serie": False,
            "fundo": True,
            "variedad": True,
            "cuarteles": True,
            "muestras": True,
            "temporada": True,
            "fecha": "|%Y-%m-%d",
            "valor": ":.3f",
            "n_muestras": True,
        },
    )
    fig.update_layout(
        height=520,
        xaxis_title="Fecha",
        yaxis_title=variable,
        legend_title_text="Fundo - variedad" + (" - cuartel" if group_by_cuartel else ""),
    )
    return fig


def observed_vs_pred(preds: pd.DataFrame, target: str | None = None) -> go.Figure:
    if preds.empty:
        return empty_figure("Sin predicciones")
    d = preds.copy()
    y_col = target if target in d.columns else None
    if not y_col:
        candidates = [c for c in d.columns if c not in {"prediction", "split_id", "seed", "n_predictors"} and pd.api.types.is_numeric_dtype(d[c])]
        y_col = candidates[0] if candidates else None
    if not y_col or "prediction" not in d.columns:
        return empty_figure("No se detectaron observado/prediccion")
    fig = px.scatter(
        d,
        x=y_col,
        y="prediction",
        color="fundo" if "fundo" in d.columns else None,
        hover_data=["variedad", "fecha"] if {"variedad", "fecha"}.issubset(d.columns) else None,
        template="plotly_white",
    )
    fig.add_trace(go.Scatter(x=[d[y_col].min(), d[y_col].max()], y=[d[y_col].min(), d[y_col].max()], mode="lines", name="1:1"))
    fig.update_layout(height=460, xaxis_title="Observado", yaxis_title="Predicho")
    return fig


def metric_ranking(metrics: pd.DataFrame) -> go.Figure:
    if metrics.empty or "mae" not in metrics.columns:
        return empty_figure("Sin metricas")
    group_cols = [c for c in ["target_key", "scheme", "model", "method", "predictors"] if c in metrics.columns]
    d = metrics.copy()
    d["mae"] = pd.to_numeric(d["mae"], errors="coerce")
    agg = d.groupby(group_cols, dropna=False).agg(mae=("mae", "mean"), r2=("r2", "mean") if "r2" in d.columns else ("mae", "size")).reset_index()
    agg = agg.sort_values("mae").head(30)
    fig = px.bar(agg, x="mae", y="target_key", color="scheme" if "scheme" in agg.columns else None, orientation="h", hover_data=group_cols, template="plotly_white")
    fig.update_layout(height=620, yaxis_title="", xaxis_title="MAE promedio")
    return fig


def importance_bar(df: pd.DataFrame, value_col: str) -> go.Figure:
    if df.empty or value_col not in df.columns or "feature" not in df.columns:
        return empty_figure("Sin importancias")
    d = df.copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    agg = d.groupby("feature", dropna=False)[value_col].mean().reset_index().sort_values(value_col, ascending=False).head(25)
    fig = px.bar(agg, x=value_col, y="feature", orientation="h", template="plotly_white")
    fig.update_layout(height=560, yaxis_title="", xaxis_title=value_col)
    return fig
