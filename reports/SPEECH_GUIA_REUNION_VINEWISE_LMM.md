# Guía de Conducción y Guion Fluido para Reunión de Asesoría
## Vendimia 5.0 (Objetivo Específico 3) & Apoyo Satelital `vinewise-rs`

**Responsable Técnico e I+D:** Diego Núñez Simms  
**Asistentes en Reunión:** Sebastián (presencial/videollamada - ya conoce el trabajo) y Miguel (conectado por teléfono/audio).  
**Tono y Enfoque:** Cálido, profesional, cercano, didáctico e integrador (especialmente para describir lo visual a quien está en línea telefónica), manteniendo rigor científico y objetividad absoluta.

---

## 1. Estructura y Ritmo de la Sesión (45 - 60 min)

| Bloque | Duración | Foco de la Conversación | Apoyo en Pantalla (para Sebastián y descripción para Miguel) |
| :--- | :---: | :--- | :--- |
| **Bloque 1** | 7 min | **Saludo, Encabezado y Diagnóstico Honestamente Real:** Bienvenida cálida a Sebastián y Miguel. Puesta en común del diagnóstico del Objetivo 3 sin rodeos. | Portal `index.html` o diapositiva inicial. |
| **Bloque 2** | 15 min | **La Solución Satelital (`vinewise-rs`):** Por qué no nos podemos quedar de brazos cruzados si un sensor falla en terreno. | **Visor `visor_vinewise_era5_vs_local.html` (Sección 1: Mapa)** + Descripción verbal clara para Miguel. |
| **Bloque 3** | 15 min | **Las Curvas Diarias y el Paso a Modelos Lineales Mixtos (`LMM`):** Evidencia de terreno y por qué los árboles se marean con el calor. | **Visor `visor_vinewise_era5_vs_local.html` (Sección 2: Series)** + Acta técnica con Camilo. |
| **Bloque 4** | 8 min | **Acuerdos Prácticos y Próximos Pasos:** Tres decisiones simples para avanzar a pie firme hacia la próxima entrega. | Resumen de Acuerdos / Matriz de Decisión. |

---

## 2. Guion Fluido Paso a Paso (Cálido, Cercano y Riguroso)

### Bloque 1: Saludo Cálido, Presentación e Introducción al Diagnóstico (7 min)

> **[TIP DE CONDUCCIÓN]:** Habla relajado, con buena energía. Asegúrate de chequear que Miguel escuche bien por el teléfono antes de arrancar.

**[SPEECH]:**
> *"Hola Sebastián, qué bueno verte de nuevo. Y hola Miguel, muy bienvenido por allá al teléfono, ¿nos escuchas bien desde donde estás? Excelente.*
>
> *Bueno, para partir y para que estemos todos súper alineados —sobre todo contigo, Miguel, que te sumas hoy por llamada— les cuento muy brevemente: yo soy **Diego Núñez Simms**, estoy a cargo de toda la parte de ciencia de datos, modelación predictiva e ingeniería climática aquí en el **Objetivo 3** del proyecto Vendimia 5.0.*
>
> *Sebastián ya conoce bien el estilo con el que trabajamos, pero Miguel, te comento que mi enfoque aquí no es meter datos en una juguera o en un modelo de caja negra para sacar un número bonito. Mi rol es más bien actuar como un **auditor metodológico del ciclo de la vid**: asegurarme de que lo que modelamos en el computador refleje de verdad la física, el clima y la fisiología que ocurre en los parrones, en el campo real.*
>
> *Y mirando con mucha honestidad el estado actual de nuestro análisis y lo que revisamos en el cuarto informe con INRIA, hoy tenemos **tres grandes desafíos prácticos** en los que me gustaría que enfoquemos esta conversación:*
>
> 1. **La realidad de los sensores climáticos en terreno:** Todos sabemos que mantener redes como `Datavid`, `Zentra` o `INIA` operativas 365 días en 5 fundos repartidos desde Ovalle hasta San Clemente es difícil. Siempre hay cortes de luz, pérdidas de señal o saltos de calibración. Si justo se nos corta la estación durante 10 días en la floración o en plena pinta, se nos pierde el cálculo del frío (`IFN`) y de los Grados Día (`GDA`). Si no tenemos una malla de seguridad satelital sólida para rellenar esos huecos con rigor físico, el modelo de madurez se nos queda ciego.*
> 2. **El 'efecto mano' en la cosecha y los muestreos:** Al auditar los datos históricos, nos dimos cuenta de que variables como el `Peso de Baya` o el `pH` varían muchísimo según quién y cómo corta el racimo en el campo. Cuando probamos predecir un fundo completamente nuevo (lo que llamamos validación `Leave-One-Fundo-Out`), el error en `Peso de Baya` salta fuerte por ese ruido humano del operador. Tenemos que sincerar qué variables son realmente predecibles desde el clima y cuáles tienen demasiado ruido de muestreo.*
> 3. **El problema de la colinealidad del calor:** Casi todo en la temporada de crecimiento sube de la mano con los Grados Día. Si le pasamos eso a un modelo de árboles como `Random Forest`, el modelo se 'memoriza' la fecha o el cuartel específico y después le cuesta mucho generalizar para la temporada que viene. Por eso necesitamos un enfoque estadístico más limpio y transparente."*

---

### Bloque 2: Mostrando `vinewise-rs` y el Mapa Satelital (15 min)

> **[TIP DE CONDUCCIÓN]:** Abre la **Sección 1 (Mapa y Grilla ERA5)** en `visor_vinewise_era5_vs_local.html`. Como Miguel está solo por teléfono, describe el mapa y las distancias con analogías súper visuales y sencillas.

**[SPEECH]:**
> *"Para resolver este primer dolor —el de no quedarnos tirados si un sensor en campo falla— quiero compartirles un desarrollo proactivo que he venido trabajando en paralelo y que nos cae como anillo al dedo. Se llama **`vinewise-rs`**.*
>
> *Sebastián, en pantalla estás viendo un visor georreferenciado que armé para hoy. Y para ti, Miguel, que estás al teléfono, te lo describo esquemáticamente: imagínate el mapa de Chile con nuestros 5 fundos piloto marcados desde Ovalle hasta el Maule (`Lourdes`, `Idahue`, `Mariposas`, `Los Acacios` y `Quebrada Seca`). Lo que hicimos con `vinewise-rs` fue conectar cada una de esas estaciones físicas en tierra con la **grilla del reanálisis satelital global ERA5-Land** del Centro Europeo (ECMWF).*
>
> *En el mapa, alrededor de cada punto físico del viñedo, dibujamos un rectángulo amarillo. Ese rectángulo es exactamente **una celda satelital de ERA5-Land**, que mide $0.1^\circ \times 0.1^\circ$, algo así como **un bloque de 11 kilómetros por 11 kilómetros**.*
>
> *(Hacer clic en el polígono de **Idahue** en Colchagua)*
>
> *¿Y qué descubrimos al cruzar los 365 días de la temporada pasada? Que en valles abiertos como **Idahue** en Colchagua o **Lourdes** en Pencahue, la alineación entre la estación física y la celda satelital de 11 km es casi perfecta: tenemos una **correlación térmica de 0.956 a 0.967** y el calor acumulado da prácticamente 1 a 1 (`1.05x`). Es decir, en estos fundos, si el sensor local se apaga mañana, podemos rellenar la temperatura hora a hora desde el satélite con confianza científica total.*
>
> *(Hacer clic en el polígono de **Los Acacios** en Ovalle)*
>
> *Pero ojo, la gracia de auditar con rigor es saber dónde el satélite necesita ayuda. Si miramos **Los Acacios** o **Quebrada Seca** allá arriba en el valle encajonado de Ovalle —Miguel, te lo grafica la geografía de la zona—, una celda de 11 km por 11 km inevitablemente promedia no solo el fondo del valle donde están las parras, sino también la altura de los cerros de los costados. Eso nos genera un desnivel medio de unos $\sim 250\text{ metros}$ entre la celda satelital y el parrón.*
>
> *Gracias a `vinewise-rs`, medimos ese sesgo altitudinal al milímetro: sabemos que el satélite desfasa la temperatura estacional por la altitud. Entonces, antes de usar el satélite para rellenar un hueco en Ovalle, le aplicamos una **corrección térmica por altura ($-0.65^\circ\text{C}$ por cada 100 metros)**. Así bajamos el dato desde el cerro hasta la parra y recuperamos la precisión. Esa es exactamente la robustez agrometeorológica que le estamos regalando al Objetivo 3."*

---

### Bloque 3: Las Curvas Diarias y el Paso a Modelos Lineales Mixtos (15 min)

> **[TIP DE CONDUCCIÓN]:** Cambia a la **Sección 2 (Series Temporales Diarias)** arriba en las pestañas. Muestra cómo se mueven juntas la línea verde (local) y la línea naranja (satelital).

**[SPEECH]:**
> *"Ahora, si pasamos a la **Sección 2 del visor** —donde podemos inspeccionar el día a día de todo el año, filtrando por estación o por variable como Temperatura, Radiación, Lluvia o VPD—, podemos ver visualmente por qué esto funciona.*
>
> *Sebastián, si te fijas en la curva de **Temperatura Media de Idahue**, la línea verde del sensor en tierra y la línea discontinua naranja de ERA5 van bailando juntas todo el año: clavan los frentes fríos de invierno, las olas de calor de enero y la bajada de otoño. Miguel, para que te hagas la idea, las dos curvas van superpuestas con un error medio que apenas supera el grado Celsius.*
>
> *Y tener esta base térmica limpia y continua es lo que nos permite dar el paso metodológico más importante para la modelación de madurez, un punto en el que además coincidimos plenamente en la revisión técnica con Camilo Riveros:*
>
> *Como la acumulación de calor (`GDA`) y el frío (`IFN`) son los grandes motores biológicos de la madurez, pero cada fundo tiene su propio suelo, su propio microclima y su propia edad de parrón, **no nos conviene seguir usando modelos de árboles negros (`Random Forest` o `XGBoost`) para predecir madurez**.*
>
> *¿Por qué? Porque el árbol, al buscar cortes en los datos, termina 'memorizándose' que el cuartel de Pencahue maduró el 15 de marzo, en vez de aprender la relación fisiológica de fondo. Cuando lo llevas a predecir a otro lado, se cae.*
>
> *Por eso estamos haciendo una transición súper limpia hacia **Modelos Lineales Mixtos (LMM)**. En simple para que estemos todos en la misma página: con un Modelo Lineal Mixto, le decimos a la ecuación que la **pendiente de acumulación de calor (`Brix` ganados por cada `GDD`) es nuestro efecto fijo biológico** —la ley general de la vid—, y que todas las diferencias particulares de cada fundo (si la tierra es más arcillosa, si el cuartel es más caluroso o el sesgo de corte en cosecha) absorban su propio **efecto aleatorio por Fundo y Temporada (`1 | Fundo + Temporada`)**.*
>
> *Es una solución matemáticamente elegante, súper transparente para explicarla a cualquier agrónomo o evaluador de CORFO, y que no sobreajusta cuando validamos hacia viñedos nuevos."*

---

### Bloque 4: Acuerdos Prácticos y Próximos Pasos (8 min)

> **[TIP DE CONDUCCIÓN]:** Cierra con mucha calidez, invitando a la conversación y resumiendo 3 acuerdos concretos para que Miguel los tome nota fácilmente por teléfono.

**[SPEECH]:**
> *"Para ir cerrando esta parte y abrir la mesa para escucharlos a ustedes, me gustaría proponerles que dejemos **tres acuerdos bien prácticos y concretos** sancionados hoy para orientar el trabajo de las próximas semanas:*
>
> 1. **Respaldo satelital oficial (`vinewise-rs`):** Adoptar formalmente la grilla satelital ERA5-Land (con su corrección altitudinal por fundo) como nuestra herramienta de cabecera para hacer *gap-filling* e imputar cualquier corte o pérdida de datos en las estaciones físicas de aquí en adelante.
> 2. **Transición a Modelos Lineales Mixtos (`LMM`):** Definir como estándar de modelación predictiva para variables robustas de madurez —como **Sólidos Solubles (`Brix`), `pH` y Acidez Titulable**— el uso de modelos lineales mixtos con validación `Leave-One-Fundo-Out (LOFO)`, dejando atrás los modelos de caja negra para este propósito específico.
> 3. **Honestidad en variables con ruido de operador:** Sincerar en nuestros reportes que el **`Peso de Baya`** tiene una alta variabilidad por el factor humano de muestreo en terreno, y por lo tanto, evaluarlo siempre de forma separada sin exigirle un calce artificial con validaciones cruzadas engañosas.*
>
> *Sebastián, Miguel, abro el micrófono. Me encantaría saber cómo lo ven ustedes desde su vereda y si les hace sentido este camino para avanzar en bloque."*

---

## 3. Manejo Cercano y Sencillo de Preguntas Frecuentes (FAQ)

* **Sebastián o Miguel preguntan: *"¿Por qué no usamos imágenes de satélite más detalladas, como Sentinel de 10 metros, en vez de ERA5 que es de 11 kilómetros?"***
  * **Tu respuesta natural:** *"Es una súper buena pregunta. La diferencia clave es lo que mide cada satélite: Sentinel-2 es buenísimo para ver el color y el vigor de las hojas (`NDVI`), pero pasa cada 5 días y si está nublado se ciega. Y lo más importante: **no mide temperatura de aire ni lluvia**. ERA5-Land es un modelo de reanálisis térmico y atmosférico que nos da la temperatura y la radiación hora a hora, 24/7. Por eso usamos ERA5 para el clima y el calor (`GDA`/`Frío`), y lo cruzamos después con Sentinel si queremos ver el vigor del follaje."*
* **Miguel pregunta por teléfono: *"¿Pero qué tan seguro es corregir la temperatura del satélite cuando hay 200 metros de diferencia en los cerros de Ovalle?"***
  * **Tu respuesta natural:** *"Es totalmente seguro, Miguel, porque nos basamos en un principio físico muy conocido en meteorología que es el gradiente adiabático (la temperatura baja de forma predecible a medida que subes de cota). Como en `vinewise-rs` comparamos 365 días de datos reales en el valle con la celda de los cerros, calculamos exactamente esa pendiente térmica para cada fundo (nos dio unos $-0.65^\circ\text{C}$ cada 100m). Al aplicar esa fórmula, el dato del satélite 'baja' al valle y empalma perfecto con el sensor histórico."*
* **Sebastián o Miguel preguntan: *"¿Y por qué botamos Random Forest si venía dando buenos R-cuadrados en algunos reportes pasados?"***
  * **Tu respuesta natural:** *"Porque esos R-cuadrados altos en Random Forest venían con trampa, chiquillos. Cuando hacías validación cruzada mezclando filas (`CV5_row`), el árbol adivinaba el fundo o la fecha en vez de aprender de biología. Al momento de hacer la prueba de fuego real —es decir, esconder un fundo entero y pedirle al árbol que lo prediga desde cero (`LOFO`)—, el modelo se caía. El Modelo Lineal Mixto (`LMM`) es mucho más honesto: aprende la tasa biológica real de madurez y tolera súper bien que un viñedo nuevo tenga un suelo o un manejo un poco distinto."*
