# Clasificación de Imágenes Satelitales y Detección de Inundaciones: Caso de Estudio Bahía Blanca 2025

**Autores:** Yair Barnatan, German Samartino, Augusto Rey  
**Afiliación:** Maestría en Explotación de Datos y Descubrimiento del Conocimiento, Facultad de Ciencias Exactas y Naturales, Universidad de Buenos Aires (UBA)  
**Materia:** Sistemas de Información Geográfica (Teledetección)  
**Fecha:** Junio de 2026  

---

### Resumen
La delimitación y cuantificación precisa de áreas afectadas por inundaciones es fundamental para la gestión de riesgos y la respuesta ante desastres. Este estudio presenta una metodología híbrida basada en teledetección óptica y aprendizaje automático (Machine Learning) para caracterizar la inundación en la ciudad de Bahía Blanca en 2025. Se utilizaron imágenes multiespectrales de Sentinel-2 adquiridas antes (19 de febrero de 2025) y después (11 de marzo de 2025) del evento. Para la clasificación de agua se implementó un clasificador Random Forest de manera semi-supervisada, entrenado a partir de muestras seleccionadas automáticamente mediante los índices MNDWI y NDWI, y se comparó con un agrupamiento no supervisado K-Means. La máscara de inundación obtenida se filtró topográficamente utilizando el Modelo de Elevación Digital de Copernicus (DEM GLO-30) y se validó descontando los cuerpos de agua permanentes provistos por el Instituto Geográfico Nacional (IGN). Los resultados muestran un área inundada neta de **2206.92 hectáreas** y una población expuesta estimada de **944 habitantes** utilizando datos de WorldPop, demostrando la eficacia de integrar modelos predictivos y datos de soporte geográfico para optimizar la toma de decisiones.

**Palabras clave:** Sentinel-2, Random Forest, MNDWI, Copernicus DEM, WorldPop, WFS IGN, Bahía Blanca.

---

## 1. Introducción
Las inundaciones representan uno de los desastres naturales más recurrentes y destructivos a nivel global, afectando tanto a la infraestructura urbana como a las actividades agropecuarias y la seguridad de la población. Ante eventos de gran escala, los métodos de relevamiento terrestre resultan costosos, lentos y en ocasiones impracticables debido a la inaccesibilidad física de los sectores afectados. En este escenario, la teledetección espacial emerge como una herramienta indispensable y de bajo costo para el monitoreo temporal y espacial de la superficie terrestre.

La constelación de satélites ópticos **Sentinel-2** del programa Copernicus (ESA) proporciona imágenes multiespectrales con una resolución espacial de hasta 10 metros y un tiempo de retorno de 5 días. Estas características facilitan la identificación y caracterización de cuerpos de agua mediante técnicas de índices espectrales (como NDWI y MNDWI) combinados con clasificadores digitales.

El objetivo de este trabajo práctico es delimitar de manera precisa el área afectada por la inundación ocurrida en la ciudad de Bahía Blanca a principios del año 2025, estimar cuantitativamente la cantidad de hectáreas dañadas dentro de un polígono de referencia establecido y evaluar el impacto demográfico resultante mediante datos abiertos de población.

---

## 2. Área de Estudio y Datos Utilizados

### 2.1. Área de Estudio
El estudio se concentra en la periferia y los sectores urbanos y periurbanos de la ciudad de **Bahía Blanca**, provincia de Buenos Aires, Argentina. El área está delimitada por un polígono de referencia (AOI) con límites espaciales aproximados de `[-62.605°W, -38.938°S]` a `[-61.949°W, -38.535°S]`. Esta zona comprende llanuras bajas e interfaces costeras vulnerables a anegamientos fluviales y pluviales.

### 2.2. Datos Espectrales (Sentinel-2 L1C)
Se procesaron dos mosaicos multiespectrales del sensor Sentinel-2 compuestos por 7 bandas clave, remuestreadas a **20 metros de resolución espacial**:
*   **Fechas de Adquisición:** 19 de febrero de 2025 (pre-evento/línea de base) y 11 de marzo de 2025 (post-evento/inundación activa).
*   **Bandas Utilizadas:** Azul (B02), Verde (B03), Rojo (B04), NIR de banda estrecha (B8A), SWIR1 (B11), SWIR2 (B12) y NIR de banda ancha (B08).

### 2.3. Datos de Soporte
*   **Copernicus DEM (GLO-30):** Modelo Digital de Elevación con resolución original de 30m, descargado de forma automática desde AWS y remuestreado a 20m para compatibilidad matemática con la grilla de Sentinel-2. Se utilizó para derivar altitudes y pendientes.
*   **WorldPop:** Capa de densidad poblacional grillada (1 km de resolución original, agregada a 20m mediante interpolación bilineal) correspondiente al año 2020.
*   **Vectores Hidrológicos del IGN:** Capas de espejos y cursos de agua permanentes descargadas mediante el servicio oficial Web Feature Service (WFS) del IGN Argentina.

---

## 3. Metodología

La metodología propuesta se resume en las siguientes cuatro etapas:

```
[Imágenes Sentinel-2] ➔ [Cálculo de NDWI/MNDWI] ➔ [Clasificación Random Forest] ➔ [Filtro DEM + IGN] ➔ [Cruce con WorldPop]
```

### 3.1. Cálculo de Índices Espectrales
El agua presenta una firma espectral característica con una alta reflectancia en el espectro visible (particularmente en el verde) y una absorción casi total en las longitudes de onda del infrarrojo cercano (NIR) e infrarrojo de onda corta (SWIR). Se calcularon dos índices para discriminar el agua:
1.  **NDWI (Normalized Difference Water Index):**
    $$\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$$
2.  **MNDWI (Modified Normalized Difference Water Index):** Reemplaza el NIR por el SWIR1, reduciendo los falsos positivos causados por el ruido urbano en áreas edificadas:
    $$\text{MNDWI} = \frac{\text{Green} - \text{SWIR1}}{\text{Green} + \text{SWIR1}} = \frac{\text{B03} - \text{B11}}{\text{B03} + \text{B11}}$$

### 3.2. Clasificación Digital mediante Machine Learning
Para superar las limitaciones de la umbralización simple, se implementaron dos algoritmos de clasificación en Python utilizando `scikit-learn`:
*   **Random Forest Semi-Supervisado:** Dado que no se disponía de un dataset de entrenamiento manual, se generó un etiquetado automático utilizando regiones de alta confianza de los índices espectrales. Se consideró como *Agua* a los píxeles con $MNDWI > 0.35$ y $NDWI > 0.2$, y como *Tierra* a los píxeles con $MNDWI < -0.1$ y $NDWI < 0.0$. Se entrenaron 50 árboles utilizando las 7 bandas Sentinel-2 y las dos capas de índices (9 variables predictoras).
*   **K-Means No Supervisado:** Se agruparon los píxeles normalizados de las 7 bandas en 5 clusters. El cluster que presentó el valor promedio de MNDWI más elevado fue asignado a la clase *Agua*, sirviendo como método de comparación no supervisado.

### 3.3. Detección de Cambios y Filtrado Topográfico
La máscara cruda de la inundación se obtuvo mediante la diferencia lógica:
$$\text{Inundación Cruda} = \text{Agua}_{\text{Marzo}} \cap \neg \text{Agua}_{\text{Febrero}}$$

Para limpiar esta máscara de ruidos (tales como sombras de nubes o de edificaciones), se aplicó un filtro topográfico derivado del DEM de Copernicus:
*   Se calcularon las pendientes en grados empleando diferencias finitas.
*   Se eliminaron celdas inundadas si presentaban una pendiente superior a los **5 grados** o una altitud superior a los **45 metros** sobre el nivel del mar.
*   Finalmente, se rasterizaron los vectores de espejos de agua perennes del IGN y se restaron de la máscara para descartar lagunas o estuarios permanentes y estimar exclusivamente la superficie inundada transitoria.

---

## 4. Resultados

El análisis espacial detallado arrojó las siguientes métricas clave de impacto:

*   **Superficie Inundada Total:** **2206.92 hectáreas** (55,173 píxeles de 20m de resolución).
*   **Cuerpos de Agua Preexistentes Descontados:** **357.48 hectáreas** identificadas como cuerpos de agua perennes y constantes entre ambas fechas y las capas del IGN.
*   **Población Afectada Estimada:** **944 habitantes**.

El mapa final de superposición (disponible de forma interactiva en la aplicación web) refleja que la inundación se concentró principalmente en los sectores bajos de la periferia este de Bahía Blanca y las cuencas de escurrimiento natural hacia el estuario costero.

---

## 5. Discusión y Comparación de Algoritmos

### 5.1. Comparación: Random Forest vs. K-Means
El clasificador **Random Forest** demostró ser sustancialmente más robusto y menos propenso al ruido de sal y pimienta que el agrupamiento **K-Means**.
*   *K-Means* al agrupar de forma no supervisada tiende a clasificar de forma errónea las sombras de nubes densas y las zonas industriales oscuras como "agua" debido a la baja reflectancia general que comparten.
*   *Random Forest*, al entrenarse con firmas espectrales multidimensionales (incluyendo las bandas visibles e infrarrojas junto con los índices espectrales), delimitó los bordes de la inundación con mayor precisión y nitidez.

### 5.2. Limitaciones del Estudio
*   **Resolución Espacial:** Al trabajar con bandas combinadas a 20m, los canales de drenaje de menor escala (ancho menor a 15m) no pudieron ser resueltos con precisión, subestimando potencialmente pequeños anegamientos locales.
*   **Resolución Temporal y Nubosidad:** Los sensores ópticos dependen de cielos despejados. Aunque las dos fechas seleccionadas presentaron baja nubosidad en el AOI, la dinámica diaria de la inundación durante el pico del evento no pudo capturarse en tiempo real por restricciones del periodo de órbita del satélite y cobertura de nubes intermedia.
*   **Resolución Demográfica:** El dataset de WorldPop utilizado cuenta con una resolución nativa de 1km, lo que requirió una interpolación para integrarse a la escala de 20m. Esto asume una distribución uniforme de la población dentro de cada kilómetro cuadrado, lo cual introduce incertidumbre en el recuento urbano puntual.

---

## 6. Conclusión
El presente trabajo demuestra que la integración de técnicas avanzadas de teledetección multiespectral, algoritmos de aprendizaje automático y capas geográficas de soporte (DEM, IGN, WorldPop) permite construir una metodología eficiente, automatizada y de alta precisión para caracterizar inundaciones y estimar su impacto social en tiempo real. 

La metodología implementada en este estudio es completamente replicable para otras áreas y catástrofes debido al uso exclusivo de software libre en Python y conjuntos de datos de acceso público, constituyendo una herramienta valiosa para la planificación del territorio y la mitigación del impacto ambiental.

---

## 7. Referencias Bibliográficas
*   Ma, S., Zhou, Y., Gowda, P. H., Dong, J., Zhang, G., Kakani, V. G., ... & Jiang, W. (2019). Application of the water-related spectral reflectance indices: A review. *Ecological indicators*, 98, 68-79.
*   Weng, Q. (2011). *Advances in environmental remote sensing: sensors, algorithms, and applications*. CRC Press.
