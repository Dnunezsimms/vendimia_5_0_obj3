# Documentación Técnica (`docs/`) — Objetivo 3 Vendimia 5.0

Este directorio concentra la documentación oficial, científica y operativa que rige el desarrollo del **Objetivo Específico 3** del proyecto Vendimia 5.0.

---

## Documento Maestro Obligatorio

### 📖 [objetivo_3_vendimia_5_0.md](file:///c:/projects/vendimia_5_0_obj3_clean/docs/objetivo_3_vendimia_5_0.md)
Es el **marco técnico-operativo formal** de todo el proyecto. Define:
- Las hipótesis biológicas y agronómicas del proyecto.
- Las actividades formales (Actividades 16 a 22 y transversal 32).
- Las variables climáticas canónicas y los índices bioclimáticos de interés (GDD, BEDD, VPD, HEP, etc.).
- Las reglas estrictas para el diseño de pipelines y notebooks.

> [!IMPORTANT]
> **Lectura Obligatoria:** Cualquier investigador, colaborador o agente IA **debe leer y comprender** `objetivo_3_vendimia_5_0.md` antes de proponer cambios estructurales, modificar modelos de madurez o alterar dashboards.

---

## Bitácora de Auditorías Metodológicas y Reuniones Técnicas (`bitacora_reuniones/`)

Este directorio conserva la **trazabilidad histórica y el diagnóstico forense** de las reuniones técnicas de asesoría e investigación, sirviendo como registro auditable para la toma de decisiones metodológicas y para el traspaso ordenado a nuevos investigadores o ingenieros:

- `ACTA_01_ASESORIA_CAMILO_RIVEROS_20260713_LMM_VS_ML.md`: **Acta y Diagnóstico Metodológico #01 (Sesión con Camilo Riveros, 13 de julio de 2026).** Documenta el hallazgo forense sobre por qué el `Peso de Baya` colapsa en generalización temporal inter-anual debido a la variabilidad no controlada del muestreo manual y rotación de personal (efecto operador/racimo), la crítica estructural a los modelos de árboles (`Random Forest` / `PySR`), y la propuesta superadora de implementar **Modelos Lineales Mixtos (`Linear Mixed Models - LMM`)** para modelar la heterogeneidad territorial como efectos aleatorios (`random effects`).

---

## Subdirectorio de Traspaso y Planificación (`handoff/`)

Contiene especificaciones de arquitectura, requisitos de rediseño y guías técnicas para el equipo de desarrollo:
- `README_TECHNICAL.md`: Arquitectura técnica interna y dependencias del sistema.
- `GUIA_LANZADOR_DASHBOARD.md`: Manual operativo para el despliegue local y manejo de entorno de los visores Gradio.
- `DASHBOARD_V2_*.md`: Documentos de backlog, plan de implementación y requerimientos de rediseño para la interfaz integrada del Objetivo 3.
