# Plan de Presentación para la Defensa del TP2 (Exposición Oral de 15 Minutos)

Este documento detalla la estructura diapositiva por diapositiva para la ponencia en clase, optimizada para durar exactamente **15 minutos** y destacar los aspectos más fuertes del trabajo: el uso de Machine Learning, el filtrado topográfico y el visualizador interactivo.

---

## 🧭 Recomendaciones Generales para la Ponencia

*   **Distribución del Tiempo:** 11 minutos de diapositivas conceptuales, 3 minutos de demostración del Dashboard interactivo en vivo, y 1 minuto para conclusiones y preguntas.
*   **Diseño Visual de las Diapositivas:** Evitar textos largos. Usar títulos limpios, esquemas metodológicos (diagramas de flujo), tablas cortas y destacar fuertemente las imágenes generadas (`img/`).
*   **Rol de los Expositores:** Se sugiere dividir la presentación en tres partes lógicas (uno para datos y preprocesamiento, otro para algoritmos de ML y filtrado, y otro para resultados, dashboard e impacto).

---

## 🗂️ Estructura Diapositiva por Diapositiva

### Diapositiva 1: Carátula e Introducción
*   **Visual:** Logotipo de la Maestría/UBA, título del proyecto: "Clasificación de Imágenes Satelitales para la Detección y Cuantificación de Áreas Inundadas: Caso Bahía Blanca 2025". Nombres de los integrantes (*Yair Barnatan, German Samartino, Augusto Rey*).
*   **Contenido:**
    *   Presentación del equipo.
    *   Planteo de la problemática: La inundación de Bahía Blanca en 2025.
    *   Objetivo principal: Mapear el área afectada, calcular las hectáreas inundadas y cuantificar la población afectada dentro del polígono de referencia (AOI).
*   **Tiempo Objetivo:** 1:30 minutos.
*   **Guion:** *"Buenas tardes. En esta presentación expondremos los resultados del Trabajo Práctico N° 2. Nos enfocamos en la caracterización y mapeo de la inundación ocurrida en Bahía Blanca a comienzos de 2025, utilizando una metodología de teledetección óptica integrada con Machine Learning y filtros topográficos..."*

---

### Diapositiva 2: Datos Utilizados (Insumos del Proyecto)
*   **Visual:** Íconos representativos de cada fuente de datos y un mapa de localización rápida de la zona de estudio.
*   **Contenido:**
    *   **Sentinel-2:** Imágenes ópticas de pre-evento (19 de Febrero) y post-evento (11 de Marzo). 7 bandas remuestreadas a 20m.
    *   **Copernicus DEM GLO-30:** Datos topográficos de 30m de resolución (remuestreados a 20m).
    *   **WorldPop (2020):** Densidad poblacional a 1km de resolución para estimar el impacto social.
    *   **IGN Argentina:** Capas vectoriales oficiales de cursos e hidrología de Bahía Blanca.
*   **Tiempo Objetivo:** 1:30 minutos.
*   **Guion:** *"Para llevar a cabo este estudio nos basamos en cuatro pilares de datos abiertos. El principal insumo son las imágenes Sentinel-2 de la ESA, las cuales preprocesamos para alinear todas sus bandas a 20 metros. A esto le sumamos el DEM global de Copernicus, los mapas de población grillados de WorldPop, y las capas de referencia del IGN descargadas dinámicamente mediante WFS..."*

---

### Diapositiva 3: Metodología: Cálculo de Índices Espectrales
*   **Visual:** Gráfico de firma espectral del agua (explicando la alta reflectancia en el verde y absorción en el SWIR) y las ecuaciones de NDWI y MNDWI. A los costados, la imagen de Marzo en falso color vs el mapa de MNDWI calculado.
*   **Contenido:**
    *   **Firma Espectral:** Por qué el agua resalta en ciertas bandas.
    *   Fórmula del **NDWI** (Verde y NIR).
    *   Fórmula del **MNDWI** (Verde y SWIR1) y su ventaja en áreas periurbanas para evitar confusión con el concreto y las edificaciones.
*   **Tiempo Objetivo:** 2:00 minutos.
*   **Guion:** *"La firma espectral del agua absorbe casi toda la radiación en las longitudes del infrarrojo cercano y del SWIR, mientras que refleja en el verde. Aprovechando esto, calculamos el NDWI tradicional y el MNDWI modificado. Este último es clave en Bahía Blanca porque al usar la banda SWIR1 elimina los falsos positivos que suele dar el concreto urbano en el NDWI clásico..."*

---

### Diapositiva 4: Metodología: Clasificación por Machine Learning
*   **Visual:** Diagrama de flujo del entrenamiento del clasificador. Captura de la comparación visual de la clasificación Random Forest vs K-Means.
*   **Contenido:**
    *   **Random Forest Semi-Supervisado:** Generación de etiquetas automáticas de "alta confianza" basadas en umbrales de MNDWI y NDWI. Entrenamiento con las 7 bandas y los 2 índices (9 variables predictoras).
    *   **K-Means No Supervisado:** Agrupamiento en 5 clases y selección del cluster con mayor MNDWI medio.
    *   **Comparación:** Ventajas de Random Forest en estabilidad ante sombras y nubosidad frente a K-Means.
*   **Tiempo Objetivo:** 2:30 minutos.
*   **Guion:** *"Para clasificar el agua fuimos más allá de la umbralización simple e implementamos dos aproximaciones de Machine Learning. Para Random Forest creamos una estrategia semi-supervisada: usamos los índices espectrales para etiquetar píxeles de entrenamiento de extrema confianza, y entrenamos un bosque con las 7 bandas y los índices. Al comparar con K-Means, vimos que Random Forest es significativamente más inmune al ruido espectral provocado por sombras urbanas e industriales..."*

---

### Diapositiva 5: Metodología: Filtrado Topográfico e Hidrología IGN
*   **Visual:** Gráfico del DEM de Copernicus al lado de la máscara de inundación con las áreas filtradas marcadas en rojo/amarillo.
*   **Contenido:**
    *   **Filtro por DEM:** Cálculo de pendientes. Eliminación de píxeles inundados si la pendiente es > 5° o la altitud es > 45 m.s.n.m. (inconsistencias físicas).
    *   **Descuento de Hidrología del IGN:** Descarga de capas vectoriales, rasterización y resta de cuerpos de agua permanentes.
*   **Tiempo Objetivo:** 2:00 minutos.
*   **Guion:** *"Cualquier clasificación óptica contiene falsos positivos debido a las sombras de relieve y nubes. Para solucionarlo, aplicamos un filtro físico con el DEM de Copernicus: eliminamos las zonas clasificadas como agua en laderas con pendiente mayor a 5 grados o en elevaciones mayores a 45 metros, ya que topográficamente el agua no se acumularía allí. Por último, usamos la hidrología permanente del IGN para descontar lagunas y ríos preexistentes y quedarnos estrictamente con la inundación temporal..."*

---

### Diapositiva 6: Resultados y Análisis Demográfico
*   **Visual:** Tabla o infografía grande con las métricas clave: **2206.92 ha** inundadas netas, **944 personas** afectadas, **357.48 ha** de agua permanente descontadas.
*   **Contenido:**
    *   Cuantificación final del área afectada.
    *   Estimación demográfica cruzando la máscara espacial de inundación con el mapa de densidad poblacional de WorldPop.
    *   Análisis de vulnerabilidad social.
*   **Tiempo Objetivo:** 2:00 minutos.
*   **Guion:** *"Los resultados finales indican que la inundación afectó un total de 2206 hectáreas netas dentro del polígono. Al cruzar espacialmente esta máscara con la cuadrícula de población de WorldPop, estimamos que aproximadamente 944 personas estuvieron directamente expuestas. La mayor parte de la inundación ocurrió en áreas bajas de cultivo y humedales periféricos, lo que evitó una catástrofe mayor en el casco urbano consolidado..."*

---

### Diapositiva 7: Demostración Interactiva (Dashboard)
*   **Visual:** **[Demo en vivo]** Minimizar las diapositivas y proyectar el navegador web con la aplicación en Streamlit corriendo en `localhost` o el sitio de GitHub Pages.
*   **Contenido:**
    *   Mostrar la solapa "Resumen de Resultados" con el mapa de superposición.
    *   Navegar por "Comparación Sentinel-2" usando el comparador deslizante (si está disponible) o las imágenes de Falso Color.
    *   Mostrar el "Mapa Interactivo IGN" navegando por Leaflet, haciendo clics en los elementos vectoriales y mostrando las leyendas.
*   **Tiempo Objetivo:** 2:30 minutos.
*   **Guion:** *"Queremos mostrarles ahora la herramienta interactiva que desarrollamos para la exploración y toma de decisiones. Este tablero web permite a los equipos de emergencia visualizar las composiciones en falso color de Sentinel, contrastar los mapas de humedad MNDWI, explorar las elevaciones del terreno y navegar por un mapa interactivo con las capas oficiales de ríos y lagunas del IGN cargadas dinámicamente..."*

---

### Diapositiva 8: Discusión, Limitaciones y Trabajos Futuros
*   **Visual:** Bullet-points muy limpios.
*   **Contenido:**
    *   *Limitaciones:* Resolución espacial (20m que omite canales pequeños), resolución demográfica (WorldPop interpolado de 1km).
    *   *Trabajos futuros:* Incorporar sensores de Radar (SAR como Sentinel-1) para penetrar nubes; integrar modelos de simulación hidráulica.
*   **Tiempo Objetivo:** 1:00 minuto.
*   **Guion:** *"Como discusión, reconocemos que el sensor óptico tiene la limitación de la cobertura de nubes y que los 20m de resolución pueden omitir pequeños canales. Para futuros trabajos, proponemos incorporar imágenes de Radar Sentinel-1 que operan de noche y con tormenta, y complementar con simulaciones hidráulicas más complejas..."*

---

### Diapositiva 9: Cierre y Preguntas
*   **Visual:** "Muchas gracias". Datos de contacto e integrantes. Enlace al repositorio de GitHub y la web de GitHub Pages.
*   **Contenido:**
    *   Agradecimiento.
    *   Espacio para preguntas de los profesores y compañeros.
*   **Tiempo Objetivo:** 0:30 segundos (más el tiempo de preguntas).
*   **Guion:** *"Muchas gracias por su atención. Quedamos abiertos a cualquier consulta o sugerencia sobre nuestro trabajo."*
