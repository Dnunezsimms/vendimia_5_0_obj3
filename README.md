# Vendimia 5.0 — Objetivo Específico 3

**Marco Técnico-Operativo para Fenología, Madurez y Modelamiento Bioclimático en Vid (*Vitis vinifera* L.)**

---

## Propósito del Repositorio

Este repositorio implementa el flujo computacional y analítico del **Objetivo Específico 3** del proyecto CORFO **Vendimia 5.0**:
> *"Desarrollar modelos de inteligencia artificial explicable (XAI) para predecir el estado fenológico de la vid y la maduración de la uva a partir de variables climáticas, con el objetivo de definir el momento óptimo de cosecha mediante optimización multiobjetivo."*

El sistema está diseñado bajo estrictos principios de **trazabilidad, reproducibilidad y rigor biológico**, operando como una plataforma canónica de I+D y auditoría metodológica para conectar el clima observado/predicho con el comportamiento fisiológico de la viña.

---

## Flujo Conceptual y Metodológico

```text
Clima Observado & Predicho (DataVid, Zentra, INIA)
                     ↓
Fenología & Biofix (Escala ELP, GDD, T0 Latitudinal, Frío Dinámico)
                     ↓
Madurez Técnica (Brix, pH, Acidez Total, Peso de Baya)
                     ↓
Madurez Fenólica (Antocianinas, Taninos, Color, HPLC / UV-Vis)
                     ↓
Modelación Predictiva XAI (PySR, Random Forest, Regresión Multivariada)
                     ↓
Optimización Multiobjetivo de Fecha de Cosecha (NSGA-II / pymoo)
```

---

## Estructura del Repositorio

| Directorio / Módulo | Descripción |
| :--- | :--- |
| `data/` | **[INMUTABLE]** Almacena datos climáticos crudos (`raw/`), metadatos de cobertura y asignación fundo-estación (`metadata/`), y matrices consolidadas fenología×clima (`processed/`). **Cero datos sintéticos.** |
| `docs/` | Documentación técnica canónica. Contiene `objetivo_3_vendimia_5_0.md` (lectura obligatoria antes de modificar cualquier línea de código) y directrices de arquitectura en `handoff/`. |
| `models/` | Algoritmos y motores de cálculo: pipeline de indicador biológico (`indicador_biologico/`), aplicación interactiva Gradio (`dashboard_obj3_integrado/`), y predicciones de madurez (`dashboard_luis/`). |
| `reports/` | Informes científicos de I+D (meta-análisis de frío invernal), scripts generadores y la colección de **Dashboards HTML** estáticos/interactivos en `dashboards_html/`. |
| `src/` | Módulos de ingesta automatizada desde APIs agroclimáticas (`ingestion/`) y scripts de procesamiento, alineación temporal y biofix (`processing/`). |

---

## Acceso a Dashboards y Herramientas Visuales

El repositorio cuenta con dos modalidades visuales principales:

### 1. Suite de Dashboards HTML (Recomendado para exploración rápida)
Ubicados en `reports/dashboards_html/`, son visores autónomos, interactivos y de alto rendimiento que no requieren iniciar servidores de backend:
- 🌐 **Portal Central:** Abre `reports/dashboards_html/index.html` en cualquier navegador para acceder a toda la suite.
- ❄️ **`explorador_frio.html`**: Simulador interactivo de compensación Frío-Calor (*Chilling-Forcing*).
- 📊 **`visor_obj3.html`**: Auditoría integrada de cobertura climática, indicador biológico y curvas de madurez.
- 🗺️ **`mapa_estaciones.html`**: Mapa interactivo georreferenciado de estaciones agroclimáticas (INIA y RAN).

### 2. Dashboard Integrado de Auditoría (Gradio)
Para análisis profundos en tiempo real con ejecución de código Python:
- Ejecuta el archivo `ABRIR_DASHBOARD.bat` desde la raíz o corre en terminal:
  ```powershell
  python -m models.dashboard_obj3_integrado.app
  ```
- Se abrirá en `http://127.0.0.1:7860/` o mediante `ACCESO_DASHBOARD.html`.

---

## Reglas Inmutables y de Seguridad (Protocolo AGENTS.md)

1. **Integridad de Datos:** Prohibido inventar, imputar o introducir datos sintéticos/placebos en las series climáticas, fenológicas o de madurez.
2. **Inmutabilidad Raw:** La carpeta `data/raw/` no debe ser modificada ni sobrescrita jamás por scripts de procesamiento.
3. **Biofix y Frío:** El cálculo de frío invernal es dinámico y diagnóstico; no se debe dar por cerrado sin validar las 7/7 fuentes horarias. El predictor operativo canónico es el **T0 latitudinal**.
4. **Seguridad:** Prohibido versionar archivos `.env`, claves de API (`DATAVID_API_KEY`) o secretos.
5. **Control de Versiones:** No realizar `git add .`. Versionar exclusivamente mediante rutas explícitas y aprobadas.

---

## Contacto y Responsable Técnico
- **Diego Núñez Simms** — Análisis de datos, modelamiento biológico y trazabilidad técnica del Objetivo 3.
---

## ⚠️ Instrucciones Importantes para el uso de la Suite (Visores)

Para acceder a los visores de la Suite (como el Visor de Objetivo 3 o Modelos LMM), debes asegurarte de iniciar correctamente el servidor en segundo plano:

1. Ejecuta el archivo **ABRIR_DASHBOARD.bat** haciendo doble clic **una sola vez**.
2. Se abrirá una ventana negra de consola (cmd) y de forma automática se abrirá la "Suite Central" en tu navegador.
3. **¡IMPORTANTE!** No hagas clic en los botones de "Abrir Visor" de inmediato. Debes esperar a que la ventana de la consola termine de cargar los datos (suele tomar entre 15 a 20 segundos). 
4. Sabrás que ya puedes usar los visores cuando en la consola aparezca exactamente el siguiente mensaje:
   * Running on local URL:  http://127.0.0.1:7860
5. A partir de ese momento, puedes hacer clic libremente en los visores desde el navegador.

> **Nota:** Si la consola indica un puerto diferente (por ejemplo, 7861 o 7862), significa que probablemente ejecutaste el .bat más de una vez. En ese caso, cierra TODAS las ventanas negras de consola que tengas abiertas e inténtalo de nuevo desde el paso 1.
