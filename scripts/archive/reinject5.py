import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject the info box div below the dynamic container if it doesn't exist
info_box_html = """
<div id="tv-dynamic-info" style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #e11d48; border-radius: 5px;">
    <h4>📊 Resumen Bioclimático de la Variedad</h4>
    <div id="tv-dynamic-metrics" style="display: flex; gap: 20px; margin-bottom: 15px; font-weight: bold; flex-wrap: wrap;">
        <!-- JS will populate this -->
    </div>
    <hr style="border:0; border-top: 1px solid #ddd; margin: 10px 0;">
    <p style="font-size: 0.9em; color: #555;">
        <b>Metodología:</b> 
        El <b>Valle Térmico</b> se calcula ajustando una ecuación sinusoidal a las temperaturas mínimas de invierno y derivándola (pendiente 0) para hallar matemáticamente el día más frío (Valle Meteorológico real). 
        La acumulación de calor se realiza usando el método de <b>GDD Seno Simple</b> (Single Sine Method), que modela la curva de temperatura diaria para estimar con mayor precisión las horas efectivas sobre el umbral base.
    </p>
</div>
"""

if 'id="tv-dynamic-info"' not in text:
    text = text.replace(
        '<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>',
        '<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>\n' + info_box_html
    )

# 2. Update the Javascript logic
# I will use a regex to extract the whole fetch block and replace it.
# It's safer to just rewrite the `updateTVPanel` function.

new_js = """
function updateTVPanel() {
    const f_raw = document.getElementById('tv-fundo-select').value;
    const t = document.getElementById('tv-temp-select').value;
    const v = document.getElementById('tv-var-select').value;
    
    let f = f_raw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "_").replace(/_+/g, "_").replace(/_$/, "");
    if (f === "quebrada_seca") f = "qba_seca";
    if (f === "los_acacios") f = "los_acacios";
    
    const container = document.getElementById('tv-dynamic-container');
    const infoMetrics = document.getElementById('tv-dynamic-metrics');
    
    container.innerHTML = "<p>Cargando datos para " + f_raw + "...</p>";
    if(infoMetrics) infoMetrics.innerHTML = "";
    
    fetch('data/valles/' + f + '.json?v=' + new Date().getTime())
        .then(response => {
            if (!response.ok) throw new Error("Fundo no encontrado en data/valles");
            return response.json();
        })
        .then(jsonData => {
            if (!jsonData.data[t] || !jsonData.data[t][v]) {
                container.innerHTML = "<p>No hay datos para esta temporada y variedad.</p>";
                return;
            }
            
            let biofixes = Object.keys(jsonData.data[t][v]);
            if (biofixes.length === 0) return;
            let biofix = biofixes.includes("1_agosto") ? "1_agosto" : biofixes[0];
            
            let dataset = jsonData.data[t][v][biofix];
            
            // --- POPULATE INFO METRICS ---
            if(infoMetrics) {
                let html = "";
                if(dataset.t0_latitudinal) html += `<div style="padding: 10px; background: #e0f2fe; border-radius: 5px;">📍 T0 Latitudinal: <br><span style="color: #0369a1; font-size: 1.1em;">${dataset.t0_latitudinal}</span></div>`;
                if(dataset.fecha_brotacion_ELP4) html += `<div style="padding: 10px; background: #dcfce7; border-radius: 5px;">🌱 Fecha Brotación (ELP4): <br><span style="color: #15803d; font-size: 1.1em;">${dataset.fecha_brotacion_ELP4}</span></div>`;
                // Add GDD info if available (we will use gdd_acumulado_previo_t0 if we had it, but we didn't export it in the JSON! Let's just calculate it from the arrays or if not present just don't show it for now, wait we can extract it if we want).
                // Actually the user wants GDD between Valle Termico and T0. 
                // Let's just find the index of Valle and T0 in the array and subtract.
                let val1 = 0; let val2 = 0;
                let v_idx = dataset.fechas.indexOf(dataset.fecha_fondo_valle);
                let t0_idx = dataset.fechas.indexOf(dataset.t0_latitudinal);
                if(v_idx !== -1 && t0_idx !== -1) {
                    val1 = dataset.gdd_acumulado[v_idx];
                    val2 = dataset.gdd_acumulado[t0_idx];
                    let diff = (val2 - val1).toFixed(1);
                    html += `<div style="padding: 10px; background: #fef3c7; border-radius: 5px;">🔥 GDD (Valle a T0): <br><span style="color: #b45309; font-size: 1.1em;">${diff} GDD</span></div>`;
                }
                infoMetrics.innerHTML = html;
            }

            let traces = [];
            
            traces.push({
                x: dataset.fechas, y: dataset.gdd_diario, type: 'bar', name: 'GDD Diario', marker: {color: 'lightgray'}, yaxis: 'y2'
            });
            traces.push({
                x: dataset.fechas, y: dataset.rolling_gdd_14, mode: 'lines', name: 'Actividad Térmica (GDD Móvil 14d)', line: {color: '#00a8cc', width: 3}
            });
            traces.push({
                x: dataset.fechas, y: dataset.rolling_tmean_14, mode: 'lines', name: 'Temp. Media Móvil 14d [apoyo]', line: {color: 'gray', width: 1, dash: 'dot'}, yaxis: 'y'
            });
            traces.push({
                x: dataset.fechas, y: dataset.gdd_acumulado, mode: 'lines', name: 'GDD Acumulado (Seno Simple)', line: {color: 'purple', width: 2}, yaxis: 'y2'
            });
            
            let shapes = [];
            let annotations = [];
            
            if (dataset.threshold_GDD_usado) {
                shapes.push({type: 'line', x0: dataset.fechas[0], x1: dataset.fechas[dataset.fechas.length-1], y0: dataset.threshold_GDD_usado, y1: dataset.threshold_GDD_usado, yref: 'y2', line: {color: 'orange', width: 2, dash: 'dash'}});
                annotations.push({x: dataset.fechas[dataset.fechas.length-1], y: dataset.threshold_GDD_usado, yref: 'y2', text: 'Umbral Varietal', showarrow: false});
            }
            if (dataset.fecha_fondo_valle) {
                shapes.push({type: 'line', x0: dataset.fecha_fondo_valle, x1: dataset.fecha_fondo_valle, y0: 0, y1: 1, yref: 'paper', line: {color: 'teal', width: 2, dash: 'dash'}});
                annotations.push({x: dataset.fecha_fondo_valle, y: 1.05, yref: 'paper', text: 'Fondo Valle (CSV)', showarrow: false, font: {color: 'teal', size: 10}});
            }
            
            if (jsonData.valle_sinusoidal) {
                shapes.push({type: 'line', x0: jsonData.valle_sinusoidal, x1: jsonData.valle_sinusoidal, y0: 0, y1: 1, yref: 'paper', line: {color: '#e11d48', width: 2, dash: 'dashdot'}});
                annotations.push({x: jsonData.valle_sinusoidal, y: 1.12, yref: 'paper', text: 'Valle Sinusoidal', showarrow: false, font: {color: '#e11d48', size: 11, weight: 'bold'}, xanchor: 'left'});
            }

            if (dataset.t0_latitudinal) {
                shapes.push({type: 'line', x0: dataset.t0_latitudinal, x1: dataset.t0_latitudinal, y0: 0, y1: 1, yref: 'paper', line: {color: '#0369a1', width: 2, dash: 'solid'}});
                annotations.push({x: dataset.t0_latitudinal, y: 0.95, yref: 'paper', text: 'T0 Latitudinal', showarrow: false, font: {color: '#0369a1', size: 11, weight: 'bold'}, xanchor: 'right'});
            }

            if (dataset.fecha_brotacion_ELP4) {
                shapes.push({type: 'line', x0: dataset.fecha_brotacion_ELP4, x1: dataset.fecha_brotacion_ELP4, y0: 0, y1: 1, yref: 'paper', line: {color: '#15803d', width: 2, dash: 'solid'}});
                annotations.push({x: dataset.fecha_brotacion_ELP4, y: 0.85, yref: 'paper', text: 'Brotación ELP4', showarrow: false, font: {color: '#15803d', size: 11, weight: 'bold'}, xanchor: 'left'});
            }
            
            let layout = {
                title: "", 
                xaxis: {title: "Fecha"},
                yaxis: {title: "Actividad Térmica [GDD/día] / Temp [°C]", side: 'left'},
                yaxis2: {title: "GDD Acumulado desde Fecha candidata", overlaying: 'y', side: 'right'},
                shapes: shapes,
                annotations: annotations,
                legend: {orientation: 'h', y: -0.2},
                margin: {t: 40}
            };
            
            container.innerHTML = "";
            Plotly.newPlot(container, traces, layout);
        })
        .catch(err => {
            container.innerHTML = "<p>Error cargando datos dinámicos: " + err + "</p>";
        });
}
"""

# Extract the old function updateTVPanel()...
old_func_pattern = r'function updateTVPanel\(\)\s*\{.*?\}\s*(?=</script>|function)'
match = re.search(old_func_pattern, text, flags=re.DOTALL)
if match:
    text = text.replace(match.group(0), new_js)
else:
    # Just to be safe, find it with another regex if the first fails
    old_func_pattern2 = r'function updateTVPanel\(\)\s*\{.*?\.catch\(err.*?\}\);\s*\}'
    match2 = re.search(old_func_pattern2, text, flags=re.DOTALL)
    if match2:
        text = text.replace(match2.group(0), new_js)

with open(visor_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated UI features!")
