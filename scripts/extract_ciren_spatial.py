import os
import zipfile
import tempfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import fiona

# Habilitar soporte para KML en fiona/geopandas
fiona.drvsupport.supported_drivers['KML'] = 'rw'

def main():
    print("Iniciando extracción espacial de CIREN y Rendimientos...")
    
    # 1. Cargar coordenadas de las estaciones/fundos
    stations_path = r"data\metadata\datavid_stations_metadata.csv"
    if not os.path.exists(stations_path):
        print(f"Error: No se encontró {stations_path}")
        return
        
    df_stations = pd.read_csv(stations_path)
    
    # Crear geometría a partir de longitud y latitud
    if 'longitud' not in df_stations.columns or 'latitud' not in df_stations.columns:
        print("Error: El archivo de estaciones no tiene columnas 'longitud' y 'latitud'.")
        return
        
    gdf_stations = gpd.GeoDataFrame(
        df_stations, 
        geometry=gpd.points_from_xy(df_stations.longitud, df_stations.latitud),
        crs="EPSG:4326"
    )
    print(f"Cargadas {len(gdf_stations)} estaciones para cruce espacial.")
    
    # 2. Descomprimir e iterar por los KMZ de CIREN
    zip_path = r"C:\Users\dnunezs\Downloads\CIREN-20260803T155433Z-1-001.zip"
    ciren_gdfs = []
    
    if os.path.exists(zip_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Descomprimiendo {zip_path} en {tmpdir}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                
            # Buscar todos los .kmz extraidos
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    if file.lower().endswith('.kmz'):
                        kmz_path = os.path.join(root, file)
                        print(f"Procesando {file}...")
                        
                        # Extraer doc.kml desde el .kmz
                        with zipfile.ZipFile(kmz_path, 'r') as kmz:
                            kml_names = [n for n in kmz.namelist() if n.lower().endswith('.kml')]
                            if kml_names:
                                kmz.extract(kml_names[0], tmpdir)
                                kml_path = os.path.join(tmpdir, kml_names[0])
                                
                                try:
                                    # Leer KML con geopandas
                                    gdf_kml = gpd.read_file(kml_path, driver='KML')
                                    # Asegurar que tiene CRS
                                    if gdf_kml.crs is None:
                                        gdf_kml.set_crs("EPSG:4326", inplace=True)
                                    ciren_gdfs.append(gdf_kml)
                                except Exception as e:
                                    print(f"Error leyendo {kml_names[0]}: {e}")
    else:
        print(f"Advertencia: No se encontró el ZIP de CIREN en {zip_path}")
        
    if ciren_gdfs:
        gdf_ciren_all = pd.concat(ciren_gdfs, ignore_index=True)
        print(f"Polígonos CIREN consolidados: {len(gdf_ciren_all)} polígonos.")
        
        # 3. CRUCE ESPACIAL (Spatial Join)
        print("Realizando Spatial Join (puntos dentro de polígonos)...")
        # Asegurarse que ambos tengan el mismo CRS
        gdf_stations = gdf_stations.to_crs(gdf_ciren_all.crs)
        gdf_joined = gpd.sjoin(gdf_stations, gdf_ciren_all, how="left", predicate="intersects")
        
        # Extraer atributos de interes. El KML suele guardar los datos en 'Description' o 'Name'
        # Dependiendo del formato exacto de CIREN. Lo dejaremos genérico.
        # Guardaremos el Name (que usualmente trae la clase de suelo o textura)
        if 'Name' in gdf_joined.columns:
            gdf_joined['suelo_ciren_tipo'] = gdf_joined['Name']
        if 'Description' in gdf_joined.columns:
            gdf_joined['suelo_ciren_desc'] = gdf_joined['Description'].astype(str).str[:100] # Truncado para resumen
    else:
        print("No se encontraron capas de suelo. Continuando solo con estaciones.")
        gdf_joined = gdf_stations.copy()

    # Convertir de vuelta a DataFrame pandas normal para guardar
    df_final = pd.DataFrame(gdf_joined.drop(columns='geometry'))
    
    # 4. Integrar Rendimientos (Excel)
    excel_path = r"C:\Users\dnunezs\Downloads\Rendimiento2026_ZAG028.xlsx"
    if os.path.exists(excel_path):
        print(f"Leyendo rendimientos desde {excel_path}...")
        try:
            df_rend = pd.read_excel(excel_path)
            if not df_rend.empty:
                print(f"Rendimientos encontrados: {len(df_rend)} filas.")
                # Aquí iría el merge si supiéramos las llaves exactas. 
                # Por ej: df_final = df_final.merge(df_rend, left_on='nombre', right_on='Fundo', how='left')
            else:
                print("El archivo de rendimientos está vacío o no tiene hojas válidas.")
        except Exception as e:
            print(f"Error leyendo Excel: {e}")
    else:
        print(f"Advertencia: No se encontró {excel_path}")
        
    # Agregando placeholders para Smart Agro (actualmente caído)
    print("Añadiendo placeholders (NaN) para variables de Smart Agro (clon, marco, edad)...")
    df_final['clon_portainjerto'] = None
    df_final['edad_plantacion'] = None
    df_final['marco_plantacion'] = None
    
    # 5. Guardar el dataset agronómico consolidado
    out_dir = r"data\prepared\modeling"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "dataset_agronomico_2026.csv")
    df_final.to_csv(out_file, index=False)
    
    print(f"\n¡Extracción exitosa! Datos guardados en: {out_file}")
    print("Dimensiones finales del dataset:", df_final.shape)

if __name__ == "__main__":
    main()
