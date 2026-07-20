# ACTA Y RESUMEN METODOLÓGICO DE ASESORÍA CIENTÍFICA
**Proyecto:** Vendimia 5.0 — Objetivo Específico 3 (Madurez y Fenología Predictiva)  
**Fecha de Sesión:** 17 de julio de 2026  
**Participantes:** Camilo Riveros (Asesor Científico / Bioestadística Agronómica) & Diego Núñez Simms (Investigador / Auditor Forense Objetivo 3)  
**Ubicación de Registro Canónico (`clean`):** `docs/bitacora_reuniones/ACTA_03_CAMILO_RIVEROS_LMM_Y_COLINEALIDAD_20260717.md`

---

## 1. RESUMEN EJECUTIVO Y MARCO DE LA SESIÓN

Esta sesión de asesoría metodológica en profundidad tuvo como objetivo auditar forensement las decisiones de modelación implementadas en los reportes de INRIA (`Random Forest`, `PySR` / Regresión Simbólica, y Análisis de Componentes Principales `PCA`), contrastándolas con la biología real de la vid y la variabilidad operativa en terreno de las temporadas $2024\text{--}2025$ y $2025\text{--}2026$.

Los **4 acuerdos metodológicos canónicos** derivados de la sesión son:
1. **Transición oficial a Modelos Lineales Mixtos (`LMM`)** para aislar el ruido de muestreo humano y agronómico en biometría (`Peso de Baya`).
2. **Eliminación de colinealidad en predictores térmicos**, seleccionando un único índice canónico de calor (`BEDD_acum` o `GDA`) por modelo.
3. **Validación de la ventana de biofix fenológico ($T_0$) en base a cumplimiento de porciones de frío** ($>75\text{--}80\%$) antes de iniciar la acumulación térmica, descartando compensaciones complejas no calibradas.
4. **Diferenciación agronómica en variedades Blancas**, reconociendo el rol dominante del **Índice de Frescor Nocturno (`IFN_acum`)** sobre el `Sauvignon Blanc` versus el calor diurno sobre el `Chardonnay`.

---

## 2. ANÁLISIS DETALLADO POR EJE METODOLÓGICO

### A. Diagnóstico de Colapso en `Peso de Baya` y el Ruido del Muestreador (`Random Forest vs. LMM`)
* **Evidencia discutida:** Diego presenta la evaluación de transferencia temporal (`CV5` vs. test temporal $2024\text{--}2025 \to 2026$), donde los sólidos solubles (`Brix`) conservan un excelente desempeño, mientras que la transferibilidad del **Peso de Baya se desploma drásticamente**.
* **Indagación sobre terreno:** Camilo consulta explícitamente si la toma de muestras fue realizada por el mismo personal. Diego confirma una **alta rotación operativa** (múltiples practicantes, técnicas de terreno y relevos en semanas de colapso de muestreo).
* **Diagnóstico de Camilo:** Los modelos de Inteligencia Artificial de caja negra (`Random Forest`, árboles de regresión) "memorizan" el sesgo del muestreador o la semana exacta de esa campaña. Al transferir a un año con un practicante distinto o una carga de poda diferente, el modelo falla estructuralmente.
* **Directriz Metodológica (`LMM`):** Se establece que la herramienta correcta para absorción de este ruido son los **Modelos Lineales Mixtos (`statsmodels.MixedLM`)**. El predictor climático (`BEDD/GDA`) entra como **Efecto Fijo** pura, mientras que las fuentes de variabilidad experimental y cultural (Fundo, Temporada, Cuartel y/o Operador) entran como **Efectos Aleatorios (`Group Intercepts`)**, permitiendo conocer la verdadera magnitud biológica sin distorsión artificial.

### B. Colinealidad en el `PCA` (Figuras 44 a 51) y Selección Canónica de Predictor Térmico
* **Observación Visual:** Al analizar los biplots PCA de INRIA, se constata una colinealidad casi perfecta entre `Brix`, `GDA`, `BEDD_acum` e `IFN_acum` en el primer componente principal ($PC_1$).
* **Crítica al modelamiento automático:** Camilo cuestiona severamente que los algoritmos automáticos incluyan simultáneamente `GDA` y `BEDD_acum` (o múltiples integrales térmicas). Señala que *"el BEDD es un caso particular del GDA; incluir ambos carece de sentido agronómico y solo inflates artificialmente el $R^2$ por redundancia matemática"*.
* **Respaldo estadístico clásico (`Stepwise`):** Camilo recuerda que, mediante selección clásica (*Stepwise regression* o análisis de reducción de suma de cuadrados de error), al ingresar `GDA` como predictor primario, la adición posterior de `BEDD` aporta una mejora marginal casi nula ($<1\text{--}5\%$), confirmando que codifican el mismo proceso biofísico.
* **Directriz Metodológica:** En todo reporte u optimización del Objetivo 3, **se seleccionará formalmente un único índice térmico canónico de acumulación (`BEDD_acum` o `GDA` senoidal)** por modelo, depurando las matrices de entrada antes de alimentar cualquier algoritmo predictivo.

### C. Auditoría de Valles Térmicos, Biofix ($T_0$) y Requerimientos de Frío Invernal
* **El Problema del $T_0$:** Diego muestra la auditoría del "fondo del valle térmico" en localidades como Idagua o Queule, evaluando mover la fecha de inicio de acumulación desde el clásico 1 de septiembre hacia fines de agosto ($24\text{--}25\text{ de agosto}$) según indicadores biológicos.
* **Evaluación de Camilo:** En el centro/sur (`Maule`), la acumulación térmica entre el 20 y el 31 de agosto suele ser extremadamente baja ($30\text{ a }50\text{ GDD}$ en total), dando el salto exponencial recién en septiembre. Por ende, mover el biofix una semana atrás rara vez altera significativamente la fecha de brotación predicha, salvo en **localidades cálidas del Norte (`Coquimbo`)**.
* **Directriz sobre Compensación Frío-Calor:** Frente a la literatura extranjera que postula que "a menor frío invernal se requiere más calor primaveral para brotar", Camilo recomienda **máxima prudencia para evitar extrapolaciones peligrosas** en modelos no calibrados fisiológicamente en Chile. La directriz operativa es:
  1. Verificar empíricamente que en la fecha candidata ($T_0$) la variedad haya cumplido el **umbrál de seguridad de porciones de frío ($>75\text{--}80\%$)**.
  2. Una vez verificado ese cumplimiento, iniciar la acumulación de `BEDD/GDA` hacia brotación, sin añadir covariables complejas no lineales de compensación que solo introducen inestabilidad poblacional.

### D. Regresión Simbólica (`PySR`), Mapas de Calor (Figs. 88-89) y Ruptura de Paradigma en Blancas
* **Hallazgo en `PySR`:** En los mapas de calor de las 25 mejores ecuaciones algebraicas descubiertas por INRIA (pág. 90), el **Índice de Frescor Nocturno (`IFN_acum`)** aparece como el predictor dominante en $>90\%$ de los modelos para **Sauvignon Blanc**, mientras que para **Chardonnay** predomina el calor diurno (`BEDD_acum`).
* **Interpretación Agronómica Canónica:** Camilo y Diego acuerdan que este hallazgo permite **romper el sesgo tradicional de agrupar "todas las blancas en el mismo saco"**:
  * **Sauvignon Blanc:** Es una canopia y baya hipersensible a la respiración celular y combustión del ácido málico. Las noches frescas (`IFN_acum` moderado/alto) frenan la degradación de la acidez, conservan el pH y controlan el ritmo de acumulación de sólidos solubles.
  * **Chardonnay:** Se comporta térmicamente más cercano a un perfil de acumulación diurna (`BEDD_acum`), respondiendo directamente a las horas de sol y fotosíntesis neta.
* **Depuración de Ecuaciones Redundantes de `PySR`:** Camilo realiza una inspección forense sobre las tablas de salida de `PySR` (ej. fila 17 hacia abajo) y demuestra que **múltiples modelos reportados como "distintos" son en realidad la misma regresión lineal simple** con variaciones infinitesimales en el intercepto o la pendiente que no alteran el `MAE`. Se ordena **seleccionar la ecuación lineal más parsimoniosa y agronómicamente explicable**, descartando fórmulas polinomiales o exponenciales sobreajustadas.

---

## 3. SÍNTESIS DE ELEMENTOS DE ACCIÓN Y DIRECTRICES (`ACTION ITEMS`)

| ID | Eje Metodológico | Elemento de Acción / Directriz Sancionada | Impacto en Pipeline (`src/models/`) |
| :---: | :--- | :--- | :--- |
| **MET-01** | **Arquitectura de Modelos** | **Migrar el estándar predictivo de `Random Forest / PySR` hacia Modelos Lineales Mixtos (`LMM`):** Ajustar `statsmodels.MixedLM` para madurez técnica y biometría, fijando `BEDD_acum` como Efecto Fijo y `Fundo + Temporada` como Intercepto Aleatorio. | Elimina el sobreajuste por operador y estabiliza las predicciones `LOFO` en el próximo informe. |
| **MET-02** | **Depuración de Predictore (`Feature Selection`)** | **Eliminar la colinealidad en matrices de entrada:** Prohibir la alimentación simultánea de `GDA` y `BEDD_acum` en un mismo modelo tabular o lineal. Elegir un único índice canónico (`BEDD_acum`) según variedad. | Simplifica la arquitectura explicativa (`XAI`) y reduce la dimensionalidad redundante. |
| **MET-03** | **Fenología ($T_0$)** | **Establecer protocolo de Biofix condicionado a Porciones de Frío:** Para definir la fecha de inicio de acumulación primaveral ($T_0$), exigir como prerrequisito la validación de $>75\%$ de cumplimiento de frío invernal de la cultivar en la localidad. | Evita el inicio errático de acumulación en inviernos cálidos o valles con traslape térmico. |
| **MET-04** | **Estratificación Blancas** | **Separar formalmente los motores de maduración en variedades blancas:** Modelar `Sauvignon Blanc` integrando como variable canónica de control el **Frescor Nocturno (`IFN_acum`)**, manteniendo `BEDD_acum` para `Chardonnay` y Tintas. | Aumenta la precisión forense en la predicción de `pH` y acidez titluable en blancas tempranas. |
