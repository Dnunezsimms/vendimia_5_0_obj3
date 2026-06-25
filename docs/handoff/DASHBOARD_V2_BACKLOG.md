# Backlog de Arquitectura y Desarrollo — Dashboard v2

## Diagnostico y Auditoria Funcional (v1)
El dashboard actual (app.py) es funcional y logra hidratar los datos del proyecto, pero presenta caracteristicas prototipicas de un monolito exploratorio cientifico. Carece de desacople entre capas, posee funciones de construccion de interfaz de mas de 200 lineas y expone variables de ingenieria complejas sin traduccion agronomica directa para usuarios externos.

---

## Bloque 1: Critico para que el Dashboard sea Entendible
1. **Glosario Agronomico de Variables:** Traducir codigos internos (IFTT_acum, IFs, GDA_VPD_medio_acum, PySR, LOFO) a terminologia fisiologica estandar inteligible por agronomos, directores y enologos.
2. **Indicador Visual de Completitud Global:** Incorporar en la pestana Estado del sistema un panel resumen prominente que indique el porcentaje de ingesta horaria vs diaria por temporada.
3. **Separacion Explicita Frio vs Calor:** Diferenciar graficamente en la interfaz la naturaleza metodologica de los datos termicos (disponible diario proyectado vs receso horario medido).
4. **Resumen Ejecutivo de Interpretabilidad:** Sintetizar en tarjetas legibles el impacto de variables ambientales sobre Brix, antocianinas y taninos antes de exponer graficos SHAP puros.

---

## Bloque 2: Critico para que sea Cientificamente Defendible
1. **Intervalos de Confianza y Error Estandar:** Sombreado de dispersion en las curvas de evolucion de madurez tecnica (maturity_curve_grouped) para respaldar las variaciones entre fundos y cuarteles.
2. **Disclaimers Prominentes de Biofix (t0):** Reforzar en cada grafico predictivo que el t0 cerrado es retrospectivo y que las proyecciones operativas utilizan modelos latitudinales candidatos sujetos a validacion espacial.
3. **Auditoria de Fuga de Informacion (Data Leakage):** Incorporar metricas explicitas en la pestana de fenologia que demuestren la independencia de los sets de prueba por fundo (Leave-One-Fundo-Out).
4. **Validacion Metodologica de PySR:** Explicar el fundamento de las ecuaciones simbolicas encontradas y su plausibilidad termodinamica/biologica frente a modelos de caja negra (Random Forest).

---

## Bloque 3: Mejoras Visuales, Arquitectura y UX
1. **Desfragmentacion de app.py (Modularizacion UI):** Romper la funcion monolitica build_app() (210 lineas) separando cada pestana en submodulos independientes dentro de src/ui/tabs/.
2. **Cache de Renderizado de Graficos:** Implementar @lru_cache o memoizacion en plots.py para evitar re-calculos pesados de Matplotlib/Seaborn al cambiar filtros desplegables.
3. **Paginacion de DataFrames Masivos:** Reemplazar el volcado crudo de miles de filas en gr.Dataframe por vistas agregadas o paginadas para optimizar el rendimiento y memoria del navegador.
4. **Botones Funcionales de Descarga (gr.File):** Habilitar la descarga real de los datasets limpios canonicos y reportes generados desde la pestana Export / INRIA.
5. **Eliminación de Tablas Duplicadas:** Suprimir la exposicion redundante de climate['master'] en la pestana Integracion conceptual.

---

## Bloque 4: Futuro Despliegue Web (Vercel / Neon)
1. **Desacople del Filesystem Local:** Reemplazar la lectura sincrona de 2.054 archivos CSV y Excel en loaders.py por consultas estructuradas a una base de datos relacional Neon PostgreSQL.
2. **Migracion de Motor Grafico:** Sustituir graficos estaticos generados en servidor (Matplotlib/Plotly sobre Python) por componentes web dinamicos renderizados en cliente (Chart.js / Tremor en Next.js).
3. **API REST / GraphQL Asincronica:** Transformar el backend analitico en microservicios o serverless functions desplegadas en Vercel con revalidacion ISR.
4. **Autenticacion y RBAC:** Control de acceso por rol (Investigador INRIA, Enologo Vina, Administrador) para proteger datos crudos corporativos.
