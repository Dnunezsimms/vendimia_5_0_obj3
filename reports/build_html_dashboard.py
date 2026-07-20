import sys
import os
from pathlib import Path
import json
import pandas as pd

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from models.dashboard_obj3_integrado.src.loaders import (
    load_state, find_columns, numeric_columns,
    get_climate_station_variables, load_climate_station_series
)
from models.dashboard_obj3_integrado.src.plots import (
    climate_status_bar,
    coverage_bar,
    climate_timeseries_plot,
    latitudinal_regression_plot,
    gdd_biofix_timeseries_plot,
    panel_a_operativo_plot,
    panel_b_diagnostico_plot,
    baseline_comparison_plot,
    cabernet_diagnostic_table,
    phenology_error_plot,
    panel_d_chill_plot,
    panel_d_chill_table,
    maturity_curve_grouped,
    maturity_curve,
    metric_ranking,
    observed_vs_pred,
    importance_bar,
    prepare_maturity_traceability_table,
    empty_figure
)

def _safe(df):
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

def _filter_table(df, fundo, variedad):
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

def _choices(df, col, all_label):
    if df.empty or col not in df.columns:
        return [all_label]
    values = sorted(df[col].dropna().astype(str).unique().tolist())
    return [all_label] + values

def _filter_maturity(df, variedad, fundo, temporada):
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

def clean_id(val):
    return str(val).replace(" ", "_").replace("/", "_").replace(".", "_").replace("-", "_").replace("°", "").replace("[", "").replace("]", "").lower()

def df_to_html_table(df, max_rows=300):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return "<p><i>No hay datos disponibles para esta selección o tabla.</i></p>"
    sub = df.head(max_rows).copy()
    html = sub.to_html(classes="data-table", index=False, border=0)
    if len(df) > max_rows:
        html += f"<p class='table-note'><i>Mostrando los primeros {max_rows} registros de {len(df)} totales.</i></p>"
    return f"<div class='table-container'>{html}</div>"

def fig_to_html(fig):
    if fig is None:
        return "<p><i>Gráfico no disponible.</i></p>"
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})

def build_complete_html_dashboard():
    print("1/4 Cargando estado canónico en repo clean (load_state)...")
    state = load_state()
    climate = state.get("climate", {})
    gdd = state.get("gdd", {})
    phenology = state.get("phenology", {})
    maturity = state.get("maturity", {})
    luis = state.get("luis", {})
    gdd_latitudinal = state.get("gdd_latitudinal", {})
    climate_catalog = state.get("climate_catalog", {})

    print("1.5/4 Cargando datos de validación ERA5-Land (vinewise-rs)...")
    import plotly.graph_objects as go

    vinewise_tables_dir = Path("C:/projects/vinewise-rs/reports/tables")
    if vinewise_tables_dir.exists():
        df_era5_metrics = pd.read_csv(vinewise_tables_dir / "multisite_era5_vs_local_metrics_5fundos.csv")
        df_era5_daily = pd.read_csv(vinewise_tables_dir / "multisite_era5_vs_local_daily.csv")
        df_era5_elp = pd.read_csv(vinewise_tables_dir / "era5_elp_baseline_metrics_5fundos.csv")
        df_era5_decision = pd.read_csv(vinewise_tables_dir / "era5_obj3_decision_matrix.csv")
    else:
        df_era5_metrics = pd.DataFrame()
        df_era5_daily = pd.DataFrame()
        df_era5_elp = pd.DataFrame()
        df_era5_decision = pd.DataFrame()

    # Generar gráficos Plotly interactivos para validación ERA5
    fig_era5_gdd_scatter = go.Figure()
    if not df_era5_daily.empty:
        df_clean = df_era5_daily.dropna(subset=['GDD_seno_simple_local', 'GDD_seno_simple_era5'])
        colors = {"Lourdes": "#1f77b4", "Idahue": "#2ca02c", "Los Acacios": "#d62728", "Quebrada Seca": "#ff7f0e", "Mariposas": "#9467bd"}
        for fundo, group in df_clean.groupby("fundo"):
            fig_era5_gdd_scatter.add_trace(go.Scatter(
                x=group['GDD_seno_simple_local'],
                y=group['GDD_seno_simple_era5'],
                mode='markers',
                name=fundo,
                marker=dict(size=6, opacity=0.6, color=colors.get(fundo)),
                hovertemplate="<b>Fundo:</b> %{text}<br><b>Local:</b> %{x:.2f} GDD<br><b>ERA5:</b> %{y:.2f} GDD<br><b>Fecha:</b> %{customdata}<extra></extra>",
                text=[fundo]*len(group),
                customdata=group['fecha']
            ))
        all_min = min(df_clean['GDD_seno_simple_local'].min(), df_clean['GDD_seno_simple_era5'].min())
        all_max = max(df_clean['GDD_seno_simple_local'].max(), df_clean['GDD_seno_simple_era5'].max())
        fig_era5_gdd_scatter.add_trace(go.Scatter(
            x=[all_min, all_max],
            y=[all_min, all_max],
            mode='lines',
            name='Identidad (y = x)',
            line=dict(color='black', dash='dash', width=1)
        ))
    fig_era5_gdd_scatter.update_layout(
        title="GDD Seno Simple: Local vs ERA5-Land (Diario)",
        xaxis_title="GDD Seno Simple Local Observado (°C-día)",
        yaxis_title="GDD Seno Simple ERA5-Land (°C-día)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig_era5_temp_scatter = go.Figure()
    if not df_era5_daily.empty:
        df_clean = df_era5_daily.dropna(subset=['temperatura_media_C_local', 'temperatura_media_C_era5'])
        colors = {"Lourdes": "#1f77b4", "Idahue": "#2ca02c", "Los Acacios": "#d62728", "Quebrada Seca": "#ff7f0e", "Mariposas": "#9467bd"}
        for fundo, group in df_clean.groupby("fundo"):
            fig_era5_temp_scatter.add_trace(go.Scatter(
                x=group['temperatura_media_C_local'],
                y=group['temperatura_media_C_era5'],
                mode='markers',
                name=fundo,
                marker=dict(size=6, opacity=0.6, color=colors.get(fundo)),
                hovertemplate="<b>Fundo:</b> %{text}<br><b>Local:</b> %{x:.2f} °C<br><b>ERA5:</b> %{y:.2f} °C<br><b>Fecha:</b> %{customdata}<extra></extra>",
                text=[fundo]*len(group),
                customdata=group['fecha']
            ))
        all_min = min(df_clean['temperatura_media_C_local'].min(), df_clean['temperatura_media_C_era5'].min())
        all_max = max(df_clean['temperatura_media_C_local'].max(), df_clean['temperatura_media_C_era5'].max())
        fig_era5_temp_scatter.add_trace(go.Scatter(
            x=[all_min, all_max],
            y=[all_min, all_max],
            mode='lines',
            name='Identidad (y = x)',
            line=dict(color='black', dash='dash', width=1)
        ))
    fig_era5_temp_scatter.update_layout(
        title="Temperatura Media Diaria: Local vs ERA5-Land",
        xaxis_title="Temperatura Media Local Observado (°C)",
        yaxis_title="Temperatura Media ERA5-Land (°C)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig_era5_ratio_bar = go.Figure()
    if not df_era5_metrics.empty:
        df_sorted = df_era5_metrics.sort_values("ratio_GDD")
        colors_bar = ["#1f77b4" if f == "Lourdes" else "#2ca02c" if f == "Idahue" else "#d62728" if f == "Los Acacios" else "#ff7f0e" if f == "Quebrada Seca" else "#9467bd" for f in df_sorted["fundo"]]
        fig_era5_ratio_bar.add_trace(go.Bar(
            x=df_sorted["fundo"],
            y=df_sorted["ratio_GDD"],
            marker_color=colors_bar,
            text=[f"{val:.3f}" for val in df_sorted["ratio_GDD"]],
            textposition='auto',
            hovertemplate="<b>Fundo:</b> %{x}<br><b>Ratio ERA5 / Local:</b> %{y:.3f}<extra></extra>"
        ))
        fig_era5_ratio_bar.add_shape(type="line",
            x0=-0.5, y0=1.0, x1=len(df_sorted)-0.5, y1=1.0,
            line=dict(color="red", width=1.5, dash="dash")
        )
    fig_era5_ratio_bar.update_layout(
        title="Sesgo Acumulado: Ratio GDD ERA5-Land / Local por Fundo",
        xaxis_title="Viñedo / Fundo",
        yaxis_title="Ratio GDD ERA5 / Local",
        template="plotly_white",
        yaxis=dict(range=[0.8, 1.35])
    )

    table_era5_metrics = df_to_html_table(df_era5_metrics)
    table_era5_elp = df_to_html_table(df_era5_elp)
    table_era5_decision = df_to_html_table(df_era5_decision)
    
    fig_html_era5_gdd = fig_to_html(fig_era5_gdd_scatter)
    fig_html_era5_temp = fig_to_html(fig_era5_temp_scatter)
    fig_html_era5_ratio = fig_to_html(fig_era5_ratio_bar)

    print("2/4 Generando gráficos interactivos e igualando 100% paridad funcional con Gradio...")
    
    # --- TAB 1: ESTADO DEL SISTEMA & CLIMA INTERACTIVO ---
    resumen_clim = climate.get("resumen", pd.DataFrame())
    fig_clim_status = climate_status_bar(resumen_clim)
    fig_clim_cov = coverage_bar(resumen_clim)
    table_master = df_to_html_table(climate.get("master", pd.DataFrame()))
    table_gaps = df_to_html_table(climate.get("gaps", pd.DataFrame()))
    table_equiv = df_to_html_table(climate.get("equivalencias", pd.DataFrame()))
    table_audit = df_to_html_table(state.get("audit", pd.DataFrame()))

    print("   -> Generando explorador climático interactivo (Tab 1)...")
    _catalog_stations = climate_catalog.get("stations", {})
    _sources = list(_catalog_stations.keys()) or ["Datavid"]
    _first_source = _sources[0]
    _first_stations = _catalog_stations.get(_first_source, [])
    _first_station = _first_stations[0] if _first_stations else ""
    _first_vars = get_climate_station_variables(_first_source, _first_station) if _first_station else []
    _first_var = _first_vars[0] if _first_vars else "Temp. Media [°C]"

    ts_source_options = "".join([f'<option value="{s}" {"selected" if s == _first_source else ""}>{s}</option>' for s in _sources])
    ts_station_options = "".join([f'<option value="{st}" {"selected" if st == _first_station else ""}>{st.replace("_", " ").title()}</option>' for st in _first_stations])
    ts_var_options = "".join([f'<option value="{v}" {"selected" if v == _first_var else ""}>{v}</option>' for v in _first_vars])
    ts_freq_options = '<option value="horaria" selected>Horaria</option><option value="diaria">Diaria</option>'

    # Pre-calcular mapa JS para menús en cascada y paneles TS
    catalog_js_map = {}
    ts_panels_html = ""
    for source in _sources:
        catalog_js_map[source] = {}
        stations = _catalog_stations.get(source, [])
        for st in stations:
            vars_avail = get_climate_station_variables(source, st) if st else []
            catalog_js_map[source][st] = vars_avail
            freqs = ["diaria"] if source == "INIA/Agromet" else ["horaria", "diaria"]
            for freq in freqs:
                freq_key = "daily" if freq == "diaria" else "hourly"
                df_clim = load_climate_station_series(source, st, freq_key) if st else pd.DataFrame()
                for var in vars_avail:
                    panel_id = f"ts_{clean_id(source)}_{clean_id(st)}_{clean_id(var)}_{freq}"
                    is_active = (source == _first_source and st == _first_station and var == _first_var and freq == ("diaria" if _first_source == "INIA/Agromet" else "horaria"))
                    disp = "block" if is_active else "none"
                    fig_ts = climate_timeseries_plot(df_clim, var, st, source, freq)
                    ts_panels_html += f'<div id="{panel_id}" class="ts-panel" style="display:{disp};">{fig_to_html(fig_ts)}</div>\n'

    # --- TAB 2: FENOLOGÍA & GDD ---
    # Sub-tab A
    diag_lat = gdd_latitudinal.get("diagnostico", pd.DataFrame())
    reg_lat = gdd_latitudinal.get("regresiones", {})
    fig_sub_a = latitudinal_regression_plot(diag_lat, reg_lat) if not diag_lat.empty else None
    cols_lat = [c for c in ["Fundo", "lat", "t0_operativo", "doy_t0_operativo", "fecha_brotacion", "doy_brotacion", "doy_brotacion_pred_reg_lat", "residuo_brotacion_latitud", "incluido_en_regresion"] if c in diag_lat.columns]
    table_sub_a = df_to_html_table(diag_lat[cols_lat] if not diag_lat.empty and cols_lat else diag_lat)

    # Sub-tab B: Valle Térmico (4 Dropdowns)
    print("   -> Generando paneles combinatorios de Valle Térmico (Tab 2B)...")
    bf_df = gdd.get("biofix_timeseries", pd.DataFrame())
    bf_sum = gdd.get("biofix_summary", pd.DataFrame())
    tv_df = gdd.get("thermal_valley", pd.DataFrame())
    bf_fundos = sorted(bf_df["fundo"].dropna().unique().tolist()) if not bf_df.empty else ["qba_seca"]
    bf_temps = sorted(bf_df["temporada"].dropna().unique().tolist()) if not bf_df.empty else ["2025_2026"]
    bf_vars = sorted(bf_df["variedad"].dropna().unique().tolist()) if not bf_df.empty else ["cabernet_sauvignon"]
    bf_tipos = sorted(bf_df["biofix_tipo"].dropna().unique().tolist()) if not bf_df.empty and "biofix_tipo" in bf_df.columns else ["15_julio", "1_agosto", "15_agosto", "1_septiembre"]

    default_fundo = "idahue" if "idahue" in bf_fundos else bf_fundos[0]
    default_temp = bf_temps[0] if bf_temps else ""
    default_var = bf_vars[0] if bf_vars else ""
    default_tipo = "1_agosto" if "1_agosto" in bf_tipos else bf_tipos[0]

    tv_fundo_options = "".join([f'<option value="{f}" {"selected" if f == default_fundo else ""}>{f.replace("_", " ").title()}</option>' for f in bf_fundos])
    tv_temp_options = "".join([f'<option value="{t}" {"selected" if t == default_temp else ""}>{t}</option>' for t in bf_temps])
    tv_var_options = "".join([f'<option value="{v}" {"selected" if v == default_var else ""}>{v.replace("_", " ").title()}</option>' for v in bf_vars])
    tv_tipo_options = "".join([f'<option value="{b}" {"selected" if b == default_tipo else ""}>{b.replace("_", " ").title()}</option>' for b in bf_tipos])

    tv_panels_html = ""
    for f in bf_fundos:
        for t in bf_temps:
            for v in bf_vars:
                for b in bf_tipos:
                    panel_id = f"tv_{clean_id(f)}_{clean_id(t)}_{clean_id(v)}_{clean_id(b)}"
                    is_active = (f == default_fundo and t == default_temp and v == default_var and b == default_tipo)
                    disp = "block" if is_active else "none"
                    fig_comb = gdd_biofix_timeseries_plot(bf_df, f, t, v, b) if not bf_df.empty else None
                    
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

                    tv_panels_html += f"""
                    <div id="{panel_id}" class="tv-panel" style="display:{disp};">
                        <div class="chart-box">{fig_to_html(fig_comb)}</div>
                        <h3>📋 Resumen Canónico de Valle Térmico y Alertas ({f.replace('_', ' ').title()} — {b.replace('_', ' ').title()})</h3>
                        {df_to_html_table(sub_sum)}
                        <h3>🏔️ Matriz de Diagnóstico Detallado</h3>
                        {df_to_html_table(sub_tv)}
                    </div>
                    """

    # Sub-tab C & D
    diag_cs = gdd.get("diagnostico_cs_reg", pd.DataFrame())
    fig_sub_c = panel_a_operativo_plot(diag_cs)
    fig_sub_d1 = panel_b_diagnostico_plot(diag_cs)
    fig_sub_d2 = baseline_comparison_plot(diag_cs)
    table_alert = df_to_html_table(cabernet_diagnostic_table(diag_cs))

    # Sub-tab E: Auditoría Varietal (2 Dropdowns)
    print("   -> Generando auditoría varietal con filtros (Tab 2E)...")
    resumen_t0 = gdd.get("resumen_t0", pd.DataFrame())
    fig_sub_e = phenology_error_plot(resumen_t0) if not resumen_t0.empty else None
    fundos_t0 = ["Todos"] + sorted(resumen_clim.get("fundo_normalizado", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    gdd_var_col = "Variedad" if "Variedad" in resumen_t0.columns else "variedad" if "variedad" in resumen_t0.columns else None
    vars_t0 = ["Todas"] + sorted(resumen_t0.get(gdd_var_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) if gdd_var_col else ["Todas"]

    t0_fundo_options = "".join([f'<option value="{f}" {"selected" if f == "Todos" else ""}>{f}</option>' for f in fundos_t0])
    t0_var_options = "".join([f'<option value="{v}" {"selected" if v == "Todas" else ""}>{v}</option>' for v in vars_t0])

    t0_panels_html = ""
    for f in fundos_t0:
        for v in vars_t0:
            panel_id = f"t0_{clean_id(f)}_{clean_id(v)}"
            is_active = (f == "Todos" and v == "Todas")
            disp = "block" if is_active else "none"
            sub_t0 = _filter_table(resumen_t0, f, v)
            t0_panels_html += f'<div id="{panel_id}" class="t0-panel" style="display:{disp};">{df_to_html_table(sub_t0)}</div>\n'

    table_pheno_manifest = df_to_html_table(phenology.get("prepared_manifest", pd.DataFrame()))

    # Sub-tab F
    chill_df = gdd.get("chill_dynamic", pd.DataFrame())
    fig_sub_f = panel_d_chill_plot(chill_df)
    table_chill_summary = df_to_html_table(panel_d_chill_table(chill_df))
    table_chill_full = df_to_html_table(chill_df)

    # --- TAB 3: MADUREZ TÉCNICA (4 Dropdowns) ---
    print("   -> Generando madurez técnica multi-parámetro (Tab 3)...")
    maturity_df = pd.concat([maturity.get("tintas_historicas", pd.DataFrame()), maturity.get("raw_2026", pd.DataFrame())], ignore_index=True, sort=False)
    maturity_technical = maturity.get("tecnica_canonica", pd.DataFrame())
    maturity_vars_choices = [
        (label, col) for label, col in [
            ("Brix [°Bx]", "brix"),
            ("pH", "pH"),
            ("Acidez Sulfúrica [g/L eq.]", "acidez_sulfurica"),
            ("Acidez Tartárica [g/L eq.]", "acidez_tartarica"),
            ("Peso de Baya [g]", "peso_baya"),
            ("Azúcar Real en Baya [g/baya]", "azucar_real_baya_g"),
        ] if col in maturity_technical.columns
    ]
    if not maturity_vars_choices:
        cols = find_columns(maturity_df, ["brix", "ph", "acidez", "peso", "azucar"]) or numeric_columns(maturity_df) or ["brix"]
        maturity_vars_choices = [(c, c) for c in cols]

    default_mat_col = maturity_vars_choices[0][1] if maturity_vars_choices else "brix"
    mat_fundos = _choices(maturity_technical, "fundo", "Todos")
    mat_vars = _choices(maturity_technical, "variedad", "Todas")
    mat_temps = _choices(maturity_technical, "temporada", "Todas las temporadas")

    mat_var_options = "".join([f'<option value="{col}" {"selected" if col == default_mat_col else ""}>{label}</option>' for label, col in maturity_vars_choices])
    mat_fundo_options = "".join([f'<option value="{f}" {"selected" if f == "Todos" else ""}>{f}</option>' for f in mat_fundos])
    mat_variedad_options = "".join([f'<option value="{v}" {"selected" if v == "Todas" else ""}>{v}</option>' for v in mat_vars])
    mat_temp_options = "".join([f'<option value="{t}" {"selected" if t == "Todas las temporadas" else ""}>{t}</option>' for t in mat_temps])

    mat_panels_html = ""
    for _, col in maturity_vars_choices:
        for f in mat_fundos:
            for v in mat_vars:
                for t in mat_temps:
                    panel_id = f"mat_{clean_id(col)}_{clean_id(f)}_{clean_id(v)}_{clean_id(t)}"
                    is_active = (col == default_mat_col and f == "Todos" and v == "Todas" and t == "Todas las temporadas")
                    disp = "block" if is_active else "none"
                    d = _filter_maturity(maturity_technical, v, f, t)
                    fig_mat = maturity_curve_grouped(d, col)
                    tbl_mat = prepare_maturity_traceability_table(d, col)
                    mat_panels_html += f"""
                    <div id="{panel_id}" class="mat-panel" style="display:{disp};">
                        <div class="chart-box">{fig_to_html(fig_mat)}</div>
                        <h3>📑 Trazabilidad Analítica de Controles (Cuartel y Muestras)</h3>
                        {df_to_html_table(tbl_mat)}
                    </div>
                    """

    # --- TAB 4: MADUREZ FENÓLICA (1 Dropdown) ---
    print("   -> Generando madurez fenólica (Tab 4)...")
    phenolic_df = pd.concat([luis.get("original_tintas", pd.DataFrame()), maturity.get("raw_2026", pd.DataFrame())], ignore_index=True, sort=False)
    phenolic_vars = find_columns(phenolic_df, ["antoc", "tanino", "fenol", "hplc", "uv"]) or numeric_columns(phenolic_df) or [""]
    default_phen_var = phenolic_vars[0] if phenolic_vars else ""

    phen_var_options = "".join([f'<option value="{v}" {"selected" if v == default_phen_var else ""}>{v}</option>' for v in phenolic_vars])
    phen_panels_html = ""
    for v in phenolic_vars:
        panel_id = f"phen_{clean_id(v)}"
        is_active = (v == default_phen_var)
        disp = "block" if is_active else "none"
        fig_phen = maturity_curve(phenolic_df, v, "Curva de madurez fenólica")
        phen_panels_html += f'<div id="{panel_id}" class="phen-panel" style="display:{disp};">{fig_to_html(fig_phen)}</div>\n'
    table_mat_fen = df_to_html_table(phenolic_df)

    # --- TAB 5: MODELOS (2 Dropdowns) ---
    print("   -> Generando modelos IA (Tab 5)...")
    metrics_rf = luis.get("metrics_rf", pd.DataFrame())
    metrics_pysr = luis.get("metrics_pysr", pd.DataFrame())
    model_metrics = pd.concat([metrics_rf, metrics_pysr], ignore_index=True, sort=False)
    model_targets = ["Todos"] + sorted(model_metrics.get("target_key", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    schemes = ["Todos"] + sorted(model_metrics.get("scheme", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())

    mod_target_options = "".join([f'<option value="{t}" {"selected" if t == "Todos" else ""}>{t}</option>' for t in model_targets])
    mod_scheme_options = "".join([f'<option value="{s}" {"selected" if s == "Todos" else ""}>{s}</option>' for s in schemes])

    mod_panels_html = ""
    for t in model_targets:
        for s in schemes:
            panel_id = f"mod_{clean_id(t)}_{clean_id(s)}"
            is_active = (t == "Todos" and s == "Todos")
            disp = "block" if is_active else "none"
            d = model_metrics.copy()
            if t != "Todos" and "target_key" in d.columns:
                d = d[d["target_key"] == t]
            if s != "Todos" and "scheme" in d.columns:
                d = d[d["scheme"] == s]
            preds = luis.get("predictions_rf", pd.DataFrame()).copy()
            if t != "Todos" and "target_key" in preds.columns:
                preds = preds[preds["target_key"] == t]
            fig_rank = metric_ranking(d)
            fig_pred = observed_vs_pred(preds)
            mod_panels_html += f"""
            <div id="{panel_id}" class="mod-panel" style="display:{disp};">
                <div class="grid-2">
                    <div><h3>Ranking por Error Absoluto Medio (MAE)</h3>{fig_to_html(fig_rank)}</div>
                    <div><h3>Observado vs Predicho (Random Forest)</h3>{fig_to_html(fig_pred)}</div>
                </div>
                <h3>📊 Tabla de Desempeño Multimodelo (MAE / R²)</h3>
                {df_to_html_table(d)}
            </div>
            """

    # --- TAB 6: INTERPRETABILIDAD ---
    fig_shap = importance_bar(luis.get("shap", pd.DataFrame()), "shap_mean_abs")
    fig_perm = importance_bar(luis.get("permutation", pd.DataFrame()), "perm_importance_mean")
    table_pysr = df_to_html_table(metrics_pysr)

    print("3/4 Empaquetando en plantilla HTML con 10 pestañas e interactividad total...")

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vendimia 5.0 — Dashboard Exploratorio Integrado Obj. 3 (Paridad 100%)</title>
    <!-- Plotly CDN -->
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        :root {{
            --wine-dark: #6B1D2F;
            --wine-primary: #802338;
            --wine-light: #A84259;
            --bg-page: #F8F9FA;
            --text-main: #2D3748;
            --border-color: #E2E8F0;
        }}
        body {{
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg-page);
            color: var(--text-main);
        }}
        header {{
            background: linear-gradient(135deg, var(--wine-dark), var(--wine-primary));
            color: white;
            padding: 1.8rem 2.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        header h1 {{ margin: 0; font-size: 1.9rem; font-weight: 700; }}
        header p {{ margin: 0.5rem 0 0; opacity: 0.92; font-size: 1.02rem; }}
        
        .nav-tabs {{
            display: flex;
            background: #2D3748;
            overflow-x: auto;
            padding: 0 1rem;
        }}
        .nav-tabs button {{
            background: inherit;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 1rem 1.4rem;
            transition: 0.2s;
            color: #CBD5E0;
            font-size: 0.95rem;
            font-weight: 600;
            white-space: nowrap;
            border-bottom: 3px solid transparent;
        }}
        .nav-tabs button:hover {{ color: white; background: #4A5568; }}
        .nav-tabs button.active {{ color: white; border-bottom: 3px solid #E2E8F0; background: var(--wine-primary); }}

        .sub-nav-tabs {{
            display: flex;
            background: #EDF2F7;
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 1.5rem;
            border-radius: 6px 6px 0 0;
            overflow-x: auto;
        }}
        .sub-nav-tabs button {{
            background: inherit;
            border: none;
            cursor: pointer;
            padding: 0.8rem 1.1rem;
            font-size: 0.88rem;
            font-weight: 600;
            color: #4A5568;
            border-bottom: 3px solid transparent;
            white-space: nowrap;
        }}
        .sub-nav-tabs button:hover {{ background: #E2E8F0; }}
        .sub-nav-tabs button.active {{ color: var(--wine-dark); border-bottom: 3px solid var(--wine-primary); background: white; }}

        .tab-content {{ display: none; padding: 2rem; max-width: 1450px; margin: 0 auto; }}
        .subtab-content {{ display: none; }}
        .subtab-content.active {{ display: block; }}

        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            padding: 1.8rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border-color);
        }}
        .card h2 {{ color: var(--wine-dark); margin-top: 0; border-bottom: 2px solid #EDF2F7; padding-bottom: 0.6rem; }}
        .card h3 {{ color: var(--wine-primary); margin-top: 1.5rem; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        @media (max-width: 1024px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

        .controls-bar {{
            background: #FFF5F5;
            padding: 1.4rem;
            border-radius: 8px;
            border: 1px solid #FEB2B2;
            margin-bottom: 1.8rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            align-items: center;
        }}
        .controls-bar label {{ font-weight: 700; color: var(--wine-dark); display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.9rem; }}
        .controls-bar select {{ padding: 0.6rem 1rem; border-radius: 6px; border: 1px solid #CBD5E0; font-weight: 600; font-size: 0.9rem; background: white; cursor: pointer; }}

        .table-container {{
            max-height: 450px;
            overflow: auto;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            margin-top: 1rem;
        }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
        .data-table th, .data-table td {{ padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); text-align: left; }}
        .data-table th {{ background: #EDF2F7; color: var(--wine-dark); position: sticky; top: 0; z-index: 10; }}
        .data-table tr:hover {{ background: #F7FAFC; }}
        .table-note {{ font-size: 0.8rem; color: #718096; margin-top: 0.5rem; }}

        .alert-warn {{
            background: #FFF5F5;
            border-left: 4px solid #E53E3E;
            padding: 1rem;
            margin-bottom: 1.5rem;
            border-radius: 4px;
        }}
        
        .status-table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        .status-table th, .status-table td {{ padding: 0.8rem; border: 1px solid var(--border-color); text-align: left; }}
        .status-table th {{ background: #EDF2F7; color: var(--wine-dark); }}
    </style>
</head>
<body>
    <header>
        <h1>🍇 Vendimia 5.0 — Explorador Técnico Objetivo 3</h1>
        <p><b>Flujo Técnico de Análisis y Trazabilidad:</b> Clima Fisiológico → Modelación Fenológica → Madurez Técnica/Fenólica → Modelos IA/RF/PySR → Referencia de Cosecha</p>
    </header>

    <div class="nav-tabs">
        <button class="tab-btn active" onclick="openTab(event, 'tab-estado')">📊 Estado del sistema</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-fenologia')">🌱 Fenología & GDD</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-mad-tec')">📈 Madurez técnica</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-mad-fen')">🍷 Madurez fenólica</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-modelos')">🤖 Modelos</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-interpretacion')">🧠 Interpretabilidad agronómica</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-satelital')">🛰️ Validación Satelital ERA5-Land (vinewise-rs)</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-integracion')">🔗 Integración conceptual</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-trazabilidad')">📑 Trazabilidad CORFO</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-ayuda')">ℹ️ Ayuda & Documentación</button>
    </div>

    <!-- PESTAÑA 1: ESTADO DEL SISTEMA -->
    <div id="tab-estado" class="tab-content" style="display: block;">
        <div class="card">
            <h2>🏛️ Matriz General de Dependencias e Ingesta</h2>
            <table class="status-table">
                <thead><tr><th>Componente</th><th>Estado Operacional</th><th>Archivo Canónico / Fuente</th></tr></thead>
                <tbody>
                    <tr><td><b>Clima</b></td><td>🟢 CERRADO</td><td><code>consolidado_fenologia_ELP_OBJ3_INDICES_BIOCLIMATICOS.csv</code></td></tr>
                    <tr><td><b>Fenología</b></td><td>🟢 CERRADO</td><td><code>consolidado_fenologia_ELP_MODELABLE_FULL_v1.csv</code></td></tr>
                    <tr><td><b>Madurez Técnica</b></td><td>🟢 CERRADO</td><td><code>madurez_tecnica_2025_2026_train_test_CANONICO_V5_INDICES_ORIGINALES.csv</code></td></tr>
                    <tr><td><b>Madurez Fenólica</b></td><td>🟡 EN PROGRESO</td><td>Bloqueado por resultados lab 2026</td></tr>
                    <tr><td><b>Modelos (Baseline)</b></td><td>🟢 CERRADO</td><td><code>run_pipeline_v2.py</code> ejecutado y métricas consolidadas</td></tr>
                    <tr><td><b>Export INRIA</b></td><td>🟡 EN ESPERA</td><td><code>paquete_luis_inria_fenologia_ELP_OBJ3_CLEAN_2.zip</code></td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>🌡️ Series Temporales Climáticas — Explorador Horario/Diario</h2>
            <p>Selecciona fuente, estación y variable para inspeccionar dinámicamente las series:</p>
            <div class="controls-bar">
                <label><span>🌐 Fuente:</span><select id="ts-source-select" onchange="onTSSourceChange()">{ts_source_options}</select></label>
                <label><span>📍 Estación / Fuente Climática:</span><select id="ts-station-select" onchange="onTSStationChange()">{ts_station_options}</select></label>
                <label><span>📊 Variable Climática:</span><select id="ts-var-select" onchange="updateTSPanel()">{ts_var_options}</select></label>
                <label><span>⏱️ Frecuencia:</span><select id="ts-freq-select" onchange="updateTSPanel()">{ts_freq_options}</select></label>
            </div>
            {ts_panels_html}
        </div>

        <div class="card">
            <h2>🗂️ Auditoría de Cobertura Climática por Fundo</h2>
            <p>Ingesta climática operacional consolidada hasta Octubre 2025. Los sensores horarios de frío invernal cortan en Junio 2025.</p>
            <div class="grid-2">
                <div>{fig_to_html(fig_clim_status)}</div>
                <div>{fig_to_html(fig_clim_cov)}</div>
            </div>
        </div>
        <div class="card">
            <h2>🗃️ Catálogo Maestro Regional (Fundo - Estación - Fuente - Temporada)</h2>
            {table_master}
        </div>
        <div class="card">
            <h2>🕳️ Detección de Gaps Horarios por Fundo</h2>
            {table_gaps}
        </div>
        <div class="card">
            <h2>🔄 Equivalencias Homologadas y Auditoría</h2>
            <div class="grid-2">
                <div><h3>Equivalencias</h3>{table_equiv}</div>
                <div><h3>Auditoría del Sistema</h3>{table_audit}</div>
            </div>
        </div>
    </div>

    <!-- PESTAÑA 2: FENOLOGÍA & GDD -->
    <div id="tab-fenologia" class="tab-content">
        <div class="alert-warn">
            <b>⚠️ CRITERIO METODOLÓGICO:</b> El <b>T0 Cerrado</b> es un indicador de diagnóstico retrospectivo (*leakage* histórico); el <b>T0 Latitudinal</b> es el biofix predictivo operacional candidato a producción.
        </div>

        <div class="sub-nav-tabs">
            <button class="subtab-btn active" onclick="openSubTab(event, 'sub-feno-a')">A. Curva Latitudinal T0 / Brotación</button>
            <button class="subtab-btn" onclick="openSubTab(event, 'sub-feno-b')">B. Valle Térmico y Auditoría</button>
            <button class="subtab-btn" onclick="openSubTab(event, 'sub-feno-c')">C. Evaluación Operacional T0 Latitudinal</button>
            <button class="subtab-btn" onclick="openSubTab(event, 'sub-feno-d')">D. Diagnóstico de Leakage</button>
            <button class="subtab-btn" onclick="openSubTab(event, 'sub-feno-e')">E. Auditoría Varietal</button>
            <button class="subtab-btn" onclick="openSubTab(event, 'sub-feno-f')">F. Plausibilidad Fisiológica (Frío)</button>
        </div>

        <div id="sub-feno-a" class="subtab-content active">
            <div class="card">
                <h2>📈 A. Curva Latitudinal T0 / Brotación</h2>
                <p>Auditoría espacial del gradiente fenológico con equivalencias en fechas calendario reales.</p>
                {fig_to_html(fig_sub_a)}
                <h3>📋 Tabla de Diagnóstico por Fundo (Cabernet Sauvignon 2025–2026)</h3>
                {table_sub_a}
            </div>
        </div>

        <div id="sub-feno-b" class="subtab-content">
            <div class="card">
                <h2>🏔️ B. Valle Térmico y Auditoría de Fecha de Inicio (Multi-Filtro)</h2>
                <p>Selecciona viñedo, temporada, variedad y fecha candidata para auditar la actividad térmica:</p>
                <div class="controls-bar">
                    <label><span>📍 Viñedo / Fundo:</span><select id="tv-fundo-select" onchange="updateTVPanel()">{tv_fundo_options}</select></label>
                    <label><span>📅 Temporada:</span><select id="tv-temp-select" onchange="updateTVPanel()">{tv_temp_options}</select></label>
                    <label><span>🍇 Variedad:</span><select id="tv-var-select" onchange="updateTVPanel()">{tv_var_options}</select></label>
                    <label><span>📌 Fecha Candidata Auditada:</span><select id="tv-biofix-select" onchange="updateTVPanel()">{tv_tipo_options}</select></label>
                </div>
                {tv_panels_html}
            </div>
        </div>

        <div id="sub-feno-c" class="subtab-content">
            <div class="card">
                <h2>📐 C. Evaluación Operacional (Residuo T0 Latitudinal)</h2>
                {fig_to_html(fig_sub_c)}
            </div>
        </div>

        <div id="sub-feno-d" class="subtab-content">
            <div class="card">
                <h2>🔍 D. Diagnóstico de Leakage (T0 Cerrado vs Latitudinal)</h2>
                <div class="grid-2">
                    <div><h3>Concordancia Diagnóstico vs Retrospectivo</h3>{fig_to_html(fig_sub_d1)}</div>
                    <div><h3>Comparación de Errores Absolutos Medios (MAE)</h3>{fig_to_html(fig_sub_d2)}</div>
                </div>
                <h3>📋 Matriz de Diagnóstico y Alertas de Leakage (Cabernet Sauvignon)</h3>
                {table_alert}
            </div>
        </div>

        <div id="sub-feno-e" class="subtab-content">
            <div class="card">
                <h2>📂 E. Auditoría Varietal Heredada del Pipeline</h2>
                {fig_to_html(fig_sub_e)}
                <h3>Resumen T0 Varietal (Filtrable)</h3>
                <div class="controls-bar">
                    <label><span>📍 Viñedo / Fundo:</span><select id="t0-fundo-select" onchange="updateT0Panel()">{t0_fundo_options}</select></label>
                    <label><span>🍇 Variedad:</span><select id="t0-var-select" onchange="updateT0Panel()">{t0_var_options}</select></label>
                </div>
                {t0_panels_html}
                <h3>🧬 Registro de Matrices Emparejadas (Fenología + Clima)</h3>
                {table_pheno_manifest}
            </div>
        </div>

        <div id="sub-feno-f" class="subtab-content">
            <div class="card">
                <h2>❄️ F. Plausibilidad Fisiológica (Frío Invernal)</h2>
                <p>Auditoría fisiológica de compensación Chilling-Forcing en series subestacionales.</p>
                {fig_to_html(fig_sub_f)}
                <h3>🏷️ Semáforo de Plausibilidad Bioclimática por Fundo</h3>
                {table_chill_summary}
                <h3>📑 Detalle Analítico de Calor Disponible (GDD Mayo — Septiembre)</h3>
                {table_chill_full}
            </div>
        </div>
    </div>

    <!-- PESTAÑA 3: MADUREZ TÉCNICA -->
    <div id="tab-mad-tec" class="tab-content">
        <div class="card">
            <h2>📈 Madurez Técnica — Evolución Canónica por Viñedo (Multi-Parámetro)</h2>
            <div class="controls-bar">
                <label><span>🧪 Parámetro Enológico / Target:</span><select id="mat-var-select" onchange="updateMatPanel()">{mat_var_options}</select></label>
                <label><span>📍 Viñedo / Fundo:</span><select id="mat-fundo-select" onchange="updateMatPanel()">{mat_fundo_options}</select></label>
                <label><span>🍇 Variedad:</span><select id="mat-variedad-select" onchange="updateMatPanel()">{mat_variedad_options}</select></label>
                <label><span>📅 Temporada:</span><select id="mat-temp-select" onchange="updateMatPanel()">{mat_temp_options}</select></label>
            </div>
            {mat_panels_html}
        </div>
    </div>

    <!-- PESTAÑA 4: MADUREZ FENÓLICA -->
    <div id="tab-mad-fen" class="tab-content">
        <div class="card">
            <h2>🍷 Madurez Fenólica — Curvas HPLC y Color</h2>
            <div class="controls-bar">
                <label><span>🧪 Compuesto Fenólico:</span><select id="phen-var-select" onchange="updatePhenPanel()">{phen_var_options}</select></label>
            </div>
            {phen_panels_html}
            <h3>Registros Analíticos Tintas y HPLC</h3>
            {table_mat_fen}
        </div>
    </div>

    <!-- PESTAÑA 5: MODELOS -->
    <div id="tab-modelos" class="tab-content">
        <div class="card">
            <h2>🤖 Evaluación de Modelos Predictivos (RF vs PySR/SR)</h2>
            <div class="controls-bar">
                <label><span>🎯 Variable Objetivo (Target):</span><select id="mod-target-select" onchange="updateModPanel()">{mod_target_options}</select></label>
                <label><span>⚙️ Esquema de Validación:</span><select id="mod-scheme-select" onchange="updateModPanel()">{mod_scheme_options}</select></label>
            </div>
            {mod_panels_html}
        </div>
    </div>

    <!-- PESTAÑA 6: INTERPRETABILIDAD -->
    <div id="tab-interpretacion" class="tab-content">
        <div class="card">
            <h2>🧠 Interpretabilidad Agronómica de Modelos</h2>
            <div class="grid-2">
                <div><h3>Importancia SHAP (Media Absoluta)</h3>{fig_to_html(fig_shap)}</div>
                <div><h3>Importancia por Permutación</h3>{fig_to_html(fig_perm)}</div>
            </div>
            <h3>Métricas Regresión Simbólica (PySR/SR)</h3>
            {table_pysr}
        </div>
    </div>

    <!-- PESTAÑA 7: VALIDACION SATELITAL ERA5-LAND (vinewise-rs) -->
    <div id="tab-satelital" class="tab-content">
        <div class="card" style="border-left: 5px solid #3b82f6; background-color: #f0f7ff; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;">
            <h2 style="color: #1e3a8a; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;"><i class="fa-solid fa-satellite"></i> Contexto Estratégico CII - Viña Concha y Toro</h2>
            <p style="font-size: 1.05rem; line-height: 1.6; color: #1e293b; margin-bottom: 1rem;">
                <strong>¿Por qué evaluamos ERA5-Land?</strong> La falta de estaciones meteorológicas físicas y los vacíos operacionales de datos (gaps) en ciertos viñedos de Concha y Toro limitan la expansión de modelos predictivos. El reanálisis satelital <strong>ERA5-Land</strong> de la ECMWF provee una resolución espacial fina (~9 km) y temporal horaria continua. Esta validación evalúa la viabilidad del reanálisis satelital como fuente agrometeorológica alternativa y robusta para resolver los gaps de datos históricos y habilitar la <strong>escalabilidad territorial</strong> de los modelos predictivos del Objetivo 3 a nivel nacional.
            </p>
            <p style="font-size: 0.95rem; color: #475569; font-style: italic; margin: 0;">
                Norma del Centro de Investigación e Innovación (CII): Cero datos sintéticos. Todos los datos representados son históricos observados en terreno y reanálisis físicos validados objetivamente.
            </p>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>📈 Validación Diaria: GDD Local vs ERA5-Land</h2>
                <p>Comparación directa punto a punto entre la red local de estaciones del viñedo y la celda satelital ERA5-Land correspondiente (GDD Seno Simple diario).</p>
                {fig_html_era5_gdd}
            </div>
            <div class="card">
                <h2>🌡️ Temperatura Media Diaria: Ajuste Térmico</h2>
                <p>Correlación directa de temperatura media. Muestra una señal térmica diaria altamente robusta en todos los viñedos evaluados.</p>
                {fig_html_era5_temp}
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>📊 Sesgo Acumulado (Ratio GDD ERA5 / Local)</h2>
                <p>El sesgo de acumulación térmica no es uniforme entre fundos, variando entre <strong>0.960</strong> (Mariposas) y <strong>1.251</strong> (Los Acacios). Esto fundamenta la necesidad de correcciones locales por viñedo.</p>
                {fig_html_era5_ratio}
            </div>
            <div class="card">
                <h2>📋 Métricas de Desempeño por Fundo (ERA5-Land vs Local)</h2>
                <p>Resumen multisitio de la corrida piloto en 5 fundos.</p>
                {table_era5_metrics}
            </div>
        </div>

        <div class="card">
            <h2>🌱 Impacto en Modelación Fenológica (Baseline GDD/ELP)</h2>
            <p>Comparación de la precisión fenológica (exactitud en escala ELP) utilizando umbrales GDD locales versus ERA5-Land en validación cruzada LOFO (Leave-One-Fundo-Out).</p>
            {table_era5_elp}
        </div>

        <div class="card">
            <h2>🎯 Matriz de Decisiones y Viabilidad Operativa (vinewise-rs)</h2>
            <p>Evaluación técnica de viabilidad por línea de trabajo para integración final en el Objetivo 3.</p>
            {table_era5_decision}
        </div>
    </div>

    <!-- PESTAÑA 8: INTEGRACIÓN CONCEPTUAL -->
    <div id="tab-integracion" class="tab-content">
        <div class="card">
            <h2>🔗 Cadena Metodológica Objetivo 3 (Vendimia 5.0)</h2>
            <ol style="line-height: 2.2; font-size: 1.05rem;">
                <li><b>Clima:</b> tabla maestra por fundo, estación, fuente, gaps y calidad.</li>
                <li><b>Fenología:</b> brotación, ELP observado, DOY, t0 estimado y GDD acumulado.</li>
                <li><b>Madurez técnica:</b> Brix, pH, acidez y peso de baya cuando existan.</li>
                <li><b>Madurez fenólica:</b> antocianinas, taninos y compuestos HPLC/UV-Vis cuando existan.</li>
                <li><b>Modelos:</b> RF y PySR/SR con CV5, LOFO, predicción vs observado e interpretabilidad.</li>
                <li><b>Decisión de cosecha:</b> etapa de QA científico-técnico previo a producción territorial.</li>
            </ol>
            <h3>🗃️ Matriz Consolidada Multi-Origen</h3>
            {table_master}
        </div>
    </div>

    <!-- PESTAÑA 8: TRAZABILIDAD CORFO -->
    <div id="tab-trazabilidad" class="tab-content">
        <div class="card">
            <h2>🏛️ Seguimiento Curricular de Hitos y Entregables CORFO</h2>
            <table class="status-table">
                <thead><tr><th>Actividad</th><th>Entregable Técnico</th><th>Estado Actual</th><th>Bloqueo o Próximo Hito</th></tr></thead>
                <tbody>
                    <tr><td><b>Act. 16</b></td><td>Proyecciones Agrometeorológicas</td><td>🟡 PARCIAL</td><td>Operacional con clima histórico. Pendiente acoplar pronósticos GFS a 15 días.</td></tr>
                    <tr><td><b>Act. 17</b></td><td>Modelo Fenológico ELP</td><td>🟢 CERRADO</td><td>Dataset FULL_v1 validado. Esperando modelo final INRIA para evaluación LOFO.</td></tr>
                    <tr><td><b>Act. 18/19</b></td><td>Monitoreo de Madurez en Viñedo</td><td>🟡 EN PROGRESO</td><td>Curvas técnicas 25/26 OK. Fenólica histórica OK, esperando laboratorio 2026.</td></tr>
                    <tr><td><b>Act. 20</b></td><td>IA Predictiva de Cosecha</td><td>🟢 CERRADO</td><td>Pipeline <code>v2</code> empaquetado y verificado con métricas satisfactorias.</td></tr>
                    <tr><td><b>Act. 21</b></td><td>Optimización Multiobjetivo Bodega</td><td>🔴 NO INICIADO</td><td>Requiere parametrizar función de costos con dirección enológica.</td></tr>
                    <tr><td><b>Act. 22</b></td><td>Validación Sensorial en Bodega</td><td>⚪ PENDIENTE</td><td>Subordinado a ventanas de cosecha resultantes de Act. 21.</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- PESTAÑA 9: AYUDA & DOCUMENTACIÓN -->
    <div id="tab-ayuda" class="tab-content">
        <div class="card">
            <h2>📘 Manual Operativo del Repositorio Limpio</h2>
            <ol style="line-height: 2.2; font-size: 1.05rem;">
                <li><b>Inmutabilidad de SharePoint (<code>data/all_project/</code>):</b> <b>🚫 INTOCABLE.</b> Directorio espejo en modo lectura estricta.</li>
                <li><b>Ejecución de Pipeline:</b> Para re-entrenar modelos base, invoca <code>python src/modeling/internal_baseline_v2/run_pipeline_v2.py</code>.</li>
                <li><b>Lanzador Local:</b> Abre <code>ABRIR_DASHBOARD.bat</code> o navega a <code>ACCESO_DASHBOARD.html</code> (para versión Gradio), o abre directamente <code>reports/dashboards_html/index.html</code> (Suite HTML).</li>
                <li><b>Marco Técnico del Proyecto (CORFO):</b> Consulta <code>docs/objetivo_3_vendimia_5_0.md</code> para entender el flujo científico completo del Objetivo 3.</li>
                <li><b>Contacto técnico:</b> Diego Núñez — análisis de datos, modelamiento y trazabilidad del Objetivo 3.</li>
            </ol>
        </div>
    </div>

    <script>
        const catalogMap = {json.dumps(catalog_js_map)};

        function cleanId(val) {{
            return String(val).replace(/ /g, '_').replace(/\\//g, '_').replace(/\\./g, '_').replace(/-/g, '_').replace(/°/g, '').replace(/\\[/g, '').replace(/\\]/g, '').toLowerCase();
        }}

        function triggerPlotlyResize() {{
            setTimeout(() => {{
                window.dispatchEvent(new Event('resize'));
                document.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (el.offsetParent !== null && window.Plotly) {{
                        Plotly.Plots.resize(el);
                    }}
                }});
            }}, 50);
        }}

        function openTab(evt, tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).style.display = 'block';
            evt.currentTarget.classList.add('active');
            triggerPlotlyResize();
        }}

        function openSubTab(evt, subtabId) {{
            document.querySelectorAll('.subtab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.subtab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(subtabId).classList.add('active');
            evt.currentTarget.classList.add('active');
            triggerPlotlyResize();
        }}

        function onTSSourceChange() {{
            const source = document.getElementById('ts-source-select').value;
            const stationSelect = document.getElementById('ts-station-select');
            const freqSelect = document.getElementById('ts-freq-select');
            
            stationSelect.innerHTML = '';
            const stations = Object.keys(catalogMap[source] || {{}});
            stations.forEach(st => {{
                const opt = document.createElement('option');
                opt.value = st;
                opt.text = st.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                stationSelect.appendChild(opt);
            }});

            if (source === 'INIA/Agromet') {{
                freqSelect.innerHTML = '<option value="diaria" selected>Diaria</option>';
            }} else {{
                freqSelect.innerHTML = '<option value="horaria" selected>Horaria</option><option value="diaria">Diaria</option>';
            }}
            onTSStationChange();
        }}

        function onTSStationChange() {{
            const source = document.getElementById('ts-source-select').value;
            const st = document.getElementById('ts-station-select').value;
            const varSelect = document.getElementById('ts-var-select');
            
            varSelect.innerHTML = '';
            const vars = (catalogMap[source] && catalogMap[source][st]) || [];
            vars.forEach(v => {{
                const opt = document.createElement('option');
                opt.value = v;
                opt.text = v;
                varSelect.appendChild(opt);
            }});
            updateTSPanel();
        }}

        function updateTSPanel() {{
            const source = document.getElementById('ts-source-select').value;
            const st = document.getElementById('ts-station-select').value;
            const varName = document.getElementById('ts-var-select').value;
            const freq = document.getElementById('ts-freq-select').value;
            
            document.querySelectorAll('.ts-panel').forEach(el => el.style.display = 'none');
            const targetId = 'ts_' + cleanId(source) + '_' + cleanId(st) + '_' + cleanId(varName) + '_' + freq;
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
                target.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (window.Plotly) Plotly.Plots.resize(el);
                }});
            }}
        }}

        function updateTVPanel() {{
            const f = document.getElementById('tv-fundo-select').value;
            const t = document.getElementById('tv-temp-select').value;
            const v = document.getElementById('tv-var-select').value;
            const b = document.getElementById('tv-biofix-select').value;
            
            document.querySelectorAll('.tv-panel').forEach(el => el.style.display = 'none');
            const targetId = 'tv_' + cleanId(f) + '_' + cleanId(t) + '_' + cleanId(v) + '_' + cleanId(b);
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
                target.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (window.Plotly) Plotly.Plots.resize(el);
                }});
            }}
        }}

        function updateT0Panel() {{
            const f = document.getElementById('t0-fundo-select').value;
            const v = document.getElementById('t0-var-select').value;
            document.querySelectorAll('.t0-panel').forEach(el => el.style.display = 'none');
            const targetId = 't0_' + cleanId(f) + '_' + cleanId(v);
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
            }}
        }}

        function updateMatPanel() {{
            const col = document.getElementById('mat-var-select').value;
            const f = document.getElementById('mat-fundo-select').value;
            const v = document.getElementById('mat-variedad-select').value;
            const t = document.getElementById('mat-temp-select').value;
            
            document.querySelectorAll('.mat-panel').forEach(el => el.style.display = 'none');
            const targetId = 'mat_' + cleanId(col) + '_' + cleanId(f) + '_' + cleanId(v) + '_' + cleanId(t);
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
                target.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (window.Plotly) Plotly.Plots.resize(el);
                }});
            }}
        }}

        function updatePhenPanel() {{
            const v = document.getElementById('phen-var-select').value;
            document.querySelectorAll('.phen-panel').forEach(el => el.style.display = 'none');
            const targetId = 'phen_' + cleanId(v);
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
                target.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (window.Plotly) Plotly.Plots.resize(el);
                }});
            }}
        }}

        function updateModPanel() {{
            const t = document.getElementById('mod-target-select').value;
            const s = document.getElementById('mod-scheme-select').value;
            document.querySelectorAll('.mod-panel').forEach(el => el.style.display = 'none');
            const targetId = 'mod_' + cleanId(t) + '_' + cleanId(s);
            const target = document.getElementById(targetId);
            if (target) {{
                target.style.display = 'block';
                target.querySelectorAll('.js-plotly-plot').forEach(el => {{
                    if (window.Plotly) Plotly.Plots.resize(el);
                }});
            }}
        }}
    </script>
</body>
</html>
"""

    print("4/4 Escribiendo archivo HTML final...")
    out_path = root_dir / "reports" / "dashboards_html" / "visor_obj3.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")
    print(f"[OK] Visor Obj3 HTML (Paridad 100%) generado exitosamente en: {out_path}")

if __name__ == "__main__":
    build_complete_html_dashboard()
