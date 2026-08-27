import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add the img container if it doesn't exist
img_container = """
<div id="tv-static-graph-container" style="margin-top: 20px; text-align: center;">
    <h4>📉 Ajuste Matemático Valle Térmico (Sinusoidal)</h4>
    <img id="tv-static-img" src="" alt="Gráfico Valle Térmico" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; display: none; margin: 0 auto;">
</div>
"""
if 'id="tv-static-graph-container"' not in text:
    text = text.replace(
        '<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>',
        '<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>\n' + img_container
    )

# 2. Update the Javascript to set the image source
js_addition = """
            Plotly.newPlot(container, traces, layout);
            
            // Show the static PNG graph
            let imgEl = document.getElementById('tv-static-img');
            if(imgEl) {
                // Construct relative path: from reports/dashboards_html/ to reports/fase6/valles_termicos/
                imgEl.src = "../fase6/valles_termicos/valle_termico_" + f_raw + ".png";
                imgEl.style.display = "block";
            }
"""

if 'imgEl.src = ' not in text:
    text = text.replace(
        "Plotly.newPlot(container, traces, layout);",
        js_addition
    )

with open(visor_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected static image viewer successfully.")
