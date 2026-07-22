import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

def generate_dashboard():
    results_path = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\lmm_lofo_results.csv")
    preds_dir = Path(r"C:\projects\vendimia_5_0_obj3_clean\data\processed\lmm_preds")
    
    if not results_path.exists():
        print("Results file not found. Run train_lmm_maturity.py first.")
        return
        
    df_res = pd.read_csv(results_path)
    
    # Colores por target
    color_map = {
        'brix': '#10b981',
        'pH': '#f59e0b',
        'acidez_tartarica': '#3b82f6',
        'peso_baya': '#8b5cf6'
    }
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>LMM Maturity Predictors - Objective 3</title>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            :root { --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0; --accent: #38bdf8; }
            body { font-family: 'Inter', sans-serif; background-color: var(--bg); color: var(--text); padding: 20px; }
            h1, h2 { text-align: center; color: var(--accent); }
            .container { max-width: 1200px; margin: 0 auto; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .panel { background: var(--panel); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            .summary { background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #10b981; margin-bottom:20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Transición a Modelos Lineales Mixtos (LMM)</h1>
            <div class="summary">
                <p><strong>Hipótesis Validada (Validación LOFO - Leave-One-Fundo-Out):</strong></p>
                <p>El modelo LMM confirma que <b>Brix</b> es térmicamente robusto y generaliza de manera excelente a fundos no vistos, especialmente al usar acumuladores como <b>GDA</b> o <b>BEDD_acum</b>. En contraste, el <b>Peso de Baya</b> se desploma, ratificando que obedece a manejo cultural y no a clima termodinámico.</p>
            </div>
            
            <h2>Comparativa R² por Predictor y Target</h2>
            <div class="panel" id="bar_plot"></div>
            
            <h2>Rendimiento Detallado (MAE)</h2>
            <div class="panel" id="mae_plot"></div>
            
            <h2>Criterio de Información de Akaike (AIC Global)</h2>
            <div class="panel" id="aic_plot"></div>
            
            <h2>Correlación LMM (LOFO): Brix vs GDA</h2>
            <div class="panel" id="scatter_brix"></div>
            
        </div>
        <script>
    """
    
    # 1. Bar Plot of R2
    fig_r2 = px.bar(
        df_res, x='Target', y='R2_LOFO', color='Predictor', barmode='group',
        title="R² LOFO Score por Target y Predictor (Mayor es mejor)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_r2.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    
    # 2. Bar plot of MAE
    fig_mae = px.bar(
        df_res, x='Target', y='MAE_LOFO', color='Predictor', barmode='group',
        title="Error Absoluto Medio (MAE) LOFO (Menor es mejor)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_mae.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')

    # 3. Bar plot of AIC
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            import numpy as np
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    if 'AIC_Global' in df_res.columns:
        fig_aic = px.bar(
            df_res, x='Target', y='AIC_Global', color='Predictor', barmode='group',
            title="Akaike Information Criterion (AIC) Global (Menor es mejor)",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_aic.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        
        html_content += f"var aic_data = {json.dumps(fig_aic.to_dict(), cls=NumpyEncoder)};\n"
        html_content += f"Plotly.newPlot('aic_plot', aic_data.data, aic_data.layout);\n"
    
    html_content += f"var r2_data = {json.dumps(fig_r2.to_dict(), cls=NumpyEncoder)};\n"
    html_content += f"Plotly.newPlot('bar_plot', r2_data.data, r2_data.layout);\n"
    
    html_content += f"var mae_data = {json.dumps(fig_mae.to_dict(), cls=NumpyEncoder)};\n"
    html_content += f"Plotly.newPlot('mae_plot', mae_data.data, mae_data.layout);\n"
    
    # 3. Scatter for Brix vs GDA (if exists)
    scatter_path = preds_dir / "preds_brix_GDA.csv"
    if scatter_path.exists():
        df_scatter = pd.read_csv(scatter_path)
        fig_scatter = px.scatter(
            df_scatter, x='Y_true', y='Y_pred', color='Fundo',
            title="Predicciones LOFO LMM para Brix ~ GDA + (1|Fundo)",
            labels={'Y_true': 'Brix Real', 'Y_pred': 'Brix Predicho LMM'}
        )
        # Add y=x line
        min_val = min(df_scatter['Y_true'].min(), df_scatter['Y_pred'].min())
        max_val = max(df_scatter['Y_true'].max(), df_scatter['Y_pred'].max())
        fig_scatter.add_shape(type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val, line=dict(color="white", dash="dash"))
        fig_scatter.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        
        html_content += f"var scatter_data = {json.dumps(fig_scatter.to_dict(), cls=NumpyEncoder)};\n"
        html_content += f"Plotly.newPlot('scatter_brix', scatter_data.data, scatter_data.layout);\n"
    
    html_content += """
        </script>
    </body>
    </html>
    """
    
    out_html = Path(r"C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_lmm_madurez.html")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html_content, encoding='utf-8')
    print(f"Dashboard successfully generated at: {out_html}")

if __name__ == "__main__":
    generate_dashboard()
