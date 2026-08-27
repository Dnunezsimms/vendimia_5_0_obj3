import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove all old tv-panels
panels = re.findall(r'<div id=\"(tv_[^\"]+)\" class=\"tv-panel\"', text)
for p in panels:
    # Match the <div class="tv-panel"> ... </div> (and potentially closing tags for row/cols, wait, let's just match the tv-panel correctly)
    pattern = f'<div id=\"{p}\" class=\"tv-panel\".*?</div>\s*</div>\s*</div>'
    match = re.search(pattern, text, flags=re.DOTALL)
    if match:
        text = text.replace(match.group(0), "")

# 2. Find the updateTVPanel function and replace it
# The old function starts with function updateTVPanel() { and ends with } (which might be tricky to regex due to nested braces).
# Let's search for function updateTVPanel() and replace the entire <script> block containing it, or just do a regex replace if we know its boundary.
script_match = re.search(r'function updateTVPanel\(\)\s*\{.*?(function |</script>)', text, flags=re.DOTALL)
if script_match:
    old_script_part = re.search(r'(function updateTVPanel\(\)\s*\{.*?)\n\s*(?:function |</script>)', text, flags=re.DOTALL)
    if old_script_part:
        old_code = old_script_part.group(1)
        
        dynamic_js = """
function updateTVPanel() {
    const f_raw = document.getElementById('tv-fundo-select').value;
    const t = document.getElementById('tv-temp-select').value;
    const v = document.getElementById('tv-var-select').value;
    
    // Clean id format to match JSON filenames
    let f = f_raw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "_").replace(/_+/g, "_").replace(/_$/, "");
    // Hardcode some known mappings
    if (f === "quebrada_seca") f = "qba_seca";
    if (f === "los_acacios") f = "los_acacios";
    
    const container = document.getElementById('tv-dynamic-container');
    container.innerHTML = "<p>Cargando datos para " + f_raw + "...</p>";
    
    fetch('data/valles/' + f + '.json')
        .then(response => {
            if (!response.ok) throw new Error("Fundo no encontrado en data/valles");
            return response.json();
        })
        .then(jsonData => {
            // Check if combination exists
            if (!jsonData.data[t] || !jsonData.data[t][v]) {
                container.innerHTML = "<p>No hay datos para esta temporada y variedad.</p>";
                return;
            }
            
            // For now assume biofix '1_agosto' is default, or get first
            let biofixes = Object.keys(jsonData.data[t][v]);
            if (biofixes.length === 0) return;
            let biofix = biofixes.includes("1_agosto") ? "1_agosto" : biofixes[0];
            
            let dataset = jsonData.data[t][v][biofix];
            
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
                x: dataset.fechas, y: dataset.gdd_acumulado, mode: 'lines', name: 'GDD Acumulado', line: {color: 'purple', width: 2}, yaxis: 'y2'
            });
            
            let shapes = [];
            let annotations = [];
            
            if (dataset.threshold_GDD_usado) {
                shapes.push({type: 'line', x0: dataset.fechas[0], x1: dataset.fechas[dataset.fechas.length-1], y0: dataset.threshold_GDD_usado, y1: dataset.threshold_GDD_usado, yref: 'y2', line: {color: 'orange', width: 2, dash: 'dash'}});
                annotations.push({x: dataset.fechas[dataset.fechas.length-1], y: dataset.threshold_GDD_usado, yref: 'y2', text: 'Umbral Varietal', showarrow: false});
            }
            if (dataset.fecha_fondo_valle) {
                shapes.push({type: 'line', x0: dataset.fecha_fondo_valle, x1: dataset.fecha_fondo_valle, y0: 0, y1: 1, yref: 'paper', line: {color: 'teal', width: 2, dash: 'dash'}});
            }
            
            // VALLE SINUSOIDAL INJECTION!
            if (jsonData.valle_sinusoidal) {
                shapes.push({type: 'line', x0: jsonData.valle_sinusoidal, x1: jsonData.valle_sinusoidal, y0: 0, y1: 1, yref: 'paper', line: {color: '#e11d48', width: 2, dash: 'dashdot'}});
                annotations.push({x: jsonData.valle_sinusoidal, y: 1.15, yref: 'paper', text: 'Valle Sinusoidal', showarrow: false, font: {color: '#e11d48', size: 11, weight: 'bold'}, xanchor: 'left'});
            }
            
            let layout = {
                title: "Auditoría Valle Térmico y GDD: " + f_raw + " | " + v + " (" + t + ")",
                xaxis: {title: "Fecha"},
                yaxis: {title: "Actividad Térmica [GDD/día] / Temp [°C]", side: 'left'},
                yaxis2: {title: "GDD Acumulado desde Fecha candidata", overlaying: 'y', side: 'right'},
                shapes: shapes,
                annotations: annotations,
                legend: {orientation: 'h', y: -0.2}
            };
            
            container.innerHTML = "";
            Plotly.newPlot(container, traces, layout);
        })
        .catch(err => {
            container.innerHTML = "<p>Error cargando datos dinámicos: " + err + "</p>";
        });
}
"""
        text = text.replace(old_code, dynamic_js)


# 3. Add the placeholder container right after the filters
# The old HTML had a structure: <div id="tv-filters" ...> ... </div>
# We will insert <div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>
filter_pattern = r'(<div id=\"tv-filters\"[^>]*>.*?</div>\s*</div>)'
if re.search(filter_pattern, text, flags=re.DOTALL):
    text = re.sub(
        filter_pattern,
        r'\1\n<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>',
        text,
        flags=re.DOTALL,
        count=1
    )

with open(visor_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected dynamic module successfully.")
