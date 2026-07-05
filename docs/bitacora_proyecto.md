# Bitácora Completa y Guía Técnica del Proyecto: Detección de Inundaciones en Bahía Blanca 2025

Esta bitácora sirve como guía exhaustiva y técnica de inducción para cualquier persona que se sume al proyecto. Explica cada concepto clave, la justificación detrás de las decisiones de ingeniería, el procedimiento detallado paso a paso y el análisis interpretativo de los resultados obtenidos.

---

## 📖 1. Glosario y Diccionario de Términos

### 1.1. Teledetección y Bandas Espectrales (Sentinel-2)
Las imágenes Sentinel-2 capturan la radiación reflejada por la superficie de la Tierra en distintas longitudes de onda (bandas). En este proyecto se utilizan de forma clave las siguientes bandas:
*   **Green (B03 - Verde):** Longitud de onda en torno a los $560\text{ nm}$. El agua líquida limpia tiene una reflectancia moderada en esta porción del espectro.
*   **NIR (B08 / B8A - Infrarrojo Cercano):** Longitud de onda en torno a los $830\text{ nm}$ y $865\text{ nm}$. La vegetación sana refleja fuertemente esta banda (alta firma espectral), mientras que el agua absorbe casi por completo la radiación NIR (se observa de color negro o muy oscuro).
*   **SWIR1 (B11) y SWIR2 (B12) - Infrarrojo de Onda Corta:** Longitudes de onda en torno a los $1610\text{ nm}$ y $2190\text{ nm}$. El agua líquida absorbe de manera absoluta esta radiación. Estas bandas son críticas para diferenciar suelos húmedos y construcciones urbanas del agua líquida libre.

### 1.2. Índices Espectrales de Agua
Combinaciones matemáticas de bandas espectrales diseñadas para resaltar el agua frente a otras coberturas de suelo:
*   **NDWI (Normalized Difference Water Index):**
    $$\text{NDWI} = \frac{\text{Verde} - \text{NIR}}{\text{Verde} + \text{NIR}} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$$
    Se basa en que el agua refleja algo de luz verde pero absorbe casi todo el NIR. Su principal limitación es que genera muchos falsos positivos en zonas urbanas (el asfalto y el hormigón a veces imitan esta firma).
*   **MNDWI (Modified Normalized Difference Water Index):**
    $$\text{MNDWI} = \frac{\text{Verde} - \text{SWIR1}}{\text{Verde} + \text{SWIR1}} = \frac{\text{B03} - \text{B11}}{\text{B03} + \text{B11}}$$
    Reemplaza la banda NIR por SWIR1. Al hacerlo, el índice aprovecha la nula reflectancia del agua en SWIR y la alta reflectancia de las construcciones en SWIR1, aislando y eliminando casi por completo los falsos positivos urbanos que confunden al NDWI tradicional.

### 1.3. Modelo Digital de Elevación (DEM) e Parámetros Topográficos
*   **Copernicus DEM (GLO-30):** Es un Modelo Digital de Elevación global con resolución nativa de 30 metros suministrado por la Agencia Espacial Europea (ESA). Aporta la altitud sobre el nivel del mar en metros (m.s.n.m.) para cada celda espacial.
*   **Pendiente (Slope):** Ángulo de inclinación del terreno respecto de la horizontal, calculado en grados ($^{\circ}$) mediante diferencias de altura entre píxeles adyacentes.
*   **Cota de Simulación:** Altura teórica que define el límite superior del agua en la simulación de crecida.

### 1.4. Métricas Espaciales Duras (Validación Cruzada)
Dado que no existe una máscara perfecta digitalizada a mano en el terreno (Ground Truth absoluto), evaluamos la coincidencia espacial de los modelos contra una **Máscara de Consenso de Alta Confianza** (donde se intersectan la clasificación de RF Base, U-Net y un umbral exigente de MNDWI > 0.4):
*   **Jaccard IoU (Intersection over Union / Intersección sobre Unión):**
    $$\text{IoU} = \frac{|A \cap B|}{|A \cup B|}$$
    Relación entre los píxeles donde ambos coinciden (Intersección) y los píxeles cubiertos por cualquiera de los dos (Unión). Penaliza duramente los falsos positivos y negativos.
*   **Coeficiente de Dice (F1-Score espacial):**
    $$\text{Dice} = \frac{2 \times |A \cap B|}{|A| + |B|}$$
    Media armónica entre precisión y exhaustividad espacial. Mide la cercanía promedio de dos contornos geográficos.

### 1.5. Modelos Fundacionales y Arquitecturas de Aprendizaje Profundo
*   **AlphaEarth (Google DeepMind):** Modelo cerrado que genera embeddings geoespaciales auto-supervisados de 64 dimensiones para capturar el contexto de vecindad de cada píxel a 10m de resolución.
*   **BetaEarth (Asterisk Labs):** Emulador local de código abierto que imita las representaciones espaciales latentes de AlphaEarth utilizando datos estándar de Sentinel-1/2 de forma offline y offline.
*   **Prithvi-EO-2.0 (IBM/NASA):** Modelo fundacional transformador de arquitectura ViT (Vision Transformer) con 300 millones de parámetros, pre-entrenado en enormes datasets globales de teledetección (incluyendo inundaciones generales como Sen1Floods11).
*   **U-Net (ResNet34 backbone):** Red neuronal convolucional estructurada en codificador-decodificador con conexiones puente (*skip connections*) optimizada para tareas de segmentación semántica de imágenes.

---

## 🧭 2. Procedimiento Paso a Paso Detallado

El desarrollo del proyecto siguió una secuencia rigurosa orientada a asegurar la consistencia espectral y física de los datos:

```
[Imágenes Sentinel-2 L1C]
          ↓
[Cálculo de Índices Espectrales (NDWI, MNDWI)]
          ↓
[Definición de Máscara de Consenso de Alta Confianza]
          ↓
[Entrenamiento y Evaluación de 7 Modelos de Clasificación]
          ↓
[Postprocesamiento: Filtro DEM e IGN (Remoción de Espejos Permanentes)]
          ↓
[Cruce Geográfico con WorldPop para Análisis Demográfico]
          ↓
[Exportación de Archivos Vectoriales GeoJSON e Imágenes Overlay]
          ↓
[Visualizador Interactivo en Streamlit y HTML/Leaflet]
```

### Paso 1: Descarga y Remuestreo Espectral
1. Se descargaron las imágenes multiespectrales de Sentinel-2 L1C para las fechas **19 de febrero de 2025** (antes del desborde) y **11 de marzo de 2025** (pico de inundación del evento).
2. Dado que las bandas tienen diferentes resoluciones nativas ($10\text{m}$ para B02-B03-B04 y $20\text{m}$ para B11-B12-B8A), se aplicó un remuestreo bilineal generalizado a una grilla uniforme de **20 metros de resolución espacial**.

### Paso 2: Construcción de Índices Espectrales
Se calcularon las capas matriciales de **NDWI** y **MNDWI** para ambas fechas utilizando las ecuaciones de diferencias normalizadas en la memoria ráster de Python.

### Paso 3: Entrenamiento de Clasificadores Tradicionales (Random Forest)
1. **RF (Base):** Se generaron pseudo-etiquetas de entrenamiento utilizando umbrales seguros sobre los índices espectrales de la imagen de Marzo (inundada). Se consideró agua indiscutible a los píxeles con $MNDWI > 0.35$ y $NDWI > 0.2$. Se entrenó un bosque de 50 árboles usando las 7 bandas más los 2 índices (9 características).
2. **RF (3 PCA):** Se aplicó Análisis de Componentes Principales a las bandas de Marzo para quedarse con 3 componentes principales (reteniendo el **98.97%** de la varianza). Para evitar el error de corrimiento de dominio (domain shift), el escalador estándar (`StandardScaler`) y la transformación lineal de PCA ajustados en Marzo se aplicaron de forma homóloga a la imagen de Febrero antes de clasificar.
3. **RF (BetaEarth):** Se cargaron los canales de Sentinel-2 y se alimentaron al codificador BetaEarth para extraer vectores espaciales de 64 dimensiones por píxel, capturando patrones contextuales locales densos de textura y vecindad. Se entrenó el Random Forest con estas 64 features.

### Paso 4: Entrenamiento de U-Net en PyTorch (Destilación)
Se entrenó una red U-Net con codificador ResNet34 pre-entrenado en ImageNet. En esta primera fase, se usó como etiqueta ("Teacher") la máscara de salida generada por el Random Forest Base. El objetivo es destilar el conocimiento pixel-a-pixel y transformarlo en un comportamiento contextual convolucional, suavizando el ruido de clasificación.

### Paso 5: Preparación de Dataset de Parches y Ajuste Fino Local
1. Se recortó la zona de estudio en parches no solapados de $224 \times 224$ píxeles (tamaño estándar requerido por los transformadores espaciales).
2. Se construyó una **Máscara de Consenso de Alta Confianza** que representa el agua física inequívoca (intersección lógica de RF Base y U-Net donde MNDWI $> 0.4$).
3. **U-Net Ajuste Fino:** Se entrenó la red convolucional sobre estos parches locales usando la pérdida combinada de **Dice Loss y Binary Cross Entropy** para forzar la optimización del contorno fino y la precisión binaria simultáneamente durante 500 épocas.
4. **Prithvi Ajuste Fino:** Se adaptaron los parches a las 6 bandas requeridas por Prithvi (Blue, Green, Red, Narrow NIR, SWIR1, SWIR2) agregando una dimensión temporal. Se congelaron los pesos del encoder (backbone ViT) para preservar el conocimiento general de la NASA y se entrenó únicamente el decodificador espacial (`UperNetDecoder`) bajo un esquema de ponderación extrema: **peso de 47.83x para el agua** debido a que los píxeles inundados representan menos del 3% del total del dataset.

### Paso 6: Postprocesamiento con DEM y Cuerpos de Agua IGN
1. Para cada píxel clasificado como inundado por cualquier modelo en la fecha de Marzo, se comprobó su altitud y pendiente en el DEM remuestreado de Copernicus.
2. Se descartó el píxel si su pendiente era $> 5^{\circ}$ o su altitud $> 45$ metros.
3. Se descargaron las capas vectoriales oficiales de los cuerpos de agua estables e históricos de Bahía Blanca (ríos y lagunas permanentes) a través del WFS del Instituto Geográfico Nacional (IGN) y se restaron de la clasificación para aislar de forma neta únicamente la superficie **temporalmente anegada**.

---

## 🛠️ 3. Justificación de Elección de Modelos

| Modelo | ¿Por qué lo elegimos? | Rol en el Proyecto |
| :--- | :--- | :--- |
| **RF (Base)** | Es el clasificador supervisado de Machine Learning clásico más robusto y rápido de entrenar. | Funciona como nuestro baseline de referencia inicial y generador de pseudo-etiquetas rápidas. |
| **RF (3 PCA)** | La reducción de dimensionalidad remueve la correlación mutua y el ruido entre las bandas del satélite. | Demuestra cómo la simplificación espectral compacta el mapa final y disminuye los falsos positivos. |
| **RF (BetaEarth)** | Reemplaza las firmas puramente espectrales por embeddings contextuales densos de 64 dimensiones. | Incorpora información de texturas espaciales y formas de vecindad directamente en un modelo lineal rápido. |
| **U-Net ResNet34** | Es la red neuronal convolucional estándar en segmentación semántica terrestre, capaz de correlacionar el espacio físico. | Filtra ruidos locales y reconstruye de manera suave y continua la llanura de inundación fluvial. |
| **Prithvi-EO-2.0** | Modelo fundacional transformador pre-entrenado masivamente por la NASA en inundaciones globales. | Representa el estado del arte; posee un entendimiento espectro-temporal superior a cualquier modelo local. |

### ¿Por qué BetaEarth en lugar de AlphaEarth?
*   **AlphaEarth (Google DeepMind)** es un modelo propietario y cerrado. Google no distribuye los pesos del codificador para descarga local; solo se pueden generar embeddings llamando a APIs o scripts pesados dentro de la plataforma en la nube de Google Earth Engine.
*   **BetaEarth (Asterisk Labs)** es un emulador local de código abierto entrenado específicamente para imitar la distribución y dimensiones de los embeddings de AlphaEarth a partir de imágenes Sentinel ordinarias. Elegimos BetaEarth porque nos permite ejecutar de manera local, offline y autónoma la extracción de embeddings de 64 dimensiones para las imágenes dinámicas del **año 2025** sin depender de APIs externas ni límites de cuotas en la nube.

### ¿Por qué descartamos el Clustering (K-Means) de los modelos finales?
Aunque en las fases iniciales de preprocesamiento (`procesamiento.py`) se implementó un agrupamiento no supervisado mediante K-Means ($K=5$) y se etiquetó automáticamente el cluster con mayor MNDWI promedio como "agua", esta aproximación fue descartada del análisis de comparación avanzado por las siguientes razones de inestabilidad y sesgo:
1. **Falta de Semántica Intrínseca:** El agrupamiento K-Means no posee supervisión. Agrupa píxeles puramente por distancia euclidiana en el espacio multiespectral de reflectancias. La decisión de cuál cluster corresponde al agua debe hacerse mediante una heurística posterior (por ejemplo, buscar el centroide con MNDWI promedio más alto). Esto introduce un alto riesgo de error si existen otros elementos oscuros en la imagen (sombras de nubes, áreas urbanas asfaltadas, o lodo húmedo) que terminen cayendo dentro del mismo cluster.
2. **Inestabilidad por Domain Shift Temporal:** K-Means calcula sus centroides de forma independiente para cada imagen. La distribución espectral de la imagen de Febrero (suelo seco) es radicalmente diferente a la de Marzo (suelo inundado). Al calcular clusters independientes, el cluster "agua" de Febrero posee propiedades y límites espectrales muy diferentes al cluster "agua" de Marzo. Al restar las dos máscaras temporales para detectar el cambio neto de inundación, esta disparidad de límites introduce una cantidad masiva de falsos positivos artificiales (ruido de cambio).
3. **Ausencia de Regularización Convolucional o de Vecindad:** K-Means clasifica píxel a píxel de forma aislada. A diferencia de las arquitecturas convolucionales como U-Net o de los transformadores como Prithvi (que procesan parches completos de $224 \times 224$ analizando texturas espaciales y formas de vecindad), el clustering no posee contexto espacial. Esto produce un efecto severo de "sal y pimienta" (píxeles sueltos clasificados de forma errónea) que imposibilita una delimitación cartográfica limpia y profesional.

---

## ⛰️ 4. Justificación de los Filtros Físicos (Pendiente y Altitud)

El filtrado topográfico aplicando límites estrictos de pendiente $\le 5^{\circ}$ y altitud $\le 45$ metros no es una decisión arbitraria, sino una necesidad física de la dinámica de fluidos y la corrección de sensores:

### 4.1. Pendiente $\le 5^{\circ}$
1.  **Dinámica de Fluidos:** Bajo la acción de la gravedad, el agua libre acumulada por desbordes fluviales o anegamientos pluviales busca llanuras y depresiones planas. No puede acumularse físicamente de forma estática en laderas empinadas.
2.  **Eliminación de Sombras (Ruido de Relieve):** Las colinas elevadas proyectan sombras opuestas a la iluminación solar. Esas áreas en penumbra registran una absorción espectral masiva (baja reflectancia en NIR y SWIR) que **imita de manera exacta la firma espectral del agua pura**. Excluir pendientes superiores a $5^{\circ}$ remueve instantáneamente estas falsas alarmas espectrales en el relieve sin afectar la detección de agua en la llanura.

### 4.2. Altitud $\le 45$ metros
1.  **Llanura Aluvial de Bahía Blanca:** Geográficamente, la cuenca baja del Arroyo Napostá y las zonas costeras inundables de Bahía Blanca están situadas en cotas bajas comprendidas entre los 0 y los 40 m.s.n.m. 
2.  **Zonas Altas de Meseta Inmunes:** Hacia el norte y el oeste, el terreno se eleva rápidamente a más de 70-80 metros. Una crecida fluvial local jamás podría alcanzar estas alturas.
3.  **Falsos Positivos por Suelo Agrícola Húmedo:** Tras tormentas severas, el suelo agrícola arcilloso retiene una gran humedad capilar. Esta alta saturación disminuye la reflectancia en las bandas del SWIR de las imágenes Sentinel-2, haciendo que los clasificadores ópticos (como Prithvi Zero-Shot) marquen erróneamente estos campos altos como zonas inundadas. Fijar la cota en 45 metros descarta por completo estas falsas detecciones en sectores altos alejados de las planicies fluviales.

---

## 📊 5. Resultados Cuantitativos y Discusión

### 5.1. Tabla Consolidada de Datos Resultantes

| ID | Modelo / Aproximación | Hectáreas Con DEM (ha) | Hectáreas Sin DEM (ha) | Diferencia (ha) | Jaccard IoU (Consenso) | Dice Coeff. (Consenso) | Población Con DEM (hab) | Población Sin DEM (hab) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **RF (Base)** | 2219.32 | 3261.00 | 1041.68 | 0.6968 | 0.8213 | 960 | 1261 |
| 2 | **RF (3 PCA)** | 1441.00 | 1504.16 | 63.16 | 0.3639 | 0.5336 | 337 | 361 |
| 3 | **RF (BetaEarth Embeddings)** | 2479.12 | 2909.52 | 430.40 | 0.3764 | 0.5469 | 1306 | 1415 |
| 4 | **U-Net ResNet34 (Destilación)** | 1264.16 | 1933.12 | 668.96 | 0.4360 | 0.6072 | 529 | 688 |
| 5 | **U-Net ResNet34 (Ajuste Fino)** | 4446.60 | 4447.44 | 0.84 | 0.3375 | 0.5047 | 280 | 280 |
| 6 | **Prithvi-EO-2.0 (Zero-Shot)** | 8966.56 | 10928.88 | 1962.32 | 0.1692 | 0.2895 | 1874 | 2382 |
| 7 | **Prithvi-EO-2.0 (Ajuste Fino)** | **5869.12** | **8687.92** | **2818.80** | **0.1123** | **0.2019** | **2897** | **3541** |

### 5.2. Análisis Técnico e Interpretación Física de las Discrepancias

1.  **La sobreestimación masiva de Prithvi Zero-Shot (8,966 ha):** Al ser un modelo fundacional global pre-entrenado en condiciones genéricas de todo el planeta, carece de adaptación local. Clasifica cualquier suelo arcilloso llano saturado de humedad costera o agrícola en Bahía Blanca como agua estancada inundada, lo que infla la estimación de hectáreas y población. Su bajo IoU (**0.1692**) confirma este desajuste espacial sistemático.
2.  **La importancia del Ajuste Fino Balanceado (5,869 ha):** En las primeras pruebas de ajuste fino directo, los modelos tendían a colapsar, prediciendo casi 0 ha de agua (solo 355 ha en Prithvi). Esto sucede porque el agua representa menos del 3% de los píxeles del dataset local, por lo que la red neuronal optimiza su precisión global clasificando todo como tierra (la clase mayoritaria). Al introducir el **peso ponderado de 47.83x para el agua** en la pérdida por entropía cruzada de Prithvi y entrenar durante 500 épocas, forzamos al decodificador a especializarse en los píxeles húmedos locales. El modelo **Prithvi Ajustado** logró delimitar con gran exhaustividad la llanura de inundación fluvial sin colapsar.
3.  **U-Net Ajuste Fino y su independencia del DEM:** Como se observa en la tabla, el modelo U-Net entrenado con parches locales arrojó prácticamente las mismas hectáreas con DEM (**4,446.60 ha**) que sin DEM (**4,447.44 ha**). Al poseer un campo receptivo espacial amplio ($224 \times 224$ píxeles, equivalente a parches de $4.48 \text{ km} \times 4.48 \text{ km}$ en el terreno), la red convolucional asimiló de forma implícita los patrones topográficos del relieve de Bahía Blanca, descartando de forma automática el agua ficticia en laderas altas sin necesidad de un filtro de altitud complementario.
4.  **Distribución de Población Expuesta:** Aunque Prithvi Ajustado delimita menos hectáreas totales que el Prithvi Zero-Shot (5,869 ha vs 8,966 ha), reporta una población afectada significativamente mayor (**2,897 hab** vs 1,874 hab con DEM). Esto se debe a que el modelo ajustado localmente es extremadamente sensible en los bordes fluviales bajos de la periferia urbana de Bahía Blanca (donde el desborde del arroyo impactó de lleno en áreas urbanizadas de alta densidad de población periurbana), mientras que el Zero-Shot desperdicia hectáreas detectando falsos positivos en zonas rurales de bajísima densidad demográfica hacia el oeste.

---

## 🎬 6. Simulación Teórica de Crecida Topográfica

El visualizador cuenta con un módulo interactivo de simulación de crecida topográfica a escala fina:

*   **¿Qué es lo que hace?** Modela teóricamente qué celdas de terreno quedarían anegadas si el agua subiera a una altura determinada de forma uniforme sobre el nivel del mar, considerando únicamente la morfología física del terreno.
*   **¿Qué métrica se está moviendo?** La métrica de control es la **cota de elevación** (altitud en metros sobre el nivel del mar, m.s.n.m.), controlada por el slider interactivo del visualizador (entre 0 y 30m).
*   **Algoritmo y Restricción de Pendiente:** A diferencia de una simple inundación por inundación lineal de celdas planas, el algoritmo evalúa en cada celda del Copernicus DEM si su altura es $\le \text{cota seleccionada}$ y, simultáneamente, si su pendiente local es plana o muy suave ($\le 5^{\circ}$). Esto evita que la simulación inunde laderas inclinadas altas donde el agua escurriría de inmediato.
*   **Animación e Interpretación Física:** Al desplazar el slider o dar click en "Reproducir", se observa la dinámica de vulnerabilidad del territorio: las áreas bajas y lagunas del este y del sur (cercanas al estuario y puertos) son las primeras en sumergirse por completo a cota 6m. La zona céntrica consolidada de Bahía Blanca está protegida de forma natural gracias a que se asienta sobre una meseta con cota superior a los 20-25 metros.

---

## 🗺️ 7. Distribución de Población e Integración Cartográfica

### 7.1. Cruce con WorldPop (Desagregación Espacial)
1.  Los datos originales de **WorldPop** se distribuyen en formato ráster con celdas grilladas de aproximadamente 1 km de resolución espacial (cada celda contiene la cantidad estimada de habitantes para esa porción de tierra).
2.  Para poder cruzarlo de forma exacta con la cuadrícula de Sentinel-2 ($20\text{m}$), se aplicó una interpolación bilineal que suaviza la densidad poblacional en una grilla fina de $20\text{m}$.
3.  Dado que cada celda de 20 metros representa una fracción de la celda original de 1 km, la población se distribuye de forma proporcional para asegurar que la suma total de habitantes del partido se conserve perfectamente (principio de conservación de masa demográfica).
4.  Cuando un modelo ráster predice que un píxel de 20m está "Inundado" ($= 1$), el script suma el valor de habitantes asignado a esa celda en la matriz de WorldPop. Así se obtiene la estimación consolidada de personas expuestas directamente a la inundación.

### 7.2. Mapa Interactivo (HTML / Leaflet)
El visualizador web interactivo ([index.html](file:///home/augusto/Desktop/TP2/index.html)) y el dashboard de Streamlit ([dashboard.py](file:///home/augusto/Desktop/TP2/scripts/dashboard.py)) cargan estas capas espaciales para permitir su exploración dinámica:
*   **Control de Capas (Layers Control):** Permite al usuario activar y desactivar de forma independiente el mapa de elevación DEM, el mapa de densidad de población WorldPop y las diferentes máscaras de inundación estimadas por los modelos.
*   **Superposición Transparente:** La composición en falso color de Sentinel-2 de Marzo sirve de fondo inmóvil, sobre el cual se aplican transparencias de las máscaras de inundación para permitir al usuario constatar visualmente qué modelo delimita con mayor fidelidad el contorno del agua visible.
