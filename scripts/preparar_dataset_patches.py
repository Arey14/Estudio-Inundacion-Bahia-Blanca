import os
import sys
import numpy as np
import rasterio
import geopandas as gpd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

# Setup paths
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
IMG_FEB = DATA_DIR / "AOI_20250219_20m_clip.tif"
IMG_MAR = DATA_DIR / "AOI_20250311_20m_clip.tif"
DEM_PATH = DATA_DIR / "dem_clip.tif"
IGN_PATH = DATA_DIR / "ign_hydrology.geojson"
OUT_DIR = DATA_DIR / "dataset_finetuning"
OUT_DIR.mkdir(exist_ok=True)

# 1. Functions from comparar_modelos
def read_sentinel_image(img_path):
    band_names = ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']
    bands = {}
    with rasterio.open(img_path) as src:
        for idx, name in enumerate(band_names):
            bands[name] = src.read(idx + 1)
    return bands

def calculate_indices(bands):
    green = bands['B03'].astype(np.float32)
    nir = bands['B08'].astype(np.float32)
    ndwi = np.where((green + nir) == 0, 0, (green - nir) / (green + nir))
    swir1 = bands['B11'].astype(np.float32)
    mndwi = np.where((green + swir1) == 0, 0, (green - swir1) / (green + swir1))
    return ndwi, mndwi

def calculate_slope(dem):
    dy, dx = np.gradient(dem, 20.0)
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180.0 / np.pi)
    return slope

def apply_topographic_filter(water_mask, dem_path):
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
    slope = calculate_slope(dem)
    topo_mask = (dem <= 45) & (slope <= 5) & (dem > -9000)
    return water_mask & topo_mask

def get_ign_water_mask(img_shape, ref_crs, ref_transform):
    ign_water_mask = np.zeros(img_shape, dtype=bool)
    if IGN_PATH.exists():
        try:
            from rasterio.mask import mask
            ign_gdf = gpd.read_file(IGN_PATH)
            ign_areas = ign_gdf[ign_gdf['layer'] == 'ign:areas_de_aguas_continentales_perenne']
            if len(ign_areas) > 0:
                with rasterio.open(IMG_FEB) as src:
                    ign_areas_proj = ign_areas.to_crs(src.crs)
                    ign_water_mask_raw, _ = mask(src, ign_areas_proj.geometry, invert=False, filled=True)
                    ign_water_mask = (ign_water_mask_raw[0] > 0)
        except Exception as e:
            print(f"Error reading IGN hydrology: {e}")
    return ign_water_mask

def get_training_samples(bands_mar, ndwi_mar, mndwi_mar):
    water_mask = (mndwi_mar > 0.35) & (ndwi_mar > 0.2)
    land_mask = (mndwi_mar < -0.1) & (ndwi_mar < 0.0)
    water_indices = np.where(water_mask.ravel())[0]
    land_indices = np.where(land_mask.ravel())[0]
    n_samples = min(len(water_indices), len(land_indices), 8000)
    np.random.seed(42)
    train_water_idx = np.random.choice(water_indices, n_samples, replace=False)
    train_land_idx = np.random.choice(land_indices, n_samples, replace=False)
    return train_water_idx, train_land_idx, n_samples

def main():
    print(" leyendo imagenes Sentinel-2...")
    bands_feb = read_sentinel_image(IMG_FEB)
    bands_mar = read_sentinel_image(IMG_MAR)
    
    ndwi_feb, mndwi_feb = calculate_indices(bands_feb)
    ndwi_mar, mndwi_mar = calculate_indices(bands_mar)
    
    H, W = ndwi_mar.shape
    with rasterio.open(IMG_FEB) as src:
        ref_crs = src.crs
        ref_transform = src.transform
    ign_water_mask = get_ign_water_mask((H, W), ref_crs, ref_transform)
    
    print(" Entrenamiento de Random Forest Base para obtener pseudo-etiquetas...")
    train_water_idx, train_land_idx, n_samples = get_training_samples(bands_mar, ndwi_mar, mndwi_mar)
    
    features_feb_7 = np.stack([bands_feb[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=1)
    features_mar_7 = np.stack([bands_mar[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=1)
    
    X_all_feb_base = np.hstack([features_feb_7, ndwi_feb.ravel()[:, np.newaxis], mndwi_feb.ravel()[:, np.newaxis]])
    X_all_mar_base = np.hstack([features_mar_7, ndwi_mar.ravel()[:, np.newaxis], mndwi_mar.ravel()[:, np.newaxis]])
    
    X_train_base = np.vstack([X_all_mar_base[train_water_idx], X_all_mar_base[train_land_idx]])
    y_train = np.hstack([np.ones(n_samples), np.zeros(n_samples)])
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train_base, y_train)
    
    print(" Generando máscaras de agua...")
    water_feb_rf = rf.predict(X_all_feb_base).reshape((H, W))
    water_mar_rf = rf.predict(X_all_mar_base).reshape((H, W))
    
    inund_rf = (water_mar_rf > 0) & ~(water_feb_rf > 0)
    inund_rf = apply_topographic_filter(inund_rf, DEM_PATH)
    inund_rf = inund_rf & (~ign_water_mask)
    
    # Target mask for training (high confidence consensus: RF says flooded AND mndwi is postive/wet)
    target_mask = inund_rf & (mndwi_mar > 0.25)
    
    print(f"   ➜ Total píxeles inundados pseudo-etiquetados: {np.sum(target_mask)}")
    
    # Preparar el stack de imágenes Sentinel-2 (7 bandas)
    img_stack = np.stack([bands_mar[b] for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']], axis=0)
    
    # Extracción de parches 224x224
    tile_size = 224
    stride = 64
    patches_x = []
    patches_y = []
    
    for r in range(0, H - tile_size + 1, stride):
        for c in range(0, W - tile_size + 1, stride):
            patch_x = img_stack[:, r:r+tile_size, c:c+tile_size]
            patch_y = target_mask[r:r+tile_size, c:c+tile_size]
            
            # Omitir si hay más de 30% de píxeles sin datos (ceros en banda B02)
            if np.mean(patch_x[2] == 0) > 0.3:
                continue
                
            # Normalizar a escala [0, 1] dividiendo por 10000.0 (reflectancia Sentinel-2 L2A)
            patch_x_norm = (patch_x.astype(np.float32) / 10000.0)
            
            patches_x.append(patch_x_norm)
            patches_y.append(patch_y.astype(np.float32))
            
    patches_x = np.array(patches_x)
    patches_y = np.array(patches_y)
    
    print(f"   ➜ Cantidad total de parches extraídos: {len(patches_x)}")
    
    # Mezclar y dividir en entrenamiento/validación (80% / 20%)
    np.random.seed(42)
    indices = np.arange(len(patches_x))
    np.random.shuffle(indices)
    
    split_idx = int(0.8 * len(patches_x))
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]
    
    train_x = patches_x[train_idx]
    train_y = patches_y[train_idx]
    val_x = patches_x[val_idx]
    val_y = patches_y[val_idx]
    
    print(f"   ➜ Entrenamiento: {len(train_x)} parches")
    print(f"   ➜ Validación: {len(val_x)} parches")
    
    # Guardar en la carpeta de destino
    np.save(OUT_DIR / "train_x.npy", train_x)
    np.save(OUT_DIR / "train_y.npy", train_y)
    np.save(OUT_DIR / "val_x.npy", val_x)
    np.save(OUT_DIR / "val_y.npy", val_y)
    print(" Dataset guardado con éxito en", OUT_DIR)

if __name__ == "__main__":
    main()
