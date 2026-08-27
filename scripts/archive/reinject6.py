import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update the HTML structure of the info box to have an ID on the h4
text = text.replace(
    '<h4>📊 Resumen Bioclimático de la Variedad</h4>',
    '<h4 id="tv-dynamic-title">📊 Resumen Bioclimático de la Variedad</h4>'
)

# 2. Update the Javascript to change the title, margin, and annotation Y position
# We'll do a few targeted replace calls

# Update the H4 title
text = text.replace(
    "const container = document.getElementById('tv-dynamic-container');",
    "const container = document.getElementById('tv-dynamic-container');\n    const infoTitle = document.getElementById('tv-dynamic-title');\n    if (infoTitle) { infoTitle.innerText = '📊 Resumen Bioclimático: ' + v; }"
)

# Fix annotation Y position
text = text.replace(
    "text: 'Valle Sinusoidal', showarrow: false, font: {color: '#e11d48', size: 11, weight: 'bold'}, xanchor: 'left'",
    "text: 'Valle Sinusoidal', showarrow: false, font: {color: '#e11d48', size: 11, weight: 'bold'}, xanchor: 'left', yanchor: 'bottom'"
)
text = text.replace(
    "y: 1.12, yref: 'paper', text: 'Valle Sinusoidal'",
    "y: 1.02, yref: 'paper', text: 'Valle Sinusoidal'"
)
text = text.replace(
    "y: 1.05, yref: 'paper', text: 'Fondo Valle (CSV)'",
    "y: 1.02, yref: 'paper', text: 'Fondo Valle (CSV)'"
)

# Fix Plotly title and margin
text = text.replace(
    "title: \"\",",
    "title: v,"
)
text = text.replace(
    "margin: {t: 40}",
    "margin: {t: 80}"
)

with open(visor_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated visual tweaks.")
