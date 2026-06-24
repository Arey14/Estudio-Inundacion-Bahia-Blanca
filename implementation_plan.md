# Plan de Implementación: Fine-Tuning de Modelos de Teledetección (Prithvi & U-Net)

Este plan detalla los pasos para realizar el ajuste fino (fine-tuning) de los modelos **Prithvi-EO-2.0** (IBM/NASA) y **U-Net** para la detección de la inundación de Bahía Blanca (2025), buscando mejorar la precisión local y reducir los falsos positivos.

## User Review Required

> [!IMPORTANT]
> **Estrategia de Etiquetas (Labels) para Entrenamiento**:
> Dado que no disponemos de un mapa de verdad de terreno exhaustivo digitalizado a mano para toda la escena, utilizaremos **pseudo-etiquetas de consenso de alta confianza**:
> - Se combinarán píxeles donde el modelo Random Forest Base, U-Net y un umbral exigente de MNDWI (>0.4) coincidan plenamente.
> - Se aplicarán filtros topográficos estrictos (pendiente y altitud) y la máscara de cuerpos de agua permanentes del IGN para garantizar que solo las áreas temporalmente inundadas sean etiquetadas como positivas.
>
> **Consumo de Memoria de GPU (RTX 3090)**:
> Prithvi-EO-2.0 tiene 300M de parámetros. Haremos fine-tuning utilizando **congelamiento del backbone** (backbone freeze) y entrenando solo el decodificador (UperNetDecoder), lo que consume ~6 GB de VRAM y evita sobreajustes catastróficos.

## Open Questions

> [!NOTE]
> No hay preguntas abiertas de bloqueo. Se asume que el entrenamiento se realizará localmente usando el hardware de GPU disponible (RTX 3090) con los paquetes actualmente instalados en el entorno virtual.

## Proposed Changes

### 1. Preparación del Dataset de Entrenamiento y Validación

#### [NEW] [preparar_dataset_patches.py](file:///home/augusto/Desktop/TP2/scripts/preparar_dataset_patches.py)
*   Crear un script para recortar las imágenes Sentinel-2 de Febrero y Marzo en parches uniformes de `224x224` o `512x512` píxeles (campo receptivo estándar de Prithvi y U-Net).
*   Generar las máscaras de pseudo-etiquetas de consenso.
*   Dividir el conjunto de parches de forma aleatoria y estratificada en un 80% para entrenamiento y 20% para validación.
*   Guardar los parches y sus etiquetas en `data-Sentinel-2/dataset_finetuning/`.

---

### 2. Ajuste Fino (Fine-Tuning) de Modelos

#### [NEW] [finetune_prithvi.py](file:///home/augusto/Desktop/TP2/scripts/finetune_prithvi.py)
*   Script en PyTorch Lightning que cargue la configuración de `data-Sentinel-2/prithvi/config.yaml` y los pesos pre-entrenados de `Prithvi-EO-V2-300M-TL-Sen1Floods11.pt`.
*   Cargar el dataset de parches utilizando un cargador compatible con `terratorch`.
*   Congelar el backbone del transformador para entrenar únicamente el decodificador espacial UperNetDecoder.
*   Configurar un optimizador AdamW con una tasa de aprendizaje baja (`1e-5`) y entrenar por 5-10 épocas en la GPU RTX 3090.
*   Exportar los pesos del modelo ajustado como `data-Sentinel-2/prithvi/Prithvi-EO-V2-300M-Finetuned.pt`.

#### [NEW] [finetune_unet.py](file:///home/augusto/Desktop/TP2/scripts/finetune_unet.py)
*   Script en PyTorch nativo para realizar el ajuste fino de la red U-Net (ResNet34 backbone).
*   Cargar los pesos iniciales (previamente obtenidos de la destilación en `comparar_modelos.py`).
*   Entrenar sobre el dataset de parches usando una función de pérdida combinada de Dice Loss y Binary Cross Entropy (DiceBCE).
*   Guardar el modelo entrenado como `data-Sentinel-2/unet_finetuned.pt`.

---

### 3. Evaluación e Inferencia Comparativa

#### [MODIFY] [comparar_modelos.py](file:///home/augusto/Desktop/TP2/scripts/comparar_modelos.py)
*   Actualizar el script para cargar las versiones ajustadas (Fine-Tuned) de U-Net y Prithvi.
*   Calcular las nuevas métricas (hectáreas inundadas, población afectada e intersección con el DEM).
*   Exportar las nuevas métricas a `data-Sentinel-2/metricas_modelos.json` y `data-Sentinel-2/metricas_modelos.js`.
*   Generar los nuevos gráficos comparativos de barras y las máscaras de superposición correspondientes.

---

### 4. Actualización del Front-End (Streamlit e index.html)

#### [MODIFY] [dashboard.py](file:///home/augusto/Desktop/TP2/scripts/dashboard.py)
*   Actualizar la visualización de la pestaña de comparación de modelos para incluir las versiones originales ("Zero-Shot") y las nuevas versiones ajustadas ("Fine-Tuned"), demostrando el impacto del entrenamiento local.

#### [MODIFY] [index.html](file:///home/augusto/Desktop/TP2/index.html)
*   Actualizar la tabla dinámica y los botones de superposición interactiva de máscaras para reflejar los modelos ajustados y sus respectivas mejoras visuales y estadísticas.

## Verification Plan

### Automated Tests
*   Ejecutar `python scripts/preparar_dataset_patches.py` para verificar que se generen correctamente los parches de imágenes y etiquetas.
*   Ejecutar `python scripts/finetune_prithvi.py` y `python scripts/finetune_unet.py` en modo *fast dev run* (1 paso de entrenamiento) para validar que no haya errores de tamaño de tensores en la GPU.
*   Ejecutar la inferencia final con `python scripts/comparar_modelos.py` para regenerar las métricas integrales.

### Manual Verification
*   Validar en la interfaz de Streamlit que se muestre correctamente la mejora de precisión (por ejemplo, reducción de falsos positivos en zonas de suelos mixtos húmedos) al comparar Prithvi Zero-Shot vs Prithvi Fine-Tuned.
