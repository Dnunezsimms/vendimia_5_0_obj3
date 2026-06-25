# AGENTS.md — Protocolo Estricto para Agentes IA

## Reglas operativas fundamentales

1. **Estado del Repositorio:** Este repositorio ya funciona localmente de forma canónica. No intente refactorizaciones estructurales masivas.
2. **Prohibido `git add .`:** Realice exclusivamente staging controlado por rutas explícitas aprobadas. No versionar carpetas temporales, logs ni reportes obsoletos.
3. **Cero Datos Sintéticos:** No invente ni introduzca datos ficticios, placebos o simulaciones climáticas/fenológicas en las carpetas de datos.
4. **Integridad del Dashboard:** No modifique `config.py`, `loaders.py` o `plots.py` sin verificar localmente la hidratación completa del dashboard en Gradio (`app.py`).
5. **Bloque Frío Dinámico:** No ejecute `chill_dynamic.py` dando por cerrado el cálculo de frío hasta verificar la presencia real de los 7/7 fundos horarios (DataVid + Zentra manual + INIA manual).
6. **Despliegue Web Bloqueado:** No modifique ni prepare integraciones para Vercel, Neon PostgreSQL ni interfaces web externas sin autorización explícita.
7. **Seguridad Absoluta:** Prohibido versionar archivos `.env`, claves de API (`DATAVID_API_KEY`) o cualquier secreto.

---

## Referencia técnica obligatoria del Objetivo 3

**Antes de modificar cualquier componente del dashboard, modelo, interpretabilidad o metodología del Objetivo 3, el agente DEBE leer:**

```
docs/objetivo_3_vendimia_5_0.md
```

Este documento define el marco técnico-operativo formal del Objetivo 3 del proyecto CORFO Vendimia 5.0. Ningún cambio debe contradecir sus lineamientos metodológicos, flujo de trabajo ni restricciones.

---

## Restricciones permanentes del Objetivo 3

- No implementar cambios que contradigan el flujo conceptual del Objetivo 3:
  `Clima → Fenología → Madurez → Modelos → Optimización Multiobjetivo`.
- No afirmar que el bloque de frío invernal (Julio–Octubre 2025) está cerrado o completo.
- No mezclar frío dinámico (Chill Portions, requiere datos horarios) con el predictor formal de T0 latitudinal.
- No presentar el T0 cerrado retrospectivo como predictor operacional.
- No usar lenguaje de marketing o comercial en textos técnicos visibles del dashboard.

## Control de versiones

- `main`: versión estable compartida en GitHub. **No se modifica directamente.**
- `dev/dashboard-v2`: rama activa de desarrollo del dashboard.
- No hacer merge a `main` sin revisión explícita del responsable.
- No hacer push sin autorización.

## Contexto operativo del dashboard

- El dashboard es un explorador técnico de I+D, no un dashboard de producción definitivo.
- Flujo de paneles: Estado del sistema → Fenología → Madurez → Modelos → Interpretabilidad.
- La pestaña `Export / INRIA` no debe existir en el dashboard.
- INRIA no debe figurar como dueño ni responsable del dashboard.
- Contacto técnico: **Diego Núñez Simms** — análisis de datos, modelamiento y trazabilidad del Objetivo 3.

## Estructura de datos inmutable

- `data/raw/`: datos originales. **INMUTABLE. NO MODIFICAR.**
- `data/metadata/climate_coverage/`: CSVs de cobertura climática y asignación fundo–estación.
- `data/raw/climate/hourly/datavid/`: series horarias Datavid (48 estaciones, parquet).
- `data/raw/climate/hourly/inia_agromet/`: series horarias INIA/Agromet (xlsx).
- `data/raw/climate/hourly/zentra/`: series horarias Zentra (xlsx).
- `data/raw/phenology/`: datos fenológicos crudos (xlsx por fundo/variedad).
- `data/processed/phenology_climate/`: outputs procesados fundo×variedad×temporada (28 xlsx).
- `models/indicador_biologico/outputs_multisite_gdd/`: outputs canónicos del pipeline GDD/T0.
