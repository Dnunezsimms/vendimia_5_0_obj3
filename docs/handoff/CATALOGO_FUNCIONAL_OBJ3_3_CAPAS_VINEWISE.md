# CATÁLOGO DE REQUERIMIENTOS FUNCIONALES EN 3 CAPAS — OBJETIVO ESPECÍFICO 3
**Proyecto:** Vendimia 5.0 — Plataforma Vinewise (`Módulo Madurez y Fenología Predictiva`)  
**Autor / Auditor Forense:** Diego Núñez Simms  
**Destinatarios:** Miguel Recabarren (`MR` / Arquitectura Vinewise) & Sebastián Vargas Soto (Líder Técnico)  
**Fecha de Emisión / Actualización:** Julio de 2026 (Para entrega de cargo en Septiembre 2026)  
**Ubicación en Repo Canónico:** `docs/handoff/CATALOGO_FUNCIONAL_OBJ3_3_CAPAS_VINEWISE.md`

---

## 1. PROPÓSITO DEL CATÁLOGO Y ARQUITECTURA GENERAL

En cumplimiento con el estándar metodológico e informático acordado con **Miguel Recabarren (`PLT-01`)**, este documento empaqueta todas las funcionalidades desarrolladas e investigadas en el Objetivo Específico 3 (Madurez Técnica, Fenología Predictiva e Índices Bioclimáticos Canónicos) bajo el **Modelo de 3 Capas** de Vinewise:
1. **Capa 1 — Datos (`Data Layer`):** Variables telemetricas crudas desde estaciones meteorológicas y muestreos de laboratorio (`PostgreSQL`).
2. **Capa 2 — Reglas de Negocio y Cálculo (`Business Logic & Models Layer`):** Fórmulas exactas, biofixes ($T_0$), índices térmicos depurados y **Modelos Lineales Mixtos (`LMM` / `statsmodels.MixedLM`)**.
3. **Capa 3 — Presentación y Reportería UI (`Presentation Layer`):** Paneles interactivos HTML, semáforos de madurez, alertas tempranas de cosecha y curvas paralelas por fundo.

Cada ítem cuenta con un indicador de estado para la sesión de filtrado conjunto (`Scrubbing Session / PLT-04`):
* 🟢 **VERDE (Listo / Auditado):** Modelo o fórmula madura, probada forensement con datos reales y lista para embeber en backend o `cron job`.
* 🟡 **AMARILLO (En Desarrollo / Calibración):** Requiere validación de terreno (ej. campaña agosto/septiembre) o parametrización final de coeficientes.
* 🔴 **ROJO (Alta Complejidad / Requiere Decisión):** Depende de adquisición de nuevo hardware (ej. 2ª cámara fenológica) o auditoría especial de base de datos.

---

## 2. MATRIZ DE REQUERIMIENTOS POR CAPAS

### FUNCIONALIDAD 1: BIOFIX FENOLÓGICO Y RECESO INVERNAL ($T_0$)
* **Descripción:** Determinación objetiva y biológica del inicio de la temporada vegetativa ($T_0$) para la acumulación térmica primaveral, reemplazando la fecha fija de calendario (1 de septiembre) por el cumplimiento empírico del receso invernal (`ACTA-03 / Camilo Riveros`).

| Capa Arquitectónica | Especificación Técnica y Detalle Operativo | Estado |
| :--- | :--- | :---: |
| **1. Capa de Datos (`Data Layer`)** | • **Estaciones:** Campbell (INIA), Davis (WeatherLink), Pessl (FieldClimate) o Wiscon del cuartel.<br>• **Variables crudas:** $T_{\text{max}}$ diario, $T_{\text{min}}$ diario, $T_{\text{horaria}}$ (si disponible en BD `PostgreSQL`).<br>• **Frecuencia de lectura:** Diario (a las 00:05 hrs vía *Cron Job* de la plataforma). | 🟢 |
| **2. Capa de Reglas de Negocio (`Business Logic`)** | • **Cálculo de Porciones de Frío (`Dynamic Model` / Horas Frío):** Integración continua desde el 1 de mayo.<br>• **Umbral de Condición Prerrequisito ($T_0$):** Se activa la ventana candidata de inicio cuando la acumulación alcanza el **$>75\text{--}80\%$ del requerimiento canónico de frío** de la variedad en el sitio.<br>• **Auditoría de Valle Térmico:** Si $DOY_{\text{valle}} \ge 20\text{ de agosto}$ y Porciones $\ge 75\%$, fijar $T_0 = DOY_{\text{valle}}$. En el Maule centro/sur suele converger entre el 24 de agosto y el 1 de septiembre; en **Coquimbo / Norte (`Los Acacios`)** puede adelantarse a inicios de agosto (`MET-03`). | 🟢 |
| **3. Capa de Presentación (`UI Layer`)** | • **Semáforo de Receso en Dashboard:** Tarjeta visual por Fundo/Cuartel mostrando: Porcentaje de Frío Acumulado (Barra de progreso $0\to100\%$).<br>• **Alerta Automática:** Notificación emergente o color verde cuando el cuartel alcanza el $T_0$ oficial y comienza a contar Grados-Día de Verano. | 🟢 |

---

### FUNCIONALIDAD 2: ÍNDICES TÉRMICOS CANÓNICOS DE MADUREZ (`BEDD_acum vs. IFN_acum`)
* **Descripción:** Integración térmica diaria y acumulación sin colinealidad redundante (`ACTA-03 / MET-02`), estratificando el motor biofísico según si la variedad es Tinta/Chardonnay o Blanca Temprana (`Sauvignon Blanc`).

| Capa Arquitectónica | Especificación Técnica y Detalle Operativo | Estado |
| :--- | :--- | :---: |
| **1. Capa de Datos (`Data Layer`)** | • **Estaciones:** Red meteorológica central integrada en `PostgreSQL`.<br>• **Input crudo:** $T_{\text{max\_diaria}}$, $T_{\text{min\_diaria}}$, $DOY$ (Día del año desde $T_0$). | 🟢 |
| **2. Capa de Reglas de Negocio (`Business Logic`)** | • **A. Índice de Calor Diurno (`BEDD` - Biologically Effective Degree Days):**<br>  $$BEDD = \max\left(0, \min(T_{\text{max}}, 33^\circ\text{C}) - 10^\circ\text{C}\right) - \text{Ajuste}_{\text{estrés}}$$  (Acumulación integral $\sum BEDD$ desde $T_0$). *Se aplica como predictor primario en Tintas (`Cabernet, Carmenere`) y `Chardonnay`*.<br>• **B. Índice de Frescor Nocturno (`IFN` - Cool Night Index):**<br>  $$IFN = \text{Promedio}(T_{\text{min}}) \quad \text{en el mes previo a cosecha (o } \sum T_{\text{min}} < 14^\circ\text{C})$$<br>  *Se aplica como predictor canónico principal en `Sauvignon Blanc` para modular acidez y pH (`MET-04 / PySR`)*.<br>• **Regla Anti-Colinealidad (`MET-02`):** Prohibido ingresar `GDA` y `BEDD` en el mismo modelo. | 🟢 |
| **3. Capa de Presentación (`UI Layer`)** | • **Gráfico de Acumulación Térmica Temporada Actual vs. Histórico:** Curva temporal ($X = \text{DOY}, Y = BEDD_{\text{acum}}$) comparando la temporada en curso contra el promedio de las últimas 5 temporadas y el año más cálido/frío.<br>• **Indicador Numérico Superior:** Total acumulado a la fecha e intervalo de confianza para llegar a $1,350\text{ BEDD}$ (umbral de cosecha). | 🟢 |

---

### FUNCIONALIDAD 3: MOTOR DE PREDICCIÓN DE MADUREZ TÉCNICA VÍA `LMM` (`Modelos Lineales Mixtos`)
* **Descripción:** Reemplazo definitivo de cajas negras (`Random Forest / PySR`) por **Modelos Lineales Mixtos (`statsmodels.MixedLM`)** para absorber el sesgo y ruido experimental de terreno y operadores (`ACTA-03 / MET-01`).

| Capa Arquitectónica | Especificación Técnica y Detalle Operativo | Estado |
| :--- | :--- | :---: |
| **1. Capa de Datos (`Data Layer`)** | • **Datos Climáticos (`PostgreSQL`):** Series diarias de $BEDD_{\text{acum}}$ e $IFN_{\text{acum}}$.<br>• **Datos de Laboratorio (`Muestreos de Fruta`):** Registros semanales de Sólidos Solubles (`Brix`), pH, Acidez Total Titulable (`g/L H2SO4`) y Peso de Baya (`g`).<br>• **Metadatos de Estructura (`Categorías`):** Fundo (`Lourdes, Idagua, Queule, Los Acacios, Maipo`), Cuartel, Variedad y Temporada (`2024-2025, 2025-2026`). | 🟢 |
| **2. Capa de Reglas de Negocio (`Business Logic / LMM Engine`)** | • **Arquitectura Matemática Canónica (`MixedLM` en Python):**<br>  $$Y_{i,j} = \left( \beta_0 + b_{0,j} \right) + \beta_1 \cdot X_{i,j} + \epsilon_{i,j}$$<br>  Donde:<br>  - $Y_{i,j}$: Variable objetivo (`Brix, pH, Acidez o Peso de Baya`).<br>  - $X_{i,j}$: Predictor térmico canónico ($BEDD_{\text{acum}}$ o $IFN_{\text{acum}}$) como **Efecto Fijo** ($\beta_1$).<br>  - $b_{0,j}$: **Efecto Aleatorio (`Random Intercept`)** agrupado por `Group Var = Fundo:Temporada` (absorbe diferencias de suelo, canopia y ruido/sesgo de operador en terreno).<br>• **Modalidad de Integración en Vinewise (`MR - Modalidad 2`):** El módulo `statsmodels` corre como un script o servicio Python embebido (`micro-backend`) que se ejecuta cada vez que ingresa una nueva muestra de laboratorio a la BD. | 🟢 |
| **3. Capa de Presentación (`UI Layer / Visor Interactivo`)** | • **Panel 1 — Curvas Paralelas LMM:** Gráfico de dispersión donde la línea segmentada negra muestra la Ley Canónica Universal ($\beta_1$) y las líneas de color muestran la trayectoria ajustada de cada Fundo/Cuartel.<br>• **Panel 2 — Barras de Sesgo (`Random Effects`):** Gráfico de barras ordenando qué fundos están atrasados ($b_{0,j} < 0$) o adelantados ($b_{0,j} > 0$) respecto al promedio general.<br>• **Panel 3 — Predicción Semanal de Cosecha:** Proyección en calendario (Fecha estimada en que el cuartel tocará los $23.5^\circ\text{ o }24.0^\circ\text{ Brix}$). | 🟢 |

---

### FUNCIONALIDAD 4: AUDITORÍA FORENSE DE OUTLIERS Y SATURACIÓN EDÁFICA (`El Caso Los Acacios`)
* **Descripción:** Submódulo de monitoreo hídrico/edáfico para detectar anomalías extremas en maduración inducidas por hipoxia o mala infiltración del suelo, como el caso canónico del cuartel `Los Acacios / Coquimbo` (`ACTA-02 / ACT-05`).

| Capa Arquitectónica | Especificación Técnica y Detalle Operativo | Estado |
| :--- | :--- | :---: |
| **1. Capa de Datos (`Data Layer`)** | • **Telemetría de Suelo:** Sensores de Humedad Volumétrica de Suelo (`SWC - Soil Water Content`) o proxies satelitales SAR (`pol_moisture`) y lluvia horaria ($mm/h$).<br>• **Estación Norte (`Los Acacios`):** Nueva estación e instalación programada para **Agosto 2026 (`ACT-03`)**. | 🟡 |
| **2. Capa de Reglas de Negocio (`Business Logic`)** | • **Algoritmo de Detección de Hipoxia / Saturación:** Si Lluvia Acumulada ($24h$) $> 15\text{ mm}$ y tasa de drenaje/infiltración $< \text{Umbral}_{\text{crítico}}$, gatillar estado de `Saturación Edáfica Atípica`.<br>• **Ponderación sobre Madurez:** Ajuste de la tasa de fotosíntesis neta en el modelo térmico temporal hasta la recuperación del drenaje del perfil radicular. | 🟡 |
| **3. Capa de Presentación (`UI Layer`)** | • **Alerta Temprana de Estrés Edáfico:** Semáforo en rojo o amarillo en la vista de mapa del viñedo (`Los Acacios`), advirtiendo al agrónomo que el retraso en Brix no es falta de sol, sino saturación hídrica del suelo. | 🟡 |

---

## 3. ROADMAP Y PASOS PARA LA SESIÓN DE FILTRADO CON MIGUEL (`PLT-04`)
1. **Revisión conjunta de este catálogo:** En la reunión con Miguel y Seba, presentar este archivo fila por fila para validar la viabilidad computacional en el backend de Vinewise.
2. **Priorización para la campaña de vendimia:** Asegurar que las Funcionalidades 1, 2 y 3 entren en **fase de producción web inmediata (Verde)**, dejando la Funcionalidad 4 (Outlier edáfico) condicional a los datos que arroje la nueva estación en agosto.
