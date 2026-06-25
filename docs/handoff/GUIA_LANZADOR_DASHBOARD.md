# Handoff Técnico: Arquitectura y Desarrollo del Dashboard (Obj. 3)

Documento de orientación arquitectónica, patrones de diseño e ingeniería sobre el Dashboard Exploratorio Integrado del Objetivo 3. Orientado a científicos de datos e ingenieros de software con dominio de Python.

---

## 1. Stack Tecnológico y Paradigma

La interfaz está construida sobre **Gradio 4.x** (`gradio.Blocks`), un framework declarativo diseñado para aplicaciones de Machine Learning que encapsula un servidor web asincrónico (**FastAPI / Uvicorn**) y un frontend reactivo compilado en Svelte.

### Estructura modular:
* **Punto de entrada:** `models/dashboard_obj3_integrado/app.py`
* **Módulos de soporte (`src/`):**
  * `config.py`: Resolución espacial canónica (`REPO_ROOT` calculado dinámicamente vía `find_repo_root()`), puertos de red y rutas a directorios de datos (*raw*, *prepared*, *outputs*).
  * `loaders.py`: Motor de hidratación. Ingesta las tablas consolidadas, resuelve tipos numéricos y cachea el estado global en memoria (`load_state()`).
  * `plots.py`: Capa de visualización pura. Contiene funciones desacopladas que devuelven objetos `plotly.graph_objects` o figuras de `matplotlib`.

---

## 2. Ciclo de Vida y Flujo de Ejecución

A diferencia de frameworks como Streamlit (que re-ejecuta la totalidad del script de arriba a abajo ante cada interacción del usuario), **Gradio opera bajo un modelo basado en eventos**:

1. **Arranque del Servidor (`app.py:main`)**: Al invocar `python -m models.dashboard_obj3_integrado.app`, el sistema ejecuta `build_app()`.
2. **Hidratación Única**: Se llama a `load_state()`, cargando en la memoria RAM un diccionario maestro (`state`) con todos los DataFrames de fenología, madurez y métricas de modelos (RF/PySR). **Este paso toma ~6 segundos.**
3. **Construcción del Grafo (`gr.Blocks`)**: Se maquetan las pestañas (`gr.Tab`), filas (`gr.Row`) y componentes visuales (`gr.Dataframe`, `gr.Plot`, `gr.Dropdown`).
4. **Enlace de Callbacks**: Las interacciones se registran explícitamente mediante el método `.change()`, vinculando inputs de la UI directamente a funciones de transformación de datos.

---

## 3. Patrones para Edición y Extensión

### A. Añadir una nueva pestaña o gráfico en `app.py`
Para maquetar un nuevo análisis dentro de `build_app()`:

```python
with gr.Tab("Nueva Dimensión Fisiológica"):
    gr.Markdown("### Evaluación de Tasa Follaje/Fruto")
    with gr.Row():
        f_selector = gr.Dropdown(choices=["Cabernet", "Carmenere"], value="Cabernet", label="Variedad")
        f_grafico = gr.Plot()

    # 1. Función transformadora (pura o leyendo de 'state')
    def _generar_grafico_follaje(variedad_sel: str):
        df_sub = state["mi_modulo"][variedad_sel]
        return mi_plot_en_plots_py(df_sub)

    # 2. Binding reactivo
    f_selector.change(
        fn=_generar_grafico_follaje, 
        inputs=[f_selector], 
        outputs=[f_grafico]
    )
```

### B. Modificar esquemas o ingesta de datos (`src/loaders.py`)
Si el pipeline de modelado (`run_pipeline_v2.py`) exporta nuevas columnas o cambia el formato de los CSVs:
1. Actualizar la lógica de lectura dentro de `load_state()` o `read_table()`.
2. Si las variables dinámicas cambian de nombre, ajustar las llamadas a `find_columns(df, ["patrón_buscado"])` en `app.py` para asegurar que Gradio resuelva automáticamente los nuevos headers.

### C. Depuración y Logs
Las trazas de ejecución, advertencias de pandas y excepciones de Gradio se escriben de forma persistente mediante `logging` en:
`models/dashboard_obj3_integrado/logs/dashboard_obj3_integrado.log`

---

## 4. Integración con el Lanzador Nativo Windows

El archivo `ABRIR_DASHBOARD.bat` en la raíz canónica actúa como un *wrapper* operacional para usuarios finales:
1. Resuelve dinámicamente el ejecutable `python.exe` dentro del entorno virtual de Conda (`vendimia_obj3`).
2. Dispara un hilo secundario que abre `ACCESO_DASHBOARD.html`. Esta interfaz implementa un sondeo (`fetch` asincrónico a `http://127.0.0.1:7862`) para enmascarar los segundos de compilación inicial de Uvicorn/FastAPI, redirigiendo al DOM de Gradio únicamente cuando el backend devuelve HTTP 200.

Para despliegues en Linux, contenedores Docker o entornos CI/CD, prescindir del `.bat` e invocar directamente el módulo `app.py`.

---
*Handoff Técnico de Desarrollo - Vendimia 5.0 Obj. 3 (CORFO).*
