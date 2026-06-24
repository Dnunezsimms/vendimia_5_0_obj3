# Vendimia 5.0 – Objetivo Específico 3

## Propósito del documento

Este documento resume el contexto del proyecto **Vendimia 5.0** y define el marco técnico-operativo del **Objetivo Específico 3**. Su propósito es servir como referencia interna del repositorio para orientar tareas de análisis, desarrollo de scripts, consolidación de datos, modelamiento, validación y futuros dashboards asociados a fenología, madurez técnica, madurez fenólica y recomendación de fecha de cosecha.

Debe ser leído antes de modificar pipelines, scripts, notebooks o dashboards asociados al Objetivo 3.

---

## Contexto general del proyecto

**Vendimia 5.0** busca desarrollar un sistema digital integral para apoyar la planificación humano-máquina de la vendimia, optimizando decisiones agrícolas y enológicas mediante modelos predictivos basados en inteligencia artificial explicable (**XAI**).

El problema central que aborda el proyecto es la creciente incertidumbre de la vendimia bajo condiciones de cambio climático. La variabilidad climática afecta el desarrollo fenológico de la vid, la maduración de la uva, la calidad enológica, el momento óptimo de cosecha y la planificación operacional de bodegas.

El proyecto integra información agrícola, climática, fenológica, satelital, enológica y operacional para mejorar la toma de decisiones sobre:

- volumen de cosecha,
- fenología de la vid,
- madurez técnica,
- madurez fenólica,
- fecha óptima de cosecha,
- capacidad fermentativa,
- y planificación de operaciones enológicas.

---

## Objetivo general del proyecto

Desarrollar soluciones predictivas basadas en inteligencia artificial explicable que permitan optimizar los diversos procesos de toma de decisiones involucrados en establecer la cantidad y calidad de las uvas, el momento de su cosecha y la planificación de las operaciones enológicas necesarias para la producción de vino.

---

## Objetivo específico 3

**Desarrollar modelos de inteligencia artificial explicable para predecir el estado fenológico de la vid y la maduración de la uva a partir de variables climáticas, con el objetivo de definir el momento de cosecha mediante un problema de optimización multiobjetivo.**

En términos prácticos, el Objetivo 3 conecta la información climática, fenológica y de madurez con modelos predictivos y rutinas de optimización para apoyar decisiones de cosecha.

---

## Flujo conceptual del Objetivo 3

```text
Datos climáticos observados y predictivos
        ↓
Fenología de la vid / escala ELP
        ↓
Madurez técnica
(Brix, pH, acidez total, peso de baya)
        ↓
Madurez fenólica
(antocianinas, taninos, color, fenoles, HPLC/UV-Vis)
        ↓
Modelos predictivos XAI
        ↓
Optimización multiobjetivo de fecha de cosecha
        ↓
Validación enológica mediante fermentaciones experimentales
```

---

## Hipótesis tecnológica del Objetivo 3

Mediante inteligencia artificial explicable, utilizando datos climáticos observados y predicciones climáticas basadas en modelos, es posible predecir la fenología de la vid mediante la escala ELP.

Además, mediante un problema de optimización multiobjetivo que considere las predicciones de curvas de madurez, es posible encontrar fechas de cosecha que representen distintos compromisos entre:

- maximización de peso de baya,
- valores objetivo de acidez total,
- valores objetivo de azúcar,
- y maximización de calidad fenólica.

---

## Bases de datos relevantes del Objetivo 3

Durante la ejecución del Objetivo 3 se trabaja principalmente con las siguientes bases:

- `muestras_fenologia_2026`
- `muestras_tintas_2026`
- `muestras_blancas_2026`
- `muestras_fenoles_2026`

También existen archivos históricos de referencia de la temporada anterior, ubicados idealmente en:

```text
data/historical_reference/temporada_2024_2025/
```

Estos archivos históricos no deben considerarse datos raw, sino referencias metodológicas para:

- reconstruir asignaciones estación–fundo,
- revisar homologaciones de nombres,
- validar cálculo de índices bioclimáticos,
- comparar estructura de datos entre temporadas,
- y entender decisiones operativas tomadas en la temporada anterior.

---

## Variables climáticas principales

Las variables climáticas esperadas para alimentar modelos fenológicos, de madurez técnica y de madurez fenólica incluyen:

- fecha,
- temperatura media,
- temperatura mínima,
- temperatura máxima,
- humedad relativa,
- precipitación,
- radiación solar,
- velocidad de viento.

### Nombres estándar sugeridos

```text
fecha
temperatura_media_C
temperatura_min_C
temperatura_max_C
humedad_media_%
precipitacion_total_mm
radiacion_solar_total_MJ_m2
velocidad_viento_media_m_s
```

---

## Índices bioclimáticos de interés

A partir de las variables climáticas se podrán calcular y consolidar índices como:

- **GDD**: acumulación térmica.
- **BEDD**: calor biológicamente efectivo.
- **VPD**: déficit de presión de vapor / estrés atmosférico.
- **HEP / Hef**: horas térmicas efectivas.
- **STa**: estrés térmico acumulado.
- **IE**: índice de estrés.
- **PTQ**: cociente fototermal.
- **IFN / IFs**: índices fenológicos.
- **IFTB / IFTT**: índices térmicos de maduración.

Estos índices deben documentarse claramente antes de su uso en modelos, indicando fórmula, unidad, ventana temporal, supuestos y fuente de datos.

---

## Actividades específicas asociadas al Objetivo 3

Las actividades técnicas del Objetivo 3 corresponden a las actividades 16 a 22 del plan de trabajo, más la actividad transversal 32.

### Actividad 16 – Integración de predicciones climáticas

**Nombre:** Integrar y comunicar datos de predicción de modelos climáticos para la estimación de la fenología de la vid.

**Periodo:** Meses 1–12.

**Responsable principal:** Subcontrato / Equipo INRIA.

**Descripción:** Integrar bases de datos provenientes de modelos de predicción climática como GFS/NOAA y ECMWF a las bases locales del proyecto, mediante API, servicios SFTP u otros mecanismos equivalentes.

**Relevancia:** Permite alimentar modelos fenológicos y de madurez con información climática futura, habilitando predicciones dinámicas de fenología, maduración y posibles fechas de cosecha.

---

### Actividad 17 – Modelo predictivo fenológico ELP

**Nombre:** Elaborar y validar un modelo predictivo del estado fenológico de la vid a través de la escala ELP a partir de información agroclimática.

**Periodo:** Meses 1–36.

**Responsables:** Beneficiaria, INRIA, Asistente de Investigación Agrícola, Sebastián Vargas, Álvaro González, Genoveva Rojas, Ricardo Luna, Rodrigo Acevedo y Francisco Juanicotena.

**Descripción:** Monitorear el desarrollo fenológico de la vid mediante observaciones visuales y visión computacional, integrando esta información con datos climáticos de estaciones cercanas para evaluar modelos fenológicos existentes y desarrollar nuevos modelos predictivos.

**Relevancia:** Constituye el núcleo fenológico del Objetivo 3. Permite anticipar estados como brotación, floración, cuaja, pinta y maduración, usando datos climáticos observados y predichos.

---

### Actividad 18 – Recopilación histórica de madurez

**Nombre:** Recopilar información histórica del seguimiento de madurez de uvas blancas y tintas.

**Periodo:** Meses 1–6.

**Responsables:** Beneficiaria, Héctor Urzúa, Carolina Cortés y Manuel Celis.

**Descripción:** Recolectar información histórica de monitoreo de madurez disponible en viñedos y bodegas de la compañía, idealmente para al menos los últimos diez años.

**Relevancia:** Aumenta el set de datos y permite representar una mayor diversidad de condiciones meteorológicas, variedades, calidades, sistemas de conducción y zonas vitivinícolas.

---

### Actividad 19 – Monitoreo de madurez técnica y fenólica

**Nombre:** Recolectar y analizar uvas blancas y tintas para monitorear el seguimiento de madurez en función de cambios de pH, Brix, acidez total, peso de baya y calidad fenólica.

**Periodo:** Meses 1–48.

**Responsables:** Beneficiaria, Asistente de Investigación Agrícola, equipo de laboratorio, enología, viticultura y áreas agrícolas.

**Descripción:** Realizar monitoreo semanal desde pinta hasta dos semanas después de cosecha, considerando variables de madurez técnica y fenólica. Se contempla monitorear aproximadamente 50 bloques y, para un subconjunto, analizar fenoles mediante técnicas como espectrofotometría, UV-Vis y HPLC.

**Relevancia:** Genera la base experimental principal para modelar la evolución de madurez técnica y fenólica, y para vincular clima, fenología, composición de uva y calidad final.

---

### Actividad 20 – Modelos predictivos de madurez

**Nombre:** Elaborar y validar modelos predictivos de la evolución de pH, Brix, acidez total, peso de baya y calidad fenólica a través del tiempo entre pinta y cosecha.

**Periodo:** Meses 12–49.

**Responsables:** Subcontrato / INRIA, equipo técnico agrícola y enológico.

**Descripción:** Seleccionar y entrenar algoritmos de machine learning para predecir curvas de evolución de madurez desde pinta hasta cosecha. Para cada variable de respuesta se evaluarán métricas como R², error absoluto promedio, costo computacional, simplicidad e interpretabilidad.

**Relevancia:** Convierte los datos de madurez técnica y fenólica en modelos predictivos utilizables para anticipar el estado futuro de la uva con horizontes de 15 y 30 días.

---

### Actividad 21 – Optimización multiobjetivo de fecha de cosecha

**Nombre:** Formular y ejecutar un problema de optimización multiobjetivo que estime una fecha de cosecha óptima en función de variables como grado Brix, acidez total, tamaño de baya y calidad fenólica.

**Periodo:** Meses 36–49.

**Responsables:** Subcontrato / INRIA, equipo técnico agrícola y enológico.

**Descripción:** Formular un problema de optimización multiobjetivo que utilice modelos de madurez alimentados por predicciones climáticas. Se considera el uso de algoritmos evolutivos como NSGA-II, implementados en Python mediante frameworks como `pymoo`.

**Relevancia:** Traduce las predicciones en una recomendación práctica de fecha o ventana de cosecha, considerando múltiples objetivos agronómicos y enológicos simultáneamente.

---

### Actividad 22 – Validación enológica mediante fermentaciones

**Nombre:** Fermentar lotes de uvas en fechas de cosecha óptima, adelantada y atrasada para validar calidad final del vino.

**Periodo:** Meses 1–48.

**Responsables:** Beneficiaria, bodega experimental, laboratorio, enología y equipo técnico.

**Descripción:** Seleccionar bloques monitoreados y cosechar lotes en distintas fechas alrededor de la cosecha industrial, fermentándolos bajo protocolos homogéneos del Centro de Investigación.

**Relevancia:** Permite validar si las predicciones de fenología y madurez se reflejan en diferencias reales de composición fisicoquímica y calidad sensorial del vino.

---

### Actividad 32 – Actividad transversal de gestión

**Nombre:** Actividades transversales y habilitantes para el I+D y gestión del proyecto.

**Periodo:** Meses 1–60.

**Responsables:** Beneficiaria, Bárbara Valenzuela, Alejandro Donoso y equipo administrativo-financiero.

**Descripción:** Rendición financiera, control presupuestario y preparación de información legal, contable y financiera.

**Relevancia:** No es una actividad técnica específica del Objetivo 3, pero sostiene administrativamente la ejecución del proyecto y está asociada a los objetivos 1, 2, 3, 4 y 5.

---

## Relación entre actividades del Objetivo 3

```text
Actividad 16
Predicción climática
        ↓
Actividad 17
Modelo fenológico ELP
        ↓
Actividad 18 + Actividad 19
Datos históricos + monitoreo actual de madurez
        ↓
Actividad 20
Modelos predictivos de madurez técnica y fenólica
        ↓
Actividad 21
Optimización multiobjetivo de fecha de cosecha
        ↓
Actividad 22
Validación enológica mediante fermentaciones
```

---

## Estado operativo actual recomendado para el repositorio

Este repositorio debe priorizar, en esta etapa, la consolidación y validación de datos antes de construir dashboards definitivos.

### Prioridad 1: clima

Consolidar datos climáticos observados y revisar cobertura por:

- fundo,
- estación,
- fuente/red,
- temporada,
- variable,
- frecuencia temporal,
- calidad y completitud.

### Prioridad 2: homologación

Estandarizar nombres de:

- fundos,
- estaciones,
- variedades,
- temporadas,
- variables climáticas,
- variables de madurez,
- y estados fenológicos.

### Prioridad 3: integración temporal

Alinear las bases por:

- fecha,
- temporada,
- DOY,
- GDD,
- fundo,
- cuartel,
- variedad,
- estado fenológico,
- muestra de madurez.

### Prioridad 4: tabla maestra

Construir una tabla integrada tipo:

```text
fundo
cuartel
variedad
temporada
fecha
doy
gdd
elp_observado
brix
ph
acidez_total
peso_baya
antocianinas
taninos
indice_color
fuente_clima
estacion_clima
calidad_dato
```

Esta tabla puede contener valores faltantes, pero debe conservar trazabilidad sobre fuente, disponibilidad y calidad.

---

## Convenciones técnicas recomendadas

### Estructura sugerida

```text
data/
├── raw/
│   └── climate/
├── interim/
├── prepared/
├── historical_reference/
│   └── temporada_2024_2025/
└── external/

reports/
└── climate/
    └── coverage/

src/
├── diagnostic/
├── data_processing/
├── features/
├── models/
└── visualization/

docs/
└── objetivo_3_vendimia_5_0.md
```

### Filosofía de desarrollo

Priorizar:

- trazabilidad,
- reproducibilidad,
- robustez,
- modularidad,
- logs claros,
- validaciones explícitas,
- documentación,
- y compatibilidad con futuras temporadas.

Evitar:

- rutas absolutas,
- hardcodes innecesarios,
- transformaciones silenciosas,
- mezcla de datos raw con datos procesados,
- notebooks como única fuente de lógica,
- dashboards monolíticos,
- y decisiones automáticas sin justificación.

---

## Reglas para scripts y notebooks del Objetivo 3

Todo script o notebook nuevo debe:

1. Usar rutas relativas al repositorio.
2. No modificar archivos raw.
3. Guardar outputs en `data/interim`, `data/prepared` o `reports`, según corresponda.
4. Registrar supuestos metodológicos.
5. Documentar fuentes utilizadas.
6. Generar logs o resúmenes de ejecución.
7. Mantener columnas clave de trazabilidad.
8. Reportar datos faltantes o inconsistentes.
9. Separar claramente diagnóstico, procesamiento, modelamiento y visualización.
10. Ser reutilizable para temporadas futuras.

---

## Consideraciones para dashboards

No se recomienda construir un dashboard final integrado hasta contar con:

- clima consolidado y validado,
- homologación de fundos y estaciones,
- madurez técnica integrada con clima,
- madurez fenólica consolidada,
- estructura clara de tabla maestra,
- y criterios definidos de calidad de datos.

En la etapa actual, sí es recomendable construir dashboards exploratorios o módulos internos de I+D para:

- revisar cobertura climática,
- comparar estaciones candidatas,
- visualizar fenología por fundo/variedad,
- comparar curvas de madurez,
- revisar predicción vs observado,
- evaluar modelos PySR y Random Forest,
- y detectar inconsistencias de datos.

---

## Relación con inteligencia artificial explicable

Los modelos del Objetivo 3 deben buscar no solo buen desempeño predictivo, sino también interpretabilidad agronómica y enológica. Esto implica revisar:

- importancia de variables,
- sensibilidad climática,
- coherencia biológica,
- estabilidad entre temporadas,
- diferencias por variedad,
- diferencias por fundo,
- y capacidad de explicar resultados a usuarios agrícolas y enológicos.

---

## Uso esperado de este documento

Este documento debe usarse como contexto base para:

- prompts a Codex,
- diseño de scripts,
- revisión de pipelines,
- diagnóstico climático,
- integración de bases,
- planificación de dashboards,
- documentación del repositorio,
- y coordinación con equipos técnicos o nuevos colaboradores.

Cuando se solicite ayuda a una IA dentro del repositorio, se recomienda indicar:

```text
Antes de comenzar, lee docs/objetivo_3_vendimia_5_0.md y respeta el marco técnico del Objetivo 3.
```

---

## Fuentes internas usadas para este resumen

- Postulación proyecto Vendimia 5.0 – CORFO.
- Plan de Trabajo y Presupuesto Vendimia 5.0, hoja `PLAN DE TRABAJO`.
- Conversaciones y criterios operativos definidos para consolidación climática, fenología, madurez técnica y madurez fenólica de la temporada 2025–2026.
