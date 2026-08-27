# Plan Operativo y de Modelos 2026-2027

A continuación se detalla la lista de tareas críticas, operativas y analíticas para la nueva temporada, de acuerdo a las últimas reuniones y evaluaciones.

## Tareas Críticas y Operativas (Terreno)

- [ ] **1. Instalación y reemplazo de cámaras fenológicas:**
  - Instalar/reemplazar cámaras en los fundos **Ucuquer** y **Nilahue Keule**.
  - *Opcional/Eventual:* Evaluar e instalar una cámara de seguridad adicional en **Requínoa** o en **Mulchén**.
- [ ] **2. Monitoreo de cámaras (Permanente):**
  - Mantener un monitoreo constante del funcionamiento y conectividad de todas las cámaras fenológicas instaladas en terreno.
- [ ] **3. Nueva estructura de datos 2027:**
  - Se ha creado la carpeta datos_fenologia_2027/ en la raíz del repositorio para ir colocando allí de forma ordenada los nuevos datos fenológicos que vayan llegando esta temporada.

## Tareas de Modelación y Análisis de Datos

- [ ] **4. Actualizar modelo de Ricardo Luna:**
  - Revisar y actualizar el modelo monomolecular de Ricardo Luna utilizado para predecir estados fenológicos, integrando las curvas más recientes.
- [ ] **5. Extraer brotaciones de la red de cámaras:**
  - Realizar la extracción sistemática de los hitos de brotación en todos los fundos que cuenten con cámaras fenológicas operativas.
- [ ] **6. Optimización del Indicador Biológico:**
  - Con los nuevos datos de brotaciones extraídos, realimentar el pipeline del indicador biológico.
  - El objetivo principal es ejecutar la **primera prueba de optimización de T° base y T° umbral** para mejorar la precisión del modelo de acumulación térmica.
- [ ] **7. Integración de Fenoles al Dashboard de Luis:**
  - Incorporar los nuevos datos de fenoles consolidados a los análisis para reentrenar y realimentar el dashboard de predicciones de Luis.
  - **Instrucciones de realimentación:** Para realizar esto, buscar en la ruta:
    .\models\dashboard_luis\0_0_0_0_Predicciones_Diego_SprintMayo\Tutorial_Colab_Dashboard_Predicciones_Diego_20260515_v0.ipynb
    el tutorial con los pasos documentados para procesar la data y correr los modelos (Random Forest / PySR).

## Gestión y Seguimiento

- [ ] **8. Reuniones con Camilo Riveros (Permanente):**
  - Organizar y agendar las nuevas reuniones de seguimiento y coordinación con Camilo Riveros durante toda la temporada.

- [ ] **9. Nuevos Predictores para Modelos (Instrucción Seba/Camilo):**
  - Incorporar y probar nuevos predictores en los modelos predictivos según la última reunión:
    - Rendimiento del fundo.
    - Año del huerto.
    - Tipo de suelo.
  - Asegurar que estas variables queden debidamente documentadas en la metadata de entrada al pipeline.
