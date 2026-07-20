# Modelos y Motores de Cálculo (`models/`) — Objetivo 3 Vendimia 5.0

Este directorio agrupa las tres líneas analíticas y computacionales del Objetivo 3: modelamiento fenológico térmico, auditoría interactiva del pipeline y modelos predictivos de madurez.

---

## Estructura de Módulos

### 1. `indicador_biologico/` (Pipeline GDD y T0 Latitudinal)
Contiene la lógica core de ecofisiología y cálculo térmico para estimar la fenología de la vid:
- `gdd_lourdes.py` & `biofix_lourdes.py`: Cálculo canónico de Biofix y Grados Día de Desarrollo (GDD) en el viñedo de referencia Lourdes.
- `chill_dynamic.py`: Estimación de frío invernal mediante el Modelo Dinámico (*Chilling Portions* / Porciones de Frío) utilizando series horarias.
- `multisite_multivariety_gdd_analysis_v2_t0_latitudinal.ipynb`: Notebook principal del análisis multisitio y multivariedad, implementando el **T0 Latitudinal** como predictor operativo canónico.
- `outputs_multisite_gdd/`: Tablas canónicas consolidadas con los requerimientos térmicos por variedad y valle.

### 2. `dashboard_obj3_integrado/` (App Gradio de Auditoría)
Aplicación web interactiva en Python (Gradio) diseñada para auditar el estado operativo del pipeline:
- `app.py`: Punto de entrada de la interfaz web.
- `src/`: Módulos de carga de datos (`loaders.py`), configuración de rutas (`config.py`) y motor de gráficos Plotly (`plots.py`).

### 3. `dashboard_luis/` (Predicciones y Madurez Fenólica)
Almacena los scripts, salidas y matrices para el seguimiento y modelamiento de la calidad fenólica y maduración técnica:
- Series de evolución de antocianinas, taninos, índice de color y compuestos fenólicos totales por baya y por kg.
- Salidas predictivas y comparativas entre tratamientos y temporadas.

---

## Principios Metodológicos

> [!NOTE]
> **Distinción T0 Cerrado vs. Latitudinal:** El *T0 cerrado* es un ejercicio retrospectivo basado en observaciones pasadas. Para predicción operativa y biofix canónico, el sistema utiliza el **T0 Latitudinal**.
