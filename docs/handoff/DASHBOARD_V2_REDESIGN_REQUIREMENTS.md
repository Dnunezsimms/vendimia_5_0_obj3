# DASHBOARD_V2_REDESIGN_REQUIREMENTS.md

## Propósito

Este documento registra los requerimientos de rediseño del Dashboard Exploratorio Objetivo 3 (Vendimia 5.0), basados en la revisión visual humana del Sprint 2.1 y los lineamientos técnicos del proyecto CORFO.

Es la especificación de referencia para el Sprint 2.2 y los sprints subsiguientes.

---

## Referencia técnica obligatoria

Leer antes de cualquier modificación:

```
docs/objetivo_3_vendimia_5_0.md
```

---

## Estado del sistema / Clima

### Problema actual

El panel actual muestra solo cobertura estática (porcentaje de completitud por fundo). Esto no permite evaluar el comportamiento real de las series climáticas, detectar saltos de calidad, ni visualizar el gradiente temporal de temperatura o acumulación térmica.

### Requerimientos de rediseño

1. **Panel principal: series temporales interactivas**
   - Selector de estación/fundo (basado en equivalencias confirmadas).
   - Selector de variable: `tempMedia`, `tempMinima`, `tempMaxima`, `humedadRelativa`, `radiacion`, `precipitacion`, `dpv` (VPD).
   - Selector de frecuencia disponible: horaria (fuente Datavid, INIA, Zentra) o agregada a diaria.
   - Selector de rango temporal o temporada.
   - Visualización como serie temporal con Plotly. Línea temporal con puntos, marcación de gaps si hay.

2. **Panel secundario: auditoría de cobertura**
   - El gráfico de barras de cobertura % actual se mantiene, pero como panel secundario/colapsable.
   - Tabla de gaps y equivalencias también secundaria.

3. **Si no hay datos suficientes:**
   - Mostrar mensaje técnico claro: qué archivo falta, cuál es la fuente, cómo agregar.
   - No inventar datos ni mostrar gráfico vacío sin explicación.

### Datos disponibles confirmados

| Fuente | Frecuencia | Estaciones | Columnas clave |
|---|---|---|---|
| Datavid (hourly) | Horaria | 48 estaciones | `fecha`, `tempMedia`, `tempMinima`, `tempMaxima`, `humedadRelativa`, `radiacion`, `precipitacion`, `dpv` |
| INIA/Agromet (hourly) | Horaria | 6 estaciones (Los Acacios, Lourdes, Peumo, Rucahue, San Clemente, Villa Alegre) | xlsx nativos |
| Zentra (hourly) | Horaria | 7 estaciones (Idahue, Keule, Nilahue, Pencahue, Qba Seca, Santa Raquel, Ucuquer) | xlsx Zentra nativos |
| **Datavid daily** | **Diaria** | **0 archivos procesados** | **No existe aún en repo limpio** |

> **Nota:** No hay archivos `.parquet` ni `.csv` en `data/raw/climate/daily/`. Los datos horarios existen y pueden agregarse a diario en el loader. Los datos diarios directos deben ser exportados o procesados desde horarios.

### Restricciones

- No descargar datos nuevos sin autorización.
- Si se agregan a diario, hacerlo en memoria en `loaders.py`, no escribir archivos nuevos en `data/raw/`.

---

## Fenología / GDD / T0 / Biofix

### Problema actual

Los paneles actuales heredan outputs del pipeline sin contextualizar adecuadamente la diferencia entre T0 cerrado (retrospectivo) y T0 latitudinal (operativo). El panel GDD no permite explorar el punto de inicio de acumulación. La curva latitudinal del notebook no está exportada al dashboard.

### Requerimientos de rediseño

#### Panel A — Evaluación Operacional del T0 Latitudinal

**Estado actual:** Existe `panel_a_operativo_plot()` en `plots.py`. Muestra error del T0 latitudinal.

**Mejoras requeridas:**
- Título claro: *"Auditoría de Biofix Latitudinal: Residuo vs Brotación ELP4 Observada"*.
- Eje Y: residuo en días con signo (positivo = biofix adelantado, negativo = tardío).
- Línea horizontal en 0, con MAE y sesgo anotados.
- Color por fundo para identificar outliers.
- Los Acacios marcado como diagnóstico/excluido si corresponde.

#### Panel Nuevo — Curva Latitudinal T0/Brotación

**Estado actual:** Esta visualización solo existe en el notebook antiguo `multisite_multivariety_gdd_analysis_v2_t0_latitudinal.ipynb`. **No hay CSV exportado ni función en `plots.py`.**

**Requerimiento:**
- Crear función `latitudinal_regression_plot(diagnostico_df, regresiones_df)` en `plots.py`.
- Usar datos de `diagnostico_cs_reg` (sheet del xlsx canónico) y `regresiones_cs`.
- Mostrar:
  - Eje X: latitud (grados decimales, negativo).
  - Eje Y: DOY (día del año).
  - Scatter de brotación observada por fundo (color), con nombre anotado.
  - Scatter de T0 operativo por fundo.
  - Línea de regresión DOY brotación ~ latitud (pendiente ≈ -5.82, R²=0.86).
  - Línea de regresión DOY T0 ~ latitud (pendiente ≈ -5.07, R²=0.74).
  - Los Acacios marcado explícitamente como excluido de la regresión con símbolo distinto.
  - Leyenda clara diferenciando curva brotación vs curva T0.

> **Los datos YA EXISTEN** en `method_pipeline_summary.xlsx` sheets `regresiones_cs` y `diagnostico_cs_reg`. No es necesario correr el notebook.

#### Panel GDD Acumulado — Nuevo

**Estado actual:** `gdd_progress_bar()` existe pero muestra solo porcentaje de avance relativo al umbral. No permite explorar el punto de inicio (biofix).

**Requerimiento:**
- Crear función `gdd_cumulative_plot(gdd_df, climate_df, biofix_col, biofix_date)` en `plots.py`.
- Selectores en `app.py`:
  - Fundo.
  - Variedad indicadora (Cabernet Sauvignon como referencia).
  - Temporada.
  - Biofix / base de conteo: `1-Jul`, `1-Ago`, `15-Ago`, `1-Sep`, `t0 operativo`, `t0 latitudinal`.
- Mostrar:
  - Curva de GDD acumulado diario desde el biofix seleccionado.
  - Línea vertical en el biofix seleccionado.
  - Línea vertical en T0 operativo.
  - Línea vertical en brotación ELP4 observada.
  - Línea horizontal en umbral GDD (70 GDD base).
  - Valor de GDD acumulado al T0.
  - Advertencia si el biofix es muy temprano (sugiere se contará calor de temporada previa).
  - Advertencia si GDD acumulado al T0 es muy bajo o muy alto respecto al umbral.

> **Problema:** Los datos de series diarias de GDD por fundo no están en el repo limpio. El notebook los calcula desde la serie horaria/diaria. **Se necesita exportar este CSV desde el notebook o calcularlo en `loaders.py` desde los datos horarios.**

#### Panel B — Diagnóstico de Leakage

**Mantener con mejoras menores:**
- Aclarar en título que T0 cerrado es retrospectivo y NO debe usarse operativamente.
- Anotación de cuántos días median entre T0 cerrado y brotación (ventana de leakage).

#### Panel D — Frío Dinámico

**Estado:** Diagnóstico fisiológico pendiente. **NO es predictor de T0 ni de brotación.**

- Mantener como subpestaña.
- Aviso explícito: *"Diagnóstico fisiológico exploratorio. Datos horarios invernales incompletos (cortan Junio 2025). No usar como predictor operativo."*
- No mostrar barras de chill si los datos están incompletos. Solo mostrar el aviso.

---

## Madurez Técnica

> **No tocar en Sprint 2.2.**

Pendiente de revisión de unidades, normalización y diseño de curvas. Se abordará en Sprint 2.3.

---

## Madurez Fenólica

> **No tocar en Sprint 2.2.**

Requiere auditoría de unidades (mg/baya, mg/kg, % extractable) y homologación de variables HPLC/UV-Vis entre temporadas. Se abordará en Sprint 2.3.

---

## Modelos RF / PySR

> **No tocar en Sprint 2.2.**

Requiere rediseño de visualización de métricas (MAE/R² por target_key y scheme) y del scatter observado vs predicho con identificación por fundo/temporada. Se abordará en Sprint 2.4.

---

## Interpretabilidad (SHAP / Permutación)

> **No tocar en Sprint 2.2.**

Requiere traducción agronómica exhaustiva de variables predictoras y reorganización por target. Etiquetas deben explicar en lenguaje de campo qué significa cada predictor. Se abordará junto a Modelos en Sprint 2.4.

---

## Estructura e Identidad del Dashboard

| Elemento | Requerimiento |
|---|---|
| Contacto técnico | Diego Núñez Simms — análisis de datos, modelamiento y trazabilidad del Objetivo 3 |
| INRIA | No debe figurar como responsable ni dueño del dashboard |
| Lenguaje | Técnico sobrio: trazabilidad, diagnóstico, referencia, completitud, advertencia metodológica |
| Export/INRIA tab | Eliminada permanentemente |
| Trazabilidad CORFO | Mantener como pestaña con estado real de actividades 16–22 |

---

## Restricciones del Sprint 2.2

- No hacer commit sin revisión.
- No hacer push sin autorización.
- No merge a main.
- No descargar datos nuevos.
- No modificar datos crudos.
- No tocar Madurez, Modelos ni Interpretabilidad.
- No tocar Vercel ni Neon.

---

## Outputs faltantes que se deben exportar del notebook (antes de implementar Panel GDD)

| Output | Descripción | Estado | Acción requerida |
|---|---|---|---|
| GDD acumulado diario por fundo/temporada/biofix | Series de GDD desde distintos puntos de inicio | **No existe en repo limpio** | Exportar desde notebook o calcular en `loaders.py` |
| `regresiones_cs` + `diagnostico_cs_reg` | Curva latitudinal T0/brotación | ✅ Existe en `method_pipeline_summary.xlsx` | Leer directo desde xlsx |
| `method_pipeline_varietal_evaluation_by_fundo.csv` | Evaluación varietal | ✅ Existe | Leer directo |
| `chill_dynamic_diagnostics_by_fundo_temporada.csv` | Frío dinámico | ✅ Existe (vacío) | Aviso de datos incompletos |
