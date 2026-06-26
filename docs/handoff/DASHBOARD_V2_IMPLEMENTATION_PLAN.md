# Sprint Correctivo 2.5: Auditoría de Causas Raíz y Plan de Reconstrucción (Fenología y Madurez Técnica)

Este documento contiene la auditoría obligatoria de causas raíz solicitada por el usuario y el plan de diseño técnico para corregir los 4 módulos funcionales del Dashboard v2 sin alterar datos crudos ni modelos de interpretabilidad.

---

## FASE 1: Auditoría de Causas Raíz

### 1. Causa de Resolución INIA (Horario vs Diario)
* **Diagnóstico Canónico:** Se auditaron los archivos climáticos en `data/raw/climate/daily/inia_agromet`. 
* **Resultado (Caso B confirmado):** Los archivos disponibles en el repositorio limpio contienen **exclusivamente resolución diaria** (1 registro por día, intervalos de 24 horas, ej. `2025-01-01`, `2025-01-02`). No existen observaciones horarias subdiarias cargadas en la fuente INIA de este espacio de trabajo.
* **Causa Raíz:** Al solicitar la serie "horaria" de INIA en la interfaz, el cargador `_load_raw_station_hourly` devolvía la misma tabla diaria que "diaria", aparentando ser clones.

### 2. Confirmación de Sensibilidad Biofix Incompleta
* **Auditoría de Código:** Se revisó `app.py` (líneas 315-340) y `build_gdd_biofix_timeseries.py`. 
* **Causa Raíz:** El selector actual de biofix únicamente filtra el dataframe precalculado `gdd_acumulado_por_biofix.csv` para actualizar las curvas del Panel B. **No ejecuta ningún motor dinámico** que recalcule el umbral biológico en Lourdes, la búsqueda inversa de $T0$ en los demás viñedos ni la regresión lineal latitudinal.

### 3. Causa del Leakage "Calor Previo a T0 = 0.0 GDD" y Ausencia de Valle Tércmico
* **Auditoría de Algoritmo:** En `build_gdd_biofix_timeseries.py`, el cálculo de calor previo verifica `if b_dt < t0_ref_dt: sum(gdd)`. Cuando el usuario selecciona el biofix cerrado operativo o latitudinal, la fecha candidata $b_{dt}$ es idéntica a $t0_{ref}$, haciendo la condición falsa y forzando `0.0 GDD`.
* **Ausencia de Valle Térmico:** El script recorta las series climáticas empezando en la fecha del biofix (`clima_df['Fecha'] >= b_dt`). Al descartar el otoño e invierno previos, imposibilita observar el descenso otoñal y el fondo del valle invernal.

### 4. Causa de Desaparición de Chardonnay y Cobertura de Madurez Técnica
* **Auditoría Comparativa:** En el repositorio antiguo (`C:\projects\vendimia_5_0_obj3`), el cargador `load_maturity_tables()` consumía `consolidado_madurez_tintas.csv` (122 filas) **más** los libros `muestras_blancas_2026.xlsx` (202 filas) y `muestras_tintas_2026.xlsx` (159 filas), totalizando **322 registros consolidados** con 4 variedades (`Chardonnay`, `Sauvignon Blanc`, `Cabernet Sauvignon`, `Carmenere`).
* **Causa Raíz en Repo Limpio:** Durante la limpieza y migración, la carpeta `data/raw/maturity/` del repositorio limpio **solo recibió `consolidado_madurez_tintas.csv`** (122 filas de uvas tintas). Los libros de muestras blancas y 2026 no fueron migrados a dicho directorio.

---

## FASE 2: Matriz Comparativa (Madurez Técnica Antiguo vs Nuevo)

| Dimensión Analítica | Repo Antiguo (`vendimia_5_0_obj3`) | Repo Limpio Actual (`vendimia_5_0_obj3_clean`) | Acción Correctiva Requerida |
| :--- | :--- | :--- | :--- |
| **Archivos Fuente** | `consolidado_madurez_tintas.csv`<br>`muestras_blancas_2026.xlsx`<br>`muestras_tintas_2026.xlsx` | `consolidado_madurez_tintas.csv` *(exclusivamente)* | Copiar archivos `.xlsx` faltantes desde repo antiguo a `data/raw/maturity/`. |
| **Total Filas** | **322** | **122** | Restaurar a 322 filas estandarizadas. |
| **Total Columnas** | **13** *(post normalización)* | **13** | Mantener esquema `prepare_maturity_technical`. |
| **Fundos / Viñedos** | **19 viñedos** | **10 viñedos** | Recuperar los 9 viñedos adicionales (ej. Mariposas, Yungay). |
| **Variedades** | **4** (`Chardonnay`, `Sauvignon Blanc`, `Cabernet Sauvignon`, `Carmenere`) | **2** (`Cabernet Sauvignon`, `Carmenere`) | Reintegrar variedades blancas en el catálogo visual. |
| **Temporadas** | `2024_2025` y `2025_2026` | `2024_2025` | Recuperar controles de vendimia 2026. |
| **Rango de Fechas** | `2025-02-03` a `2026-04-05` | `2025-02-03` a `2025-04-04` | Extender rango temporal completo. |
| **Registros Chardonnay** | **89** | **0** | Restaurar visibilidad canónica. |
| **Registros Sauvignon Blanc** | **75** | **0** | Restaurar visibilidad canónica. |
| **Registros Cabernet Sauv.** | **77** | **63** | Unificar histórico + campaña 2026. |
| **Registros Carmenere** | **81** | **59** | Unificar histórico + campaña 2026. |

---

## FASE 3: Plan de Propuesta Técnica

### 1. Diagnóstico e Interfaz INIA
* En `app.py` y `loaders.py`: Deshabilitar u ocultar la opción "Horaria" cuando la fuente seleccionada sea `INIA/Agromet`.
* Desplegar el mensaje institucional requerido en el gráfico secundario:
  > *"La fuente INIA disponible contiene resolución diaria; no existen observaciones horarias en el archivo cargado."*

### 2. Motor Dinámico de Recálculo Biofix (Paneles A, C, D)
* Implementar función `recalculate_biofix_chain(biofix_date)` en `src/processing/` que:
  1. Calcule en Lourdes el GDD acumulado desde `biofix_date` hasta ELP4 observado para las temporadas disponibles e infiera el umbral promedio `gdd_ref`.
  2. Búsqueda inversa de $T0$ en los demás fundos para alcanzar `gdd_ref`.
  3. Ajuste polinómico lineal latitudinal ($Lat \times DOY$) y actualización de $R^2$, MAE, pendiente e intercepto.
* Conectar este motor al dropdown de Biofix en `app.py` para que al cambiar de candidato se actualicen simultáneamente los Paneles A, C y D.
* **Mapa Contextual (Panel A):** Inyectar silueta cartográfica como marca de agua tenue en segundo plano (`opacity=0.15`), preservando el eje X estrictamente como DOY agronómico sin alineación geométrica forzada.

### 3. Valle Térmico y Suma Móvil (Panel B)
* Reestructurar `build_gdd_biofix_timeseries.py` para cargar ventanas climáticas continuas desde el otoño anterior (1 de mayo del año previo) hasta noviembre.
* Graficar:
  * Curva diaria real de GDD.
  * **Suma móvil térmica (30 días)** que evidencie claramente el monte estival anterior, el descenso otoñal, el fondo del valle invernal y el repunte primaveral.
  * Marcadores verticales de: Fondo del Valle, Fecha de Biofix, $T0$ inferido y Brotación ELP4.
* Corregir algoritmo de calor previo sumando directamente sobre lecturas reales de GDD invernal sin truncar a cero.

### 4. Restauración Integral de Madurez Técnica
* Copiar `muestras_blancas_2026.xlsx`, `muestras_tintas_2026.xlsx` y `muestras_fenoles_2026.xlsx` desde `C:\projects\vendimia_5_0_obj3\data\raw\maturity\` hacia el directorio espejo en el repo limpio.
* Pulir `maturity_curve_grouped()` para ordenar cronológicamente las fechas antes de trazar y evitar conexiones indebidas entre grupos o hileras transversales.

---

## Revisión de Usuario Requerida

> [!IMPORTANT]
> **APROBACIÓN DE EJECUCIÓN:** Confirmar si autoriza proceder con la FASE 3 (ejecución técnica de recálculos y restauración de archivos crudos faltantes en `data/raw/maturity/`). No se aplicará ningún commit ni push sin su revisión posterior del diff.
