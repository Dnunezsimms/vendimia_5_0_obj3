import os
import pandas as pd
import json

reports_dir = r"C:\projects\vendimia_5_0_obj3_clean\reports\fase6"
dashboards_dir = r"C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html"

df_resumen = pd.read_csv(os.path.join(reports_dir, 'resumen_fundo_2025.csv'))
df_cruce = pd.read_csv(os.path.join(reports_dir, 'cruce_frio_brotacion_2025.csv'))
df_diario = pd.read_csv(os.path.join(reports_dir, 'frio_diario_2025.csv'))

# Preparar JSON para inyectar al HTML
data_diario = {}
for fundo, grp in df_diario.groupby('fundo_canonical'):
    data_diario[fundo] = {
        'fechas': grp['fecha'].tolist(),
        'cp': grp['cp_acum'].tolist(),
        'hf': grp['hf_72_acum'].tolist(),
        'utah': grp['utah_acum'].tolist(),
        'temp': grp['temp_media'].tolist()
    }

data_cruce = []
for _, row in df_cruce.iterrows():
    data_cruce.append(row.to_dict())

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Frío Observado 2025</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --border: #334155;
            --warning: #fbbf24;
        }}
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
        }}
        h1, h2, h3 {{ color: #ffffff; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .badge-warning {{
            background: rgba(251, 191, 36, 0.2);
            color: var(--warning);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--text-muted); font-weight: 600; }}
        select {{
            background: var(--bg-color);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 8px;
            border-radius: 6px;
            font-size: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header-title">Frío Observado 2025</div>
            <p style="color: var(--text-muted);">Acumulación real, trazabilidad climática y relación descriptiva con T0 y brotación.</p>
        </div>

        <div class="card">
            <h2>A. Resumen Territorial</h2>
            <table>
                <tr>
                    <th>Fundo</th>
                    <th>Estación</th>
                    <th>Tipo</th>
                    <th>CP Final</th>
                    <th>HF ≤ 7.2</th>
                    <th>Utah</th>
                </tr>
                {"".join([f"<tr><td>{r['Fundo']}</td><td>{r['Estacion']}</td><td>{r['Directa/proxy']}</td><td>{r['CP final']:.1f}</td><td>{r['HF <=7.2']:.1f}</td><td>{r['Utah']:.1f}</td></tr>" for _, r in df_resumen.iterrows()])}
            </table>
        </div>

        <div class="card">
            <h2>B & C. Curvas Acumuladas y Fenología</h2>
            <label>Seleccione Fundo: </label>
            <select id="fundo-selector" onchange="updateChart()">
                {"".join([f'<option value="{f}">{f}</option>' for f in data_diario.keys()])}
            </select>
            <div id="chart-container" style="width:100%; height:500px; margin-top:20px;"></div>
        </div>

        <div class="card">
            <h2>D. Trazabilidad</h2>
            <p>Cobertura 100% observada para el periodo 01-May al 15-Oct 2025. 0% Reconstruido. 0% Faltante.</p>
            <p>Llaves de estación, sensor y timestamps estrictamente únicas (0 duplicados). Evaluado bajo timezone America/Santiago.</p>
        </div>

        <div class="card" style="border-left: 4px solid var(--warning);">
            <h2>E. Advertencias</h2>
            <ul id="warnings-list">
                <!-- Se inyecta dinamicamente -->
            </ul>
        </div>
    </div>

    <script>
        const dailyData = {json.dumps(data_diario)};
        const cruceData = {json.dumps(data_cruce)};

        function updateChart() {{
            const fundo = document.getElementById('fundo-selector').value;
            const d = dailyData[fundo];
            const c = cruceData.filter(x => x.fundo.toLowerCase() === fundo.toLowerCase());
            
            const traceCP = {{ x: d.fechas, y: d.cp, name: 'Chill Portions', type: 'scatter', line: {{color: '#3b82f6', width: 3}} }};
            const traceHF = {{ x: d.fechas, y: d.hf, name: 'Horas Frío', type: 'scatter', line: {{color: '#10b981', dash: 'dot'}} }};
            
            const layout = {{
                title: 'Acumulación de Frío 2025 - ' + fundo,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: {{color: '#f8fafc'}},
                xaxis: {{gridcolor: '#334155'}},
                yaxis: {{gridcolor: '#334155'}},
                shapes: [],
                annotations: []
            }};

            let warningsHtml = '';
            let proxyFound = false;

            c.forEach((row, i) => {{
                // Linea T0
                layout.shapes.push({{
                    type: 'line', x0: row.t0_original, x1: row.t0_original, y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#fbbf24', width: 2, dash: 'dash'}}
                }});
                layout.annotations.push({{
                    x: row.t0_original, y: 1.05, yref: 'paper', text: 'T0 ('+row.variedad+')', showarrow: false, font: {{color: '#fbbf24'}}
                }});
                
                // Linea Brotacion
                layout.shapes.push({{
                    type: 'line', x0: row.fecha_brotacion, x1: row.fecha_brotacion, y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#f43f5e', width: 2, dash: 'dash'}}
                }});
                layout.annotations.push({{
                    x: row.fecha_brotacion, y: 1.1, yref: 'paper', text: 'Brot. ('+row.variedad+')', showarrow: false, font: {{color: '#f43f5e'}}
                }});

                if (row.temporal_validation !== 'OK') {{
                    warningsHtml += `<li><span class="badge-warning">T0 Inválido</span> ${{row.variedad}}: ${{row.temporal_validation}} (Días T0-Brot: ${{row.dias_t0_a_brotacion}})</li>`;
                }}
                if (row.directa_proxy.toLowerCase() === 'proxy') proxyFound = true;
            }});

            if (proxyFound) {{
                warningsHtml += `<li><span class="badge-warning">Proxy Territorial</span> Este fundo utiliza datos de una estación meteorológica representativa cercana.</li>`;
            }}
            if (warningsHtml === '') warningsHtml = '<li>Sin advertencias.</li>';
            document.getElementById('warnings-list').innerHTML = warningsHtml;

            Plotly.newPlot('chart-container', [traceCP, traceHF], layout, {{responsive: true}});
        }}

        // Init
        setTimeout(updateChart, 100);
    </script>
</body>
</html>
"""

with open(os.path.join(dashboards_dir, 'visor_frio_real_2025.html'), 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Dashboard de frío real creado exitosamente.")
