import os
import sys
import json
import numpy as np
import rasterio
import geopandas as gpd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp
import matplotlib.pyplot as plt

# Agregar rutas para poder importar de prithvi e indexar
sys.path.append(str(Path("/home/augusto/Desktop/TP2/scripts")))
sys.path.append(str(Path("/home/augusto/Desktop/TP2/data-Sentinel-2/prithvi")))

# Configuración de Rutas
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
IMG_DIR = BASE_DIR / "img"
IMG_FEB = DATA_DIR / "AOI_20250219_20m_clip.tif"
IMG_MAR = DATA_DIR / "AOI_20250311_20m_clip.tif"
DEM_PATH = DATA_DIR / "dem_clip.tif"
POP_PATH = DATA_DIR / "worldpop_clip.tif"
IGN_PATH = DATA_DIR / "ign_hydrology.geojson"

# Asegurar directorios
IMG_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# 1. Funciones de Lectura y Preprocesamiento
# ----------------------------------------------------------------------

def read_sentinel_image(img_path):
    """Lee las 7 bandas de la imagen recortada de Sentinel-2."""
    band_names = ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']
    bands = {}
    with rasterio.open(img_path) as src:
        for idx, name in enumerate(band_names, start=1):
            bands[name] = src.read(idx)
    return bands

def calculate_indices(bands):
    """Calcula NDWI y MNDWI."""
    green = bands['B03'].astype(np.float32)
    nir = bands['B08'].astype(np.float32)
    ndwi = np.where((green + nir) == 0, 0, (green - nir) / (green + nir))
    
    swir1 = bands['B11'].astype(np.float32)
    mndwi = np.where((green + swir1) == 0, 0, (green - swir1) / (green + swir1))
    return ndwi, mndwi

def calculate_slope(dem):
    """Calcula la pendiente en grados."""
    dy, dx = np.gradient(dem, 20.0)
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180.0 / np.pi)
    return slope

def apply_topographic_filter(water_mask, dem_path):
    """Filtra la máscara eliminando zonas elevadas o con alta pendiente."""
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
    slope = calculate_slope(dem)
    topo_mask = (dem <= 45) & (slope <= 5) & (dem > -9000)
    return water_mask & topo_mask

def get_ign_water_mask(img_shape, ref_crs, ref_transform):
    """Genera la máscara de agua permanente basada en el IGN."""
    ign_water_mask = np.zeros(img_shape, dtype=bool)
    if IGN_PATH.exists():
        try:
            from rasterio.mask import mask
            ign_gdf = gpd.read_file(IGN_PATH)
            ign_areas = ign_gdf[ign_gdf['layer'] == 'ign:areas_de_aguas_continentales_perenne']
            if len(ign_areas) > 0:
                # Usar una imagen Sentinel como referencia de perfil
                with rasterio.open(IMG_FEB) as src:
                    ign_areas_proj = ign_areas.to_crs(src.crs)
                    ign_water_mask_raw, _ = mask(src, ign_areas_proj.geometry, invert=False, filled=True)
                    ign_water_mask = (ign_water_mask_raw[0] > 0)
        except Exception as e:
            print(f"⚠️ Error al rasterizar hidrología IGN: {e}")
    return ign_water_mask

# ----------------------------------------------------------------------
# 2. Dataset y Entrenamiento de Modelos
# ----------------------------------------------------------------------

# Dataset para U-Net
class SentinelTileDataset(Dataset):
    def __init__(self, tiles_x, tiles_y):
        self.tiles_x = tiles_x
        self.tiles_y = tiles_y
        
    def __len__(self):
        return len(self.tiles_x)
        
    def __getitem__(self, idx):
        x = torch.tensor(self.tiles_x[idx], dtype=torch.float32)
        y = torch.tensor(self.tiles_y[idx], dtype=torch.float32)
        return x, y

def extract_tiles(image_arr, mask_arr, tile_size=256):
    C, H, W = image_arr.shape
    tiles_x = []
    tiles_y = []
    for r in range(0, H - tile_size + 1, tile_size):
        for c in range(0, W - tile_size + 1, tile_size):
            tile_x = image_arr[:, r:r+tile_size, c:c+tile_size]
            tile_y = mask_arr[r:r+tile_size, c:c+tile_size]
            # Omitir si la mayoría es no data
            if np.mean(tile_x == 0) > 0.4:
                continue
            tiles_x.append(tile_x / 10000.0)  # Normalización básica
            tiles_y.append(tile_y[np.newaxis, :, :])
    return np.array(tiles_x), np.array(tiles_y)

def get_training_samples(bands_mar, ndwi_mar, mndwi_mar):
    """Extrae muestras balanceadas para entrenar los clasificadores clásicos."""
    water_mask = (mndwi_mar > 0.35) & (ndwi_mar > 0.2)
    land_mask = (mndwi_mar < -0.1) & (ndwi_mar < 0.0)
    
    water_indices = np.where(water_mask.ravel())[0]
    land_indices = np.where(land_mask.ravel())[0]
    
    n_samples = min(len(water_indices), len(land_indices), 8000)
    np.random.seed(42)
    train_water_idx = np.random.choice(water_indices, n_samples, replace=False)
    train_land_idx = np.random.choice(land_indices, n_samples, replace=False)
    
    return train_water_idx, train_land_idx, n_samples

# ----------------------------------------------------------------------
# 3. Flujo Principal de Ejecución
# ----------------------------------------------------------------------

def main():
    print("🔮 Leyendo imágenes Sentinel-2 de Febrero y Marzo...")
    bands_feb = read_sentinel_image(IMG_FEB)
    bands_mar = read_sentinel_image(IMG_MAR)
    
    ndwi_feb, mndwi_feb = calculate_indices(bands_feb)
    ndwi_mar, mndwi_mar = calculate_indices(bands_mar)
    
    H, W = ndwi_mar.shape
    pixel_area_ha = 0.04  # 20x20m / 10000
    
    # Cargar dem y poblacion
    with rasterio.open(POP_PATH) as src:
        pop_density = src.read(1)
        pop_density = np.where(pop_density < 0, 0, pop_density)
        
    with rasterio.open(IMG_FEB) as src:
        ref_crs = src.crs
        ref_transform = src.transform
        
    ign_water_mask = get_ign_water_mask((H, W), ref_crs, ref_transform)
    
    # Obtener muestras de entrenamiento balanceadas sobre la imagen de Marzo
    train_water_idx, train_land_idx, n_samples = get_training_samples(bands_mar, ndwi_mar, mndwi_mar)
    
    # Preparar matriz de características (7 bandas)
    features_feb_7 = np.stack([bands_feb[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=1)
    features_mar_7 = np.stack([bands_mar[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=1)
    
    # Muestras para RF Base (7 bandas + ndwi + mndwi)
    X_all_feb_base = np.hstack([features_feb_7, ndwi_feb.ravel()[:, np.newaxis], mndwi_feb.ravel()[:, np.newaxis]])
    X_all_mar_base = np.hstack([features_mar_7, ndwi_mar.ravel()[:, np.newaxis], mndwi_mar.ravel()[:, np.newaxis]])
    
    X_train_base = np.vstack([X_all_mar_base[train_water_idx], X_all_mar_base[train_land_idx]])
    y_train = np.hstack([np.ones(n_samples), np.zeros(n_samples)])
    
    results = {}
    
    # ------------------------------------------------------------------
    # MODELO 1: Random Forest Base (9 features)
    # ------------------------------------------------------------------
    print("\n🟢 Model 1: Random Forest Base (Bandas + Índices)...")
    rf_base = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf_base.fit(X_train_base, y_train)
    water_feb_rf = rf_base.predict(X_all_feb_base).reshape(H, W)
    water_mar_rf = rf_base.predict(X_all_mar_base).reshape(H, W)
    
    # Inundación final
    inund_rf = (water_mar_rf > 0) & ~(water_feb_rf > 0)
    inund_rf = apply_topographic_filter(inund_rf, DEM_PATH)
    inund_rf = inund_rf & (~ign_water_mask)
    
    pix_rf = int(np.sum(inund_rf))
    ha_rf = float(pix_rf * pixel_area_ha)
    pop_rf = int(np.sum(pop_density[inund_rf]) * 0.0004)
    results["rf_base"] = {"nombre": "Random Forest (Base)", "hectareas": round(ha_rf, 2), "poblacion": pop_rf, "pixeles": pix_rf}
    print(f"   ➜ Hectáreas: {ha_rf:.2f} ha, Población afectada: {pop_rf}")
    
    # Guardar máscara RF
    with rasterio.open(IMG_MAR) as src:
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.uint8, nodata=0, compress='DEFLATE')
        with rasterio.open(DATA_DIR / "inundacion_rf_base.tif", "w", **profile) as dst:
            dst.write(inund_rf.astype(np.uint8), 1)

    # ------------------------------------------------------------------
    # MODELO 2: Random Forest con PCA (3 componentes)
    # ------------------------------------------------------------------
    print("\n🟢 Model 2: Random Forest con PCA (3 Componentes)...")
    # Escalar datos usando el mismo fit de Marzo para ambas fechas (evitar domain shift)
    scaler = StandardScaler()
    X_scaled_mar = scaler.fit_transform(features_mar_7)
    X_scaled_feb = scaler.transform(features_feb_7)
    
    # Ajustar PCA sobre Marzo y proyectar ambas fechas
    pca = PCA(n_components=3, random_state=42)
    X_pca_mar = pca.fit_transform(X_scaled_mar)
    X_pca_feb = pca.transform(X_scaled_feb)
    
    print(f"   ➜ Varianza explicada acumulada (3 componentes): {np.sum(pca.explained_variance_ratio_)*100:.2f}%")
    
    # Entrenar RF en PCA
    X_train_pca = np.vstack([X_pca_mar[train_water_idx], X_pca_mar[train_land_idx]])
    rf_pca = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf_pca.fit(X_train_pca, y_train)
    
    water_feb_pca = rf_pca.predict(X_pca_feb).reshape(H, W)
    water_mar_pca = rf_pca.predict(X_pca_mar).reshape(H, W)
    
    inund_pca = (water_mar_pca > 0) & ~(water_feb_pca > 0)
    inund_pca = apply_topographic_filter(inund_pca, DEM_PATH)
    inund_pca = inund_pca & (~ign_water_mask)
    
    pix_pca = int(np.sum(inund_pca))
    ha_pca = float(pix_pca * pixel_area_ha)
    pop_pca = int(np.sum(pop_density[inund_pca]) * 0.0004)
    results["rf_pca"] = {"nombre": "Random Forest (3 PCA)", "hectareas": round(ha_pca, 2), "poblacion": pop_pca, "pixeles": pix_pca}
    print(f"   ➜ Hectáreas: {ha_pca:.2f} ha, Población afectada: {pop_pca}")
    
    # Guardar máscara PCA
    with rasterio.open(DATA_DIR / "inundacion_rf_pca.tif", "w", **profile) as dst:
        dst.write(inund_pca.astype(np.uint8), 1)

    # ------------------------------------------------------------------
    # MODELO 3: Random Forest con BetaEarth (64D embeddings)
    # ------------------------------------------------------------------
    print("\n🟢 Model 3: Random Forest con Embeddings BetaEarth...")
    
    def generate_betaearth_embeddings(bands, doy):
        # Reconstruir las bandas Red Edge ausentes interpolando linealmente entre Red y NIR
        # B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B05, B06, B07 (Red Edge), B11 (SWIR1), B12 (SWIR2)
        b02 = bands['B02']
        b03 = bands['B03']
        b04 = bands['B04']
        b08 = bands['B08']
        b11 = bands['B11']
        b12 = bands['B12']
        
        # Interpolaciones lineales
        b05 = (0.75 * b04 + 0.25 * b08).astype(np.uint16)
        b06 = (0.50 * b04 + 0.50 * b08).astype(np.uint16)
        b07 = (0.25 * b04 + 0.75 * b08).astype(np.uint16)
        
        # Band order para BetaEarth: [B02, B03, B04, B08, B05, B06, B07, B11, B12]
        s2_input = np.stack([b02, b03, b04, b08, b05, b06, b07, b11, b12], axis=0)
        
        print("   ➜ Extrayendo embeddings de 64 dimensiones...")
        from betaearth import BetaEarth
        be_model = BetaEarth.from_pretrained(device="cuda")
        emb = be_model.predict(s2_l2a=s2_input, doy=doy, tile_size=224, overlap=32)
        return emb
        
    print("   ➜ Procesando Marzo (evento)...")
    emb_mar = generate_betaearth_embeddings(bands_mar, doy=70) # Mar 11 ~ Day 70
    print("   ➜ Procesando Febrero (pre-evento)...")
    emb_feb = generate_betaearth_embeddings(bands_feb, doy=50) # Feb 19 ~ Day 50
    
    # Entrenar clasificador RF en los embeddings de 64D
    emb_mar_flat = emb_mar.reshape(-1, 64)
    emb_feb_flat = emb_feb.reshape(-1, 64)
    
    X_train_emb = np.vstack([emb_mar_flat[train_water_idx], emb_mar_flat[train_land_idx]])
    rf_emb = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf_emb.fit(X_train_emb, y_train)
    
    water_feb_emb = rf_emb.predict(emb_feb_flat).reshape(H, W)
    water_mar_emb = rf_emb.predict(emb_mar_flat).reshape(H, W)
    
    inund_emb = (water_mar_emb > 0) & ~(water_feb_emb > 0)
    inund_emb = apply_topographic_filter(inund_emb, DEM_PATH)
    inund_emb = inund_emb & (~ign_water_mask)
    
    pix_emb = int(np.sum(inund_emb))
    ha_emb = float(pix_emb * pixel_area_ha)
    pop_emb = int(np.sum(pop_density[inund_emb]) * 0.0004)
    results["rf_betaearth"] = {"nombre": "Random Forest (BetaEarth)", "hectareas": round(ha_emb, 2), "poblacion": pop_emb, "pixeles": pix_emb}
    print(f"   ➜ Hectáreas: {ha_emb:.2f} ha, Población afectada: {pop_emb}")
    
    # Guardar máscara BetaEarth
    with rasterio.open(DATA_DIR / "inundacion_rf_betaearth.tif", "w", **profile) as dst:
        dst.write(inund_emb.astype(np.uint8), 1)

    # ------------------------------------------------------------------
    # MODELO 4: U-Net entrenado con PyTorch (Destilación)
    # ------------------------------------------------------------------
    print("\n🟢 Model 4: U-Net en PyTorch (Destilación)...")
    
    # Armar stack de bandas (7 canales)
    img_stack_mar = np.stack([bands_mar[b] for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=0)
    img_stack_feb = np.stack([bands_feb[b] for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=0)
    
    # Extraer tiles de 256x256
    tiles_x, tiles_y = extract_tiles(img_stack_mar, water_mar_rf.astype(np.uint8), tile_size=256)
    
    print(f"   ➜ Cantidad de tiles para entrenamiento: {len(tiles_x)}")
    dataset = SentinelTileDataset(tiles_x, tiles_y)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    # Definir U-Net con ResNet34
    unet = smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=7, classes=1).to("cuda")
    optimizer = torch.optim.AdamW(unet.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()
    
    print("   ➜ Entrenando U-Net por 6 épocas...")
    unet.train()
    for epoch in range(6):
        epoch_loss = 0
        for x, y in dataloader:
            x, y = x.to("cuda"), y.to("cuda")
            optimizer.zero_grad()
            out = unet(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        print(f"     Época {epoch+1}/6 - Loss: {epoch_loss/len(dataloader):.4f}")
        
    # Inferencia con U-Net
    unet.eval()
    
    def unet_predict(img):
        # Pad a múltiplos de 32
        _, h_orig, w_orig = img.shape
        pad_h = (32 - (h_orig % 32)) % 32
        pad_w = (32 - (w_orig % 32)) % 32
        img_padded = np.pad(img, ((0,0), (0, pad_h), (0, pad_w)), mode='reflect')
        
        # Pasar a tensor
        x_tensor = torch.tensor(img_padded / 10000.0, dtype=torch.float32).unsqueeze(0).to("cuda")
        x_tensor = torch.clip(x_tensor, 0.0, 1.0)
        with torch.no_grad():
            out = unet(x_tensor)
            pred = torch.sigmoid(out).squeeze().cpu().numpy()
        return (pred[:h_orig, :w_orig] > 0.5).astype(np.uint8)
        
    print("   ➜ Prediciendo con U-Net...")
    water_feb_unet = unet_predict(img_stack_feb)
    water_mar_unet = unet_predict(img_stack_mar)
    
    inund_unet = (water_mar_unet > 0) & ~(water_feb_unet > 0)
    inund_unet = apply_topographic_filter(inund_unet, DEM_PATH)
    inund_unet = inund_unet & (~ign_water_mask)
    
    pix_unet = int(np.sum(inund_unet))
    ha_unet = float(pix_unet * pixel_area_ha)
    pop_unet = int(np.sum(pop_density[inund_unet]) * 0.0004)
    results["unet"] = {"nombre": "U-Net (Distilación)", "hectareas": round(ha_unet, 2), "poblacion": pop_unet, "pixeles": pix_unet}
    print(f"   ➜ Hectáreas: {ha_unet:.2f} ha, Población afectada: {pop_unet}")
    
    # Guardar máscara U-Net
    with rasterio.open(DATA_DIR / "inundacion_unet.tif", "w", **profile) as dst:
        dst.write(inund_unet.astype(np.uint8), 1)

    # ------------------------------------------------------------------
    # MODELO 4B: U-Net en PyTorch (Ajuste Fino)
    # ------------------------------------------------------------------
    print("\n🟢 Model 4B: U-Net en PyTorch (Ajuste Fino)...")
    try:
        unet_ft = smp.Unet(encoder_name="resnet34", encoder_weights=None, in_channels=7, classes=1).to("cuda")
        unet_ft.load_state_dict(torch.load(DATA_DIR / "unet_finetuned.pt"))
        unet_ft.eval()
        
        def unet_ft_predict(img):
            _, h_orig, w_orig = img.shape
            pad_h = (32 - (h_orig % 32)) % 32
            pad_w = (32 - (w_orig % 32)) % 32
            img_padded = np.pad(img, ((0,0), (0, pad_h), (0, pad_w)), mode='reflect')
            x_tensor = torch.tensor(img_padded / 10000.0, dtype=torch.float32).unsqueeze(0).to("cuda")
            x_tensor = torch.clip(x_tensor, 0.0, 1.0)
            with torch.no_grad():
                out = unet_ft(x_tensor)
                pred = torch.sigmoid(out).squeeze().cpu().numpy()
            return (pred[:h_orig, :w_orig] > 0.5).astype(np.uint8)
            
        print("   ➜ Prediciendo con U-Net Ajustada...")
        water_feb_unet_ft = unet_ft_predict(img_stack_feb)
        water_mar_unet_ft = unet_ft_predict(img_stack_mar)
        
        inund_unet_ft = (water_mar_unet_ft > 0) & ~(water_feb_unet_ft > 0)
        inund_unet_ft = apply_topographic_filter(inund_unet_ft, DEM_PATH)
        inund_unet_ft = inund_unet_ft & (~ign_water_mask)
        
        pix_unet_ft = int(np.sum(inund_unet_ft))
        ha_unet_ft = float(pix_unet_ft * pixel_area_ha)
        pop_unet_ft = int(np.sum(pop_density[inund_unet_ft]) * 0.0004)
        results["unet_finetuned"] = {"nombre": "U-Net (Ajuste Fino)", "hectareas": round(ha_unet_ft, 2), "poblacion": pop_unet_ft, "pixeles": pix_unet_ft}
        print(f"   ➜ Hectáreas: {ha_unet_ft:.2f} ha, Población afectada: {pop_unet_ft}")
        
        with rasterio.open(DATA_DIR / "inundacion_unet_finetuned.tif", "w", **profile) as dst:
            dst.write(inund_unet_ft.astype(np.uint8), 1)
    except Exception as e:
        print(f"⚠️ Error al ejecutar U-Net Ajustada: {e}")
        results["unet_finetuned"] = {"nombre": "U-Net (Ajuste Fino)", "hectareas": 0.0, "poblacion": 0, "pixeles": 0}

    # ------------------------------------------------------------------
    # MODELO 5: Prithvi-EO-2.0-300M (Zero-Shot)
    # ------------------------------------------------------------------
    print("\n🟢 Model 5: Prithvi-EO-2.0-300M...")
    try:
        from inference import LightningInferenceModel, run_model
        
        print("   ➜ Cargando LightningInferenceModel...")
        lightning_model = LightningInferenceModel.from_config(
            str(DATA_DIR / "prithvi" / "config.yaml"),
            str(DATA_DIR / "prithvi" / "Prithvi-EO-V2-300M-TL-Sen1Floods11.pt")
        )
        lightning_model.model.eval()
        
        def run_prithvi(bands, doy):
            # Select Blue, Green, Red, Narrow NIR, SWIR1, SWIR2
            prithvi_bands = [bands['B02'], bands['B03'], bands['B04'], bands['B8A'], bands['B11'], bands['B12']]
            input_arr = np.stack(prithvi_bands, axis=0).astype(np.float32) / 10000.0
            input_data = np.expand_dims(input_arr, axis=(0, 2))  # shape (1, 6, 1, H, W)
            
            pred = run_model(
                input_data=input_data,
                temporal_coords=[[2025, doy]],
                location_coords=None,
                model=lightning_model.model,
                datamodule=lightning_model.datamodule,
                img_size=512
            )
            # pred es de tipo torch.Tensor de forma (1, H, W). Se aplica squeeze para que sea 2D.
            return (pred.squeeze().numpy() > 0).astype(np.uint8)
            
        print("   ➜ Prediciendo con Prithvi (Marzo)...")
        water_mar_prithvi = run_prithvi(bands_mar, doy=70)
        print("   ➜ Prediciendo con Prithvi (Febrero)...")
        water_feb_prithvi = run_prithvi(bands_feb, doy=50)
        
        inund_prithvi = (water_mar_prithvi > 0) & ~(water_feb_prithvi > 0)
        inund_prithvi = apply_topographic_filter(inund_prithvi, DEM_PATH)
        inund_prithvi = inund_prithvi & (~ign_water_mask)
        
        pix_prithvi = int(np.sum(inund_prithvi))
        ha_prithvi = float(pix_prithvi * pixel_area_ha)
        pop_prithvi = int(np.sum(pop_density[inund_prithvi]) * 0.0004)
        results["prithvi"] = {"nombre": "Prithvi-EO-2.0", "hectareas": round(ha_prithvi, 2), "poblacion": pop_prithvi, "pixeles": pix_prithvi}
        print(f"   ➜ Hectáreas: {ha_prithvi:.2f} ha, Población afectada: {pop_prithvi}")
        
        # Guardar máscara Prithvi
        with rasterio.open(DATA_DIR / "inundacion_prithvi.tif", "w", **profile) as dst:
            dst.write(inund_prithvi.astype(np.uint8), 1)
            
        # ------------------------------------------------------------------
        # MODELO 5B: Prithvi-EO-2.0-300M (Ajuste Fino)
        # ------------------------------------------------------------------
        print("\n🟢 Model 5B: Prithvi-EO-2.0-300M (Ajuste Fino)...")
        try:
            print("   ➜ Cargando modelo Prithvi Ajustado...")
            lightning_model_ft = LightningInferenceModel.from_config(
                str(DATA_DIR / "prithvi" / "config.yaml"),
                str(DATA_DIR / "prithvi" / "Prithvi-EO-V2-300M-TL-Sen1Floods11.pt")
            )
            lightning_model_ft.model.load_state_dict(torch.load(DATA_DIR / "prithvi" / "Prithvi-EO-V2-300M-Finetuned.pt"))
            lightning_model_ft.model.eval()
            
            def run_prithvi_ft(bands, doy):
                prithvi_bands = [bands['B02'], bands['B03'], bands['B04'], bands['B8A'], bands['B11'], bands['B12']]
                input_arr = np.stack(prithvi_bands, axis=0).astype(np.float32) / 10000.0
                input_data = np.expand_dims(input_arr, axis=(0, 2))  # shape (1, 6, 1, H, W)
                
                pred = run_model(
                    input_data=input_data,
                    temporal_coords=[[2025, doy]],
                    location_coords=None,
                    model=lightning_model_ft.model,
                    datamodule=lightning_model_ft.datamodule,
                    img_size=512
                )
                return (pred.squeeze().numpy() > 0).astype(np.uint8)
                
            print("   ➜ Prediciendo con Prithvi Ajustada (Marzo)...")
            water_mar_prithvi_ft = run_prithvi_ft(bands_mar, doy=70)
            print("   ➜ Prediciendo con Prithvi Ajustada (Febrero)...")
            water_feb_prithvi_ft = run_prithvi_ft(bands_feb, doy=50)
            
            inund_prithvi_ft = (water_mar_prithvi_ft > 0) & ~(water_feb_prithvi_ft > 0)
            inund_prithvi_ft = apply_topographic_filter(inund_prithvi_ft, DEM_PATH)
            inund_prithvi_ft = inund_prithvi_ft & (~ign_water_mask)
            
            pix_prithvi_ft = int(np.sum(inund_prithvi_ft))
            ha_prithvi_ft = float(pix_prithvi_ft * pixel_area_ha)
            pop_prithvi_ft = int(np.sum(pop_density[inund_prithvi_ft]) * 0.0004)
            results["prithvi_finetuned"] = {"nombre": "Prithvi (Ajuste Fino)", "hectareas": round(ha_prithvi_ft, 2), "poblacion": pop_prithvi_ft, "pixeles": pix_prithvi_ft}
            print(f"   ➜ Hectáreas: {ha_prithvi_ft:.2f} ha, Población afectada: {pop_prithvi_ft}")
            
            with rasterio.open(DATA_DIR / "inundacion_prithvi_finetuned.tif", "w", **profile) as dst:
                dst.write(inund_prithvi_ft.astype(np.uint8), 1)
        except Exception as e_ft:
            print(f"⚠️ Error al ejecutar Prithvi Ajustada: {e_ft}")
            results["prithvi_finetuned"] = {"nombre": "Prithvi (Ajuste Fino)", "hectareas": 0.0, "poblacion": 0, "pixeles": 0}
            
    except Exception as e:
        print(f"⚠️ Error al ejecutar Prithvi: {e}")
        # Fallback en caso de error
        results["prithvi"] = {"nombre": "Prithvi-EO-2.0", "hectareas": 0.0, "poblacion": 0, "pixeles": 0}
        results["prithvi_finetuned"] = {"nombre": "Prithvi (Ajuste Fino)", "hectareas": 0.0, "poblacion": 0, "pixeles": 0}

    # ------------------------------------------------------------------
    # 4. Guardar Métricas e Gráficas Comparativas
    # ------------------------------------------------------------------
    print("\n📊 Guardando métricas comparativas consolidadas...")
    with open(DATA_DIR / "metricas_modelos.json", "w") as f:
        json.dump(results, f, indent=2)
        
    # Guardar métricas en formato JS para evitar CORS en index.html
    with open(DATA_DIR / "metricas_modelos.js", "w") as f:
        f.write(f"window.metricasModelos = {json.dumps(results, indent=2)};\n")
        
    print("🎨 Generando gráfica comparativa...")
    model_names = [results[k]["nombre"] for k in results]
    hectareas = [results[k]["hectareas"] for k in results]
    poblaciones = [results[k]["poblacion"] for k in results]
    
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=150)
    
    color = '#1E3A8A'
    ax1.set_xlabel('Modelos de Clasificación', fontweight='bold', labelpad=15)
    ax1.set_ylabel('Hectáreas Inundadas (ha)', color=color, fontweight='bold')
    bars1 = ax1.bar(np.arange(len(model_names)) - 0.2, hectareas, width=0.4, color=color, label='Hectáreas')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Crear segundo eje para población
    ax2 = ax1.twinx()
    color = '#EF4444'
    ax2.set_ylabel('Población Afectada (personas)', color=color, fontweight='bold')
    bars2 = ax2.bar(np.arange(len(model_names)) + 0.2, poblaciones, width=0.4, color=color, label='Población')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.xticks(np.arange(len(model_names)), model_names, rotation=15, ha='right')
    ax1.set_xticklabels(model_names)
    
    plt.title('Comparación Cuantitativa de Modelos y Embeddings', fontweight='bold', fontsize=14, pad=20)
    fig.tight_layout()
    plt.savefig(IMG_DIR / "comparacion_metricas_modelos.png", bbox_inches='tight')
    plt.close()
    
    # ------------------------------------------------------------------
    # 5. Generar Superposición Comparativa
    # ------------------------------------------------------------------
    print("🎨 Generando composiciones visuales individuales para el visualizador...")
    # Cargar fondo en falso color
    with rasterio.open(IMG_MAR) as src:
        swir = src.read(5)
        nir = src.read(6)
        green = src.read(2)
        
        # percentile stretch
        def stretch(band):
            valid = (band > 0)
            low = np.percentile(band[valid], 2)
            high = np.percentile(band[valid], 98)
            return np.clip((band - low) / (high - low), 0, 1)
            
        rgb = np.stack([stretch(swir), stretch(nir), stretch(green)], axis=2)
        
    masks = {
        "rf_base": inund_rf,
        "rf_pca": inund_pca,
        "rf_betaearth": inund_emb,
        "unet": inund_unet,
        "unet_finetuned": inund_unet_ft if 'inund_unet_ft' in locals() else np.zeros((H,W)),
        "prithvi": inund_prithvi if 'inund_prithvi' in locals() else np.zeros((H,W)),
        "prithvi_finetuned": inund_prithvi_ft if 'inund_prithvi_ft' in locals() else np.zeros((H,W))
    }
    
    for key, mask in masks.items():
        plt.figure(figsize=(10, 8), dpi=150)
        plt.imshow(rgb)
        masked = np.ma.masked_where(mask == 0, mask)
        plt.imshow(masked, cmap="winter_r", alpha=0.5)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(IMG_DIR / f"inundacion_overlay_{key}.png", bbox_inches='tight', pad_inches=0)
        plt.close()
        
    print("✔️ Proceso de comparación finalizado con éxito!")

if __name__ == "__main__":
    main()
