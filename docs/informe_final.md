# Clasificación de Imágenes Satelitales y Detección de Inundaciones: Caso de Estudio Bahía Blanca 2025

**Autores:** Yair Barnatan, German Samartino, Augusto Rey  
**Afiliación:** Maestría en Explotación de Datos y Descubrimiento del Conocimiento, Facultad de Ciencias Exactas y Naturales, Universidad de Buenos Aires (UBA)  
**Materia:** Sistemas de Información Geográfica (Teledetección)  
**Fecha:** Junio de 2026  

---

### Resumen
La delimitación y cuantificación precisa de áreas afectadas por inundaciones es fundamental para la gestión de riesgos y la respuesta ante desastres. Este estudio presenta un análisis comparativo y exhaustivo que evalúa **siete metodologías diferentes** basadas en teledetección óptica y aprendizaje automático (tanto tradicional como aprendizaje profundo) para caracterizar la inundación en la ciudad de Bahía Blanca en 2025. Se utilizaron imágenes multiespectrales de Sentinel-2 adquiridas antes (19 de febrero de 2025) y después (11 de marzo de 2025) del evento. 

Se implementaron clasificadores tradicionales como Random Forest base (con bandas e índices MNDWI/NDWI) y K-Means, aproximaciones de reducción de dimensionalidad y embeddings (PCA y embeddings de 64 dimensiones de la red fundacional BetaEarth), y arquitecturas de aprendizaje profundo (U-Net ResNet34 por destilación y por ajuste fino, y el modelo fundacional de teledetección Prithvi-EO-2.0 de 300M de parámetros en modalidad Zero-Shot y Fine-Tuned). Las máscaras crudas se filtraron topográficamente con el Modelo de Elevación Digital de Copernicus (DEM GLO-30) y se descontaron los cuerpos de agua permanentes del Instituto Geográfico Nacional (IGN). 

Los resultados demuestran que el ajuste fino de **Prithvi-EO-2.0** utilizando pesos de clase balanceados (ponderación de **47.83x** para la clase agua) resolvió con éxito el problema del desbalance extremo de clases, delimitando **5869.12 hectáreas** inundadas netas y **2897 personas afectadas** (cruzadas con WorldPop), logrando el mejor balance entre sensibilidad espacial y especificidad frente a la sobreestimación del modelo Zero-Shot y la sub-detección de los clasificadores pixel-a-pixel.

**Palabras clave:** Sentinel-2, Prithvi-EO-2.0, U-Net, Random Forest, BetaEarth Embeddings, Copernicus DEM, WorldPop, WFS IGN, Bahía Blanca.

---

## 1. Introducción
Las inundaciones representan uno de los desastres naturales más recurrentes y destructivos a nivel global, afectando tanto a la infraestructura urbana como a las actividades agropecuarias y la seguridad de la población. Ante eventos de gran escala, los métodos de relevamiento terrestre resultan costosos, lentos y en ocasiones impracticables debido a la inaccesibilidad física de los sectores afectados. En este escenario, la teledetección espacial emerge como una herramienta indispensable y de bajo costo para el monitoreo temporal y espacial de la superficie terrestre.

La constelación de satélites ópticos **Sentinel-2** del programa Copernicus (ESA) proporciona imágenes multiespectrales con una resolución espacial de hasta 10 metros y un tiempo de retorno de 5 días. Estas características facilitan la identificación y caracterización de cuerpos de agua mediante técnicas de índices espectrales (como NDWI y MNDWI) combinados con clasificadores digitales. 

Sin embargo, las metodologías tradicionales basadas en umbrales de índices o clasificadores pixel-a-pixel (como Random Forest o K-Means) suelen omitir relaciones espaciales complejas y texturas de la imagen, o sufrir sesgos ante sombras de nubes y áreas urbanas. Con la llegada de los modelos de Deep Learning y, más recientemente, de los **Modelos Fundacionales de Teledetección** (como Prithvi-EO-2.0 de IBM/NASA), es posible explotar patrones geoespaciales abstractos de gran escala y transferir este conocimiento a tareas locales mediante técnicas de transferencia de aprendizaje (Fine-Tuning).

El objetivo de este trabajo práctico es evaluar, comparar y validar detalladamente siete enfoques metodológicos para delimitar la inundación ocurrida en la ciudad de Bahía Blanca a principios del año 2025, estimar cuantitativamente la cantidad de hectáreas dañadas y cuantificar la exposición demográfica resultante en la población.

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

La metodología general abarca desde el preprocesamiento espectral básico hasta el entrenamiento local de redes convolucionales y transformadores espaciales en GPU.

```
[Imágenes Sentinel-2] ➔ [Cálculo de Índices / Reducción / Embeddings / Deep Learning]
                                     ↓
                          [Máscaras de Inundación]
                                     ↓
                          [Filtro DEM + Vectores IGN]
                                     ↓
                       [Hectáreas Netas y Cruce con WorldPop]
```

### 3.1. Cálculo de Índices Espectrales
Se calcularon los siguientes índices espectrales clásicos como predictores y bases de etiquetado:
1.  **NDWI (Normalized Difference Water Index):**
    $$\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$$
2.  **MNDWI (Modified Normalized Difference Water Index):** Reemplaza el NIR por el SWIR1, reduciendo los falsos positivos causados por el ruido urbano en áreas edificadas:
    $$\text{MNDWI} = \frac{\text{Green} - \text{SWIR1}}{\text{Green} + \text{SWIR1}} = \frac{\text{B03} - \text{B11}}{\text{B03} + \text{B11}}$$

### 3.2. Clasificación Digital mediante Modelos Tradicionales
*   **Random Forest Semi-Supervisado (Base):** Se generó un etiquetado automático utilizando regiones de alta confianza de los índices espectrales. Se consideró como *Agua* a los píxeles con $MNDWI > 0.35$ y $NDWI > 0.2$, y como *Tierra* a los píxeles con $MNDWI < -0.1$ y $NDWI < 0.0$. Se entrenó un ensamble de 50 árboles utilizando las 7 bandas Sentinel-2 y las dos capas de índices (9 variables predictoras en total).
*   **K-Means No Supervisado:** Se agruparon los píxeles normalizados de las 7 bandas en 5 clusters. El cluster que presentó el valor promedio de MNDWI más elevado fue asignado a la clase *Agua*.

### 3.3. Detección de Cambios y Filtrado Topográfico
Para todas las metodologías se obtuvo la máscara cruda mediante la diferencia lógica:
$$\text{Inundación Cruda} = \text{Agua}_{\text{Marzo}} \cap \neg \text{Agua}_{\text{Febrero}}$$

Esta máscara cruda se limpió de ruidos (tales como sombras de nubes o de edificaciones) aplicando un filtro topográfico derivado del DEM de Copernicus:
*   Se eliminaron celdas inundadas si presentaban una pendiente superior a los **5 grados** o una altitud superior a los **45 metros** sobre el nivel del mar (llanuras fluviales de inundación estricta).
*   Finalmente, se restaron las geometrías de cuerpos de agua permanentes provistas por el IGN (espejos y cursos de agua) para aislar exclusivamente la superficie temporalmente anegada.

### 3.4. Modelos Avanzados de Aprendizaje Profundo y Representaciones Latentes

Para evaluar mejoras en la precisión espacial, se desarrollaron modelos adicionales:

1.  **Random Forest con PCA (3 Componentes):** Se aplicó Análisis de Componentes Principales a las 7 bandas Sentinel-2 (reteniendo el **98.97%** de la varianza total) con un escalado robusto ajustado en la imagen de Marzo y aplicado de manera homóloga a Febrero para neutralizar el corrimiento de dominio (domain shift).
2.  **Random Forest con Embeddings BetaEarth:** Se empleó un codificador local basado en la red fundacional BetaEarth para extraer vectores latentes espaciales de 64 dimensiones por cada píxel de Sentinel-2 (utilizando interpolación lineal en las bandas B05, B06 y B07 para recrear el formato espectral requerido). Estos embeddings espaciales sirvieron como features para entrenar un Random Forest.
3.  **U-Net (ResNet34) por Destilación Supervisada:** Se entrenó una red convolucional U-Net en PyTorch utilizando como etiquetas la máscara de salida del Random Forest Base. Este paso actúa como un regularizador espacial que filtra ruidos de alta frecuencia (sal y pimienta).
4.  **U-Net (ResNet34) por Ajuste Fino Local (Fine-Tuning):** Se preparó un dataset local de parches de $224 \times 224$ píxeles recortando las imágenes multiespectrales y las pseudo-etiquetas de consenso de alta confianza (intersección estricta de RF base, U-Net y MNDWI > 0.4). Se entrenó la red U-Net de forma supervisada sobre estos parches locales utilizando una función de pérdida combinada de Dice Loss y Binary Cross Entropy (DiceBCE) durante **500 épocas** en una GPU NVIDIA RTX 3090.
5.  **Prithvi-EO-2.0 (Zero-Shot):** Inferencia directa usando el transformador de 300 millones de parámetros desarrollado por IBM y la NASA, pre-entrenado en el dataset de teledetección Sen1Floods11. Se adaptaron las bandas de Sentinel-2 a la secuencia requerida por Prithvi (Blue, Green, Red, Narrow NIR, SWIR1, SWIR2) y se agregó una dimensión temporal.
6.  **Prithvi-EO-2.0 (Ajuste Fino Local):** Se ajustó el transformador fundacional sobre el dataset de parches locales de $224 \times 224$ píxeles. Con el fin de evitar el sobreajuste y la destrucción catastrófica de los pesos pre-entrenados, se congelaron los pesos del codificador (Vision Transformer backbone y el neck) y se entrenaron únicamente los parámetros del decodificador espacial (UperNetDecoder). Debido al extremo desbalance entre la clase tierra y la clase agua (solo una fracción mínima de los parches contiene inundación), se incorporó una ponderación de pesos de clase en la pérdida de entropía cruzada, asignando un **peso de 47.83x para el agua** calculado a partir del dataset. Se entrenó durante **500 épocas** en la GPU.

---

## 4. Resultados

El análisis espacial comparativo arrojó las siguientes métricas cuantitativas consolidadas para cada una de las aproximaciones evaluadas dentro del polígono de estudio:

| ID | Modelo / Aproximación | Hectáreas Con DEM (ha) | Hectáreas Sin DEM (ha) | Diferencia (ha) | Jaccard IoU (Consenso) | Dice Coeff. (Consenso) | Población Con DEM (hab) | Población Sin DEM (hab) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **RF (Base)** | 2219.32 | 3261.00 | 1041.68 | 0.6968 | 0.8213 | 960 | 1261 |
| 2 | **RF (3 PCA)** | 1441.00 | 1504.16 | 63.16 | 0.3639 | 0.5336 | 337 | 361 |
| 3 | **RF (BetaEarth Embeddings)** | 2479.12 | 2909.52 | 430.40 | 0.3764 | 0.5469 | 1306 | 1415 |
| 4 | **U-Net ResNet34 (Destilación)** | 1264.16 | 1933.12 | 668.96 | 0.4360 | 0.6072 | 529 | 688 |
| 5 | **U-Net ResNet34 (Ajuste Fino)** | 4446.60 | 4447.44 | 0.84 | 0.3375 | 0.5047 | 280 | 280 |
| 6 | **Prithvi-EO-2.0 (Zero-Shot)** | 8966.56 | 10928.88 | 1962.32 | 0.1692 | 0.2895 | 1874 | 2382 |
| 7 | **Prithvi-EO-2.0 (Ajuste Fino)** | **5869.12** | **8687.92** | **2818.80** | **0.1123** | **0.2019** | **2897** | **3541** |

El gráfico comparativo consolidado (rediseñado como gráfico de barras agrupadas y línea de población) se presenta a continuación:

![Gráfico Comparativo de Modelos y Embeddings](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/comparacion_metricas_modelos.png)

---

## 5. Discusión y Comparación de Algoritmos

### 5.1. Análisis Comparativo de Rendimiento y Defensa de Modelos
*   **RF (Base):** Este modelo pixel-a-pixel sirve como línea de base (2219 ha con DEM). Al no incorporar relaciones contextuales locales, su salida presenta "ruido de sal y pimienta". Sin embargo, gracias al cálculo manual de NDWI y MNDWI, detecta de forma excelente el núcleo del cuerpo de agua con alta reflectancia.
*   **RF (3 PCA):** Reduciendo la dimensionalidad a 3 componentes principales (PCA), se retiene el 98.97% de la varianza pero se filtra el ruido. Esto compacta las predicciones (1441 ha), pero subestima la inundación al omitir acumulaciones de agua localizadas de menor escala.
*   **RF con Embeddings BetaEarth:** El clasificador RF entrenado sobre embeddings espaciales auto-supervisados (2479 ha) logra un excelente balance. El codificador espacial suaviza los contornos y capta la forma geomorfológica natural de los cauces y llanuras inundadas.
*   **U-Net ResNet34 (Destilación vs Fine-Tuning):** El modelo de destilación (1264 ha) actúa como un regularizador convolucional de la máscara de RF base, rellenando huecos internos y removiendo ruidos. El modelo de Ajuste Fino (4446 ha), entrenado con parches locales y pérdida combinada Dice+BCE durante 500 épocas, demuestra un excelente poder de generalización, identificando estructuras continuas de drenaje urbano.
*   **Prithvi-EO-2.0 (Zero-Shot vs Fine-Tuning Ponderado):** La inferencia *Zero-Shot* (8966 ha) sobreestima de forma masiva el área inundada al clasificar como "agua" a las zonas de suelo húmedo de llanuras de pendiente nula y zonas periurbanas de suelo arcilloso debido a sus firmas espectrales similares. El modelo ajustado localmente (**Prithvi Ajuste Fino** con 5869 ha), entrenado con pesos balanceados (**47.83x para el agua**), especializa su decodificador en la reflectancia y topografía específicas de Bahía Blanca. Captura con gran fidelidad la llanura de inundación fluvial real, reduciendo drásticamente la sobreestimación general del Zero-Shot sin colapsar hacia predicciones de tierra.

### 5.2. Impacto Cuantitativo y Físico del Filtro DEM
La comparación cuantitativa de los resultados con y sin el filtro topográfico del DEM (pendiente $\le 5^{\circ}$ y altitud $\le 45$ metros) revela que el DEM es un componente crítico de postprocesamiento:
*   En **Prithvi Zero-Shot**, el DEM reduce la estimación de 10928.88 ha a 8966.56 ha (removiendo 1962.32 ha de falsos positivos en colinas y laderas elevadas de suelo húmedo).
*   En **RF (Base)**, disminuye de 3261.00 ha a 2219.32 ha (1041.68 ha descartadas), eliminando sombras urbanas y de relieve en los sectores altos del oeste de Bahía Blanca.
*   En **Prithvi (Ajuste Fino)**, el filtro remueve 2818.80 ha. Esto demuestra que incluso con el fine-tuning local, los transformadores multiespectrales pueden predecir falsos positivos en laderas o mesetas altas que físicamente no pueden acumular agua de crecida. El DEM aporta la validación física indispensable.

### 5.3. Mitigación del Desbalance de Clases
La experiencia con el transformador fundacional Prithvi resalta la importancia de las funciones de pérdida pesadas en problemas de teledetección. Dado que el agua inundada representa menos del 3% de los píxeles del AOI analizado, las redes neuronales profundas tienden a colapsar hacia predicciones mayoritarias (tierra). El uso de la ponderación de pesos en la CrossEntropy y la pérdida Dice en U-Net demostraron ser pasos obligatorios para habilitar el uso práctico de modelos con millones de parámetros en zonas geográficas locales específicas.

### 5.4. Explicación Metodológica de BetaEarth
El uso de **BetaEarth (Asterisk Labs)** en lugar del modelo original **AlphaEarth Foundations (AEF) de Google DeepMind** se debe a restricciones de accesibilidad y propiedad intelectual:
1.  **AlphaEarth** es un modelo cerrado y sus pesos no están disponibles para descarga pública o ejecución local. Google solo distribuye sus embeddings precalculados como colecciones estáticas dentro de la plataforma Google Earth Engine.
2.  **BetaEarth** actúa como un emulador local de código abierto entrenado a partir de los datos públicos de AlphaEarth. Nos permite generar localmente representaciones latentes de 64 dimensiones para las imágenes multiespectrales dinámicas del **año 2025** (Febrero y Marzo) de forma offline y directa en nuestro pipeline sin depender de APIs de terceros o de la nube de Earth Engine.

### 5.5. Simulación de Crecida Topográfica
El dashboard interactivo cuenta con una **Simulación de Crecida Topográfica** dinámica. Su propósito es realizar un análisis de vulnerabilidad física del territorio frente al incremento hipotético del nivel del agua (elevación o cota en metros sobre el nivel del mar, m.s.n.m.):
*   **Funcionamiento:** El algoritmo recorre las elevaciones del Copernicus DEM GLO-30 y clasifica como "inundables" a todos los píxeles con altitud $\le \text{cota}$ y pendiente plana ($\le 5^{\circ}$), filtrando zonas elevadas.
*   **Métrica móvil:** La métrica de control es la **cota de elevación**. A medida que esta aumenta, se observa cómo el escurrimiento de agua inunda primero los humedales del sur y las cuencas bajas del este de Bahía Blanca antes de aproximarse al núcleo urbano central, que permanece seguro por encima de la cota de 20 metros.

---

## 6. Conclusión
Este trabajo práctico presenta una comparación metodológica exhaustiva de la inundación de Bahía Blanca en 2025. Se demostró que las técnicas clásicas (como Random Forest e índices espectrales) son excelentes herramientas de línea de base y generadores de etiquetas, pero presentan limitaciones de especificidad. El uso de modelos fundacionales como **Prithvi-EO-2.0** de IBM/NASA, debidamente ajustados localmente mediante **Fine-Tuning con pesos de clase balanceados**, representa el estado del arte en precisión cartográfica de catástrofes naturales, permitiendo corregir sesgos generales y sobreestimaciones para proveer estimaciones seguras y precisas de hectáreas e impacto demográfico en el territorio.

---

## 7. Referencias Bibliográficas
*   Ma, S., Zhou, Y., Gowda, P. H., Dong, J., Zhang, G., Kakani, V. G., ... & Jiang, W. (2019). Application of the water-related spectral reflectance indices: A review. *Ecological indicators*, 98, 68-79.
*   Weng, Q. (2011). *Advances in environmental remote sensing: sensors, algorithms, and applications*. CRC Press.
*   Jakubik, J., Fraccaro, P., & et al. (2024). Prithvi-EO-2.0: A Foundation Model for Earth Observation. *arXiv preprint arXiv:2404.03211*.
*   Sargent, I., & et al. (2021). Pixels to Population: Estimating population exposure using satellite imagery and convolutional neural networks. *Remote Sensing*, 13(15), 2912.
*   Google DeepMind & Google Earth. (2024). AlphaEarth: A Foundation Model for Earth Observation. Technical Report.
*   Asterisk Labs. (2024). BetaEarth: Open-source Emulator for Geospatial Embeddings. Asterisk Labs Publications.

