from pathlib import Path
import requests
import pandas as pd
import time
import os


# =====================================================
# CONFIG
# =====================================================

BASE_URL = "https://app.datavid.cl/services/api/v1"

API_KEY = os.getenv("DATAVID_API_KEY")
if not API_KEY:
    raise ValueError("Falta la variable de entorno DATAVID_API_KEY")

HEADERS = {
    "API-KEY": API_KEY,
    "Accept": "application/json"
}

OUTPUT_DIR = Path("data/raw/climate/datavid")

START_DATE = "2024-01-01"
END_DATE = "2026-05-18"

WINDOW_DAYS = 90

SLEEP_SECONDS = 1

REQUEST_TIMEOUT = 120

MAX_RETRIES = 3
RETRY_WAIT = 10

# =====================================================
# HELPERS
# =====================================================

def limpiar_nombre(nombre):

    nombre = nombre.lower()

    reemplazos = {
        " ": "_",
        "-": "_",
        "/": "_",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

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

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

    except requests.exceptions.RequestException as e:

        print("\n❌ ERROR CONSULTANDO ESTACIONES")
        print(e)

        return []

    if r.status_code != 200:

        print("\n❌ ERROR API")
        print(r.text)

        return []

    return r.json()


# =====================================================
# DESCARGAR BLOQUE
# =====================================================

def descargar_bloque(id_estacion, desde, hasta):

    desde_api = desde.strftime("%Y%m%d0000")
    hasta_api = hasta.strftime("%Y%m%d2359")

    url = (
        f"{BASE_URL}/datos/rango"
        f"?idEstacion={id_estacion}"
        f"&desde={desde_api}"
        f"&hasta={hasta_api}"
    )

    for intento in range(1, MAX_RETRIES + 1):

        try:

            r = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            if r.status_code != 200:

                print(
                    f"❌ Error {r.status_code} "
                    f"(intento {intento}/{MAX_RETRIES})"
                )

                try:
                    print(r.text[:300])
                except:
                    pass

                time.sleep(RETRY_WAIT)

                continue

            data = r.json()

            return data

        except requests.exceptions.RequestException as e:

            print(
                f"\n❌ REQUEST ERROR "
                f"(intento {intento}/{MAX_RETRIES})"
            )

            print(e)

            time.sleep(RETRY_WAIT)

    print("\n❌ BLOQUE FALLÓ DEFINITIVAMENTE")

    return None

# =====================================================
# DESCARGAR ESTACION COMPLETA
# =====================================================

def descargar_estacion(estacion):

    nombre = estacion["nombre"]
    id_estacion = estacion["identificacion"]

    print("\n" + "=" * 60)
    print(f"📍 {nombre}")
    print(f"🆔 {id_estacion}")

    carpeta = OUTPUT_DIR / limpiar_nombre(nombre)

    carpeta.mkdir(
        parents=True,
        exist_ok=True
    )

    start = pd.Timestamp(START_DATE)
    end = pd.Timestamp(END_DATE)

    dfs = []

    current = start

    # =================================================
    # LOOP TEMPORAL
    # =================================================

    while current < end:

        bloque_inicio = current

        bloque_fin = min(
            current + pd.Timedelta(days=WINDOW_DAYS - 1),
            end
        )

        print(
            f"⬇ Descargando "
            f"{bloque_inicio.date()} → {bloque_fin.date()}"
        )

        data = descargar_bloque(
            id_estacion,
            bloque_inicio,
            bloque_fin
        )

        # =============================================
        # DATA OK
        # =============================================

        if data is not None and len(data) > 0:

            df = pd.DataFrame(data)

            dfs.append(df)

            print(f"✔ {len(df)} registros")

        else:

            print("⚠ Sin datos")

        # =============================================
        # NEXT BLOCK
        # =============================================

        current = bloque_fin + pd.Timedelta(days=1)

        time.sleep(SLEEP_SECONDS)

    # =================================================
    # SIN DATOS
    # =================================================

    if len(dfs) == 0:

        print("❌ No se descargaron datos")

        return

    # =================================================
    # CONCATENAR
    # =================================================

    df_final = pd.concat(
        dfs,
        ignore_index=True
    )

    # =================================================
    # FECHA
    # =================================================

    if "fecha" in df_final.columns:

        df_final["fecha"] = pd.to_datetime(
            df_final["fecha"],
            format="%d-%m-%Y %H:%M",
            errors="coerce"
        )

        # eliminar fechas inválidas
        df_final = df_final.dropna(
            subset=["fecha"]
        )

        # ordenar
        df_final = df_final.sort_values(
            "fecha"
        )

    # =================================================
    # DUPLICADOS
    # =================================================

    df_final = df_final.drop_duplicates(
        subset=["fecha"]
    )

    # =================================================
    # RESET INDEX
    # =================================================

    df_final = df_final.reset_index(
        drop=True
    )

    # =================================================
    # SAVE
    # =================================================

    csv_path = carpeta / "climate_hourly.csv"

    parquet_path = carpeta / "climate_hourly.parquet"

    df_final.to_csv(
        csv_path,
        index=False
    )

    df_final.to_parquet(
        parquet_path,
        index=False
    )

    # =================================================
    # METADATA
    # =================================================

    metadata = {
        "station_name": nombre,
        "station_id": id_estacion,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "records": len(df_final),
        "first_timestamp": df_final["fecha"].min(),
        "last_timestamp": df_final["fecha"].max()
    }

    metadata_path = carpeta / "metadata.csv"

    pd.DataFrame([metadata]).to_csv(
        metadata_path,
        index=False
    )

    # =================================================
    # SUMMARY
    # =================================================

    print(f"\n💾 Guardado:")
    print(csv_path)
    print(parquet_path)

    print(f"\n📊 Total registros: {len(df_final)}")

    print(
        f"📅 Cobertura: "
        f"{df_final['fecha'].min()} "
        f"→ "
        f"{df_final['fecha'].max()}"
    )


# =====================================================
# MAIN
# =====================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # =================================================
    # ESTACIONES
    # =================================================

    estaciones = obtener_estaciones()

    if len(estaciones) == 0:

        print("\n❌ No se encontraron estaciones")

        return

    # =================================================
    # SAVE STATION LIST
    # =================================================

    df_estaciones = pd.DataFrame(estaciones)

    estaciones_parquet = (
        OUTPUT_DIR /
        "listado_estaciones.parquet"
    )

    estaciones_csv = (
        OUTPUT_DIR /
        "listado_estaciones.csv"
    )

    df_estaciones.to_parquet(
        estaciones_parquet,
        index=False
    )

    df_estaciones.to_csv(
        estaciones_csv,
        index=False
    )

    print(f"\n📡 Total estaciones: {len(estaciones)}")

    # =================================================
    # DESCARGA
    # =================================================

    for estacion in estaciones:

        descargar_estacion(estacion)

    # =================================================
    # RESUMEN FINAL
    # =================================================

    print("\n==============================")
    print("RESUMEN FINAL")
    print("==============================")

    parquets = list(
        OUTPUT_DIR.glob("*/climate_hourly.parquet")
    )

    print(f"\nParquet generados: {len(parquets)}")

    print("\n✅ DESCARGA COMPLETA")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    main()