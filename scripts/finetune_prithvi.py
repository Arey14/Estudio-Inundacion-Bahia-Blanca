import os
import sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

# Setup paths and environment
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
PRITHVI_DIR = DATA_DIR / "prithvi"
sys.path.append(str(PRITHVI_DIR))

from terratorch.cli_tools import LightningInferenceModel

class PrithviFinetuningDataset(Dataset):
    def __init__(self, x_path, y_path):
        self.x = np.load(x_path)  # shape (N, 7, 224, 224)
        self.y = np.load(y_path)  # shape (N, 224, 224)
        
    def __len__(self):
        return len(self.x)
        
    def __getitem__(self, idx):
        # Extract Prithvi bands: Blue, Green, Red, Narrow NIR, SWIR1, SWIR2
        # Index in our 7-band stack: B02->2, B03->1, B04->0, B8A->3, B11->6, B12->4
        x_7bands = self.x[idx]
        x_prithvi = x_7bands[[2, 1, 0, 3, 6, 4], :, :]  # shape (6, 224, 224)
        
        # Add temporal dimension -> shape (6, 1, 224, 224)
        x_prithvi = np.expand_dims(x_prithvi, axis=1)
        
        # Class label should be int64 (long) for CrossEntropyLoss
        y = self.y[idx].astype(np.int64)
        
        return torch.tensor(x_prithvi, dtype=torch.float32), torch.tensor(y, dtype=torch.long)

def main():
    print("🚀 Cargando dataset de parches para Prithvi...")
    train_dataset = PrithviFinetuningDataset(
        DATA_DIR / "dataset_finetuning" / "train_x.npy",
        DATA_DIR / "dataset_finetuning" / "train_y.npy"
    )
    val_dataset = PrithviFinetuningDataset(
        DATA_DIR / "dataset_finetuning" / "val_x.npy",
        DATA_DIR / "dataset_finetuning" / "val_y.npy"
    )
    
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False, num_workers=2)
    
    print(f"   ➜ Dataset cargado. {len(train_dataset)} muestras de entrenamiento, {len(val_dataset)} de validación.")
    
    print("🚀 Cargando pesos base de Prithvi...")
    lim = LightningInferenceModel.from_config(
        str(PRITHVI_DIR / "config.yaml"),
        str(PRITHVI_DIR / "Prithvi-EO-V2-300M-TL-Sen1Floods11.pt")
    )
    model = lim.model
    
    # Congelar el backbone (encoder) y el neck para prevenir sobreajuste
    print("   ➜ Congelando el encoder (Vision Transformer) y el neck de Prithvi...")
    for param in model.model.encoder.parameters():
        param.requires_grad = False
    for param in model.model.neck.parameters():
        param.requires_grad = False
        
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    print(f"   ➜ Parámetros entrenables: {len(trainable_params)} / {len(list(model.parameters()))}")
    
    # Calcular pesos de clase para mitigar el fuerte desbalance de clases (tierra vs agua)
    labels = train_dataset.y
    num_pos = np.sum(labels == 1)
    num_neg = np.sum(labels == 0)
    weight_pos = num_neg / num_pos if num_pos > 0 else 1.0
    print(f"   ➜ Desbalance de clases: {num_neg} píxeles de tierra, {num_pos} de agua. Peso asignado al agua: {weight_pos:.2f}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    class_weights = torch.tensor([1.0, weight_pos], dtype=torch.float32).to(device)
    
    optimizer = torch.optim.AdamW(trainable_params, lr=1e-4, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    model.to(device)
    
    best_val_loss = float("inf")
    checkpoint_out_path = PRITHVI_DIR / "Prithvi-EO-V2-300M-Finetuned.pt"
    
    print(f"🚀 Iniciando entrenamiento en {device} por 500 épocas...")
    for epoch in range(500):
        # Modo Entrenamiento
        model.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            
            # Forward pass: model(x) retorna ModelOutput con .output
            out = model(x)
            loss = criterion(out.output, y)
            
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        avg_train_loss = train_loss / len(train_loader)
        
        # Modo Validación (cada 5 épocas o en la última para velocidad)
        if (epoch + 1) % 5 == 0 or epoch == 499:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for x, y in val_loader:
                    x, y = x.to(device), y.to(device)
                    out = model(x)
                    loss = criterion(out.output, y)
                    val_loss += loss.item()
                    
            avg_val_loss = val_loss / len(val_loader)
            print(f"   Época {epoch+1:03d}/500 ➜ Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            
            # Guardar mejor checkpoint
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), checkpoint_out_path)
                print(f"   ➜  Guardado mejor checkpoint (Val Loss: {best_val_loss:.4f})")
        else:
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"   Época {epoch+1:03d}/500 ➜ Train Loss: {avg_train_loss:.4f}")
            
    print(f"🎉 Ajuste Fino completado. Pesos guardados en: {checkpoint_out_path}")

if __name__ == "__main__":
    main()
