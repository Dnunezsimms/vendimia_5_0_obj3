# PLAN MAESTRO Y ROADMAP DE TRASPASO DE CARGO (ENTREGA SEPTIEMBRE 2026)
**Proyecto:** Vendimia 5.0 — Objetivo Específico 3 (Madurez y Fenología Predictiva)  
**Titular del Cargo / Autor:** Diego Núñez Simms  
**Líder Técnico / Receptor:** Sebastián Vargas Soto (`Seba`)  
**Arquitectura e Integración:** Miguel Recabarren (`MR` / plataforma) & Camilo Riveros (Asesoría Científica)  
**Fecha de Emisión del Documento:** 17 de julio de 2026  
**Ubicación Canónica (`clean`):** `docs/handoff/HANDOFF_CARGO_OBJETIVO_3_ROADMAP_SEPTIEMBRE_2026.md`

---

## 1. RESUMEN EJECUTIVO Y OBJETIVO DE LA ENTREGA DE CARGO

Este documento formaliza la hoja de ruta (`Roadmap`) para la entrega ordenada, trazable y forensement auditable del cargo de Diego Núñez Simms en el Objetivo Específico 3 para el mes de **septiembre de 2026**.

El propósito fundamental es consolidar todo el trabajo científico, algorítmico y de auditoría de campo realizado durante las temporadas $2024\text{--}2025$ y $2025\text{--}2026$ en un **paquete interoperable y listo para producción (`Turnkey Delivery`)**, garantizando que el nuevo encargado o el equipo central (`Seba / Miguel / Luis`) pueda ejecutar las predicciones de madurez, biofixes y reportería sin pérdida de continuidad ni cajas negras.

---

## 2. ARQUITECTURA DE REPOSITORIOS Y ESTADO DEL ARTE (`LO QUE SE ENTREGA`)

El trabajo se encuentra dividido estratégicamente en dos repositorios paralelos:

```
[Repositorio de Trabajo e Investigación Cruda]
C:\projects\vendimia_5_0_obj3\
 ├── data/prepared/modeling/        # Bases canónicas de madurez y clima (540 muestras censadas)
 ├── reports/                       # Dashboards HTML interactivos, visores LMM y actas de terreno
 └── exports/inria/                 # Paquetes enviados y recibidos en las auditorías cruzadas con INRIA

                   ║
                   ▼ (Sincronización Curada y Trazable para Handoff)
                   ║

[Repositorio Limpio Instituciona / Entrega de Cargo]
C:\projects\vendimia_5_0_obj3_clean\
 ├── docs/bitacora_reuniones/       # ACTAS OFICIALES Y DECISIONES SANCTIONADAS (Seba, Camilo, Miguel)
 ├── docs/handoff/                  # CATÁLOGO DE 3 CAPAS (plataforma), ROADMAP y guías de traspaso
 ├── src/processing/                # Scripts de integración climatológica y biofixes (T0 / GDD)
 └── models/indicador_biologico/    # Notebooks canónicos de valles térmicos y gradiente latitudinal
```

### Principales Logros Científicos y Herramientas Operativas Dejadas en Producción:
1. **Migración Arquitectónica de Cajas Negras a Modelos Lineales Mixtos (`LMM` / `statsmodels`):**  
   Se superó el colapso de transferibilidad en biometría (`Peso de Baya` LOFO) integrando el clima (`BEDD_acum`) como Efecto Fijo y las fuentes de ruido de terreno/operadores (`Fundo:Temporada`) como Efecto Aleatorio (`ACTA-03 / Camilo Riveros`).
2. **Eliminación de la Colinealidad Redundante (`XAI`):**  
   Se fijó un único índice térmico canónico por modelo (`BEDD_acum` para Tintas/Chardonnay e `IFN_acum` para `Sauvignon Blanc`), eliminando la inflación espuria del $R^2$ observada en reportes automáticos (`PySR / PCA`).
3. **Establecimiento del Biofix Fisiológico ($T_0$):**  
   Se formuló la regla de activación del receso invernal basada en el cumplimiento canónico de $>75\%$ de porciones de frío, eliminando el inicio arbitrario del 1 de septiembre (`MET-03`).
4. **Empaquetamiento en Catálogo de 3 Capas para plataforma:**  
   Traducción completa del Objetivo 3 (Datos $\to$ Cálculo $\to$ UI) para su consumo en la base de datos `PostgreSQL` en nube (`PLT-01 / Miguel Recabarren`).

---

## 3. ROADMAP Y CRONOGRAMA DE TRASPASO (`JULIO — AGOSTO — SEPTIEMBRE 2026`)

```
   [ JULIO 2026 ]                   [ AGOSTO 2026 ]                  [ SEPTIEMBRE 2026 ]
  Sincronización y                 Campaña de Terreno               Campaña Maipo y
  Catálogo 3 Capas                 Norte & Auditoría                Entrega Formal de Cargo
────────────────────             ─────────────────────            ───────────────────────────
 • Consolidar Actas (✔️)          • HITO CRÍTICO: Viaje a          • HITO CRÍTICO: Viaje a
 • Entregar Catálogo               Coquimbo (`Los Acacios`)         Valle del Maipo e
   3 Capas a Miguel (✔️)           para instalar Estación y         instalación de Estación.
 • Coordinar OC de                 Cámara Fenológica antes        • Traspaso de credenciales
   Cámaras con Daniel              de brotación ($T_0$).            PostgreSQL y validación
 • Sesión de filtrado            • Auditoría edáfica del            en vivo del backend LMM.
   conjunto (`PLT-04`).            outlier `Los Acacios`.         • Firma de Acta de Handoff.
```

---

## 4. MATRIZ DE DELIMITACIÓN: LO QUE EL AGENTE AI ELABORÓ vs. REVISIÓN MANUAL DE DIEGO

Para garantizar un traspaso sin cabos sueltos, a continuación se distingue con absoluta transparencia y rigor forense qué artefactos y modelos han sido elaborados automatizada y científicamente, y qué ítems **deben ser verificados y gestionados manualmente por Diego en terreno y con el equipo humano**:

### A. LO QUE EL AGENTE AI YA ELABORÓ Y DEJÓ EN EL REPOSITORIO (`LISTO PARA TRASPASO`)
* ✔️ **Actas Oficiales Institucionales Sincronizadas (`docs/bitacora_reuniones/`):**
  * `ACTA_02_SEBASTIAN_LOGISTICA_Y_OUTLIERS_20260717.md`
  * `ACTA_03_CAMILO_RIVEROS_LMM_Y_COLINEALIDAD_20260717.md`
  * `ACTA_04_MIGUEL_RECABARREN_PLATAFORMA_Y_CATALOGO_3_CAPAS_20260717.md`
* ✔️ **Catálogo Canónico en 3 Capas de plataforma (`docs/handoff/`):**
  * `CATALOGO_FUNCIONAL_OBJ3_3_CAPAS_plataforma.md` (Traduce el LMM, los índices BEDD/IFN, el biofix y los dashboards al formato exigido por Miguel).
* ✔️ **Código y Visores Interactivos de Diagnóstico (`LMM Engine`):**
  * Script `build_html_dashboard.py` y salida HTML `visor_lmm_madurez_obj3.html` con 4 paneles interactivos demostrando el ajuste canónico y los efectos aleatorios.
* ✔️ **Borradores de Comunicación Gubernanza / Proveedores:**
  * Correo formal y cercano a Daniel (proveedor de cámaras) justificando la prioridad de la campaña de agosto en Coquimbo (`Los Acacios`).

---

### B. LO QUE DIEGO DEBE REVISAR Y EJECUTAR MANUALMENTE POR SU CUENTA (`CHECKLIST DE CAMPO Y GESTIÓN HUMANA`)

> [!IMPORTANT]
> **1. Seguimiento Administrativo y Logístico con Daniel (`ACT-01 / Cámaras Fenológicas`)**
> * **Acción Manual:** Enviar o llamar personalmente a Daniel con la propuesta de correo generada, hacer seguimiento a la liberación de los recursos de la Orden de Compra (`OC` - plazo 30 días) y confirmar la disponibilidad física de una segunda unidad para agosto.
> * **Verificación de Hardware en Lab (`ACT-02`):** Revisar físicamente en el laboratorio, formatear e insertar las tarjetas SD en la cámara fenológica existente para asegurar que esté encendida y transmitiendo antes del viaje.

> [!CAUTION]
> **2. Campañas de Instalación en Terreno (`ACT-03 y ACT-04` — Hitos Impostergables de Agosto y Septiembre)**
> * **Campaña Agosto (Norte / `Los Acacios` - Coquimbo):** Ejecutar presencialmente con Seba el viaje de instalación al norte antes de la brotación invernal (*"en agosto hay que ir para allá sí o sí"*). Calibrar la cámara apuntando a las parras canónicas del ensayo.
> * **Campaña Septiembre (Valle del Maipo):** Ejecutar presencialmente con Seba el montaje de la estación meteorológica en Maipo.

> [!WARNING]
> **3. Auditoría Forense de Terreno sobre el Outlier `Los Acacios` (`ACT-05`)**
> * **Acción Manual:** En el viaje al Norte en agosto, inspeccionar *in situ* el perfil del suelo y las calicatas/drenajes del cuartel `Los Acacios`. Corroborar con el administrador de campo la hipótesis técnica conversada con Seba: si la saturación por lluvias lentas/fuertes efectivamente provoca asfixia radicular temprana y retrasa la madurez.

> [!TIP]
> **4. Supervisión de Calidad en Toma de Muestras de Laboratorio (`Control de Ruido Humano / Camilo`)**
> * **Acción Manual:** Dado que Camilo identificó que la rotación de practicantes y técnicos desplomó la transferibilidad del `Peso de Baya`, Diego debe reunirse con la técnico de terreno fija o redactar un instructivo corto estandarizando la cosecha de racimos para la campaña 2026-2027 antes de entregar el cargo, blindando la recolección de fruta contra sesgos de operador.

> [!NOTE]
> **5. Sesión Técnica de Interoperabilidad con Miguel Recabarren (`PLT-02, PLT-03 y PLT-04`)**
> * **Acción Manual:** Agendar y liderar presencial/virtualmente con Seba y Miguel la reunión de filtrado del Catálogo de 3 Capas (`Scrubbing Session`). Confirmar directamente con Miguel las credenciales de acceso a `PostgreSQL` y verificar que su base de datos esté recibiendo en vivo y sin baches las variables Campbell/INIA/Davis que necesita el backend de Python `LMM`.

---

## 5. CONCLUSIÓN Y CIERRE DE ETAPA
Al completar la revisión manual de los 5 puntos anteriores entre julio y septiembre de 2026, Diego Núñez Simms entregará un Objetivo Específico 3 **científicamente irreprochable, informáticamente interoperable en la plataforma plataforma y logísticamente ejecutado en terreno**, dejando un estándar metodológico de primer nivel para las futuras vendimias del proyecto.
