# Código Fuente y Automatización (src/) – Objetivo 3 Vendimia 5.0

Este directorio contiene los scripts esenciales del pipeline: ingesta de datos de múltiples proveedores, auditoría de calidad, procesamiento de series temporales y entrenamiento de modelos.

---

## Estructura de Subdirectorios

### 1. ingestion/ (Descarga y Automatización Climática DataVid)
- download_datavid_full.py: Descarga histórica completa de las estaciones de la red DataVid.
- download_datavid_incremental.py: Descarga incremental para actualizar series horarias y completar gaps.

### 2. processing/ (Otras APIs, Auditoría y Cruces Bioclimáticos)
- **Extracción de otras fuentes:**
  - download_inia_api.py: Conector para la API de agrometeorología de INIA.
  - process_agromet.py: Procesamiento de datos de la red Agromet.
  - extract_era5.py: Extracción de datos satelitales (ERA5-Land).
- **Auditoría de Calidad (QA):**
  - udit_hourly_climate_gaps.py, udit_missing_variables.py, udit_temporal_gaps.py: Herramientas de apoyo para diagnosticar huecos de datos.
- **Motores de Cálculo:**
  - uild_merge_pheno_climate.py: Une observaciones fenológicas (ELP) con la climatología.
  - uild_gdd_biofix_timeseries.py: Motor que construye series de acumulación térmica (GDD) y fija los hitos biológicos (*Biofix*).

### 3. models/ (Modelamiento Matemático)
- 	rain_lmm_maturity.py: Entrenamiento de Modelos Lineales Mixtos (LMM) de predicción de madurez.

---

> [!WARNING]
> **Seguridad de APIs:** Las claves de acceso a APIs (DataVid, INIA, Copernicus) deben cargarse desde variables de entorno o archivos .env. **Estrictamente prohibido versionar claves en Git.**

## Filosofía de Diseño
Todo script en src/ debe:
1. Usar rutas relativas basadas en la raíz del proyecto.
2. Leer desde data/raw/ sin modificar jamás los archivos originales.
3. Generar salidas trazables en data/processed/ o 
eports/.
4. Incluir manejo de errores y logging claro en consola.
