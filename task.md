# Checklist de Implementación: Fine-Tuning de Modelos

- `[x]` Preparar el dataset de entrenamiento y validación (`scripts/preparar_dataset_patches.py`)
- `[x]` Desarrollar el script de fine-tuning de Prithvi (`scripts/finetune_prithvi.py`)
- `[x]` Desarrollar el script de fine-tuning de U-Net (`scripts/finetune_unet.py`)
- `[x]` Ejecutar el entrenamiento de ambos modelos en la GPU RTX 3090
- `[x]` Modificar `scripts/comparar_modelos.py` para cargar los modelos ajustados y calcular métricas
- `[x]` Actualizar el front-end del Dashboard de Streamlit (`scripts/dashboard.py`)
- `[x]` Actualizar el front-end de la página web estática (`index.html`)
