# ACTA Y RESUMEN EJECUTIVO DE REUNIÓN DE COORDINACIÓN
**Proyecto:** Vendimia 5.0 — Objetivo Específico 3 (Madurez y Fenología Predictiva)  
**Fecha de Reunión:** 17 de julio de 2026  
**Participantes:** Sebastián Vargas Soto (Jefe / Líder Técnico) & Diego Núñez Simms (Investigador / Auditor Forense Objetivo 3)  
**Ubicación de Registro Canónico (`clean`):** `docs/bitacora_reuniones/ACTA_02_SEBASTIAN_LOGISTICA_Y_OUTLIERS_20260717.md`

---

## 1. RESUMEN EJECUTIVO Y MARCO DE LA CONVERSACIÓN

Durante la sesión de coordinación se abordaron tres ejes estratégicos para el desarrollo operativo y de modelación del Objetivo 3:
1. **Monitoreo meteorológico en tiempo real y vulnerabilidad edáfica por cuartel** frente al frente de precipitaciones de julio 2026.
2. **Logística de adquisición, plazos administrativos y despliegue de infraestructura de monitoreo fenológico (Cámaras de Terreno)** para el inicio del nuevo ciclo vegetativo.
3. **Identificación y directriz de investigación sobre anomalías estadísticas en modelación ("Outlier severo en el cuartel Los Acacios")**, vinculando el comportamiento hidrológico del suelo con las curvas de madurez.

---

## 2. ANÁLISIS Y DESGLOSE POR TEMA

### A. Diagnóstico Meteorológico e Infiltración de Suelos (`Sur vs. Norte / Los Acacios`)
* **Situación Climática Inmediata:** Al momento de la sesión, las estaciones del centro-sur (`Talca`) registraban una precipitación paulatina y constante de aproximadamente $1\text{ mm/hora}$ (acumulando $15\text{ a }16\text{ mm}$). Se prevé la intensificación del evento hacia el día siguiente, pudiendo alcanzar los $50\text{ mm}$ en $24\text{ horas}$.
* **Vulnerabilidad Edáfica Diferenciada:**
  * **Cuarteles del Sur/Centro:** La tasa de lluvia suave ($1\text{ mm/h}$) permite una infiltración progresiva sin riesgo inminente de saturación o escorrentía destructiva.
  * **Cuarteles del Norte (`El Norte` / `Los Acacios`):** Se identifica como el sector de **mayor riesgo operativo**. Los suelos del norte carecen de buena capacidad de infiltración superficial, por lo que ante precipitaciones acumuladas ($>15\text{--}20\text{ mm}$) sufren rápida saturación e hipoxia radicular temporal, lo que condiciona fuertemente la brotación primaveral y el balance térmico de inicio de temporada.

### B. Infraestructura y Estado del Hardware (`Cámaras Fenológicas` & Tarjetas SD)
* **Estado en Laboratorio:** Diego Núñez Simms informa que mantiene las tarjetas de memoria (`SD Cards`) en el laboratorio para revisión, respaldo y formateo previo al próximo despliegue en campo.
* **Gestión de Compras (Proveedor/Socio: Daniel):**
  * Sebastián Vargas confirma que **la Orden de Compra (`OC`) ya fue liberada y el pago está en proceso de ejecución**.
  * Se proyecta un plazo administrativo de **aproximadamente 30 días** para que los recursos estén disponibles con Daniel y se concrete la entrega formal de los equipos.
* **Estrategia de Mitigación (Corto Plazo):** Dado el desfase de 30 días en la compra de la nueva unidad, el equipo mantendrá operativa la cámara fenológica actual. Adicionalmente, Sebastián gestionará con Daniel la incorporación de **una segunda cámara adicional** para asegurar la redundancia de monitoreo en los dos focos geográficos prioritarios del proyecto.

### C. Cronograma e Hitos Críticos de Despliegue en Terreno (`Agosto y Septiembre`)
Se estableció una ventana de instalación estricta y vinculante antes de que el avance fenológico (brotación) imposibilite la calibración de las estaciones en reposo invernal:
1. **HITO 1 — AGOSTO 2026 (Prioridad 1 e Impostergable): Instalación en El Norte (`Los Acacios` / Coquimbo).**  
   Sebastián enfatiza que el viaje de instalación al norte debe realizarse obligatoriamente durante agosto (*"En agosto hay que ir para allá sí o sí a poner esa estación... esa es la que más me urge"*), garantizando que el hardware esté transmitiendo antes del despegue térmico ($T_0$).
2. **HITO 2 — SEPTIEMBRE 2026 (Prioridad 2): Instalación en Valle del Maipo.**  
   Una vez asegurada la estación del norte en agosto, el equipo se desplegará en el cuartel **Maipo** durante septiembre (*"Instalando en septiembre salvamos también"*).

### D. Investigación Metodológica: El Cuartel `Los Acacios` como *Outlier* Canónico
* **Diagnóstico en Modelación:** Diego levanta la alerta de que, en los modelos de madurez y correlación térmica del Objetivo 3 (`BEDD/GDA vs Brix/Acidez`), el cuartel **Los Acacios** se posiciona actualmente como un **"outlier brígido" (anomalía estadística severa)** que distorsiona las proyecciones globales.
* **Hipótesis y Directriz de Trabajo (`Desmenuzamiento`):** Ambos coinciden en que no se debe eliminar o truncar el dato, sino **"desmenuzarlo" a cabalidad**. La hipótesis de trabajo apunta directamente a la **saturación hídrica y mala infiltración del suelo en Los Acacios** (discutida en el punto A), lo que altera el régimen térmico del perfil de suelo, descalibra la acumulación térmica efectiva de la planta (`BEDD_acum`) o genera un estrés radicular diferencial que desincroniza la madurez técnica y fenológica respecto a los viñedos con buen drenaje.

---

## 3. MATRIZ DE TAREAS Y ELEMENTOS DE ACCIÓN (`ACTION ITEMS`)

| ID | Categoría | Tarea / Elemento de Acción | Responsable | Plazo / Hito | Estado |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **ACT-01** | **Gestión Logística** | **Seguimiento directo de Cámaras con Daniel:** Contactar y gestionar en paralelo el estado del despacho de la orden de compra en curso (plazo 30 días) y negociar la disponibilidad inmediata de la segunda unidad fenológica para la campaña del norte. | **Diego Núñez Simms**<br>*(con apoyo de Sebastián)* | **Inmediato**<br>*(Julio 2026)* | 🟡 En Inicio |
| **ACT-02** | **Hardware / Laboratorio** | **Preparación de Tarjetas y Cámara Actual:** Mantener revisadas, respaldadas y listas para terreno las tarjetas SD de memoria en el laboratorio y verificar la calibración de la cámara fenológica existente. | **Diego Núñez Simms** | **Julio 2026** | 🟢 En Proceso |
| **ACT-03** | **Despliegue de Terreno** | **Campaña de Instalación El Norte (`Los Acacios` / Coquimbo):** Programar logística, transporte y montaje de la estación meteorológica y cámara fenológica en el cuartel Norte. | **Sebastián Vargas & Diego Núñez** | **AGOSTO 2026**<br>*(Impostergable)* | 🔴 Pendiente |
| **ACT-04** | **Despliegue de Terreno** | **Campaña de Instalación Valle del Maipo:** Ejecutar el montaje y puesta en marcha de la estación de monitoreo en el cuartel Maipo. | **Sebastián Vargas & Diego Núñez** | **SEPTIEMBRE 2026** | 🔴 Pendiente |
| **ACT-05** | **Auditoría de Datos (Obj3)** | **Desmenuzamiento Forense del Outlier `Los Acacios`:** Realizar un estudio profundo sobre las bases canónicas de Los Acacios, cruzando datos de precipitación/infiltración edáfica, registros térmicos locales y curvas de madurez para explicar biofísicamente su comportamiento atípico en los modelos (`LMM / PCA`). | **Diego Núñez Simms** | **Siguientes 2 semanas**<br>*(Julio/Agosto)* | 🟡 Prioritaria |
