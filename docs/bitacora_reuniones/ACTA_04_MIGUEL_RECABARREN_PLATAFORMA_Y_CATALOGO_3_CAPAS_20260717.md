# ACTA Y RESUMEN TÉCNICO DE ARQUITECTURA E INTEGRACIÓN
**Proyecto:** Vendimia 5.0 — Plataforma Vinewise & Ecosistema de Modelos (Integración Objetivo 3)  
**Fecha de Sesión:** 17 de julio de 2026  
**Participantes:** Miguel Recabarren (`MR` / Arquitectura y Desarrollo Plataforma), Sebastián Vargas Soto (Jefe / Líder Técnico) & Diego Núñez Simms (Investigador / Auditor Forense Objetivo 3)  
**Ubicación de Registro Canónico (`clean`):** `docs/bitacora_reuniones/ACTA_04_MIGUEL_RECABARREN_PLATAFORMA_Y_CATALOGO_3_CAPAS_20260717.md`

---

## 1. RESUMEN EJECUTIVO Y MARCO DE LA CONVERSACIÓN

Esta sesión técnica tuvo como objetivo alinear la **arquitectura de software e interoperabilidad** entre el equipo de desarrollo de la plataforma central (`Vinewise / Miguel Recabarren`) y los módulos científicos del proyecto (como los modelos de oídio/índices de la U. de Talca, alertas de INIA y el Objetivo 3 de Madurez/Fenología).

Los **3 hitos y acuerdos arquitectónicos** principales son:
1. **Adopción del estándar de "Catálogo de Requerimientos Funcionales en 3 Capas"** (Datos, Reglas de Negocio/Cálculo y Presentación) para normar qué funcionalidades entran a la plataforma operativa sin sobrecargar ni quedar cortos en alcance.
2. **Establecimiento de las 3 modalidades canónicas de integración** según el proveedor científico: integración vía `API REST/JSON` externa (ej. INIA), embebido de código backend (ej. U. de Talca) o consulta directa en la base de datos central en la nube (`PostgreSQL`).
3. **Mapeo del ecosistema actual de telemetría e infraestructura**, confirmando que la plataforma ya opera de forma automatizada (*cron jobs*) conectada a 5 grandes redes de estaciones meteorológicas (`Wiscon`, `WeatherLink`, `FieldClimate`, `Sentra` e `INIA/Campbell`).

---

## 2. ANÁLISIS DETALLADO DE LOS EJES DE ARQUITECTURA

### A. El Catálogo de Requerimientos Funcionales (Modelo de 3 Capas)
Miguel Recabarren presenta la necesidad de formalizar la gestión hídrica, fenológica y de índices en un catálogo estructurado, abandonando los listados informales de ideas. El catálogo se divide canónicamente en:
1. **Capa de Datos (`Data Layer`):** Identificación precisa de la variable de entrada, unidad de medida, estación de origen, frecuencia de captura y tabla en base de datos.
2. **Capa de Reglas de Negocio / Cálculos (`Business Logic Layer`):** Fórmulas exactas, constantes paramétricas, umbrales de alerta y lógica matemática (ej. cálculo de grados-día `BEDD/GDA`, modelos del oídio, algoritmos de predicción de cosecha).
3. **Capa de Presentación / Reportería (`Presentation & UI Layer`):** Formato de salida visual en el dashboard del usuario final, semáforos de alerta (verde/amarillo/rojo), reportes descargables y vistas personalizadas.

* **Beneficio Operativo:** Permite auditar fila por fila con el equipo científico (`Seba & Diego`), marcar con semáforo el nivel de avance (verde = resuelto/claro, amarillo = en desarrollo, rojo = duda o alta complejidad) y acotar el alcance para asegurar completitud y mantenibilidad.

### B. Modalidades Canónicas de Integración Tecnológica
Miguel detalla cómo se empaquetan los diferentes módulos en la plataforma central según la naturaleza técnica de cada institución asociada:

| Modalidad de Integración | Caso de Uso / Socio Científico | Mecanismo Arquitectónico | Flujo Operativo en Plataforma (`Vinewise`) |
| :--- | :--- | :--- | :--- |
| **1. Consumo de API Externa (`REST / JSON`)** | **INIA**<br>*(Alertas de Heladas y Olas de Calor Nocturnas)* | El socio ejecuta sus propios modelos en sus servidores y disponibiliza un *endpoint* `JSON` con la salida estructurada (`fecha_pronostico`, `probabilidad_evento`, `temperatura_esperada`). | La plataforma ejecuta un `cron job` diario en horarios definidos, consulta la API, valida el `JSON`, almacena en `PostgreSQL` y renderiza la alerta en el dashboard web. |
| **2. Embebido de Código en Backend (`Code Embedding`)** | **Universidad de Talca**<br>*(Índices Bioclimáticos y Alerta de Oídio)* | El socio entrega el código fuente o módulos matemáticos (ej. algoritmos escritos en `Java` o rutinas algebraicas de infección fungosa). | El equipo de plataforma reempaqueta (`embed`) el código dentro del *backend* de Vinewise, alimentándolo diariamente con las series térmicas de la base de datos interna. |
| **3. Integración Directa en BD (`PostgreSQL + Cron`)** | **Redes Meteorológicas**<br>*(Telemetría de Campo en Tiempo Real)* | Conexión e ingesta automatizada desde las APIs de los fabricantes de hardware de monitoreo de campo hacia la nube central. | Sincronización continua de variables crudas ($T^\circ$, Humedad, Lluvia, Radiación) para alimentar las Capas 1 y 2. |

### C. Estado Actual del Ecosistema e Infraestructura en la Nube
Miguel confirma a Sebastián y Diego que la plataforma ya se encuentra en fase **operativa y productiva en la nube**, contando con las siguientes piezas fundacionales activas:
* **Motor de Base de Datos Central:** `PostgreSQL` alojado en nube, estructurado relacionalmente para series temporales y multipropiedad.
* **Redes de Estaciones Integradas y Transmitiendo en Vivo (5 Redes):**
  1. **Wiscon**
  2. **WeatherLink (`Davis Instruments`)**
  3. **FieldClimate (`Pessl / Metos`)**
  4. **Sentra**
  5. **INIA (`Campbell Scientific` vía interconexión INIA)**
* **Automatización (`Cron Jobs`):** Rutinas activas en segundo plano que gatillan la actualización de reportería e índices bioclimáticos sin intervención manual.

---

## 3. IMPLICANCIAS Y DIRECTRICES PARA EL OBJETIVO 3 (`MADUREZ Y FENOLOGÍA`)

A partir de la exposición de Miguel, se definen los siguientes pasos para encajar el trabajo forense y de modelación de Diego Núñez en la plataforma central:
1. **Empaquetamiento del Objetivo 3 en el Catálogo Funcional:**  
   Todo lo desarrollado en el Objetivo 3 (Índice canónico de calor `BEDD_acum`, el nuevo estándar de **Modelos Lineales Mixtos `LMM`**, los proxies de humedad `SAR/SWC` y los semáforos del visor HTML de madurez) debe ser transcrito al formato del **Catálogo de 3 Capas de Miguel** antes de pedir su puesta en producción en la web.
2. **Elección de la Modalidad de Integración para el Objetivo 3:**  
   Dado que el Objetivo 3 maneja bases canónicas ampliadas en `Python / Pandas / Statsmodels` sobre la misma telemetría climatológica, la estrategia óptima de integración será la **Modalidad 2 (Embebido de Código / Scripts Python en Backend)** o la creación de un servicio *micro-backend* en Python que corra los `LMM` sobre las vistas de `PostgreSQL`.
3. **Sesión de Depuración Conjunta (`Filtro del Catálogo`):**  
   Se acuerda que Diego y Sebastián revisarán con Miguel el catálogo de funcionalidades para filtrar qué gráficos predictivos y qué alertas de cosecha (como el tablero de curvas paralelas por fundo) pasan a la interfaz de usuario final en la próxima versión de la plataforma.

---

## 4. MATRIZ DE ELEMENTOS DE ACCIÓN (`ACTION ITEMS`)

| ID | Categoría | Tarea / Elemento de Acción | Responsable | Plazo / Hito | Estado |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **PLT-01** | **Estandarización** | **Levantamiento del Catálogo Funcional del Objetivo 3:** Traducir los modelos canónicos de madurez (`LMM`), fenología ($T_0$) e índices (`BEDD_acum / IFN_acum`) al formato de 3 capas (Datos $\to$ Cálculo $\to$ Presentación UI). | **Diego Núñez Simms** | **Próximas 2 semanas** | 🟡 Prioritorio |
| **PLT-02** | **Arquitectura de Software** | **Definición técnica del empaquetamiento de `statsmodels / LMM`:** Coordinar con Miguel Recabarren si los scripts `.py` de predicción de madurez de Diego se ejecutarán como módulo embebido en el servidor central o como tarea *cron* contra `PostgreSQL`. | **Diego Núñez & Miguel Recabarren** | **Julio / Agosto 2026** | 🔴 Pendiente |
| **PLT-03** | **Interoperabilidad** | **Revisión de tablas climáticas en `PostgreSQL`:** Verificar que la base de datos central de Miguel contenga todas las variables exigidas por el Objetivo 3 (radiación solar, temperaturas máximas/mínimas limpias y registros Campbell/INIA del norte y sur) para alimentar los modelos `LMM` en tiempo real. | **Diego Núñez Simms** | **Agosto 2026** | 🔴 Pendiente |
| **PLT-04** | **Reunión de Trabajo** | **Sesión de Filtrado de Catálogo (`Scrubbing Session`):** Agendar sesión con Miguel, Seba y Diego para revisar ítem por ítem el catálogo de funcionalidades y definir el alcance exacto de la interfaz web de la próxima vendimia. | **Seba, Diego & Miguel** | **Julio 2026** | 🔴 Pendiente |
