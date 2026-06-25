#!/bin/bash
PID=43771

echo "⏳ Esperando a que finalice el proceso de Prithvi (PID: $PID)..."
while kill -0 $PID 2>/dev/null; do
    sleep 10
done

echo "🚀 Proceso de Prithvi terminado. Iniciando entrenamiento de U-Net (500 épocas)..."
.venv/bin/python scripts/finetune_unet.py

echo "🚀 Entrenamiento de U-Net terminado. Ejecutando comparación de modelos..."
.venv/bin/python scripts/comparar_modelos.py

echo "✔️ Todo el pipeline de fine-tuning y comparación ha finalizado con éxito!"
