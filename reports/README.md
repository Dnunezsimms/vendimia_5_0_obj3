# Reportes y Dashboards HTML (`reports/`) — Objetivo 3 Vendimia 5.0

Este directorio almacena los informes de investigación, literatura de referencia y la **Suite de Dashboards HTML** para visualización interactiva y transferencia tecnológica.

---

## 1. Suite de Dashboards HTML (`dashboards_html/`)
Carpeta dedicada que concentra las interfaces visuales autónomas (sin necesidad de servidor Python activo) generadas para el proyecto. Todos cuentan con nombres cortos, creativos y explicativos:

- 🌐 **`index.html` (Portal de Acceso):** Landing page moderna e interactiva que conecta los 3 visores con un clic.
- ❄️ **`explorador_frio.html`:** *Simulador Interactivo de Compensación Frío-Calor (Chilling-Forcing).* Modela dinámicamente cómo el déficit de frío invernal eleva el requerimiento de calor (GDD) en primavera.
- 📊 **`visor_obj3.html`:** *Visor Integrado Objetivo 3.* Panel 360° que consolida la cobertura climática, el indicador biológico varietal y las predicciones de madurez técnica/fenólica.
- 🗺️ **`mapa_estaciones.html`:** *Mapa de Estaciones Agroclimáticas.* Interfaz georreferenciada con la red de estaciones INIA y RAN conectadas al proyecto.

---

## 2. Scripts Generadores de Visores
Scripts en Python responsables de consultar las bases consolidadas de `data/` y `models/` para compilar los tableros HTML:
- `generate_cold_simulator.py`: Compila y emite `dashboards_html/explorador_frio.html`.
- `build_html_dashboard.py`: Compila y emite `dashboards_html/visor_obj3.html`.

---

## 3. Informes Científicos, Guías de Reunión y Actas de Asesoría (`I+D`)
- `../docs/bitacora_reuniones/ACTA_01_ASESORIA_CAMILO_RIVEROS_20260713_LMM_VS_ML.md`: **Acta y Diagnóstico Metodológico #01 (Asesoría Camilo Riveros, 13/07/2026).** Registro forense que documenta por qué las variables agronómicas (`Peso de Baya`, `pH`) colapsan en generalización temporal debido al ruido en el protocolo manual de muestreo en terreno, crítica a árboles (`PySR`/Random Forest) y propuesta superadora de **Modelos Lineales Mixtos (`LMM`)**.
- `SPEECH_Y_GUIA_MAESTRA_REUNION_ASESORIA.md`: Documento maestro de encuadre y speech operativo utilizado en las asesorías metodológicas senior, restringiendo proyecciones en pantalla a gráficos limpios y curvas de optimización.
- `visor_speech_guia_maestra.html`: Visor ejecutivo HTML en formato de tarjetas de la Guía Maestra de Reunión.
- `metaanalisis_efecto_frio_requerimiento_calor_vid.md`: Síntesis bibliográfica y meta-análisis científico sobre la regulación ecofisiológica del receso invernal y la relación logarítmica/exponencial entre Chilling Portions y GDD en *Vitis vinifera*.
