# README Técnico — Vendimia 5.0 (Objetivo 3)

## 1. ¿Qué es este repositorio?
Repositorio canónico limpio (endimia_5_0_obj3_clean) para el pronóstico regional de vendimia, acumulación térmica y evolución de madurez fenológica/química en viñedos de la zona central de Chile (temporada 2025-2026).

## 2. Instrucciones de Clonado y Acceso
`ash
git clone <URL_DEL_REPO_PRIVADO>
cd vendimia_5_0_obj3_clean
`

## 3. ¿Cómo abrir el Dashboard localmente?
1. **Entorno Conda:** Asegúrese de tener activo el entorno conda activate vendimia_obj3.
2. **Lanzador Acelerado (Windows):** Haga doble clic en ABRIR_DASHBOARD.bat en la raíz. Esto levantará el servidor local en el puerto 7862.
3. **Acceso Seguro en Navegador:** Abra el archivo ACCESO_DASHBOARD.html en su navegador. Esta página incluye un cliente de sondeo (polling) asincrónico que redirige automáticamente a http://127.0.0.1:7862/ tan pronto como Gradio responde 200 OK, eliminando errores de conexión prematuros.
4. **Ejecución Manual Canónica:**
   `ash
   python models/dashboard_obj3_integrado/app.py
   `

## 4. Arquitectura y Estructura Principal
*   models/dashboard_obj3_integrado/app.py: **Punto de entrada principal** de la interfaz Gradio.
*   models/dashboard_obj3_integrado/src/loaders.py: Módulo centralizado de carga e hidratación del estado global (State).
*   models/dashboard_obj3_integrado/src/config.py: Definición canónica de rutas físicas hacia el layout de datos.
*   data/metadata/climate_coverage/: Tablas de cobertura horaria, gaps climáticos y 	abla_maestra_clima_obj3_2025_2026.csv.
*   data/raw/ & data/processed/: Planillas físicas de control de fenología (phenology/) y curvas consolidadas de madurez (maturity/consolidado_madurez_tintas.csv).
*   models/dashboard_luis/0_0_0_0_Predicciones_Diego_SprintMayo/: Base canónica de 2.054 archivos CSV con métricas de evaluación (Random Forest vs PySR), curvas de predicción e importancias SHAP/Permutación.

## 5. Carga de Paneles e Hidratación
Todos los menús desplegables y gráficos se generan dinámicamente en el arranque consultando las rutas de config.py. El sistema no requiere pre-cálculos ad-hoc para operar visualmente.

## 6. Precisión Metodológica Estricta (Frío Dinámico)
El cálculo de **Frío Dinámico / Chill Portions** (chill_dynamic.py) cumple exclusivamente un rol de **diagnóstico fisiológico y validación de plausibilidad** del receso invernal (biofix). *No constituye todavía un predictor formal u operativo del parámetro t0.* El t0 operativo actual corresponde a un modelo latitudinal candidato.

## 7. Protocolo de Seguridad y Secretos (DataVid)
La ingesta de clima horario operativo (src/ingestion/download_datavid_full.py) requiere autenticación mediante la variable de entorno DATAVID_API_KEY.
*   **PROHIBIDO** versionar o subir archivos .env o credenciales planas al repositorio.
*   Utilice únicamente .env.example como referencia estructural.

## 8. Fuera de Alcance Actual
La migración asincrónica a bases de datos en **Neon PostgreSQL**, interfaces web en **Next.js** y despliegue en **Vercel** queda estrictamente diferida para fases posteriores.
