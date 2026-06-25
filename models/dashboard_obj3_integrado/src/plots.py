from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .loaders import find_columns, normalize_text

# --- CONFIGURACIÓN VISUAL TÉCNICA SOBRIA E INVESTIGATIVA ---
WINE_PALETTE = ["#6b1d2f", "#2d3748", "#d69e2e", "#319795", "#805ad5", "#dd6b20", "#e53e3e", "#38a169", "#3182ce"]
FONT_FAMILY = "Inter, Roboto, sans-serif"

GLOSSARY = {
    "GDA_VPD_medio_acum_IFTT_acum_rendimientoton_ha": "Calor Acum. + VPD + Índice Frío + Rendimiento",
    "GDA_VPD_medio_acum_IFs_acum": "Calor Acum. + VPD + Frío Estacional",
    "GDA_VPD_medio_acum_IFs_acum_azucar_real_baya_g": "Calor Acum. + VPD + Frío + Azúcar Baya",
    "GDA_VPD_medio_acum_IFs_acum_azucar_real_baya_g_peso_baya": "Calor + VPD + Frío + Azúcar + Peso Baya",
    "GDA_VPD_medio_acum_IFs_acum_azucar_real_baya_g_rendimientoton_ha": "Calor + VPD + Frío + Azúcar + Rendimiento",
    "GDA_VPD_medio_acum_IFs_acum_peso_baya": "Calor + VPD + Frío + Peso Baya",
    "GDA_VPD_medio_acum_IFs_acum_rendimientoton_ha": "Calor + VPD + Frío + Rendimiento",
    "VPD_medio_acum": "Déficit de Presión de Vapor Acumulado (VPD)",
    "GDA": "Acumulación Térmica (Grados Día - GDD)",
    "residuo_brotacion_latitud": "Error Brotación Latitudinal [días]",
    "doy_t0_pred_reg_lat": "DOY T0 Latitudinal [estimado]",
    "doy_t0_operativo": "DOY T0 Cerrado [observado]",
    "brix": "Sólidos Solubles [°Brix]",
    "ph": "pH del Mosto",
    "acidez_tartarica": "Acidez Tartárica [g/L]",
    "acidez_sulfurica": "Acidez Total [g/L H2SO4]",
    "peso_baya": "Peso de Baya [g]",
    "azucar_real_baya_g": "Azúcar Real por Baya [g]",
    "antocianinas_mg_baya": "Antocianinas [mg/baya]",
    "taninos_mg_baya": "Taninos [mg/baya]",
    "suma_compuestos_fenolicos_mg_kg": "Compuestos Fenólicos Totales [mg/kg]",
    "cv5_mixed": "Validación Cruzada Estratificada (CV5)",
    "lofo_mixed": "Validación Espacial (LOFO — Leave One Fundo Out)",
    "shap_mean_abs": "Importancia SHAP Media Absoluta",
    "perm_importance_mean": "Importancia por Permutación Media",
    "mae": "Error Medio Absoluto [MAE]",
    "r2": "Coeficiente de Determinación [R²]"
}

def translate_text(text: str) -> str:
    s = str(text)
    return GLOSSARY.get(s, s.replace('_', ' ').title())

def apply_corporate_style(fig: go.Figure, height: int = 440) -> go.Figure:
    fig.update_layout(
        height=height,
        template="plotly_white",
        font=dict(family=FONT_FAMILY, size=12, color="#2d3748"),
        title_font=dict(family=FONT_FAMILY, size=15, color="#1a202c"),
        plot_bgcolor="#fafbfc",
        paper_bgcolor="white",
        margin=dict(l=45, r=30, t=55, b=45)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#edf2f7", zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#edf2f7", zeroline=False)
    return fig

def empty_figure(message: str = "Sin datos disponibles") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=f"<b>ℹ️ Aviso:</b> {message}", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper", font=dict(size=14, color="#718096"))
    return apply_corporate_style(fig, height=340)


def climate_status_bar(resumen: pd.DataFrame) -> go.Figure:
    if resumen.empty or "estado" not in resumen.columns:
        return empty_figure("Sin resumen climático")
    d = resumen.groupby("estado", dropna=False).size().reset_index(name="fundos")
    fig = px.bar(d, x="estado", y="fundos", color="estado", text="fundos", color_discrete_sequence=WINE_PALETTE)
    fig.update_layout(showlegend=False, xaxis_title="Estado Operacional", yaxis_title="Fundos en Monitoreo", title="Estado de Red Climática Regional")
    return apply_corporate_style(fig, height=320)


def coverage_bar(resumen: pd.DataFrame) -> go.Figure:
    if resumen.empty or "cobertura_%" not in resumen.columns:
        return empty_figure("Sin cobertura climática")
    d = resumen.copy()
    d["cobertura_%"] = pd.to_numeric(d["cobertura_%"], errors="coerce")
    d = d.sort_values("cobertura_%")
    fig = px.bar(
        d,
        x="cobertura_%",
        y="fundo_normalizado",
        color="estado",
        orientation="h",
        color_discrete_sequence=WINE_PALETTE,
        hover_data=["estacion_recomendada", "red", "station_id"],
        title="Porcentaje de Cobertura de Datos Climáticos por Fundo"
    )
    fig.update_layout(xaxis_title="Cobertura Horaria [%]", yaxis_title="Fundo")
    return apply_corporate_style(fig, height=540)


def gdd_progress_bar(gdd: pd.DataFrame) -> go.Figure:
    if gdd.empty:
        return empty_figure("Sin salidas de Acumulación Térmica (GDD)")
    d = gdd.copy()
    if "GDD_alcanzado" not in d.columns or "GDD Lourdes Variedad" not in d.columns:
        return empty_figure("No se detectaron columnas de GDD acumulado/umbral")
        
    d["GDD_alcanzado"] = pd.to_numeric(d["GDD_alcanzado"], errors="coerce")
    d["GDD Lourdes Variedad"] = pd.to_numeric(d["GDD Lourdes Variedad"], errors="coerce")
    d = d.dropna(subset=["GDD_alcanzado", "GDD Lourdes Variedad"])
    if d.empty:
        return empty_figure("Sin valores numéricos válidos para GDD")
        
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
        color_discrete_sequence=WINE_PALETTE,
        title="Avance Térmico hacia Umbral de Brotación Fisiológica",
        hover_data={"GDD_alcanzado": ":.1f", "GDD Lourdes Variedad": ":.1f"}
    )
    fig.update_layout(xaxis_title="Avance Térmico [%]", yaxis_title="")
    return apply_corporate_style(fig, height=440)


def phenology_error_plot(gdd: pd.DataFrame) -> go.Figure:
    pass


def panel_a_operativo_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "residuo_brotacion_latitud" not in diagnostico.columns:
        return empty_figure("Sin datos de T0 Latitudinal")
    
    d = diagnostico.copy()
    d["error_dias_lat"] = pd.to_numeric(d["residuo_brotacion_latitud"], errors="coerce")
    d = d.dropna(subset=["error_dias_lat"])
    
    if d.empty:
        return empty_figure("Sin errores válidos para T0 Latitudinal")
        
    fig = px.bar(
        d.sort_values("error_dias_lat"),
        x="Fundo" if "Fundo" in d.columns else "fundo",
        y="error_dias_lat",
        color="error_dias_lat",
        color_continuous_scale="RdBu",
        title="Desempeño Operativo del Biofix Latitudinal (Brotación Cabernet)",
        hover_data={"doy_t0_pred_reg_lat": True}
    )
    
    mae = d["error_dias_lat"].abs().mean()
    bias = d["error_dias_lat"].mean()
    
    fig.add_hline(y=0, line_dash="dash", line_color="#38a169", annotation_text=f"Concordancia Exacta | MAE: {mae:.1f} días | Sesgo: {bias:.1f} días")
    
    fig.update_layout(xaxis_title="Viñedo / Fundo", yaxis_title="Residuo [Días de Desvío]")
    return apply_corporate_style(fig, height=450)


def panel_b_diagnostico_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "doy_t0_pred_reg_lat" not in diagnostico.columns:
        return empty_figure("Sin datos para diagnóstico")
        
    d = diagnostico.copy()
    
    fig = px.scatter(
        d,
        x="doy_t0_pred_reg_lat",
        y="doy_t0_operativo",
        color="Fundo" if "Fundo" in d.columns else "fundo",
        color_discrete_sequence=WINE_PALETTE,
        title="Diagnóstico Fisiológico: Biofix Latitudinal vs Cerrado [DOY]",
        hover_data={"ventana_dias_t0_brotacion": True}
    )
    
    min_val = min(d["doy_t0_pred_reg_lat"].min(), d["doy_t0_operativo"].min()) - 5
    max_val = max(d["doy_t0_pred_reg_lat"].max(), d["doy_t0_operativo"].max()) + 5
    fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", name="1:1 (Concordancia Ideal)", line=dict(dash="dash", color="#718096")))
    
    fig.update_layout(xaxis_title="DOY T0 Latitudinal [Modelo Operativo]", yaxis_title="DOY T0 Cerrado [Retrospectivo]")
    return apply_corporate_style(fig, height=450)


def baseline_comparison_plot(diagnostico: pd.DataFrame) -> go.Figure:
    if diagnostico.empty or "residuo_brotacion_latitud" not in diagnostico.columns:
        return empty_figure("Sin datos para comparación")
        
    d = diagnostico.copy()
    d["doy_brotacion"] = pd.to_numeric(d["doy_brotacion"], errors="coerce")
    
    mae_lat = d["residuo_brotacion_latitud"].abs().mean()
    mae_cerrado = d["error_dias"].abs().mean()
    
    mean_brot = d["doy_brotacion"].mean()
    mae_fijo = (d["doy_brotacion"] - mean_brot).abs().mean()
    
    comp = pd.DataFrame({
        "Esquema": ["A. T0 Cerrado (Retrospectivo)", "B. T0 Latitudinal (Operativo)", "C. Promedio Fijo (Ingenuo)"],
        "MAE [días]": [mae_cerrado, mae_lat, mae_fijo],
        "Tipo": ["Diagnóstico", "Operativo", "Baseline"]
    })
    
    fig = px.bar(
        comp,
        x="Esquema",
        y="MAE [días]",
        color="Tipo",
        text_auto=".1f",
        color_discrete_sequence=["#6b1d2f", "#319795", "#a0aec0"],
        title="Auditoría de Modelos: Error Medio Absoluto en Brotación [MAE]"
    )
    fig.update_layout(yaxis_title="MAE [Días de Desvío]", xaxis_title="Esquema Metodológico")
    return apply_corporate_style(fig, height=400)


def cabernet_diagnostic_table(diagnostico: pd.DataFrame) -> pd.DataFrame:
    if diagnostico.empty:
        return pd.DataFrame()
    
    d = diagnostico.copy()
    
    if "t0_operativo" in d.columns and "doy_t0_pred_reg_lat" in d.columns:
        d["t0_operativo"] = pd.to_datetime(d["t0_operativo"], errors="coerce")
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
    out["Error T0 Lat. [Días]"] = d.get("residuo_brotacion_latitud", pd.Series(dtype=float)).round(1)
    out["Ventana T0 Cerrado - Brotación"] = d.get("ventana_dias_t0_brotacion", pd.Series(dtype=float))
    
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
    out["Frío [CP] hasta T0 Lat."] = d.get("chill_hasta_t0_lat", pd.Series(dtype=float))
    out["Calor Prev. al T0 [GDD]"] = d.get("gdd_jul1_a_t0_lat", pd.Series(dtype=float))
    out["Calor T0 a Brotación [GDD]"] = d.get("gdd_t0_lat_a_brotacion", pd.Series(dtype=float))
    out["Estado Cobertura"] = d.get("estado_cobertura_horaria", pd.Series(dtype=str))
    
    def eval_status(row):
        cov = str(row.get("estado_cobertura_horaria", ""))
        cp = row.get("chill_hasta_t0_lat")
        gdd = row.get("gdd_jul1_a_t0_lat")
        
        if "INCOMPLETA" in cov:
            return "🔴 INCOMPLETO (Faltan datos Jul-Sep)"
        if pd.notna(cp) and pd.notna(gdd):
            if cp < 20 and gdd > 80:
                return "🔴 CRÍTICO (Bajo frío invernal)"
            elif cp < 30:
                return "🟡 SOSPECHOSO (Frío límite)"
            return "🟢 PLAUSIBLE"
        return "⚪ SIN DATOS"
        
    out["Alerta Fisiológica"] = [eval_status(r) for _, r in d.iterrows()]
    return out


def panel_d_chill_plot(chill: pd.DataFrame) -> go.Figure:
    if chill.empty or "chill_hasta_t0_lat" not in chill.columns:
        return empty_figure("Cobertura horaria insuficiente para calcular frío dinámico invernal.")
        
    d = chill.copy()
    d = d[~d["estado_cobertura_horaria"].str.contains("INCOMPLETA", na=False)]
    if d.empty:
        return empty_figure("Pendiente ingesta de datos horarios invernales (Julio - Octubre 2025).")
        
    fig = px.bar(
        d,
        x="Fundo",
        y=["chill_hasta_t0_lat", "chill_hasta_t0_cerrado", "chill_hasta_brotacion"],
        barmode="group",
        color_discrete_sequence=WINE_PALETTE,
        title="Acumulación de Frío Invernal [Chill Portions] por Hito Fenológico"
    )
    fig.update_layout(yaxis_title="Chill Portions Acumuladas", legend_title="Hito Fisiológico")
    return apply_corporate_style(fig, height=450)


def maturity_curve(df: pd.DataFrame, variable: str, title: str) -> go.Figure:
    if df.empty or not variable:
        return empty_figure("Sin datos para renderizar curva")
    d = df.copy()
    date_col = next((c for c in d.columns if normalize_text(c) in {"fecha", "date"} or "fecha" in normalize_text(c)), None)
    if date_col:
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    else:
        d["_row"] = range(len(d))
        date_col = "_row"
    color = next((c for c in d.columns if normalize_text(c) in {"fundo", "campo"} or "fundo" in normalize_text(c)), None)
    line_dash = next((c for c in d.columns if "variedad" in normalize_text(c)), None)
    
    var_clean = translate_text(variable)
    fig = px.line(
        d.sort_values(date_col),
        x=date_col,
        y=variable,
        color=color,
        line_dash=line_dash,
        markers=True,
        color_discrete_sequence=WINE_PALETTE,
        title=f"{title}: Evolución de {var_clean}"
    )
    fig.update_layout(xaxis_title="Fecha de Muestreo", yaxis_title=var_clean)
    return apply_corporate_style(fig, height=460)


def maturity_curve_grouped(df: pd.DataFrame, variable: str, group_by_cuartel: bool = False) -> go.Figure:
    if df.empty or not variable or variable not in df.columns:
        return empty_figure("Sin datos de madurez técnica para los filtros seleccionados")
    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    d[variable] = pd.to_numeric(d[variable], errors="coerce")
    d = d.dropna(subset=["fecha", "fundo", "variedad", variable])
    if d.empty:
        return empty_figure("Sin registros numéricos válidos en el rango seleccionado")

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

    var_clean = translate_text(variable)
    fig = px.line(
        agg.sort_values("fecha"),
        x="fecha",
        y="valor",
        color="serie",
        markers=True,
        color_discrete_sequence=WINE_PALETTE,
        title=f"Evolución Enológica Temporal: {var_clean}",
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
        xaxis_title="Fecha de Control",
        yaxis_title=var_clean,
        legend_title_text="Viñedo — Variedad" + (" — Cuartel" if group_by_cuartel else ""),
    )
    return apply_corporate_style(fig, height=520)


def observed_vs_pred(preds: pd.DataFrame, target: str | None = None) -> go.Figure:
    if preds.empty:
        return empty_figure("Sin predicciones disponibles")
    d = preds.copy()
    y_col = target if target in d.columns else None
    if not y_col:
        candidates = [c for c in d.columns if c not in {"prediction", "split_id", "seed", "n_predictors"} and pd.api.types.is_numeric_dtype(d[c])]
        y_col = candidates[0] if candidates else None
    if not y_col or "prediction" not in d.columns:
        return empty_figure("No se detectaron columnas de valores observados vs predichos")
        
    tgt_clean = translate_text(y_col)
    fig = px.scatter(
        d,
        x=y_col,
        y="prediction",
        color="fundo" if "fundo" in d.columns else None,
        color_discrete_sequence=WINE_PALETTE,
        hover_data=["variedad", "fecha"] if {"variedad", "fecha"}.issubset(d.columns) else None,
        title=f"Concordancia de Modelo: {tgt_clean} Observado vs Predicho"
    )
    
    min_v = min(d[y_col].min(), d["prediction"].min())
    max_v = max(d[y_col].max(), d["prediction"].max())
    fig.add_trace(go.Scatter(x=[min_v, max_v], y=[min_v, max_v], mode="lines", name="Concordancia Exacta (1:1)", line=dict(dash="dash", color="#a0aec0")))
    
    fig.update_layout(xaxis_title=f"Valor Observado [{tgt_clean}]", yaxis_title=f"Valor Predicho [{tgt_clean}]")
    return apply_corporate_style(fig, height=460)


def metric_ranking(metrics: pd.DataFrame) -> go.Figure:
    if metrics.empty or "mae" not in metrics.columns:
        return empty_figure("Sin métricas de evaluación")
    group_cols = [c for c in ["target_key", "scheme", "model", "method", "predictors"] if c in metrics.columns]
    d = metrics.copy()
    d["mae"] = pd.to_numeric(d["mae"], errors="coerce")
    agg = d.groupby(group_cols, dropna=False).agg(mae=("mae", "mean"), r2=("r2", "mean") if "r2" in d.columns else ("mae", "size")).reset_index()
    agg = agg.sort_values("mae").head(30)
    
    if "target_key" in agg.columns:
        agg["target_clean"] = agg["target_key"].apply(translate_text)
    else:
        agg["target_clean"] = "Objetivo"
        
    if "scheme" in agg.columns:
        agg["scheme_clean"] = agg["scheme"].apply(translate_text)
    else:
        agg["scheme_clean"] = None

    fig = px.bar(
        agg,
        x="mae",
        y="target_clean",
        color="scheme_clean" if "scheme_clean" in agg.columns else None,
        orientation="h",
        color_discrete_sequence=WINE_PALETTE,
        hover_data=group_cols,
        title="Ranking de Precisión Predictiva por Parámetro [Menor MAE es Mejor]"
    )
    fig.update_layout(yaxis_title="Parámetro Evaluado", xaxis_title="Error Medio Absoluto Promedio [MAE]", legend_title="Esquema de Validación")
    return apply_corporate_style(fig, height=620)


def importance_bar(df: pd.DataFrame, value_col: str) -> go.Figure:
    if df.empty or value_col not in df.columns or "feature" not in df.columns:
        return empty_figure("Sin datos de interpretabilidad")
    d = df.copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    agg = d.groupby("feature", dropna=False)[value_col].mean().reset_index().sort_values(value_col, ascending=False).head(25)
    
    # TRADUCIR PREDICTORES SINTÉTICOS ENCRIPTADOS A LENGUAJE AGRONÓMICO
    agg["feature_clean"] = agg["feature"].apply(translate_text)
    
    metric_name = translate_text(value_col)
    fig = px.bar(
        agg,
        x=value_col,
        y="feature_clean",
        orientation="h",
        color=value_col,
        color_continuous_scale="Viridis",
        title=f"Drivers Agronómicos: {metric_name}"
    )
    fig.update_layout(yaxis_title="Variable Ambientales y Productivas", xaxis_title=metric_name)
    return apply_corporate_style(fig, height=560)


# ---------------------------------------------------------------------------
# Sprint 2.2 — Serie temporal climática horaria/diaria
# ---------------------------------------------------------------------------

def climate_timeseries_plot(
    df: pd.DataFrame,
    variable: str,
    station_name: str,
    source: str,
    freq: str = "horaria",
) -> go.Figure:
    """Serie temporal de una variable climática para una estación dada.

    Args:
        df: DataFrame con columna 'fecha' y variable climática.
        variable: nombre de la columna a graficar (nombre display).
        station_name: nombre legible de la estación.
        source: fuente ('Datavid', 'INIA/Agromet', 'Zentra').
        freq: 'horaria' | 'diaria (agregada en memoria)'.
    """
    if df.empty or variable not in df.columns:
        msg = f"Sin datos disponibles para {variable} en {station_name}."
        if not df.empty:
            available = [c for c in df.columns if c != "fecha"]
            msg += f"\nVariables disponibles en esta fuente: {', '.join(available[:8]) or 'ninguna'}."
        return empty_figure(msg)

    d = df[["fecha", variable]].dropna(subset=[variable]).copy()
    if d.empty:
        return empty_figure(f"Todos los registros de {variable} son nulos para {station_name}.")

    freq_label = "agregación diaria en memoria (no guardada)" if freq == "diaria" else "horaria"
    title = f"Serie Temporal — {variable} | {station_name.replace('_', ' ').title()} ({source})"
    subtitle = f"<span style='font-size:11px;color:#718096'>Frecuencia: {freq_label} · Fuente: {source}</span>"

    fig = px.line(
        d,
        x="fecha",
        y=variable,
        title=f"{title}<br>{subtitle}",
        color_discrete_sequence=[WINE_PALETTE[0]],
    )
    fig.update_traces(line_width=1.2, opacity=0.9)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=variable,
        hovermode="x unified",
    )
    return apply_corporate_style(fig, height=420)


# ---------------------------------------------------------------------------
# Sprint 2.2 — Curva latitudinal T0/Brotación (Fenología — Panel A/nuevo)
# ---------------------------------------------------------------------------

def latitudinal_regression_plot(
    diagnostico: pd.DataFrame,
    regresiones: pd.DataFrame,
) -> go.Figure:
    """Scatter latitud × DOY con curvas de regresión brotación y T0.

    Usa los outputs canónicos de method_pipeline_summary.xlsx:
    - sheet diagnostico_cs_reg: datos por fundo (lat, DOY brotación, DOY T0, incluido/excluido)
    - sheet regresiones_cs: parámetros de regresión (pendiente, intercepto, R², fundos)

    Nota metodológica: El T0 cerrado retrospectivo NO es un predictor operacional.
    La curva T0 ~ latitud es exploratoria; la curva brotación ~ latitud (R²=0.86) es la de referencia.
    Los Acacios se marca como caso diagnóstico excluido de la regresión.
    """
    if diagnostico.empty:
        return empty_figure(
            "Sin datos de diagnóstico latitudinal.\n"
            "Fuente esperada: models/indicador_biologico/outputs_multisite_gdd/method_pipeline_summary.xlsx\n"
            "Sheet: diagnostico_cs_reg"
        )

    d = diagnostico.copy()
    required = {"lat", "doy_brotacion", "doy_t0_operativo", "Fundo"}
    missing = required - set(d.columns)
    if missing:
        return empty_figure(f"Columnas faltantes en diagnostico_cs_reg: {', '.join(sorted(missing))}")

    lat_range = [d["lat"].min() - 0.5, d["lat"].max() + 0.5]

    fig = go.Figure()

    # --- Datos por fundo ---
    incluidos = d[d.get("incluido_en_regresion", pd.Series(True, index=d.index)).astype(str).str.upper() != "FALSE"].copy()
    excluidos = d[d.get("incluido_en_regresion", pd.Series(False, index=d.index)).astype(str).str.upper() == "FALSE"].copy()

    # Scatter brotación ELP4 observada — incluidos
    if not incluidos.empty:
        fig.add_trace(go.Scatter(
            x=incluidos["lat"],
            y=incluidos["doy_brotacion"],
            mode="markers+text",
            name="Brotación ELP4 observada",
            text=incluidos["Fundo"],
            textposition="top right",
            textfont=dict(size=10, color="#2d3748"),
            marker=dict(size=11, color=WINE_PALETTE[0], symbol="circle"),
        ))
        fig.add_trace(go.Scatter(
            x=incluidos["lat"],
            y=incluidos["doy_t0_operativo"],
            mode="markers+text",
            name="T0 operativo (biofix CS)",
            text=incluidos["Fundo"],
            textposition="bottom right",
            textfont=dict(size=9, color="#805ad5"),
            marker=dict(size=9, color=WINE_PALETTE[4], symbol="diamond"),
        ))

    # Los Acacios / excluidos
    if not excluidos.empty:
        fig.add_trace(go.Scatter(
            x=excluidos["lat"],
            y=excluidos["doy_brotacion"],
            mode="markers+text",
            name="Brotación ELP4 (excluido de regresión)",
            text=excluidos["Fundo"],
            textposition="top right",
            textfont=dict(size=10, color="#e53e3e"),
            marker=dict(size=12, color="#e53e3e", symbol="circle-open", line=dict(width=2)),
        ))
        fig.add_trace(go.Scatter(
            x=excluidos["lat"],
            y=excluidos["doy_t0_operativo"],
            mode="markers",
            name="T0 operativo (excluido)",
            marker=dict(size=10, color="#e53e3e", symbol="diamond-open", line=dict(width=2)),
        ))

    # --- Curvas de regresión ---
    import numpy as np
    lat_line = np.linspace(lat_range[0], lat_range[1], 100)

    if not regresiones.empty:
        for _, row in regresiones.iterrows():
            reg_name = str(row.get("regresion", ""))
            pendiente = float(row.get("pendiente", 0))
            intercepto = float(row.get("intercepto", 0))
            r2 = float(row.get("r2", 0))
            mae = float(row.get("mae", 0))
            n = int(row.get("n", 0))
            fundos_incl = str(row.get("fundos_incluidos", ""))

            doy_line = pendiente * lat_line + intercepto
            is_brotacion = "brotacion" in normalize_text(reg_name)
            color = WINE_PALETTE[0] if is_brotacion else WINE_PALETTE[4]
            label = (
                f"Curva brotación ~ lat (R²={r2:.2f}, MAE={mae:.1f}d, n={n})"
                if is_brotacion
                else f"Curva T0 ~ lat (R²={r2:.2f}, MAE={mae:.1f}d, n={n}) [exploratoria]"
            )
            fig.add_trace(go.Scatter(
                x=lat_line,
                y=doy_line,
                mode="lines",
                name=label,
                line=dict(color=color, width=2, dash="solid" if is_brotacion else "dash"),
            ))

    # Annotations
    fig.add_annotation(
        x=0.01, y=0.02, xref="paper", yref="paper",
        text=(
            "⚠️ <b>Nota metodológica:</b> Curva brotación ~ latitud es la referencia operacional (R²=0.86). "
            "Curva T0 ~ latitud es exploratoria. "
            "Los Acacios excluido de la regresión (diagnóstico fisiológico pendiente)."
        ),
        showarrow=False,
        font=dict(size=10, color="#718096"),
        align="left",
        bgcolor="rgba(237,242,247,0.85)",
        borderpad=6,
    )

    fig.update_layout(
        title="Auditoría Latitudinal: Biofix T0 y Brotación ELP4 Cabernet Sauvignon 2025–2026",
        xaxis_title="Latitud [grados decimales]",
        yaxis_title="DOY (Día del Año)",
        legend=dict(orientation="v", x=1.01, y=1),
    )
    return apply_corporate_style(fig, height=520)
