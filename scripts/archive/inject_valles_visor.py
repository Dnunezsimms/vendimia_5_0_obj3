import os
import pandas as pd

def inject_valleys(html_path, dict_fechas):
    if not os.path.exists(html_path):
        return
    with open(html_path, 'r', encoding='utf-8') as f:
        text = f.read()

    target_str = "if (proxyFound) {"
    
    # Limpiar inyecciones anteriores si las hubiera (esto es seguro ya que revertimos antes)
    
    js_dict = "{\n"
    for k, v in dict_fechas.items():
        js_dict += f"                '{k}': '{v}',\n"
    js_dict += "            }"

    inyeccion = f"""
            // Inyectar Valle Matematico Sinusoidal
            const valle_math_dates = {js_dict};
            
            const vdate = valle_math_dates[fundo] || valle_math_dates[fundo.split(',')[0].trim()];
            if(vdate) {{
                layout.shapes.push({{
                    type: 'line', x0: vdate, x1: vdate, y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#e11d48', width: 2, dash: 'dashdot'}}
                }});
                layout.annotations.push({{
                    x: vdate, y: 1.15, yref: 'paper', text: 'Valle Sinusoidal', showarrow: false, font: {{color: '#e11d48', size: 11, weight: 'bold'}}, xanchor: 'left'
                }});
            }}

            if (proxyFound) {{"""

    if text.count(target_str) > 0:
        new_text = text.replace(target_str, inyeccion)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print(f"[{os.path.basename(html_path)}] Inyección exitosa.")
    else:
        print(f"[{os.path.basename(html_path)}] No se encontró el marcador objetivo.")

if __name__ == "__main__":
    d = r"C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html"
    csv_path = r"C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\resumen_valles_termicos_2025.csv"
    
    df = pd.read_csv(csv_path)
    # create dict
    fechas = dict(zip(df['fundo'], df['fecha_valle_matematico']))
    
    inject_valleys(os.path.join(d, "visor_obj3.html"), fechas)
