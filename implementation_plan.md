# Plan de Implementación de Mejoras - TP2 Teledetección

Este documento detalla el plan de acción propuesto para abordar las mejoras sugeridas en el archivo [Mejoras.md](file:///home/augusto/Desktop/TP2/Mejoras.md) para el Trabajo Práctico N° 2 de Sistemas de Información Geográfica.

---

## User Review Required

> [!IMPORTANT]
> **Consumo de recursos en entrenamiento de Embeddings y UNET**:
> El uso de modelos fundacionales de teledetección como **Prithvi-EO-2.0** (300M de parámetros) y la generación de embeddings con **TESSERA** y **BetaEarth** (emulador de **AlphaEarth**) requieren la instalación de librerías de Deep Learning (`torch`, `transformers`, `terratorch`, `betaearth`) y descargas de pesos de modelos (~1.2 GB en total). El procesamiento se ejecutará en la GPU **RTX 3090** local para garantizar máxima velocidad.

---

## Open Questions

> [!IMPORTANT]
> **Pregunta 1: Animación de la crecida de agua**
> Sentinel-2 tiene una frecuencia de revisión de ~5 días y alta vulnerabilidad a nubes. Acordamos implementar una **combinación de ambos enfoques**:
> 1.  **Simulación Interactiva por DEM**: Un slider interactivo en el dashboard para controlar la altura teórica del agua en metros sobre el nivel del mar y ver la inundación progresiva de zonas bajas.
> 2.  **Serie Temporal Real**: Secuencia real animada de las máscaras de inundación clasificadas en las fechas históricas disponibles de febrero y marzo de 2025.

---

## Proposed Changes

A continuación se agrupan los cambios según los componentes del proyecto:

### 1. Actualización de Datos Demográficos

#### [MODIFY] [procesamiento.py](file:///home/augusto/Desktop/TP2/scripts/procesamiento.py)
*   Cambiar la URL de WorldPop 2020 por el dataset optimizado y proyectado para 2025:
    `https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2025/ARG/v1/1km_ua/constrained/arg_pop_2025_CN_1km_R2025A_UA_v1.tif`
*   Actualizar la lógica de lectura y cálculo del impacto de población para adaptarla al nuevo raster.

---

### 2. Análisis por Componentes Principales (PCA)

#### [MODIFY] [procesamiento.py](file:///home/augusto/Desktop/TP2/scripts/procesamiento.py)
*   Agregar un módulo de PCA que reduzca las 7 bandas multiespectrales de Sentinel-2 (+ índices MNDWI y NDWI) a los 2 o 3 componentes principales de mayor varianza explicada.
*   Entrenar modelos Random Forest y K-Means utilizando los componentes principales como características (Features) y comparar el tiempo de ejecución y la exactitud contra el modelo base.
*   Exportar los resultados de los componentes principales para su representación gráfica.

#### [MODIFY] [dashboard.py](file:///home/augusto/Desktop/TP2/scripts/dashboard.py)
*   Añadir una sección interactiva de **Análisis PCA** en el dashboard, incluyendo:
    *   Gráfico de varianza explicada acumulada.
    *   Diagrama de dispersión 2D (PC1 vs PC2) de una muestra de píxeles, coloreados según la clasificación de agua/tierra, para demostrar la separabilidad espectral de las clases.

---

### 3. Animación de Inundación

#### [MODIFY] [dashboard.py](file:///home/augusto/Desktop/TP2/scripts/dashboard.py)
*   **Simulador de Inundación (DEM)**: Crear una pestaña interactiva que utilice el DEM de Copernicus. Mediante un slider de Streamlit (ej. de 0 a 30 metros de elevación), se filtrará dinámicamente el terreno con pendiente baja, mostrando en tiempo real la progresión del anegamiento en el mapa interactivo de Bahía Blanca.
*   **Control de Autoplay**: Agregar un botón de animación automática (Play/Pause) que incremente el nivel del agua secuencialmente para generar el efecto visual de "crecida".
*   **Visor de la Serie Temporal Real**: Integrar una línea de tiempo (o reproductor GIF) que muestre la evolución real de la mancha de inundación obtenida de las imágenes Sentinel-2 capturadas en febrero y marzo de 2025.

---

### 4. Modelos Avanzados de Deep Learning y Embeddings

#### [NEW] [Modelos_Avanzados_Embeddings.ipynb](file:///home/augusto/Desktop/TP2/notebooks/Modelos_Avanzados_Embeddings.ipynb)
Crear un cuaderno Jupyter especializado para la evaluación de arquitecturas de Deep Learning:
*   **Pipeline TESSERA (Cambridge)**:
    *   Uso de embeddings temporales de reflectancia espectral.
    *   Alineación de embeddings al AOI y entrenamiento de un clasificador ligero (Random Forest / MLP) sobre el espacio latente.
*   **Pipeline AlphaEarth / BetaEarth (Emulación local)**:
    *   Instalar `betaearth` en el entorno virtual.
    *   Ejecutar el modelo emulador sobre nuestras imágenes para generar embeddings geoespaciales de 64 dimensiones (idénticos en estructura a los de AlphaEarth de Google DeepMind).
    *   Entrenar un clasificador Random Forest sobre estos embeddings y comparar su capacidad de segmentación.
*   **Pipeline Prithvi (IBM-NASA)**:
    *   Descarga e inicialización de `Prithvi-EO-2.0-300M-TL-Sen1Floods11` desde Hugging Face.
    *   Adaptación de las bandas espectrales de Sentinel-2 al orden y normalización esperados por Prithvi.
    *   Inferencia zero-shot/fine-tuning en el área de Bahía Blanca.
*   **Comparación contra UNET**:
    *   Implementación de una red U-Net sencilla en PyTorch.
    *   Entrenamiento supervisado utilizando como etiquetas (labels) la máscara refinada del modelo Random Forest actual (aprendizaje por destilación).
*   **Métricas Comparativas**:
    *   Generar una tabla y gráficos comparativos de las máscaras de inundación estimadas por: *Random Forest (bandas), RF (PCA), RF (TESSERA), RF (AlphaEarth/BetaEarth), Prithvi-EO-2.0* y *U-Net*.

---

## Verification Plan

### Automated Tests
*   Ejecución local de `python scripts/procesamiento.py` para asegurar que el pipeline con PCA y WorldPop 2025 finaliza sin errores.
*   Verificación de la carga del modelo Prithvi e inferencia en PyTorch dentro de un script de prueba.

### Manual Verification
*   Validación visual de la animación y del gráfico PCA interactivo en la aplicación web de Streamlit ejecutando:
    ```bash
    .venv/bin/streamlit run scripts/dashboard.py
    ```
