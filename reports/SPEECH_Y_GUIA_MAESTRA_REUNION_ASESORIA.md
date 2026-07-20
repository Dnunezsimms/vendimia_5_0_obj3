# SPEECH Y GUIA MAESTRA DE OPERACION VISUAL PARA LA REUNION DE ASESORIA TECNICA
**Proyecto Vendimia 5.0 — Objetivo 3 (Madurez y Fenologia Predictiva)**  
**Asesoría Metodológica:** Camilo Riveros | **Fecha:** 10 de julio de 2026  
**Regla de Operación:** Cero lenguaje inflado, máxima rigurosidad biofísica, enfoque pedagógico y co-análisis participativo.  
**Regla Estricta de Proyección en Pantalla:** *Solo se deben mostrar gráficos interactivos, curvas analíticas, diagramas de valles térmicos o los paneles de simulación biofísica. Queda proscrito proyectar semáforos decorativos, tablas de texto largo o tarjetas sin contenido numérico visual.*

---

## ESTRUCTURA EJECUTIVA DE LA REUNION (60 MINUTOS)

La sesión se organiza en **4 Bloques Lógicos** diseñados para no abrumar con información ("no vomitar datos"), sino para invitar a mirar las evidencias visuales y sancionar las decisions metodológicas pendientes:

* **Bloque 1: Madurez Técnica y Generalización Temporal `train 2025 -> test 2026`** (00:00 - 00:20)
* **Bloque 2: Fenología ELP, Valles Térmicos y Pertinencia del Biofix $T_0$** (00:20 - 00:40)
* **Bloque 3: Simulación de Frío (`IFN_acum`), Regresión Simbólica (`PySR`) y API `Datavid`** (00:40 - 00:52)
* **Bloque 4: Cierre Formal y Sanción de los 5 Acuerdos Metodológicos** (00:52 - 01:00)

---

# BLOQUE 1: MADUREZ TECNICA Y VALIDACION TEMPORAL (`train 2025 -> test 2026`)
**Objetivo del Bloque:** Certificar con evidencia empírica por qué la transferencia temporal inter-anual es la única prueba de fuego válida en viticultura y por qué no debemos mezclar variables mecánicas térmicas (`Brix`) con variables de manejo cultural (`Peso de Baya`).

### PASO 1.1: Evaluación Comparativa de Validación (`CV5_row` vs. `train 2025 -> test 2026`)
* 🖥️ **QUÉ GRÁFICO O PANEL MOSTRAR EN PANTALLA:**  
  Abrir el visor interactivo `visualizacion_train2025_test2026.html` y enfocar exclusivamente el **Gráfico de Barras Comparativo de $R^2$ y MAE** (Pestaña 3 del HTML, gráfico principal superior).  
  *(Ruta de respaldo en disco: `C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visualizacion_train2025_test2026.html`)*.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Camilo, buenos días. Para aprovechar tu asesoría metodológica al máximo, queremos hacer un co-análisis directo sobre las decisiones críticas del Objetivo 3, enfocándonos estrictamente en la evidencia visual y en los puntos que revisamos en el Informe de INRIA.  
  > Si miramos este gráfico de barras de nuestra Línea Base Interna V2, comparamos dos mundos opuestos de validación sobre el mismo dataset canónico: en barras grises tenemos la validación cruzada aleatoria (`CV5_row`) y en barras de color tenemos el test temporal estricto donde entrenamos con la vendimia 2024-2025 y evaluamos a ciegas sobre la vendimia 2025-2026 (`train -> test` o `LOFO`).  
  > Como puedes ver en el gráfico, el Sólido Soluble (`Brix`) mantiene un desempeño excelente e intacto en transferencia temporal con un $R^2 = 0.809$ y un error absoluto medio de solo $1.43^\circ\text{ Brix}$. Sin embargo, el Peso de Baya se desploma desde un $R^2$ aparente de $0.84$ en `CV5_row` a un $R^2 = 0.221$ al transferir de año. Queremos poner este contraste sobre la mesa y pedir tu visión sobre por qué `CV5_row` genera una falsa ilusión predictiva por auto-correlación espacial e intra-serie en datos vitivinícolas."*

* 🔬 **SUSTENTO FISICO, AGRONOMICO Y METODOLOGICO (SI PREGUNTA DETALLES):**  
  La validación `CV5_row` intercala observaciones de la misma hilera y semana entre train y test, provocando un *data leakage* territorial severo. La acumulación de azúcar (`Brix`) transfiere excelentemente de un año a otro porque es un proceso termodinámico impulsado por integrales térmicas estacionales. El Peso de Baya, en cambio, depende del balance hídrico del canopia, la carga de poda, el raleo y los turnos de riego presurizado del agrónomo en cada campaña, variables que no son estrictamente estables en el tiempo ni modelables por puro clima.

---

### PASO 1.2: El Respaldo de INRIA sobre Caída Temporal en `SEASON_TRANSFER`
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar directamente las **Figuras 96 y 97 (Página 98)** junto al encabezado numérico de la **Sección 3.8 (Página 94)** del Informe Corfo INRIA (Julio 2026).

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Ahora, si contrastamos nuestro resultado con el cuarto informe de INRIA en las **Figuras 96 y 97 en la página 98** (Sección 3.8), vemos exactamente el mismo diagnóstico independiente: los boxplots de INRIA muestran que cuando sus modelos tabulares se someten a la prueba `SEASON_TRANSFER` (transferencia temporal estricta de una campaña a otra), la varianza del error se amplifica notablemente respecto a las evaluaciones por bloques intra-temporada.  
  > Que nuestra curación canónica V2 logre sostener un $R^2 > 0.80$ en Brix bajo este exacto test temporal confirma que la depuración biofísica que realizamos en las variables de entrada es el cimiento metodológico más confiable del proyecto para la predicción de madurez de cosecha."*

---

### PASO 1.3: Análisis de Componentes Principales (PCA) y Causalidad Fisiológica
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar los **Biplots de Componentes Principales ($PC_1$ vs $PC_2$) de la Figura 44** (y siguientes hasta la 50 en las páginas 39 a 45 del Informe Corfo).

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Finalmente para cerrar el bloque de madurez, miremos los **Biplots de PCA en las Figuras 44 a 50 (Págs. 39 a 45)**. Al proyectar las variables sobre el primer componente principal ($PC_1$), se observa visualmente una colinealidad casi perfecta y directa entre los Sólidos Solubles (`Brix`) y los índices térmicos canónicos (`GDA`, `BEDD_acum`, `IFN_acum`).  
  > En contraste, las Acideces Tartárica/Sulfúrica y el Peso de Baya se proyectan en ejes ortogonales sobre el $PC_2$. Esto nos da una demostración geométrica y matemática de por qué debemos estratificar el tablero de madurez en 3 capas distintas: el azúcar responde al calor acumulado; la acidez responde a la respiración y temperatura nocturna; y el peso obedece al balance hídrico y manejo agrícola."*

---

# BLOQUE 2: FENOLOGIA ELP, VALLES TERMICOS Y PERTINENCIA DEL BIOFIX $T_0$
**Objetivo del Bloque:** Demostrar por qué los modelos fenológicos no pueden iniciar en fechas de calendario fijo (ej. 1 de mayo o 1 de septiembre) y revisar gráficamente cómo el Indicador Biológico detecta el valle de dormancia invernal para fijar el día cero operativo ($T_0$).

### PASO 2.1: El Panel de Valles Térmicos y Pertinencia de Cálculo del Biofix $T_0$
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar el **Gráfico de Valles y Picos Térmicos del Invierno / Regresión Latitudinal de $T_0$** proveniente del módulo del Indicador Biológico (`v2_t0_latitudinal.ipynb`), o en su defecto, graficar en pantalla los datos del archivo canónico `method_pipeline_cs_t0_operativo_by_fundo.csv` mostrando la curva térmica invernal y la fecha en que cada fundo toca su punto de mínima temperatura antes del despertar vegetativo.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Pasando a fenología (predicción de brotación ELP 4 y floración), te invito a mirar este gráfico de **Valles y Picos Térmicos invernales de GDA y temperatura media diaria** para nuestros fundos canónicos.  
  > En la literatura vitivinícola tradicional es común ver que la suma de grados día se inicia mecánicamente el 1 de mayo o el 1 de septiembre por una convención de escritorio. Pero al examinar la curva térmica de la temporada en este gráfico, se hace evidente que cada territorio alcanza su receso invernal profundo (su 'valle térmico') en fechas muy distantes: en el norte (`Quebrada Seca`, latitud -30.5°) el valle térmico y quiebre vegetativo ($T_0$) ocurre el **2 de agosto**, mientras que en la costa sur (`Keule`, latitud -35.8°) el valle se extiende hasta el **29 de agosto**.  
  > Si iniciamos la suma de calor el 1 de mayo, estamos inyectando meses de calor otoñal que la yema en dormancia no metaboliza para brotar. Y si iniciamos el 1 de septiembre, ignoramos semanas completas de calentamiento primaveral en fundos precoces. Por eso desarrollamos nuestro módulo de **Indicador Biológico**: detecta objetivamente este valle térmico ($T_0$) por fundo para iniciar la acumulación de calor justo en el momento biológico pertinente."*

* 🔬 **SUSTENTO FISICO, AGRONOMICO Y METODOLOGICO (SI PREGUNTA DETALLES):**  
  Durante el receso invernal profunda (*endodormancia*), los haces vasculares entre el sarmiento y la yema están obturados por calosa y altas tasas de ácido abscísico (ABA); la acumulación térmica por encima de la temperatura base en mayo o junio no genera división celular ni brotación activa. La planta sólo comienza a sumar calor efectivo (*ecodormancia* / *Forcing*) una vez satisfecho el requerimiento de frío y superado el mínimo térmico invernal ($T_0$).

---

### PASO 2.2: Acumulación Senoidal ($T_c=35^\circ\text{C}$): Biofix $T_0$ vs. Fijo 1 de Septiembre
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar las curvas de acumulación temporal comparadas en el gráfico de líneas del simulador o en el notebook de fenología, mostrando el caso empírico de **Cabernet Sauvignon en Lourdes** frente al caso de **Chardonnay en Keule**.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Para verificar la pertinencia biofísica de este cálculo de $T_0$, miremos el comportamiento de acumulación senoidal con corte superior a 35°C (`gdd_seno_simple`).  
  > Al calcular desde la fecha empírica del mínimo térmico ($T_0$), vemos que el Cabernet Sauvignon alcanza brotación ELP 4 en **Lourdes con 69.35 GDD**, en **Quebrada Seca con 71.02 GDD**, en **Ucuquer con 71.11 GDD** y en **Keule con 71.00 GDD**. ¡Todos los fundos convergen en un umbral hiper-estable de **~70 GDD $\pm 1$ GDD**!  
  > En contraste, si miramos qué ocurre al imponer un calendario fijo de escritorio (1 de septiembre) en **Keule en Chardonnay (`keule_chardonnay`)**, la brotación real ocurrió el **26 de agosto**, es decir, días antes del biofix fijo, arrojando un absurdo matemático de **0.0 GDD al brotar** con un error predictivo de $-9 \text{ días}$. Esto confirma con paridad absoluta que el Biofix $T_0$ no es una sutileza académica, sino una necesidad arquitectónica para el Feature Store del Objetivo 3."*

---

# BLOQUE 3: CLIMA, SIMULADOR DE FRIO E INDICES CANONICOS EN BIGQUERY (PySR Y API `DATAVID`)
**Objetivo del Bloque:** Analizar visualmente la relación compensatoria entre frío invernal y calor primaveral con nuestros datos reales, respaldar el rol crítico del Frío Nocturno (`IFN_acum`) descubierto por `PySR` y plantear el mandato de saneamiento de la API `Datavid` en BigQuery.

### PASO 3.1: Panel Interactivo del Simulador de Frío con Nuestros Datos Reales
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Abrir en vivo el archivo HTML `simulador_frio_datos_reales.html` y enfocar el **Gráfico 1: Curva Chilling-Forcing Empírica con los 7 Fundos del Proyecto** (la curva asintótica azul con los puntos rojos de nuestros fundos).  
  *(Ruta de respaldo en disco: `C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\simulador_frio_datos_reales.html`)*.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Camilo, aquí en nuestro nuevo simulador `simulador_frio_datos_reales.html` graficamos la curva canónica de compensación invernal Chilling-Forcing ($GDD^* = a + b \cdot e^{-c \cdot CP}$) calibrada con los datos de fenología y climatología 2025 de nuestros 7 fundos.  
  > Miremos dónde se posiciona cada territorio en la curva: fundos como **Lourdes** acumulan un invierno muy frío (**342.5 IFN / ~42 CP**), posicionándose en la zona de 'Saturación Óptima de Frío', donde la planta sale limpia de su receso y requiere el mínimo térmico basal para brotar ($\sim 69 \text{ GDD}$).  
  > Pero si movemos la mirada o el deslizador hacia fundos del norte costero o semiarido como **Quebrada Seca** (que acumula solo **195.8 IFN / ~25 CP**), vemos que la planta se sitúa en la zona de 'Déficit de Frío'. En esta zona, al no completar su requerimiento hormonal endodormante, la vid se ve obligada a compensar la falta de frío exigiendo una suma térmica primaveral significativamente mayor para gatillar la brotación. Este simulador nos permite auditar y predecir exactamente cómo se comportarán nuestras variedades frente a inviernos benignos o anomalías del cambio climático."*

* 🔬 **SUSTENTO FISICO, AGRONOMICO Y METODOLOGICO (SI PREGUNTA DETALLES):**  
  El modelo ecofisiológico de Cannell & Smith (1983) y Chuine (2000) demuestra que el frío ($CP$) y el calor ($GDD$) no operan en fases rígidamente separadas en climas templados. Cuando el frío endodormante no es saturante, los promotores enzimáticos intracelulares requieren una mayor dosis de energía cinética térmica (*Forcing*) para degradar los inhibidores hormonales (ABA) y activar la división celular meristemática en la yema.

---

### PASO 3.2: Regresión Simbólica (`PySR`) y Dominancia del Frío Nocturno (`IFN_acum`)
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar los **Heatmaps de Regresión Simbólica (`PySR`) en las Figuras 88 y 89 (Págs. 91 a 93)** del Informe Corfo INRIA.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Este comportamiento del frío encaja perfectamente con uno de los descubrimientos analíticos más sorprendentes del Informe Corfo en la **Figura 89 (Pág. 93)**. Al ejecutar Regresión Simbólica (`PySR`) evaluando millones de combinaciones matemáticas, INRIA descubrió que, para **Sauvignon Blanc**, el **Índice de Frío Nocturno Acumulado (`IFN_acum`)** domina el $>90\%$ de las 25 mejores ecuaciones algebraicas descubiertas por el algoritmo.  
  > Agronómicamente, esto tiene un calce biofísico exacto: la respiración del ácido málico en las uvas blancas acelera de forma exponencial con el calor nocturno ($Q_{10}$). Noches frías (`IFN_acum` elevado) protegen el ácido málico, preservan el pH y regulan la maduración. Este hallazgo valida al 100% que el `IFN_acum` y la suma térmica senoidal (`GDA`) deben ser las variables estructurales columnares de nuestra Capa Canónica V5."*

---

### PASO 3.3: Curvas de Optimización de Complejidad y Saneamiento de `Datavid` en BigQuery
* 🖥️ **QUÉ GRAFICO O PANEL MOSTRAR EN PANTALLA:**  
  Proyectar las **Curvas de Optimización y Saturación de Variables en las Figuras 70, 74, 78 y 82 (Págs. 75 a 87)** del Informe Corfo INRIA.

* 🎙️ **SPEECH TEXTUAL (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Finalmente, en las **Figuras 70 a 82 (Págs. 75 a 87)**, el análisis estadístico de sensibilidad del informe Corfo demuestra que el error predictivo en todas las variedades alcanza su punto de saturación máxima entre las **11 y 17 variables predictoras**. Añadir 40 o 60 variables climáticas o satelitales adicionales no genera ninguna mejora estadísticamente significativa en el error de test.  
  > Por ello, invocando el criterio de parsimonia, queremos plantear un punto crítico de arquitectura para nuestra base de datos canónica en BigQuery: al auditar con climatología la ingesta de la nueva API meteorológica **`Datavid`**, identificamos que Temperatura y Radiación presentan saltos de calibración transitorios. Como nuestros índices (`GDA`, `BEDD_acum`, `IFN_acum`) integran sobre 180 días continuos, solo 4 días con sensores corrompidos fuera de rango deterioran el Feature Store completo. Proponemos encomendar como prioridad prioritaria la implementación en BigQuery de una **Capa Conformance con Truncamiento Estadístico Pre-Ingesta** (filtros intercuartílicos o Hampel) antes del cálculo de integrales térmicas."*

---

# BLOQUE 4: CIERRE TECNICO Y SANCION DE LOS 5 ACUERDOS DE ARQUITECTURA
**Objetivo del Bloque:** Cerrar la reunión firmando formalmente los acuerdos en la bitácora del proyecto sin proyectar texto largo en pantalla (solo mantener el gráfico final de saturación o el simulador mientras se discuten los puntos).

* 🎙️ **SPEECH TEXTUAL DE CIERRE Y SANCION (QUÉ DECIR EN VOZ ALTA A CAMILO):**  
  > *"Camilo, para cerrar este co-análisis con un mandato ejecutivo claro y auditable en nuestro repositorio y para el equipo de modelación de INRIA, proponemos sancionar formalmente en la minuta de hoy estos **5 acuerdos metodológicos vinculantes**:  
  > 
  > 1. **Estandarización del Test de Generalización:** Adoptar la validación temporal estricta `train 2025 -> test 2026` y `LOFO` como el único estándar de evaluación para madurez y fenología, proscribiendo formalmente `CV5_row` en informes técnicos por su sesgo de interpolación intra-serie.  
  > 2. **Estratificación del Dashboard por Predictibilidad:** Segmentar la visualización del Objetivo 3 en tres capas explícitas según su mecanismo biológico: (a) Sólidos Solubles (`Brix`) como modelo térmico primario de alta transferencia; (b) pH y Acideces con bandas territoriales de incertidumbre; y (c) Peso de Baya y Antocianinas como módulo exploratorio de manejo cultural condicionado a datos de riego/poda.  
  > 3. **Protocolo Dual de Biofix Fenológico:** En las predicciones de brotación ELP 4 y floración, utilizar exclusivamente acumulación térmica senoidal ($T_c=35^\circ\text{C}$) iniciada desde el día cero empírico del fundo ($T_0$ operativo por Indicador Biológico / Valle Térmico), con un resguardo de contingencia en el 1 de septiembre para cuarteles sin estación propia.  
  > 4. **Parsimonia e Índices Canónicos V5:** Consolidar como predictores nucleares e innegociables en el Feature Store de BigQuery las variables respaldadas por física vegetal y `PySR`: `gdd_seno_simple_local`, `BEDD_acum`, `PTQ_acum`, e `IFN_acum`, limitando la dimensionalidad tabular al umbral de saturación de 11 a 17 variables.  
  > 5. **Saneamiento Pre-Ingesta (`Datavid` en BigQuery):** Mandatar a la mesa de climatología y arquitectura de datos el diseño e implementación inmediata de una Capa Conformance en BigQuery con truncamiento estadístico intercuartílico pre-ingesta, bloqueando anomalias de sensorización antes de calcular las integrales estacionales de los modelos productivos en Vertex AI.  
  > 
  > ¿Estás de acuerdo en que formalicemos estos 5 puntos como la normativa oficial y hoja de ruta del Objetivo 3 a partir de hoy?"*

---
*Fin del Documento Maestro de Speech y Guía Visual. Todas las rutas HTML y CSV referenciadas están verificadas e implementadas en ambos repositorios (`clean` y `obj3`).*
