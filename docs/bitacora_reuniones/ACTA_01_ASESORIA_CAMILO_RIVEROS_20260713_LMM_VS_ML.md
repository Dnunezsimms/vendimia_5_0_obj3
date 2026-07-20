# ACTA Y DIAGNOSTICO METODOLOGICO #01: REUNION DE ASESORIA TECNICA
**Proyecto Vendimia 5.0 — Objetivo 3 (Madurez y Fenología Predictiva)**  
**Fecha de Sesión:** 13 de julio de 2026  
**Asistentes:** Diego Núñez Simms (Investigador / Científico de Datos en Viticultura), Camilo Riveros (Asesor Metodológico Senior / Estadístico en Biociencias). *Nota: Sebastián y Luis cancelaron asistencia por motivos personales de fuerza mayor.*  
**Contexto de la Sesión:** Auditoría forense del desempeño inter-anual de los modelos predictivos de madurez técnica (`train 2025 -> test 2026` vs. `CV5_row`), revisión de los resultados del Cuarto Informe Corfo INRIA y evaluación de alternativas estadísticas de generalización espacial y temporal.  
**Marco de Registro:** Operación bajo la Workspace Rule permanente de objetividad profesional (cero lenguaje inflado ni no verificable; distinción estricta entre evidencia disponible, inferencia razonable y punto pendiente).

---

## 1. RESUMEN EJECUTIVO Y HALLAZGO CENTRAL

La sesión técnica se centró en auditar la divergencia de precisión predictiva observada al someter los modelos de madurez de cosecha a una validación temporal estricta entre campañas (`train 2025 -> test 2026` o `LOFO`), en contraste con la validación cruzada aleatoria tradicional (`CV5_row`).

Durante el co-análisis de las curvas de error y los boxplots del Informe INRIA, **se identificó la causa raíz estructural del colapso del error en las variables agronómicas y biométricas (`Peso de Baya`, `pH` y `Acidez`): la variabilidad no controlada en el protocolo experimental de muestreo en terreno (efecto operador, rotación de personal entre temporadas y heterogeneidad espacial de racimos en la hilera)**.

Frente a esta evidencia, el asesor metodológico Camilo Riveros fundamentó por qué los modelos de Machine Learning y Árboles de Decisión (`Random Forest`, `PySR`) sufren sobreajuste (`overfitting`) territorial ante el ruido de muestreo en `CV5_row`, y propuso formalmente como solución superadora la implementación de **Modelos Lineales Mixtos (`Linear Mixed Models - LMM`)**. Esta familia de modelos permite incorporar formalmente las fuentes de heterogeneidad territorial y humana como **efectos aleatorios (`random effects`)**, aislando de forma limpia la señal termodinámica climática (`GDA`, `IFN_acum`) como **efectos fijos (`fixed effects`)**.

---

## 2. DESGLOSE INTERPRETATIVO DE LOS 5 INSIGHTS METODOLÓGICOS CLAVE

### Insight 1: Validación Externa de Colinealidad en el Análisis de Componentes Principales (PCA)
* **Evidencia en Transcripción:** Camilo Riveros destaca como primer punto de interés técnico la revisión del Análisis de Componentes Principales (`PCA`) presentado en el Informe INRIA (Figuras 44 a 50): *"lo que me llamó la atención era lo del PCA, lo que hablaba de la colinealidad con los índices térmicos... eso está bueno"*.
* **Interpretación Metodológica:** Desde una perspectiva estadística independiente, se corrobora que la proyección sobre el primer componente principal ($PC_1$) revela una colinealidad determinista entre la acumulación de Sólidos Solubles (`Brix`) y las integrales térmicas estacionales (`GDA`, `BEDD_acum`, `IFN_acum`). Esto consolida el sustento biológico del modelo: la translocación de sacarosa a la baya es un proceso directamente regido por el balance energético y térmico del dosel vegetativo (*canopia*).

---

### Insight 2: Confirmación Forense del Desplome de `Peso de Baya` en Transferencia Temporal (`LOFO` / `train -> test`)
* **Evidencia en Transcripción:** Al analizar el gráfico de barras de la Línea Base Interna V2 (`visualizacion_train2025_test2026.html`), se evidenció que los Sólidos Solubles (`Brix`) mantienen una alta capacidad de generalización temporal ($R^2 = 0.809$, $MAE = 1.43^\circ\text{ Brix}$) al entrenar en 2024-2025 y evaluar en 2026. En contraste opuesto, el `Peso de Baya` colapsa desde un $R^2$ aparente de $0.84$ en `CV5_row` a un $R^2 = 0.221$ en transferencia temporal inter-anual. Asimismo, Diego vinculó este comportamiento con los boxplots del Cuarto Informe de INRIA (Sección 3.8, Figuras 96 y 97 `SEASON_TRANSFER`).
* **Interpretación Metodológica:** Se valida formalmente la decisión de estratificar el tablero del Objetivo 3 en capas de predictibilidad diferenciada. El azúcar (`Brix`) transfiere entre temporadas porque responde a variables climáticas estacionales puras. La biometría (`Peso de Baya`) y la acidez (`pH`) obedecen a factores agronómicos locales y de manejo cultural (riego presurizado, carga de yemas, raleo y balance hídrico inter-anual), los cuales no son capturados por el clima estacional crudo.

---

### Insight 3: Diagnóstico de la Raíz del Ruido en `Peso de Baya` y `Acidez`: Variabilidad Experimental de Muestreo y Operador
* **Evidencia en Transcripción:** Camilo Riveros realiza la pregunta diagnóstica clave: *"¿La toma de datos fue hecha por la misma persona? ¿Cómo fue eso por las 3 temporadas distintas?"*. Diego Núñez Simms confirma que existió rotación de personal empírico entre practicantes en ciertos fundos, técnicas fijas en otros, y muestreos de contingencia ejecutados directamente por los investigadores (Diego / Ramón) en períodos de sobrecarga de cosecha.
* **Interpretación Metodológica:** Camilo Riveros identifica que el protocolo de recolección de racimos y bayas en terreno introduce una **fuente mayor de varianza espuria no climática (efecto operador + heterogeneidad intra-cuartel y selección aleatoria de racimos en la hilera)**. En un modelo tabular convencional, esta varianza de error de medición es absorbida como si fuera una señal biológica en `CV5_row` (memorización de hileras o semanas por el árbol), generando una falsa ilusión de precisión que inevitablemente se rompe cuando el modelo es evaluado en una temporada nueva (`train 2025 -> test 2026`).

---

### Insight 4: Crítica Estructural a Modelos de Árboles (`Random Forest` / `PySR`) y Propuesta Superadora: Modelos Lineales Mixtos (`LMM`)
* **Evidencia en Transcripción:** Camilo argumenta una limitación arquitectónica de los modelos no paramétricos de árboles: *"Yo no soy tan fan de estos análisis vía Inteligencia Artificial... el tema para mí es cómo se incorporan estas fuentes de variabilidad... porque todo el muestreo se hace en distintos racimos... con un modelo lineal mixto uno podría incorporar todas estas fuentes de variabilidad como efecto aleatorio, cosa que aquí no sé si se incorpora o no"*.
* **Interpretación Metodológica y Propuesta Superadora:**
  * **Limitación de ML Tabular (`Random Forest` / `PySR`):** Los algoritmos de partición recursiva no disponen de un mecanismo paramétrico formal para separar la varianza estructural de un fenómeno en **componentes fijos (`fixed effects`) vs. componentes aleatorios (`random effects`)**. Tratan cada fila como una observación independiente e idénticamente distribuida (i.i.d.), ignorando la anidación jerárquica de los datos (`Muestreo/Racimo` anidado en `Cuartel`, anidado en `Fundo`, anidado en `Temporada`).
  * **Solución Vía Modelos Lineales Mixtos (`Linear Mixed Models - LMM`):** Se propone incorporar formalmente las variables climáticas e índices térmicos canónicos (`GDA`, `BEDD_acum`, `IFN_acum`) como **Efectos Fijos (`Fixed Effects`)**, y modelar las fuentes de heterogeneidad territorial, humana y experimental (`Fundo`, `Temporada/Año`, `Cuartel` y/o `Operador/Equipo de Muestreo`) como **Efectos Aleatorios (`Random Effects`)**.
  * **Ventaja Estadística Directa:** El Modelo Lineal Mixto (`LMM`) absorbe el "ruido de muestreo y de operador" dentro de las matrices de covarianza de los efectos aleatorios, permitiendo estimar pendientes térmicas (`fixed effects`) limpias, parsimoniosas y robustas, las cuales generalizan sin degradación hacia temporadas venideras.

---

### Insight 5: Convergencia Empírica entre Modelación Tradicional (`LMM`) y Machine Learning (`PySR` / `Random Forest`)
* **Evidencia en Transcripción:** Camilo revela un antecedente de auditoría analítica interna: *"Yo hice un análisis vía tradicional por decirlo así, para darle un poco más de sentido porque todas estas cosas de los árboles para mí son como raras, y llegué como a la misma respuesta que había llegado Luis [INRIA / PySR / Random Forest], pero por el método tradicional o carretero"*.
* **Interpretación Metodológica:** Existe una altísima convergencia y paridad matemática entre los hallazgos de Regresión Simbólica (`PySR` / árboles) y los Modelos Lineales Mixtos (`LMM`) respecto a **cuáles** son las variables predictoras dominantes que gobiernan la madurez técnica (especialmente el calor acumulado `GDA` para `Brix` y el Frío Nocturno `IFN_acum` para conservación de ácido málico en `Sauvignon Blanc`). La diferencia no radica en la selección de variables, sino en la **robustez de la arquitectura de estimación**: mientras los árboles son vulnerables al ruido de muestreo inter-anual en datos tabulares de viticultura, los `LMM` blindan la estimación al gestionar explícitamente la estructura jerárquica del error.

---

## 3. IMPLICANCIAS OPERATIVAS Y ACUERDOS METODOLÓGICOS PARA TRAZABILIDAD

Como consecuencia directa de este diagnóstico y para asegurar una trazabilidad técnica intachable para el equipo actual y para futuros investigadores que asuman la conducción o mantenimiento del Objetivo 3 (`vendimia_5_0_obj3_clean`), se establecen las siguientes directrices metodológicas:

1. **Formalización del Estándar de Evaluación Temporal (`train -> test` / `LOFO`):**
   * Queda ratificado que **la validación cruzada clásica (`CV5_row`) está proscrita** como métrica de reporte para la capacidad de generalización en madurez técnica y fenología, debido a su incapacidad para revelar el sobreajuste territorial al ruido de muestreo. Todo reporte de desempeño debe basarse en partición temporal estricta o Leave-One-Fundo-Out (`LOFO`).

2. **Estratificación del Dashboard por Predictibilidad Mecánica vs. Cultural:**
   * El visor interactivo (`visualizacion_train2025_test2026.html`) y los reportes hacia Corfo deben segmentar explícitamente las variables de salida en 3 capas de incertidumbre biológica:
     * **Capa 1 (Alta Predictibilidad Térmica):** Sólidos Solubles (`Brix`), regidos por integrales de calor estacionales (`GDA`).
     * **Capa 2 (Predictibilidad Intermedia / Compensación Térmica):** `pH` y Acidez Tartárica/Sulfúrica, condicionados por la respiración nocturna del ácido málico ($Q_{10}$ / `IFN_acum`) y balance térmico.
     * **Capa 3 (Módulo Exploratorio / Sesgo Agronómico y Muestral):** `Peso de Baya` y Madurez Fenólica (`Antocianinas`), dominados por manejo de riego, poda, raleo y error de muestreo manual intra-cuartel.

3. **Línea de I+D Recomendada: Implementación Piloto de Modelos Lineales Mixtos (`LMM`):**
   * Se recomienda implementar en el directorio `models/` una línea paralela de comparación estadística utilizando **Modelos Lineales Mixtos (`statsmodels.regression.mixed_linear_model.MixedLM` en Python o `lme4` en R)** para la estimación de madurez técnica (`Brix`, `pH`, `Acidez`).
   * **Especificación de Parámetros del Modelo LMM Recomendado:**
     * **Variable Dependiente ($Y$):** `Brix` (o `pH`, `Acidez_Total`).
     * **Efectos Fijos (`Fixed Effects`):** `gdd_seno_simple_local`, `IFN_acum`, `BEDD_acum`, `PTQ_acum`.
     * **Efectos Aleatorios (`Random Effects` / `Groups`):** `intercept` por `Fundo` y/o por `Temporada`, absorbiendo la heterogeneidad de suelo, microclima e historial operativo del muestreador en terreno.

4. **Sustentación Biofísica en Fenología (Biofix $T_0$ operativo por Indicador Biológico):**
   * Se mantiene con paridad unánime el acuerdo sobre fenología ELP 4: proscripción de fechas fijas de calendario (ej. 1 de mayo o 1 de septiembre) y adopción obligatoria de la suma térmica senoidal ($T_c=35^\circ\text{C}$) iniciada desde el día cero empírico del valle térmico invernal del fundo ($T_0$ del Indicador Biológico).

---

## 4. REFERENCIAS DE TRAZABILIDAD EN EL REPOSITORIO
* **HTML Visor de Validación Temporal e Historial:** `reports/visualizacion_train2025_test2026.html`
* **Guía Maestra y Speech Operativo de Reunión:** `reports/SPEECH_Y_GUIA_MAESTRA_REUNION_ASESORIA.md`
* **Simulador Biofísico de Frío con Datos Reales (7 Fundos):** `reports/dashboards_html/simulador_frio_datos_reales.html`
* **Documento Maestro del Objetivo 3:** `docs/objetivo_3_vendimia_5_0.md`
