# Código Fuente y Automatización (`src/`) — Objetivo 3 Vendimia 5.0

Este directorio contiene los scripts utilitarios de ingesta de datos, conectividad con APIs climáticas y procesamiento inicial de series temporales.

---

## Estructura de Subdirectorios

### 1. `ingestion/` (Descarga y Automatización Climática)
Scripts encargados de conectar con los proveedores meteorológicos (como DataVid / Meteovid) para obtener series horarias actualizadas:
- `download_datavid_full.py`: Descarga histórica completa de las 48 estaciones automáticas de la red DataVid.
- `download_datavid_incremental.py`: Descarga incremental para actualizar series horarias y completar gaps sin reprocesar todo el histórico.

> [!WARNING]
> **Seguridad de APIs:** Las claves de acceso a APIs (ej. `DATAVID_API_KEY`) deben cargarse desde variables de entorno locales o archivos `.env`. **Estrictamente prohibido versionar claves en Git.**

### 2. `processing/` (Alineación y Cruces Bioclimáticos)
Scripts de preparación de datos que transforman las series crudas en matrices analíticas:
- `build_merge_pheno_climate.py`: Script de cruce que une las observaciones fenológicas de campo (escala ELP) con la climatología horaria y diaria de la estación asignada a cada fundo.
- `build_gdd_biofix_timeseries.py`: Motor de cálculo que construye las series temporales continuas de acumulación térmica (GDD) y fija los hitos biológicos (*Biofix*) de cada temporada.

---

## Filosofía de Diseño
Todo script en `src/` debe:
1. Usar rutas relativas basadas en la raíz del proyecto.
2. Leer desde `data/raw/` sin modificar jamás los archivos originales.
3. Generar salidas trazables en `data/processed/` o `reports/`.
4. Incluir manejo de errores y logging claro en consola.
