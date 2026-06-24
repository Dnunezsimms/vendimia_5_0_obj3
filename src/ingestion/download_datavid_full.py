from pathlib import Path
import requests
import pandas as pd
import time
import os
import argparse


# =====================================================
# CONFIG & CREDENTIALS
# =====================================================

BASE_URL = "https://app.datavid.cl/services/api/v1"

WINDOW_DAYS = 90
SLEEP_SECONDS = 1
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
RETRY_WAIT = 10

# Mapping explícito para estandarizar carpetas de salida
FUNDO_MAPPING = {
    66: "nilahue",
    64: "quebrada_seca"
}

def get_headers():
    api_key = os.getenv("DATAVID_API_KEY")
    if not api_key:
        raise ValueError("Falta la variable de entorno DATAVID_API_KEY")
    return {
        "API-KEY": api_key,
        "Accept": "application/json"
    }

# =====================================================
# HELPERS
# =====================================================

def limpiar_nombre(nombre):
    nombre = nombre.lower()
    reemplazos = {" ": "_", "-": "_", "/": "_", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for k, v in reemplazos.items():
        nombre = nombre.replace(k, v)
    while "__" in nombre:
        nombre = nombre.replace("__", "_")
    return nombre.strip("_")


# =====================================================
# ESTACIONES
# =====================================================

def obtener_estaciones():
    url = f"{BASE_URL}/estacion/listado"
    try:
        r = requests.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print("\n❌ ERROR CONSULTANDO ESTACIONES")
        print(e)
        return []

    if r.status_code != 200:
        print("\n❌ ERROR API")
        return []
    return r.json()


# =====================================================
# DESCARGAR BLOQUE
# =====================================================

def descargar_bloque(id_estacion, desde, hasta):
    desde_api = desde.strftime("%Y%m%d0000")
    hasta_api = hasta.strftime("%Y%m%d2359")
    url = f"{BASE_URL}/datos/rango?idEstacion={id_estacion}&desde={desde_api}&hasta={hasta_api}"

    for intento in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                print(f"❌ Error {r.status_code} (intento {intento}/{MAX_RETRIES})")
                time.sleep(RETRY_WAIT)
                continue
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"\n❌ REQUEST ERROR (intento {intento}/{MAX_RETRIES})")
            time.sleep(RETRY_WAIT)
    print("\n❌ BLOQUE FALLÓ DEFINITIVAMENTE")
    return None

# =====================================================
# DESCARGAR ESTACION COMPLETA
# =====================================================

def descargar_estacion(estacion, args):
    nombre = estacion["nombre"]
    
    # Cast a entero por seguridad
    try:
        id_estacion = int(estacion["identificacion"])
    except:
        id_estacion = estacion["identificacion"]

    print("\n" + "=" * 60)
    print(f"📍 {nombre}")
    print(f"🆔 {id_estacion}")

    # Mapeo canónico si existe
    if id_estacion in FUNDO_MAPPING:
        nombre_carpeta = FUNDO_MAPPING[id_estacion]
    else:
        nombre_carpeta = limpiar_nombre(nombre)

    carpeta = Path(args.output_root) / nombre_carpeta
    
    if args.dry_run:
        print(f"[DRY-RUN] Directorio destino que se usaría: {carpeta}")
        print(f"[DRY-RUN] Se descargarían datos desde {args.start} hasta {args.end}")
        return

    # A partir de acá NO es dry-run
    carpeta.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    dfs = []
    current = start

    while current < end:
        bloque_inicio = current
        bloque_fin = min(current + pd.Timedelta(days=WINDOW_DAYS - 1), end)
        print(f"⬇ Descargando {bloque_inicio.date()} → {bloque_fin.date()}")

        data = descargar_bloque(id_estacion, bloque_inicio, bloque_fin)
        if data is not None and len(data) > 0:
            df = pd.DataFrame(data)
            dfs.append(df)
            print(f"✔ {len(df)} registros")
        else:
            print("⚠ Sin datos")

        current = bloque_fin + pd.Timedelta(days=1)
        time.sleep(SLEEP_SECONDS)

    if len(dfs) == 0:
        print("❌ No se descargaron datos")
        return

    df_final = pd.concat(dfs, ignore_index=True)

    # Validar que exista la columna de tiempo (fecha)
    col_tiempo = None
    if "fecha" in df_final.columns:
        col_tiempo = "fecha"
    elif "timestamp" in df_final.columns:
        col_tiempo = "timestamp"

    if not col_tiempo:
        print("\n❌ ERROR FATAL: No se encontró columna de fecha o timestamp en los datos descargados.")
        print("Columnas disponibles:", list(df_final.columns))
        return

    df_final[col_tiempo] = pd.to_datetime(df_final[col_tiempo], format="%d-%m-%Y %H:%M", errors="coerce")
    df_final = df_final.dropna(subset=[col_tiempo]).sort_values(col_tiempo)
    df_final = df_final.drop_duplicates(subset=[col_tiempo]).reset_index(drop=True)

    csv_path = carpeta / "climate_hourly.csv"
    parquet_path = carpeta / "climate_hourly.parquet"

    # Guardar CSV (Siempre seguro)
    df_final.to_csv(csv_path, index=False)

    # Guardar Parquet (Puede fallar por falta de motor)
    try:
        df_final.to_parquet(parquet_path, index=False)
    except Exception as e:
        print(f"\n⚠ ADVERTENCIA: Falló el guardado a Parquet ({e}). El CSV se guardó correctamente.")

    metadata = {
        "station_name": nombre,
        "station_id": id_estacion,
        "start_date": args.start,
        "end_date": args.end,
        "records": len(df_final),
        "first_timestamp": df_final[col_tiempo].min(),
        "last_timestamp": df_final[col_tiempo].max()
    }
    pd.DataFrame([metadata]).to_csv(carpeta / "metadata.csv", index=False)

    print(f"\n📊 Total registros: {len(df_final)}")
    print(f"📅 Cobertura: {df_final[col_tiempo].min()} → {df_final[col_tiempo].max()}")

# =====================================================
# MAIN
# =====================================================

def main():
    parser = argparse.ArgumentParser(description="Descarga automatizada desde DataVid API")
    parser.add_argument("--ids", nargs="+", type=int, help="IDs numéricos de estaciones a descargar (ej: 64 66)")
    parser.add_argument("--start", type=str, required=True, help="Fecha de inicio (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="Fecha de fin (YYYY-MM-DD)")
    parser.add_argument("--output-root", type=str, default="data/raw/climate/hourly/datavid", help="Carpeta destino raíz")
    parser.add_argument("--dry-run", action="store_true", help="Validar API, rutas y estaciones sin descargar y sin crear carpetas")
    args = parser.parse_args()

    try:
        get_headers() # Validate API Key exists
    except Exception as e:
        print(f"❌ ERROR DE CREDENCIALES: {e}")
        return

    if args.dry_run:
        print("\n==============================")
        print("🚀 MODO DRY-RUN ACTIVADO")
        print("==============================")
        print("✔ API Key configurada exitosamente (validación local).")
    
    # Crear root dir solo si no estamos en dry-run
    if not args.dry_run:
        Path(args.output_root).mkdir(parents=True, exist_ok=True)
        
    estaciones_todas = obtener_estaciones()

    if len(estaciones_todas) == 0:
        print("\n❌ No se encontraron estaciones en el listado base.")
        return

    # Robust filter: Normalize inputs and data to int
    if args.ids:
        estaciones_filtradas = []
        for s in estaciones_todas:
            try:
                sid = int(s["identificacion"])
                if sid in args.ids:
                    estaciones_filtradas.append(s)
            except:
                pass
    else:
        estaciones_filtradas = estaciones_todas

    if len(estaciones_filtradas) == 0:
        print("\n❌ Ninguna estación coincide con los IDs entregados.")
        return

    if args.dry_run:
        print(f"\n[DRY-RUN] Estaciones detectadas para procesar: {len(estaciones_filtradas)}")
        for s in estaciones_filtradas:
            print(f"  -> ID: {s['identificacion']} | Nombre crudo: {s['nombre']}")
        print(f"[DRY-RUN] Periodo configurado: {args.start} al {args.end}")
        print(f"[DRY-RUN] Directorio raíz de salida: {args.output_root}")
        print("\n[DRY-RUN] Simulando ejecución por estación...\n")

    for estacion in estaciones_filtradas:
        descargar_estacion(estacion, args)

    print("\n✅ PROCESO COMPLETADO" + (" (DRY-RUN)" if args.dry_run else ""))


if __name__ == "__main__":
    main()