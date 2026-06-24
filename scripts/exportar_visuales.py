import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path

# Rutas
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
IMG_FEB = DATA_DIR / "AOI_20250219_20m_clip.tif"
IMG_MAR = DATA_DIR / "AOI_20250311_20m_clip.tif"
DEM_PATH = DATA_DIR / "dem_clip.tif"
POP_PATH = DATA_DIR / "worldpop_clip.tif"
INUND_PATH = DATA_DIR / "inundacion_limpia_final.tif"

IMG_DIR = BASE_DIR / "img"
IMG_DIR.mkdir(exist_ok=True)

def percentile_stretch(band, low_pct=2, high_pct=98):
    """Aplica un estiramiento de contraste basado en percentiles para mejorar la visualización."""
    # Filtrar valores nodata o cero para el cálculo de percentiles
    valid_mask = (band > 0)
    if not np.any(valid_mask):
        return np.zeros_like(band, dtype=np.uint8)
        
    low = np.percentile(band[valid_mask], low_pct)
    high = np.percentile(band[valid_mask], high_pct)
    
    stretched = np.clip((band - low) / (high - low), 0, 1)
    return (stretched * 255).astype(np.uint8)

def export_rgb_false_color():
    """Exporta imágenes en Falso Color Compuesto (SWIR1, NIR, Green) para resaltar el agua en color azul/negro."""
    print("🎨 Generando composiciones RGB Falso Color...")
    for path, name in [(IMG_FEB, "feb"), (IMG_MAR, "mar")]:
        with rasterio.open(path) as src:
            # Bandas: B12 (SWIR2) es 5, B08 (NIR) es 6, B03 (Green) es 2
            swir = src.read(5)
            nir = src.read(6)
            green = src.read(2)
            
            # Estirar cada banda
            r = percentile_stretch(swir)
            g = percentile_stretch(nir)
            b = percentile_stretch(green)
            
            rgb = np.stack([r, g, b], axis=2)
            
            plt.figure(figsize=(10, 8), dpi=150)
            plt.imshow(rgb)
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(IMG_DIR / f"rgb_false_{name}.png", bbox_inches='tight', pad_inches=0)
            plt.close()
    print("✔️ Falso Color generado.")

def export_mndwi():
    """Calcula y exporta mapas de calor de MNDWI."""
    print("🎨 Generando mapas de calor MNDWI...")
    for path, name in [(IMG_FEB, "feb"), (IMG_MAR, "mar")]:
        with rasterio.open(path) as src:
            green = src.read(2).astype(np.float32)
            swir1 = src.read(7).astype(np.float32)
            
            mndwi = np.where((green + swir1) == 0, 0, (green - swir1) / (green + swir1))
            
            plt.figure(figsize=(10, 8), dpi=150)
            plt.imshow(mndwi, cmap="RdYlBu", vmin=-0.6, vmax=0.6)
            plt.colorbar(label="MNDWI")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(IMG_DIR / f"mndwi_{name}.png", bbox_inches='tight')
            plt.close()
    print("✔️ MNDWI generado.")

def export_dem_and_pop():
    """Exporta visuales de DEM y Población."""
    print("🎨 Generando visuales de DEM y Densidad Poblacional...")
    # 1. DEM
    if DEM_PATH.exists():
        with rasterio.open(DEM_PATH) as src:
            dem = src.read(1)
        plt.figure(figsize=(10, 8), dpi=150)
        plt.imshow(dem, cmap="terrain", vmin=0, vmax=60)
        plt.colorbar(label="Elevación (m.s.n.m.)")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(IMG_DIR / "dem_map.png", bbox_inches='tight')
        plt.close()
        
    # 2. Población
    if POP_PATH.exists():
        with rasterio.open(POP_PATH) as src:
            pop = src.read(1)
            pop = np.where(pop < 0, 0, pop)
        plt.figure(figsize=(10, 8), dpi=150)
        plt.imshow(pop, cmap="YlOrRd", vmin=0, vmax=50)
        plt.colorbar(label="Densidad Poblacional (hab/ha)")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(IMG_DIR / "poblacion_map.png", bbox_inches='tight')
        plt.close()
    print("✔️ DEM y Población generados.")

def export_inundation_overlay():
    """Exporta la máscara de inundación superpuesta en el RGB de Marzo."""
    print("🎨 Generando superposición de inundación...")
    if INUND_PATH.exists() and IMG_MAR.exists():
        with rasterio.open(IMG_MAR) as src:
            swir = src.read(5)
            nir = src.read(6)
            green = src.read(2)
            r = percentile_stretch(swir)
            g = percentile_stretch(nir)
            b = percentile_stretch(green)
            rgb = np.stack([r, g, b], axis=2)
            
        with rasterio.open(INUND_PATH) as src:
            inund = src.read(1)
            
        plt.figure(figsize=(10, 8), dpi=150)
        plt.imshow(rgb)
        # Superponer máscara de inundación con color cian semi-transparente
        masked_inund = np.ma.masked_where(inund == 0, inund)
        plt.imshow(masked_inund, cmap="winter_r", alpha=0.5)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(IMG_DIR / "inundacion_overlay.png", bbox_inches='tight', pad_inches=0)
        plt.close()
    print("✔️ Superposición de inundación generada.")

def export_dem_simulation_frames():
    """Genera fotogramas de la simulación teórica de inundación basada en elevación (DEM)."""
    print("🎨 Generando fotogramas de simulación por DEM...")
    anim_dir = IMG_DIR / "animacion_dem"
    anim_dir.mkdir(exist_ok=True)
    
    if not (DEM_PATH.exists() and IMG_MAR.exists()):
        print("⚠️ Faltan archivos para la simulación por DEM. Saltando.")
        return
        
    with rasterio.open(DEM_PATH) as src:
        dem = src.read(1)
        
    with rasterio.open(IMG_MAR) as src:
        swir = src.read(5)
        nir = src.read(6)
        green = src.read(2)
        r = percentile_stretch(swir)
        g = percentile_stretch(nir)
        b = percentile_stretch(green)
        rgb = np.stack([r, g, b], axis=2)
        
    # Calcular pendiente para filtrar zonas planas
    dy, dx = np.gradient(dem, 20.0)
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180.0 / np.pi)
    
    # Alturas a simular (en metros sobre el nivel del mar)
    alturas = [0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30]
    
    for h_val in alturas:
        # Criterio: elevación <= h_val y pendiente <= 5 grados, y DEM válido
        water_mask = (dem <= h_val) & (slope <= 5) & (dem > -9000)
        
        # 1. Versión con Fondo Satelital (para Streamlit)
        plt.figure(figsize=(10, 8), dpi=150)
        plt.imshow(rgb)
        masked_water = np.ma.masked_where(~water_mask, water_mask)
        plt.imshow(masked_water, cmap="Blues_r", alpha=0.6)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(anim_dir / f"frame_{h_val}.png", bbox_inches='tight', pad_inches=0)
        plt.close()
        
        # 2. Versión Transparente (para Leaflet)
        h, w = dem.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        
        # Color azul de agua: R=30, G=144, B=255 (DodgerBlue), Alfa=160
        rgba[water_mask] = [30, 144, 255, 160]
        # El resto queda en [0, 0, 0, 0] (completamente transparente)
        
        from PIL import Image
        img = Image.fromarray(rgba, 'RGBA')
        img.save(anim_dir / f"water_{h_val}.png")
        
    print("✔️ Fotogramas de simulación por DEM (con fondo y transparentes) generados.")

if __name__ == "__main__":
    export_rgb_false_color()
    export_mndwi()
    export_dem_and_pop()
    export_inundation_overlay()
    export_dem_simulation_frames()
