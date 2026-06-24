"""
build_datavid_catalog.py
------------------------

Construye catálogo de estaciones descargadas desde Datavid.

✔ Detecta estaciones válidas
✔ Resume cobertura temporal
✔ Cuenta registros
✔ Calcula porcentaje cobertura
✔ Detecta inicio y fin real
✔ Genera catálogo CSV + PARQUET
✔ Clasifica calidad estación

Requisitos:
pip install pandas pyarrow
"""

from pathlib import Path
import pandas as pd


# =====================================================
# CONFIG
# =====================================================

DATA_DIR = Path("data/raw/climate/datavid")

OUTPUT_CSV = DATA_DIR / "stations_catalog.csv"
OUTPUT_PARQUET = DATA_DIR / "stations_catalog.parquet"


# =====================================================
# HELPERS
# =====================================================

def clasificar_cobertura(porcentaje):

    if porcentaje >= 95:
        return "alta"

    elif porcentaje >= 70:
        return "media"

    elif porcentaje > 0:
        return "baja"

    return "sin_datos"


# =====================================================
# MAIN
# =====================================================

def main():

    print("\n📡 CONSTRUYENDO CATÁLOGO DATAVID\n")

    carpetas = [
        x for x in DATA_DIR.iterdir()
        if x.is_dir()
    ]

    resumen = []

    for carpeta in carpetas:

        parquet_path = carpeta / "climate_hourly.parquet"

        print("=" * 60)
        print(f"📂 {carpeta.name}")

        if not parquet_path.exists():

            print("⚠ No existe parquet")

            resumen.append({
                "estacion": carpeta.name,
                "n_registros": 0,
                "fecha_inicio": None,
                "fecha_fin": None,
                "dias_cobertura": 0,
                "porcentaje_cobertura": 0,
                "clasificacion": "sin_datos"
            })

            continue

        try:

            df = pd.read_parquet(parquet_path)

            if len(df) == 0:

                print("⚠ Dataset vacío")

                resumen.append({
                    "estacion": carpeta.name,
                    "n_registros": 0,
                    "fecha_inicio": None,
                    "fecha_fin": None,
                    "dias_cobertura": 0,
                    "porcentaje_cobertura": 0,
                    "clasificacion": "sin_datos"
                })

                continue

            # =============================================
            # FECHA
            # =============================================

            df["fecha"] = pd.to_datetime(
                df["fecha"],
                errors="coerce"
            )

            df = df.dropna(subset=["fecha"])

            fecha_inicio = df["fecha"].min()
            fecha_fin = df["fecha"].max()

            # =============================================
            # COBERTURA
            # =============================================

            n_registros = len(df)

            dias = (
                fecha_fin - fecha_inicio
            ).days + 1

            horas_esperadas = dias * 24

            porcentaje = (
                n_registros / horas_esperadas
            ) * 100

            porcentaje = round(porcentaje, 2)

            clasificacion = clasificar_cobertura(
                porcentaje
            )

            # =============================================
            # RESUMEN
            # =============================================

            row = {
                "estacion": carpeta.name,
                "n_registros": n_registros,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "dias_cobertura": dias,
                "horas_esperadas": horas_esperadas,
                "porcentaje_cobertura": porcentaje,
                "clasificacion": clasificacion
            }

            resumen.append(row)

            # =============================================
            # PRINT
            # =============================================

            print(f"✔ Registros: {n_registros}")

            print(
                f"📅 Inicio: "
                f"{fecha_inicio.strftime('%Y-%m-%d')}"
            )

            print(
                f"📅 Fin: "
                f"{fecha_fin.strftime('%Y-%m-%d')}"
            )

            print(
                f"📊 Cobertura: "
                f"{porcentaje}%"
            )

            print(
                f"🏷 Calidad: "
                f"{clasificacion}"
            )

        except Exception as e:

            print("❌ ERROR")
            print(e)

    # =================================================
    # DATAFRAME FINAL
    # =================================================

    catalogo = pd.DataFrame(resumen)

    if len(catalogo) == 0:

        print("\n❌ No se generó catálogo")

        return

    catalogo = catalogo.sort_values(
        by=[
            "porcentaje_cobertura",
            "n_registros"
        ],
        ascending=False
    )

    # =================================================
    # GUARDAR
    # =================================================

    catalogo.to_csv(OUTPUT_CSV, index=False)

    catalogo.to_parquet(
        OUTPUT_PARQUET,
        index=False
    )

    print("\n" + "=" * 60)
    print("✅ CATÁLOGO GENERADO")
    print("=" * 60)

    print(f"\n💾 CSV:")
    print(OUTPUT_CSV)

    print(f"\n💾 PARQUET:")
    print(OUTPUT_PARQUET)

    print("\n🏆 TOP ESTACIONES\n")

    print(
        catalogo[
            [
                "estacion",
                "n_registros",
                "porcentaje_cobertura",
                "clasificacion"
            ]
        ].head(15)
    )


if __name__ == "__main__":
    main()