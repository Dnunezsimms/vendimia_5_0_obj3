# Meta-Análisis y Síntesis Bibliográfica: Efecto de la Acumulación de Frío Invernal sobre los Requerimientos de Calor (GDD) en *Vitis vinifera* L.

---

## 1. Resumen Ejecutivo y Consenso Científico

La modelación fenológica clásica de la vid (*Vitis vinifera* L.) se ha basado históricamente en modelos térmicos de una sola etapa (acumulación de Grados Día de Desarrollo o GDD desde una fecha calendario fija, como el 1 de julio o 1 de agosto en el hemisferio sur). Sin embargo, un amplio cuerpo de investigación ecofisiológica y meta-análisis internacionales (García de Cortázar-Atauri et al., 2009; Caffarra & Eccel, 2010; Luedeling, 2012; Sgubin et al., 2018; Parker et al., 2013) demuestra que **la brotación está regulada por una interacción secuencial y compensatoria entre la acumulación de frío invernal (Chilling) y la acumulación de calor primaveral (Forcing)**.

El consenso científico internacional establece cuatro principios empíricos fundamentales:

1. **Relación de Compensación Inversa (Chilling-Forcing Relationship):** Existe una relación matemática exponencial negativa o logarítmica entre la cantidad de frío invernal recibido durante la endodormancia y la cantidad de calor (GDD) requerida para la brotación (ecodormancia). A menor acumulación de frío, la planta exige una cantidad significativamente **mayor de GDD** para brotar.
2. **Meseta de Saturación del Frío en Vid:** *Vitis vinifera* es considerada una especie frutal de bajo a moderado requerimiento de frío en comparación con pomáceas o carozos. El requerimiento típico para salir del receso invernal oscila entre **30 y 50 Chilling Portions (CP)** (o aproximadamente 200 a 600 Horas Frío, según variedad y latitud). Una vez que se supera ese umbral de saturación, el requerimiento de calor (GDD) se estabiliza en su valor mínimo y constante.
3. **Penalización por Inviernos Cálidos o Déficit de Frío:** En primaveras precedidas por inviernos cálidos o en viñedos de baja latitud (donde no se alcanza el umbral de saturación de frío antes de agosto), la endodormancia se prolonga o se desbloquea de forma incompleta. Esto provoca:
   - Una brotación errática, desuniforme y temporalmente retrasada.
   - Un incremento aparente en el requerimiento térmico operacional (ej. el umbral que en un año normal es de 150 GDD puede elevarse a 220+ GDD en el mismo fundo).
4. **Variabilidad Intervarietal:**
   - **Variedades Tempranas (ej. Chardonnay, Pinot Noir, Sauvignon Blanc):** Requieren menor cantidad de frío para salir del receso y responden con alta sensibilidad biológica a los primeros aumentos de temperatura (bajo forcing), haciéndolas vulnerables a heladas primaverales tempranas.
   - **Variedades Tardías (ej. Cabernet Sauvignon, Carmenere):** Presentan una mayor inercia fisiológica; exigen un acoplamiento más estricto entre el término del valle térmico invernal y la acumulación sostenida de GDD.

---

## 2. Evidencia Empírica y Modelos Comparados en Viticultura

| Modelo / Enfoque | Variables de Entrada | Resolución Requerida | Ventajas Operativas | Limitaciones Metodológicas |
| :--- | :--- | :--- | :--- | :--- |
| **GDD Clásico (Thermal Time / Spring Warming)** | Solo Temperatura Media / Máx-Mín primaveral. Fecha inicial fija ($T_0$). | Diaria | Alta simplicidad operativa. Funciona bien en zonas templado-frías donde el frío siempre se satura. | **Falla en años o zonas con déficit de frío**, generando errores sistemáticos de pronóstico (*leakage* o sobreestimación). |
| **Modelo Utah / Horas Frío + GDD (Dos Etapas Secuenciales)** | Horas Frío (< 7.2°C) o Unidades Frío invernales $\rightarrow$ luego GDD. | Horaria (o interpolada) | Representa la transición endodormancia $\rightarrow$ ecodormancia. | El modelo Utah penaliza en exceso temperaturas moderadas (15-18°C) comunes en inviernos mediterráneos chilenos. |
| **Modelo Dinámico (Chilling Portions / BRIN Model)** | Intermediario reversible de frío (Fishman et al., 1987) acoplado a forcing sigmoidal (García de Cortázar-Atauri et al., 2009). | **Horaria continua** | Es el **estándar de oro científico internacional**. Robusto frente a calentamiento global e inviernos variables. | **Exigencia crítica de datos horarios multianuales sin gaps.** Muy sensible a datos diarios interpolados sintéticamente. |
| **Modelo de Compensación Logarítmica Diaria** | $GDD_{req} = a + b \cdot \exp(-c \cdot Frio_{diario})$ | Diaria | Compatible con redes meteorológicas agrícolas estándar (Tmax/Tmin). | Requiere calibración local por variedad y al menos 5-10 temporadas históricas para estabilizar parámetros $a, b, c$. |

---

## 3. Implicaciones Críticas para el Proyecto (Vendimia 5.0 - Objetivo 3)

Al contrastar la evidencia científica con nuestro pipeline operacional en `C:\projects\vendimia_5_0_obj3`, emergen tres implicaciones que justifican plenamente la discusión con Camilo:

1. **La debilidad del $T_0$ rígido por calendario:** Asumir que el conteo de GDD parte invariablemente el 1 de julio o 1 de agosto (o predecirlo exclusivamente mediante regresión latitudinal sin verificar la condición térmica previa) asume de facto que la planta ya alcanzó las ~40 Chilling Portions en todos los fundos. En viñedos costeros o septentrionales (ej. Quebrada Seca o sectores del norte), o tras inviernos benignos, esa presunción se rompe.
2. **El Diagnóstico de "Fondo del Valle Térmico" como puente operacional:** Dado que no disponemos de series horarias ininterrumpidas para calcular *Chilling Portions* en todos los sitios históricos, la implementación que realizamos del **Panel de Auditoría del Valle Térmico (GDD diario y curva móvil de 14 días)** actúa como una herramienta de validación ecofisiológica excelente: permite confirmar visual y cuantitativamente si la fecha candidata de $T_0$ ocurre efectivamente en el mínimo de receso invernal (donde el frío ya actuó) o si se está capturando ruido térmico prematuro.
3. **Decisión Metodológica Estratégica:**
   - **Opción A (Implementación explícita):** Incorporar una rutina de estimación diaria de frío empírico como co-variable moderadora del umbral de GDD (ej. ajustar los 150 GDD según el frío acumulado a mayo-julio).
   - **Opción B (Justificación canónica como limitación del Baseline actual):** Mantener el modelo térmico operacional en 1 Etapa (GDD desde fecha candidata / $T_0$ latitudinal), pero blindarlo en el informe técnico y en la publicación adjuntando este meta-análisis para demostrar que **reconocemos el efecto compensatorio del frío y justificamos su exclusión explícita por la resolución de la red meteorológica territorial**.

---

## 4. Conclusión para Presentación

Este documento otorga el respaldo científico para presentar ante Camilo y el equipo directivo. Demuestra que no estamos modelando cajas negras puramente estadísticas, sino que estamos alineando nuestra ingeniería de datos con la ecofisiología de la vid, utilizando el dashboard interactivo para auditar justamente las fronteras donde la planta pasa de receso invernal a respuesta térmica primaveral.
