import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

def compute_metrics(y_true, y_pred, name):
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    if len(y_true) == 0:
        return {"Proxy": name, "RMSE": 0, "MAE": 0, "R2": 0}
        
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"Proxy": name, "RMSE": rmse, "MAE": mae, "R2": r2}

def generate_report():
    base_dir = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly")
    
    # Paths
    path_pencahue_inia = base_dir / "inia_proxy_test" / "pencahue" / "climate_hourly.parquet"
    path_san_clemente_inia = base_dir / "inia_proxy_test" / "san_clemente" / "climate_hourly.parquet"
    path_pencahue_era5 = base_dir / "era5" / "pencahue" / "climate_hourly.parquet"
    path_pencahue_agro = base_dir / "agromet_pencahue" / "climate_hourly.parquet"
    
    # Load
    df_p = pd.read_parquet(path_pencahue_inia).rename(columns={'tempMedia': 'Pencahue_INIA'})
    df_sc = pd.read_parquet(path_san_clemente_inia).rename(columns={'tempMedia': 'San_Clemente_INIA'})
    df_era5 = pd.read_parquet(path_pencahue_era5).rename(columns={'tempMedia': 'ERA5_Land'})
    df_agro = pd.read_parquet(path_pencahue_agro).rename(columns={'tempMedia': 'Pencahue_Agromet'})
    
    # Ensure naive datetime
    for df in [df_p, df_sc, df_era5, df_agro]:
        if df['fecha_hora'].dt.tz is not None:
            df['fecha_hora'] = df['fecha_hora'].dt.tz_localize(None)
            
    # Merge
    df_merged = df_p.merge(df_sc, on='fecha_hora', how='inner')
    df_merged = df_merged.merge(df_era5, on='fecha_hora', how='inner')
    df_merged = df_merged.merge(df_agro, on='fecha_hora', how='inner')
    
    df_merged = df_merged.dropna()
    
    # Metrics
    metrics_sc = compute_metrics(df_merged['Pencahue_INIA'], df_merged['San_Clemente_INIA'], "San Clemente INIA")
    metrics_agro = compute_metrics(df_merged['Pencahue_INIA'], df_merged['Pencahue_Agromet'], "Pencahue Agromet")
    metrics_era5 = compute_metrics(df_merged['Pencahue_INIA'], df_merged['ERA5_Land'], "ERA5-Land")
    
    df_metrics = pd.DataFrame([metrics_sc, metrics_agro, metrics_era5])
    
    # Create subplots:
    # Top left: Scatter SC vs P
    # Top right: Scatter Agro vs P
    # Middle left: Scatter ERA5 vs P
    # Middle right: Bar charts for metrics
    # Bottom: Time series snippet (last 7 days of overlap)
    
    fig = make_subplots(
        rows=3, cols=2,
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "scatter", "colspan": 2}, None]
        ],
        subplot_titles=(
            "San Clemente INIA vs Pencahue INIA",
            "Pencahue Agromet vs Pencahue INIA",
            "ERA5-Land vs Pencahue INIA",
            "Métricas de Error (R2, RMSE, MAE)",
            "Series de Tiempo (Últimos 14 días)"
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Helper to add 1:1 line
    def add_scatter_with_identity(col_pred, row, col):
        fig.add_trace(
            go.Scatter(x=df_merged['Pencahue_INIA'], y=df_merged[col_pred],
                       mode='markers', marker=dict(size=3, opacity=0.3),
                       name=col_pred, showlegend=False),
            row=row, col=col
        )
        min_val = df_merged['Pencahue_INIA'].min()
        max_val = df_merged['Pencahue_INIA'].max()
        fig.add_trace(
            go.Scatter(x=[min_val, max_val], y=[min_val, max_val],
                       mode='lines', line=dict(color='black', dash='dash'),
                       name="Identidad", showlegend=False),
            row=row, col=col
        )
        fig.update_xaxes(title_text="Pencahue INIA (°C)", row=row, col=col)
        fig.update_yaxes(title_text=col_pred + " (°C)", row=row, col=col)

    # Scatters
    add_scatter_with_identity('San_Clemente_INIA', 1, 1)
    add_scatter_with_identity('Pencahue_Agromet', 1, 2)
    add_scatter_with_identity('ERA5_Land', 2, 1)
    
    # Bar Chart for metrics
    fig.add_trace(
        go.Bar(name='R2', x=df_metrics['Proxy'], y=df_metrics['R2'], marker_color='rgb(55, 83, 109)'),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(name='RMSE (°C)', x=df_metrics['Proxy'], y=df_metrics['RMSE'], marker_color='rgb(26, 118, 255)'),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(name='MAE (°C)', x=df_metrics['Proxy'], y=df_metrics['MAE'], marker_color='rgb(255, 127, 14)'),
        row=2, col=2
    )
    
    # Time series snippet
    df_snip = df_merged.tail(24 * 14) # Last 14 days
    
    fig.add_trace(
        go.Scatter(x=df_snip['fecha_hora'], y=df_snip['Pencahue_INIA'], name='Real (Pencahue INIA)', line=dict(color='black', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df_snip['fecha_hora'], y=df_snip['San_Clemente_INIA'], name='Proxy San Clemente', line=dict(color='blue', dash='dot')),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df_snip['fecha_hora'], y=df_snip['Pencahue_Agromet'], name='Proxy Pencahue Agromet', line=dict(color='orange', dash='dash')),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df_snip['fecha_hora'], y=df_snip['ERA5_Land'], name='Proxy ERA5-Land', line=dict(color='red', dash='dash')),
        row=3, col=1
    )
    
    fig.update_layout(
        title="Evaluación de Proxies Climáticos para Pencahue (Lourdes)",
        height=1000,
        width=1200,
        barmode='group',
        hovermode="x unified",
        template="plotly_white"
    )
    
    out_html = Path(r"C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\proxy_test_pencahue.html")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_html)
    print(f"HTML generado en {out_html}")

if __name__ == "__main__":
    generate_report()
