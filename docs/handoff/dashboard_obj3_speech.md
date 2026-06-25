## Speech — Explicación del Dashboard Obj3 Vendimia 5.0

La idea central de este dashboard es integrar, en una sola interfaz, el estado operativo del Objetivo 3 de Vendimia 5.0: clima, fenología, indicador biológico, frío dinámico, acumulación térmica y modelos de madurez. No es solamente un panel visual; funciona como una capa de auditoría metodológica del pipeline.

El dashboard está pensado para responder tres preguntas principales:

Primero, ¿tenemos datos climáticos suficientes y trazables para cada fundo?
Segundo, ¿el indicador biológico de fenología está funcionando de forma coherente?
Tercero, ¿los modelos de madurez técnica y fenólica están siendo alimentados por datos consistentes?

La primera parte del dashboard revisa el estado climático. Ahí se muestran las fuentes asociadas a cada fundo, los gaps, las estaciones recomendadas y la trazabilidad general. Esto es clave porque el proyecto combina fuentes distintas: Zentra Cloud, DataVid —antes Meteovid—, e INIA/Agrometeorología. Por eso no basta con tener temperatura; necesitamos saber de qué estación viene, qué periodo cubre, qué frecuencia tiene, qué tan confiable es y si es reproducible o descarga manual.

La segunda parte corresponde al bloque fenológico. Aquí se analiza el indicador biológico asociado a brotación, acumulación térmica y t0. Es importante distinguir tres conceptos. El t0 cerrado es retrospectivo: usa información observada y por tanto no debe venderse como predictor operativo. El t0 latitudinal es el candidato operativo, porque intenta estimar el inicio de acumulación térmica sin mirar directamente la brotación observada. Y el GDD permite evaluar cuánto calor se acumula desde ese punto hasta la brotación.

Dentro de esta parte también está la evaluación varietal. El dashboard separa el dato crudo observado de Lourdes del valor final ajustado. Esto es importante porque algunas variedades tenían solo una temporada válida, lo que hacía injusta la comparación directa. Por eso se incorporó un ajuste suavizado por delta varietal. La lógica no es inventar fisiología, sino evitar que una variedad tardía como Carmenere quede artificialmente por debajo de Cabernet Sauvignon solo por tener una temporada menos robusta.

El tercer bloque es el de frío dinámico. Aquí usamos datos horarios de temperatura para estimar Chill Portions, pero con una precisión metodológica importante: en esta versión, el frío dinámico no define formalmente el t0. Se usa como diagnóstico fisiológico de plausibilidad. En otras palabras, permite revisar si el receso invernal tuvo sentido desde el punto de vista térmico antes de interpretar la brotación y el inicio de acumulación de calor. Más adelante se podría construir un modelo frío + calor, pero actualmente el frío dinámico es una capa diagnóstica, no el motor del biofix.

El cuarto bloque se relaciona con madurez. Aquí hay que separar muy bien las cosas: los datos horarios de invierno sirven para frío dinámico y fenología temprana, pero no reemplazan la climatología diaria de temporada completa que se necesita para madurez. Para madurez técnica o fenólica se requiere clima diario desde primavera hasta cosecha: temperatura media, mínima, máxima, humedad relativa, radiación, precipitación y variables derivadas como VPD. Por eso el dashboard distingue entre clima horario para frío y clima diario para modelos de madurez.

Metodológicamente, el valor del dashboard no es solo mostrar gráficos. Su valor es que obliga a mirar la cadena completa: fuente de datos, estación, periodo, variable, cálculo, output y advertencia. Si un panel aparece vacío, no necesariamente significa que el modelo falló; puede significar que falta una dependencia, que una ruta cambió, que un archivo no está en el nuevo layout o que el dato aún no está validado.

En resumen, este dashboard funciona como un sistema de control del pipeline Obj3. Integra tres capas: una capa de datos climáticos y trazabilidad, una capa ecofisiológica de fenología y frío, y una capa de modelación aplicada para madurez. Su objetivo final es que cualquier persona que tome el proyecto pueda entender qué está calculado, con qué datos, desde qué fuente, con qué limitaciones y qué falta para cerrar la temporada.

La filosofía del sistema es simple: no confiar en gráficos bonitos si no hay trazabilidad detrás. Cada resultado debe poder responder de dónde salió, qué archivo lo alimentó, qué estación representa, qué periodo cubre y qué tan robusto es. Esa es la diferencia entre un dashboard exploratorio y una herramienta realmente útil para investigación aplicada y transferencia tecnológica.