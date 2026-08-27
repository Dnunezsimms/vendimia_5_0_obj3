# Sección de Datos (`data/`) — Objetivo 3 Vendimia 5.0

Este directorio centraliza la ingesta, validación y consolidación de las series de datos agronómicas, fenológicas y climáticas utilizadas para el modelamiento y la optimización de cosecha en el proyecto Vendimia 5.0.

---

## Estructura de Subdirectorios

### 1. `raw/` — **[INMUTABLE]**
Contiene las series de datos originales recopiladas en campo y descargadas desde las redes agroclimáticas. **Ningún script o usuario debe modificar, sobrescribir o eliminar archivos en esta carpeta.**
- `climate/hourly/datavid/`: Series horarias de 48 estaciones automáticas en formato `.parquet`.
- `climate/hourly/inia_agromet/`: Planillas Excel (`.xlsx`) de estaciones INIA.
- `climate/hourly/zentra/`: Planillas Excel (`.xlsx`) descargadas manualmente de Zentra Cloud.
- `phenology/`: Monitoreos en campo de brotación, floración, cuaja, pinta y madurez (escala ELP y fisicoquímica).

### 2. `metadata/`
Almacena los catálogos y mapas de relación territorial y operativa:
- Asignaciones canónicas **fundo—estación** (qué estación representa climáticamente a cada viñedo y cuartel).
- Análisis de cobertura climática, porcentajes de completitud y reporte de gaps por variable.

### 3. `prepared/` — **[STAGING]**
Carpeta de preparación intermedia utilizada por los scripts del pipeline (`build_phenology_consolidate.py`, `build_maturity_consolidates_2026.py`, etc.).
- Contiene catálogos pre-procesados y matrices combinadas temporales (ej. cruces temporales de clima y fenología) que aún no están listos para modelamiento, pero son insumo necesario para el paso final. 
- **Nota:** No debe eliminarse, ya que rompería la ejecución de los pipelines en tránsito.

### 4. `processed/`
Almacena las matrices listas para análisis y modelamiento econométrico/machine learning:
- `phenology_climate/`: Archivos que cruzan fundos - variedades - temporadas con sus respectivos índices bioclimáticos (GDD, acumulaciones, temperaturas medias/extremas y biofix).
- `modeling/`: Datasets agronómicos espaciales integrados para el *Stepwise Forward Selection*.
- `lmm_preds/`: Predicciones resultantes de los modelos mixtos.
- `chill/`: Indicadores dinámicos de frío.



## Estatus de Laboratorio (HPLC / UV-Vis)
- **Madurez Técnica:** ✅ CERRADO (Brix, pH, AT procesados y habilitados para el modelo Stepwise).
- **Madurez Fenólica (HPLC/UV-Vis):** ⏳ PENDIENTE. Los modelos predictivos RF/PySR para antocianinas y taninos están **bloqueados** a la espera de los resultados del laboratorio de la vendimia 2026. Una vez ingresados los perfiles en `raw/phenology`, se podrá habilitar la pestaña correspondiente en el Dashboard.

---

## Reglas Inmutables de Protocolo (AGENTS.md)

> [!CAUTION]
> **CERO DATOS SINTÉTICOS:** Está estrictamente prohibido inventar, simular o introducir datos ficticios o placebos en series climáticas, fenológicas o de madurez para rellenar vacíos. Los vacíos (*gaps*) deben ser reportados e investigados metodológicamente, jamás ocultados con datos generados artificialmente.

> [!WARNING]
> **NO MODIFICAR RAW:** Todo procesamiento debe leer desde `raw/` y escribir exclusivamente en `prepared/`, `processed/` o `reports/`.
