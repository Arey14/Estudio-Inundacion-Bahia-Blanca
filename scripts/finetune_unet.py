import os
import sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp
from pathlib import Path

# Setup paths
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"

class UnetFinetuningDataset(Dataset):
    def __init__(self, x_path, y_path):
        self.x = np.load(x_path)  # shape (N, 7, 224, 224)
        self.y = np.load(y_path)  # shape (N, 224, 224)
        
    def __len__(self):
        return len(self.x)
        
    def __getitem__(self, idx):
        x = self.x[idx]  # shape (7, 224, 224)
        y = self.y[idx][np.newaxis, :, :]  # shape (1, 224, 224)
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def main():
    print("🚀 Cargando dataset de parches para U-Net...")
    train_dataset = UnetFinetuningDataset(
        DATA_DIR / "dataset_finetuning" / "train_x.npy",
        DATA_DIR / "dataset_finetuning" / "train_y.npy"
    )
    val_dataset = UnetFinetuningDataset(
        DATA_DIR / "dataset_finetuning" / "val_x.npy",
        DATA_DIR / "dataset_finetuning" / "val_y.npy"
    )
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=2)
    
    print(f"   ➜ Dataset cargado. {len(train_dataset)} muestras de entrenamiento, {len(val_dataset)} de validación.")
    
    print("🚀 Inicializando modelo U-Net (ResNet34 backbone)...")
    unet = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=7,
        classes=1
    )
    
    # Pérdida combinada Dice + BCE para segmentaciones más limpias
    dice_loss = smp.losses.DiceLoss(mode="binary", from_logits=True)
    bce_loss = nn.BCEWithLogitsLoss()
    
    optimizer = torch.optim.AdamW(unet.parameters(), lr=1e-3, weight_decay=1e-4)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    unet.to(device)
    
    best_val_loss = float("inf")
    checkpoint_out_path = DATA_DIR / "unet_finetuned.pt"
    
    print(f"🚀 Iniciando entrenamiento de U-Net en {device} por 10 épocas...")
    for epoch in range(10):
        # Entrenamiento
        unet.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            
            out = unet(x)
            loss = dice_loss(out, y) + bce_loss(out, y)
            
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        avg_train_loss = train_loss / len(train_loader)
        
        # Validación
        unet.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = unet(x)
                loss = dice_loss(out, y) + bce_loss(out, y)
                val_loss += loss.item()
                
        avg_val_loss = val_loss / len(val_loader)
        print(f"   Época {epoch+1:02d}/10 ➜ Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
        # Guardar el mejor modelo
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(unet.state_dict(), checkpoint_out_path)
            print(f"   ➜  Guardado mejor checkpoint U-Net (Val Loss: {best_val_loss:.4f})")
            
    print(f"🎉 Entrenamiento U-Net completado. Pesos guardados en: {checkpoint_out_path}")

if __name__ == "__main__":
    main()
