# Dashboard exploratorio integrado Obj.3

Dashboard interno de QA cientifico-tecnico para Vendimia 5.0 Objetivo 3.

Ubicacion elegida: `models/dashboard_obj3_integrado`.

La app queda separada del dashboard de Luis para no mezclar objetivos ni modificar su infraestructura, pero reutiliza sus artefactos bajo `models/dashboard_luis/0_0_0_0_Predicciones_Diego_SprintMayo`.

## Ejecutar

```powershell
python models\dashboard_obj3_integrado\app.py
```

Con `uv`:

```powershell
uv run --with gradio --with pandas --with numpy --with plotly --with openpyxl --with pyarrow --with statsmodels python models\dashboard_obj3_integrado\app.py
```

Puerto por defecto: `127.0.0.1:7862`.

## Modulos

- Estado del sistema: cobertura climatica, gaps, equivalencias y tabla maestra.
- Fenologia: salidas GDD/t0 del notebook multisite.
- Madurez tecnica: archivos raw de madurez 2026 y consolidado historico disponible.
- Madurez fenolica: datos preparados y predicciones del trabajo de Luis.
- Modelos: RF/PySR/SR, CV5, LOFO, metricas y prediccion vs observado.
- Interpretabilidad agronomica: SHAP, permutacion y lectura agronomica.
- Integracion conceptual: cadena clima -> fenologia -> madurez -> modelos -> decision.

El dashboard no entrena modelos ni modifica datos originales.
