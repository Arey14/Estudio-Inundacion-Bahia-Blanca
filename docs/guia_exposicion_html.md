# Guión y Defensa Técnica del Visualizador Web (Exposición Oral de index.html)

Este documento es una guía paso a paso diseñada para estructurar tu exposición oral sobre el visualizador web interactivo ([index.html](file:///home/augusto/Desktop/TP2/index.html)) y brindarte argumentos sólidos para responder cualquier pregunta del jurado sobre los modelos, métricas y decisiones metodológicas del proyecto.

---

## 💻 1. Guión para la Explicación del Visualizador Web (Exposición en Vivo)

### Introducción (La Arquitectura del Visualizador)
> **Qué decir:**
> *"Desarrollamos un visualizador interactivo del lado del cliente utilizando HTML5, CSS3 vainilla para el diseño de componentes y la librería Leaflet para la representación de mapas interactivos. Elegimos esta arquitectura porque procesa los datos geográficos de forma estática en cualquier navegador ordinario (o mediante GitHub Pages) sin necesidad de configurar un backend pesado. Para evitar problemas de seguridad del navegador por CORS al cargar archivos JSON locales, las métricas y datos de los modelos se inyectan como un objeto de Javascript (`window.metricasModelos`) cargado desde un archivo estático compilado en nuestro pipeline de Python."*

---

### Paso 1: Pestaña "Resumen del Evento" y Mapa Base
> **Qué decir:**
> *"Al ingresar al visualizador, la primera pestaña ofrece un resumen del evento de Bahía Blanca en 2025. Aquí inicializamos un mapa Leaflet (`mymap`) centrado en las coordenadas geográficas de Bahía Blanca `[-38.72, -62.27]` con un nivel de zoom 11. La capa de fondo es un TileLayer de OpenStreetMap. Sobre este mapa base superponemos capas ráster PNG con transparencia que representan el Copernicus DEM y la densidad poblacional de WorldPop. El usuario puede activar y desactivar estas capas de forma independiente para explorar la topografía y la concentración demográfica de la zona."*

---

### Paso 2: Pestaña "Comparación Sentinel-2"
> **Qué decir:**
> *"En la segunda pestaña, el usuario puede contrastar visualmente la escena antes (Febrero) y después (Marzo) del desborde fluvial. Presentamos composiciones multiespectrales en Falso Color Compuesto combinando las bandas del SWIR1, NIR y Verde de Sentinel-2. En esta combinación, el agua líquida libre absorbe toda la luz y se destaca de forma nítida en tonos azul profundo o negro, mientras que la vegetación refleja fuertemente el NIR y se observa en verde brillante. También incluimos los mapas del índice de agua MNDWI para visualizar la firma de humedad espectral."*

---

### Paso 3: Pestaña "Mapa Interactivo (IGN)"
> **Qué decir:**
> *"En la tercera pestaña integramos la cartografía oficial. Cargamos las geometrías vectoriales de ríos, arroyos y cuerpos de agua estables del Instituto Geográfico Nacional (IGN) a través del servicio oficial WFS. El usuario puede hacer clic en cualquier arroyo (como el Napostá) para desplegar un popup con sus metadatos del IGN. Esto nos permitió restar de forma precisa el agua preexistente y aislar únicamente la inundación temporal."*

---

### Paso 4: Pestaña "Comparación de Modelos"
> **Qué decir:**
> *"La cuarta pestaña es el núcleo analítico de la aplicación. Muestra una tabla comparativa generada dinámicamente con Javascript. El script recorre el objeto `window.metricasModelos` y genera celdas HTML con:*
> 1. *Las Hectáreas Inundadas estimadas con y sin el filtro del DEM.*
> 2. *La Diferencia neta en hectáreas eliminadas por la topografía.*
> 3. *Los Coeficientes espaciales de Jaccard IoU y Dice.*
> 4. *La Población afectada estimada en cada aproximación.*
> *Abajo se presenta la visualización de las máscaras estimadas por cada uno de los 7 modelos. Al hacer clic en los botones, una función en Javascript cambia de forma instantánea el archivo de imagen de superposición (`inundacion_overlay_{modelo}.png`) sobre el mapa de composición espectral."*

---

### Paso 5: Pestaña "Simulación de Crecida"
> **Qué decir:**
> *"La última pestaña es una simulación teórica interactiva de crecida topográfica. Inicializamos un segundo mapa Leaflet (`simmap`). A través de un slider, el usuario controla la cota de elevación topográfica del agua en metros sobre el nivel del mar (m.s.n.m.). Un script en Javascript gestiona el evento de cambio y actualiza en tiempo real la máscara ráster que representa el terreno inundado a esa altitud. También agregamos un botón de 'Play' que arranca un temporizador (`setInterval`) para reproducir automáticamente la animación del avance del agua."*

---

## 🛡️ 2. Guía para la Defensa de Preguntas Técnicas del Jurado

A continuación, se listan las preguntas más difíciles y críticas que el jurado podría plantearte, con las respuestas técnicas exactas para defender tu proyecto:

### Pregunta 1: ¿Por qué el Random Forest Base tiene un Jaccard (IoU) y Dice tan elevados frente a los modelos más complejos? ¿Significa que es mejor?
*   **Respuesta de Defensa:** 
    *"No, no significa que sea el mejor modelo. Esto ocurre debido a la **Paradoja de la Tautología** en la definición de la máscara de referencia. Como no contábamos con un Ground Truth absoluto digitalizado a mano en el terreno, construimos una Máscara de Consenso de Alta Confianza combinando físicamente el MNDWI y la clasificación estadística del Random Forest Base. Es metodológicamente inevitable que el RF Base tenga el solapamiento más alto (Jaccard: 0.6968, Dice: 0.8213) porque él mismo ayudó a definir la máscara contra la que se está comparando.*
    *La verdadera utilidad de Jaccard y Dice es medir cómo se desvían de forma espacial los modelos complejos que no participaron de ese consenso original. Por ejemplo, los modelos avanzados de Ajuste Fino (U-Net FT y Prithvi FT) tienen IoUs más bajos (0.33 y 0.11) porque capturan de forma sensible canales de drenaje estrechos y desbordes periurbanos que la máscara de consenso original (que era excesivamente restrictiva) subestimó por completo."*

### Pregunta 2: ¿Por qué es necesario aplicar un filtro DEM de pendiente menor a 5 grados y altitud menor a 45 metros?
*   **Respuesta de Defensa:** 
    *"El filtro topográfico resuelve dos problemas físicos y un problema de los sensores satelitales:*
    1.  * **Dinámica de Fluidos:** El agua líquida de inundación se comporta bajo la gravedad y busca áreas planas y depresiones. Es físicamente inviable que se acumule agua estancada sobre laderas empinadas orientadas hacia los cerros. Por ello excluimos pendientes $> 5^{\circ}$.*
    2.  * **Sombras de Lomas (Ruido Óptico):** Las colinas elevadas proyectan sombras opuestas al sol. Estas áreas de sombra registran una reflectancia muy baja en NIR y SWIR, **imitando perfectamente la firma del agua** en Sentinel-2. El límite de pendiente de $5^{\circ}$ descarta de inmediato estas falsas alarmas de las sombras.*
    3.  * **Suelos Agrícolas Húmedos de Altura:** Las lluvias saturan la humedad de los suelos arcillosos cultivados en las mesetas altas occidentales (altitud $> 70\text{ m.s.n.m.}$). Esto reduce su reflectancia en el SWIR, engañando a los clasificadores multiespectrales que los etiquetan como agua. La cota máxima de 45 metros descarta estas falsas alarmas, confinando el análisis estrictamente a la llanura de inundación aluvial real."*

### Pregunta 3: ¿Por qué Prithvi Zero-Shot reporta tantas hectáreas inundadas (8966 ha) frente a los demás modelos?
*   **Respuesta de Defensa:** 
    *"Prithvi-EO-2.0 es un modelo fundacional de 300M de parámetros pre-entrenado de forma global en inundaciones (Sen1Floods11). Al carecer de ajuste local (Zero-Shot), opera con umbrales espectrales muy amplios y genéricos. Confunde los suelos arcillosos costeros salinos y muy húmedos de Bahía Blanca con agua estancada inundada. Al no tener calibración fina para el tipo de suelo específico de nuestro polígono, sobreestima de forma severa el agua. Esto se corrigió mediante el **Ajuste Fino Local**, recortando los falsos positivos a 5,869 ha y concentrando la detección únicamente en el agua fluvial real."*

### Pregunta 4: ¿Cómo afectó el desbalance de clases al entrenamiento y cómo lo solucionaron?
*   **Respuesta de Defensa:** 
    *"En Bahía Blanca, el agua inundada representa menos del 3% de los píxeles totales del polígono de estudio. Si entrenamos una red neuronal profunda clásica (como Prithvi o U-Net) de forma directa, el modelo sufre de **colapso de clases**: aprende que clasificar todo como 'tierra' le otorga un 97% de precisión (Accuracy), reduciendo el agua detectada a casi cero (solo 355 ha).*
    *Para resolverlo, implementamos dos estrategias:*
    1.  *En la U-Net, utilizamos una **función de pérdida combinada de Dice Loss y Binary Cross Entropy** (DiceBCE), obligando al modelo a optimizar el contorno del agua.*
    2.  *En Prithvi, incorporamos una ponderación de pesos en la pérdida de entropía cruzada, aplicando un **peso balanceado de 47.83x para la clase agua**, calculada a partir de la proporción de clases del dataset local. Esto obligó al decodificador a especializarse en las características de los píxeles húmedos."*

### Pregunta 5: ¿Por qué usaron BetaEarth y qué es?
*   **Respuesta de Defensa:** 
    *"Los embeddings geoespaciales auto-supervisados de Google DeepMind (AlphaEarth Foundations) tienen la ventaja de capturar las texturas espaciales y formas contextuales de la vecindad de cada píxel a 10m de resolución. Sin embargo, los pesos del codificador de AlphaEarth son cerrados y no se pueden descargar para ejecución local; solo se pueden procesar en la nube de Google Earth Engine.*
    *Para poder desarrollar un pipeline local, autónomo y offline para las imágenes dinámicas del **año 2025**, utilizamos **BetaEarth** (de Asterisk Labs), que es un emulador de código abierto entrenado específicamente para imitar la distribución y dimensiones de los embeddings de AlphaEarth a partir de imágenes Sentinel ordinarias. Esto nos permitió extraer embeddings de 64 dimensiones de forma offline en nuestro entorno de hardware local."*

### Pregunta 6: ¿Cómo estiman la población afectada y qué limitaciones tiene esa estimación?
*   **Respuesta de Defensa:** 
    *"Tomamos la cuadrícula de densidad poblacional de **WorldPop** (que tiene una resolución nativa de 1 km) y la interpolamos bilinealmente a 20 metros de resolución para que se alinee píxel a píxel con la máscara de Sentinel-2. Cuando el modelo predice que una celda de 20 metros está inundada, sumamos los habitantes correspondientes a esa pequeña celda.*
    *La limitación metodológica principal es que la interpolación bilineal asume una distribución demográfica homogénea dentro del kilómetro cuadrado original. En áreas periféricas, industriales o de interfaz periurbana, esto puede generar imprecisiones finas en la cantidad exacta de habitantes, aunque funciona de manera excelente como un indicador regional del nivel de exposición al desastre."*

### Pregunta 7: ¿Por qué en la visualización interactiva de máscaras del HTML decidieron cambiar los colores azul y verde (winter_r) a un color sólido de Cyan Eléctrico?
*   **Respuesta de Defensa:** 
    *"En las primeras versiones de prueba utilizamos un gradiente de color azul y verde (colormap `winter_r`) para las máscaras. Sin embargo, nos topamos con un problema de contraste visual: en la composición de falso color de Sentinel-2 (SWIR-NIR-Green), la vegetación y los campos agrícolas activos se observan en **verde brillante**. El verde de la máscara de inundación se perdía por completo entre los campos vegetados de fondo.*
    *Para resolver este problema de usabilidad, cambiamos la paleta de colores por un **color sólido de Cyan Eléctrico Brillante (#00F5FF)** con una opacidad del 60% (`alpha=0.6`). El Cyan Eléctrico ofrece el máximo contraste físico y visual posible en esta composición de fondo: destaca inmediatamente sobre el verde brillante de las plantas y sobre el azul oscuro/negro del agua de fondo, permitiendo al usuario identificar con absoluta claridad los límites y contornos de la inundación sin confusión espectral."*
