import os
import pandas as pd
import folium
import re

base_dir = str(Path(__file__).resolve().parent.parent)
metadata_dir = os.path.join(base_dir, "data", "metadata")
processed_dir = os.path.join(base_dir, "data", "prepared", "modeling")
html_out_dir = os.path.join(base_dir, "reports", "dashboards_html")
csv_out = os.path.join(metadata_dir, "puntos_geospaciales.csv")

puntos = []

# 1. CÃ¡maras FenolÃ³gicas Manuales (del input directo)
manual_points = [
    {"nombre": "Camara Fenologica Mariposas", "tipo": "Camara Fenologica", "lat": -35.528553, "lon": -71.444700, "fuente": "Usuario"},
    {"nombre": "Camara Fenologica Quebrada Seca", "tipo": "Camara Fenologica", "lat": -30.526184, "lon": -71.450934, "fuente": "Usuario"},
    {"nombre": "Estacion Quebrada Seca (ATMOS 41/Zentra)", "tipo": "Estacion", "lat": -30.527093, "lon": -71.450252, "fuente": "Usuario"},
    {"nombre": "Camara Fenologica Los Acacios", "tipo": "Camara Fenologica", "lat": -30.69947605605556, "lon": -71.28792590185242, "fuente": "Usuario"}
]
puntos.extend(manual_points)

# 2. Fundos Reales del Muestreo Madurez de InterÃ©s
fundos_interes = [
    'lourdes', 'mariposa', 'villa alegre', 'keule', 'nilahue', 'idahue', 
    'quebrada seca', 'los acacios', 'ucuquer', 'santa isabel', 'quebrada de agua', 
    'san ignacio', 'rauco', 'yungay', 'quinta maipo', 'san adolfo', 'palo santo'
]

# Extraer coordenadas desde el HTML de mapas
html_map_path = r"C:\Users\dnunezs\ViÃ±a Concha y Toro S.A\Vendimia 5.0 - UC\Proyecto\Madurez uva - IC\Muestreo Madurez equipo viticultura y enologÃ­a\Temporada 2026\1_DATA\maps\fundos_estaciones.html"
if os.path.exists(html_map_path):
    with open(html_map_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    blocks = text.split('L.circleMarker(')
    for block in blocks[1:]:
        coords_match = re.search(r'\[([-\d\.]+),\s*([-\d\.]+)\]', block)
        if coords_match:
            lat, lon = coords_match.groups()
            name_match = re.search(r'>Fundo:\s*(.*?)<\/div>', block, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                # Verificar si es de interes
                if any(f_name in name.lower() for f_name in fundos_interes):
                    # Normalizar nombre
                    clean_name = name.title()
                    puntos.append({
                        "nombre": f"Fundo/Tratamiento Muestreo: {clean_name}",
                        "tipo": "Tratamiento Muestreo",
                        "lat": float(lat),
                        "lon": float(lon),
                        "fuente": "fundos_estaciones.html"
                    })

# 3. Estaciones de Clima Recomendadas (que acompaÃ±an los tratamientos)
estaciones_validas = []
tabla_maestra = os.path.join(metadata_dir, "tabla_maestra_clima_obj3_2025_2026.csv")
if os.path.exists(tabla_maestra):
    try:
        df_maestra = pd.read_csv(tabla_maestra)
        estaciones_validas = df_maestra['estacion_recomendada'].dropna().unique().tolist()
    except Exception as e:
        pass

def norm_name(name):
    return str(name).lower().strip()

validas_norm = [norm_name(x) for x in estaciones_validas]

datavid_file = os.path.join(metadata_dir, "datavid_stations_metadata.csv")
if os.path.exists(datavid_file):
    try:
        df_datavid = pd.read_csv(datavid_file)
        for _, row in df_datavid.iterrows():
            if pd.notna(row.get('latitud')) and pd.notna(row.get('longitud')):
                nombre = str(row.get('nombre', ''))
                n_norm = norm_name(nombre)
                es_valida = any(v in n_norm or n_norm in v for v in validas_norm)
                
                if es_valida:
                    puntos.append({
                        "nombre": f"Estacion Climatica: {nombre.title()}",
                        "tipo": "Estacion",
                        "lat": float(row['latitud']),
                        "lon": float(row['longitud']),
                        "fuente": "datavid_stations_metadata.csv"
                    })
    except Exception as e:
        pass

zentra_dir = os.path.join(base_dir, "data", "raw", "climate", "hourly", "zentra")
if os.path.exists(zentra_dir):
    for root, dirs, files in os.walk(zentra_dir):
        for file in files:
            if "Metadata" in file and file.endswith(".csv"):
                filepath = os.path.join(root, file)
                estacion_name = os.path.basename(root)
                n_norm = norm_name(estacion_name)
                es_valida = any(v in n_norm or n_norm in v for v in validas_norm)
                
                if es_valida:
                    try:
                        lat, lon = None, None
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                if "Latitude" in line:
                                    parts = line.strip().split(',')
                                    if len(parts) >= 3:
                                        lat = float(parts[2])
                                elif "Longitude" in line:
                                    parts = line.strip().split(',')
                                    if len(parts) >= 3:
                                        lon = float(parts[2])
                                if lat is not None and lon is not None:
                                    break
                        if lat is not None and lon is not None:
                            if not ("quebrada" in n_norm): # Evitar duplicado manual
                                puntos.append({
                                    "nombre": f"Estacion Climatica Zentra: {estacion_name.capitalize()}",
                                    "tipo": "Estacion",
                                    "lat": lat,
                                    "lon": lon,
                                    "fuente": "Metadata Zentra"
                                })
                    except Exception:
                        pass

# Consolidar CSV final
df_puntos = pd.DataFrame(puntos)
df_puntos = df_puntos[(df_puntos['lat'] < 0) & (df_puntos['lat'] > -60)]

# Drop strict duplicates
df_puntos = df_puntos.drop_duplicates(subset=['lat', 'lon', 'nombre']).reset_index(drop=True)
df_puntos.to_csv(csv_out, index=False, encoding='utf-8-sig')
print(f"Registrados {len(df_puntos)} puntos geoespaciales FINALES en {csv_out}")

# Generar Mapa Interactivo
m = folium.Map(location=[-34.0, -71.0], zoom_start=6, tiles='CartoDB Positron')

for _, row in df_puntos.iterrows():
    popup_text = f"<b>{row['nombre']}</b><br>Tipo: {row['tipo']}<br>Lat: {row['lat']}<br>Lon: {row['lon']}"
    
    if row['tipo'] == 'Camara Fenologica':
        color = 'red'
        icon = 'camera'
    elif row['tipo'] == 'Estacion':
        color = 'blue'
        icon = 'cloud'
    else: # Tratamiento Muestreo
        color = 'green'
        icon = 'leaf'
        
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=color, icon=icon, prefix='fa'),
        tooltip=row['nombre']
    ).add_to(m)

map_path = os.path.join(html_out_dir, "mapa_geospacial.html")
m.save(map_path)
print(f"Mapa interactivo HTML generado en {map_path}")

