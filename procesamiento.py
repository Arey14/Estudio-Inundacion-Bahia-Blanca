import os
import requests
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
from rasterio.merge import merge
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path

# Configuración de Rutas y Parámetros
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
AOI_FILE = DATA_DIR / "aoi.geojson"
IMG_FEB = DATA_DIR / "AOI_20250219_20m_clip.tif"
IMG_MAR = DATA_DIR / "AOI_20250311_20m_clip.tif"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR = DATA_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# 1. Fase de Descarga de Datos Externos
# ----------------------------------------------------------------------

def download_file(url, dest_path):
    """Descarga un archivo con soporte de streaming."""
    if dest_path.exists():
        print(f"⏩ {dest_path.name} ya existe. Saltando descarga.")
        return
    print(f"📥 Descargando {url} -> {dest_path.name}...")
    res = requests.get(url, stream=True)
    res.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"✔️ Descarga completada: {dest_path.name}")

def download_dem_and_pop():
    """Descarga los rasters del DEM y de Población."""
    # 1. Copernicus DEM GLO-30 (dos cuadrículas para Bahía Blanca S39W063 y S39W062)
    dem_urls = {
        "dem_S39W063.tif": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_S39_00_W063_00_DEM/Copernicus_DSM_COG_10_S39_00_W063_00_DEM.tif",
        "dem_S39W062.tif": "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_S39_00_W062_00_DEM/Copernicus_DSM_COG_10_S39_00_W062_00_DEM.tif"
    }
    for filename, url in dem_urls.items():
        download_file(url, TEMP_DIR / filename)
        
    # 2. WorldPop 2020 1km Aggregated para Argentina
    pop_url = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/ARG/arg_ppp_2020_1km_Aggregated.tif"
    download_file(pop_url, TEMP_DIR / "arg_pop_2020_1km.tif")

def download_ign_hydrology():
    """Descarga las capas de hidrología del IGN mediante su servicio WFS en formato GeoJSON."""
    dest_geojson = DATA_DIR / "ign_hydrology.geojson"
    if dest_geojson.exists():
        print(f"⏩ {dest_geojson.name} ya existe. Saltando descarga.")
        return
        
    print("🌐 Consultando WFS del IGN para hidrología de Bahía Blanca...")
    # Bounding box del AOI en formato lon-lat
    bbox_str = "-62.605,-38.938,-61.949,-38.535"
    crs_urn = "urn:ogc:def:crs:OGC:1.3:CRS84"
    
    layers = [
        "ign:areas_de_aguas_continentales_perenne",
        "ign:areas_de_aguas_continentales_intermitente",
        "ign:areas_de_aguas_continentales_BH020",
        "ign:lineas_de_aguas_continentales_perenne",
        "ign:lineas_de_aguas_continentales_intermitentes"
    ]
    
    gdfs = []
    for ly in layers:
        url = f"https://wms.ign.gob.ar/geoserver/ows?service=wfs&version=1.1.0&request=GetFeature&typeNames={ly}&bbox={bbox_str},{crs_urn}&outputFormat=application/json"
        try:
            gdf = gpd.read_file(url)
            if len(gdf) > 0:
                print(f"   ➜ {ly}: {len(gdf)} elementos descargados.")
                # Asegurar geometría correcta y CRS
                gdf = gdf.to_crs(4326)
                gdf['layer'] = ly
                gdfs.append(gdf[['geometry', 'layer']])
        except Exception as e:
            print(f"   ⚠️ Falló descarga de {ly}: {e}")
            
    if gdfs:
        combined = gpd.GeoDataFrame(gpd.pd.concat(gdfs, ignore_index=True), crs=4326)
        combined.to_file(dest_geojson, driver="GeoJSON")
        print(f"✔️ Capas de hidrología IGN unificadas en: {dest_geojson.name}")
    else:
        print("⚠️ No se pudo descargar ninguna capa de hidrología del IGN.")

# ----------------------------------------------------------------------
# 2. Fase de Alineación y Preprocesamiento de Rasters
# ----------------------------------------------------------------------

def preprocess_rasters():
    """Une los DEMs, los reproyecta y recorta tanto el DEM como el raster de Población al AOI de Sentinel-2."""
    print("🔧 Preprocesando rasters (Mosaico, Reproyección y Recorte)...")
    
    # 1. Unir y recortar el DEM
    dem_files = [TEMP_DIR / "dem_S39W063.tif", TEMP_DIR / "dem_S39W062.tif"]
    srcs = [rasterio.open(p) for p in dem_files]
    dem_mosaic, out_trans = merge(srcs)
    meta = srcs[0].meta.copy()
    meta.update({
        "height": dem_mosaic.shape[1],
        "width": dem_mosaic.shape[2],
        "transform": out_trans
    })
    
    dem_mosaic_path = TEMP_DIR / "dem_mosaic.tif"
    with rasterio.open(dem_mosaic_path, "w", **meta) as dst:
        dst.write(dem_mosaic)
    for s in srcs: s.close()
    
    # Recortar y alinear el DEM y la Población al grid de Sentinel-2
    align_raster(dem_mosaic_path, IMG_FEB, DATA_DIR / "dem_clip.tif", resampling=Resampling.bilinear)
    align_raster(TEMP_DIR / "arg_pop_2020_1km.tif", IMG_FEB, DATA_DIR / "worldpop_clip.tif", resampling=Resampling.bilinear)
    print("✔️ Rasters alineados correctamente (dem_clip.tif y worldpop_clip.tif generados).")

def align_raster(src_path, match_path, dst_path, resampling=Resampling.bilinear):
    """Reproyecta y alinea un raster de origen para que coincida exactamente con la grilla del raster de referencia."""
    with rasterio.open(match_path) as match_ds:
        match_crs = match_ds.crs
        match_transform = match_ds.transform
        match_width = match_ds.width
        match_height = match_ds.height
        
        with rasterio.open(src_path) as src_ds:
            profile = match_ds.profile.copy()
            # actualizamos el perfil para una sola banda y el tipo de dato correspondiente
            profile.update({
                'count': 1,
                'dtype': src_ds.dtypes[0],
                'nodata': src_ds.nodata if src_ds.nodata is not None else -9999,
                'compress': 'DEFLATE',
                'tiled': True
            })
            
            with rasterio.open(dst_path, 'w', **profile) as dst_ds:
                destination = np.zeros((match_height, match_width), dtype=src_ds.dtypes[0])
                reproject(
                    source=rasterio.band(src_ds, 1),
                    destination=destination,
                    src_transform=src_ds.transform,
                    src_crs=src_ds.crs,
                    dst_transform=match_transform,
                    dst_crs=match_crs,
                    resampling=resampling
                )
                dst_ds.write(destination, 1)

# ----------------------------------------------------------------------
# 3. Fase de Procesamiento de Índices y Clasificación de Inundación
# ----------------------------------------------------------------------

def calculate_indices(bands):
    """Calcula NDWI y MNDWI a partir de un diccionario de bandas."""
    # NDWI = (Green - NIR) / (Green + NIR) = (B03 - B08) / (B03 + B08)
    green = bands['B03'].astype(np.float32)
    nir = bands['B08'].astype(np.float32)
    ndwi = np.where((green + nir) == 0, 0, (green - nir) / (green + nir))
    
    # MNDWI = (Green - SWIR1) / (Green + SWIR1) = (B03 - B11) / (B03 + B11)
    swir1 = bands['B11'].astype(np.float32)
    mndwi = np.where((green + swir1) == 0, 0, (green - swir1) / (green + swir1))
    
    return ndwi, mndwi

def read_sentinel_image(img_path):
    """Lee la imagen recortada de Sentinel y la separa en un diccionario de bandas."""
    # Orden en _20m_clip.tif: ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']
    band_names = ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']
    bands = {}
    with rasterio.open(img_path) as src:
        for idx, name in enumerate(band_names, start=1):
            bands[name] = src.read(idx)
    return bands

def classify_water_random_forest(img_path):
    """Clasifica agua usando Random Forest semi-supervisado basado en umbrales de alta confianza de MNDWI/NDWI."""
    bands = read_sentinel_image(img_path)
    ndwi, mndwi = calculate_indices(bands)
    
    # Seleccionar píxeles de entrenamiento de alta confianza
    # Agua: MNDWI > 0.35 y NDWI > 0.2
    water_mask = (mndwi > 0.35) & (ndwi > 0.2)
    # Tierra: MNDWI < -0.1 y NDWI < 0.0
    land_mask = (mndwi < -0.1) & (ndwi < 0.0)
    
    # Construir la matriz de características (Features)
    # Usamos las 7 bandas + NDWI + MNDWI (9 variables)
    h, w = ndwi.shape
    features_list = [bands[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']]
    features_list.append(ndwi.ravel())
    features_list.append(mndwi.ravel())
    X_all = np.stack(features_list, axis=1) # Shape: (Pixels, 9)
    
    # Tomar muestras de entrenamiento
    water_indices = np.where(water_mask.ravel())[0]
    land_indices = np.where(land_mask.ravel())[0]
    
    # Balancear y limitar muestras a máximo 8000 por clase para velocidad
    n_samples = min(len(water_indices), len(land_indices), 8000)
    if n_samples < 100:
        print("⚠️ Advertencia: Muy pocos píxeles de entrenamiento disponibles.")
        n_samples = max(100, min(len(water_indices), len(land_indices)))
        
    np.random.seed(42)
    train_water_idx = np.random.choice(water_indices, n_samples, replace=False)
    train_land_idx = np.random.choice(land_indices, n_samples, replace=False)
    
    X_train = np.vstack([X_all[train_water_idx], X_all[train_land_idx]])
    y_train = np.hstack([np.ones(n_samples), np.zeros(n_samples)])
    
    # Entrenar Random Forest
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    # Predecir sobre toda la imagen
    preds = rf.predict(X_all)
    water_class = preds.reshape(h, w)
    
    return water_class, ndwi, mndwi

def classify_water_kmeans(img_path):
    """Clasifica agua usando K-Means no supervisado (K=5) sobre las 7 bandas espectrales."""
    bands = read_sentinel_image(img_path)
    ndwi, mndwi = calculate_indices(bands)
    
    h, w = ndwi.shape
    features_list = [bands[b].ravel() for b in ['B04', 'B03', 'B02', 'B8A', 'B12', 'B08', 'B11']]
    X_all = np.stack(features_list, axis=1)
    
    # Escalar datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    # K-Means con K=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    # Por temas de memoria/velocidad en imágenes grandes, ajustamos K-Means
    kmeans.fit(X_scaled[::10]) # entrena en el 10% de los píxeles
    preds = kmeans.predict(X_scaled)
    labels = preds.reshape(h, w)
    
    # Identificar cuál cluster representa el agua (el de mayor MNDWI promedio)
    cluster_mndwi = []
    for c in range(5):
        mean_mndwi = np.mean(mndwi[labels == c])
        cluster_mndwi.append((c, mean_mndwi))
    
    cluster_mndwi.sort(key=lambda x: x[1], reverse=True)
    water_cluster = cluster_mndwi[0][0]
    
    water_class = (labels == water_cluster).astype(np.uint8)
    return water_class

# ----------------------------------------------------------------------
# 4. Fase de Filtrado y Análisis Geográfico
# ----------------------------------------------------------------------

def calculate_slope(dem):
    """Calcula la pendiente en grados a partir del raster de DEM (resolución 20m)."""
    # Usar diferencias finitas
    dy, dx = np.gradient(dem, 20.0) # resolución espacial = 20m
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180.0 / np.pi)
    return slope

def apply_topographic_filter(water_mask, dem_path):
    """Filtra la máscara de agua eliminando píxeles con pendiente > 5° o elevación > 45 metros."""
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
    
    # Calcular pendiente
    slope = calculate_slope(dem)
    
    # Filtrar: el agua no se acumula en pendientes altas (> 5 grados) ni alturas elevadas en Bahía Blanca (> 45msnm)
    topo_mask = (dem <= 45) & (slope <= 5)
    filtered_water = water_mask & topo_mask
    return filtered_water, dem, slope

def calculate_change_and_impact():
    """Ejecuta toda la clasificación, calcula la inundación final, cruza con población e hidrología."""
    print("🚀 Iniciando clasificación y análisis de impacto...")
    
    # 1. Clasificación Random Forest para Febrero y Marzo
    water_feb, ndwi_feb, mndwi_feb = classify_water_random_forest(IMG_FEB)
    water_mar, ndwi_mar, mndwi_mar = classify_water_random_forest(IMG_MAR)
    
    # 2. Clasificación K-Means para comparación
    kmeans_feb = classify_water_kmeans(IMG_FEB)
    kmeans_mar = classify_water_kmeans(IMG_MAR)
    
    # Guardar resultados preliminares en archivos TIF
    with rasterio.open(IMG_FEB) as src:
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.uint8, nodata=0, compress='DEFLATE')
        
        with rasterio.open(DATA_DIR / "water_mask_feb_rf.tif", "w", **profile) as dst:
            dst.write(water_feb.astype(rasterio.uint8), 1)
        with rasterio.open(DATA_DIR / "water_mask_mar_rf.tif", "w", **profile) as dst:
            dst.write(water_mar.astype(rasterio.uint8), 1)
        with rasterio.open(DATA_DIR / "water_mask_feb_kmeans.tif", "w", **profile) as dst:
            dst.write(kmeans_feb.astype(rasterio.uint8), 1)
        with rasterio.open(DATA_DIR / "water_mask_mar_kmeans.tif", "w", **profile) as dst:
            dst.write(kmeans_mar.astype(rasterio.uint8), 1)
            
    # 3. Detectar Inundación (Agua en Marzo pero no en Febrero)
    raw_inundation = (water_mar > 0) & ~(water_feb > 0)
    
    # 4. Filtrado Topográfico usando DEM
    dem_path = DATA_DIR / "dem_clip.tif"
    filtered_inundation, dem, slope = apply_topographic_filter(raw_inundation, dem_path)
    
    # Guardar máscara de inundación final
    with rasterio.open(IMG_FEB) as src:
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.uint8, nodata=0, compress='DEFLATE')
        with rasterio.open(DATA_DIR / "inundacion_final.tif", "w", **profile) as dst:
            dst.write(filtered_inundation.astype(rasterio.uint8), 1)
            
    # 5. Descontar Cuerpos de agua permanentes del IGN
    ign_path = DATA_DIR / "ign_hydrology.geojson"
    ign_water_mask = np.zeros_like(filtered_inundation, dtype=bool)
    if ign_path.exists():
        ign_gdf = gpd.read_file(ign_path)
        # Filtrar solo áreas de agua perennes
        ign_areas = ign_gdf[ign_gdf['layer'] == 'ign:areas_de_aguas_continentales_perenne']
        if len(ign_areas) > 0:
            with rasterio.open(IMG_FEB) as src:
                # Proyectar al CRS del raster
                ign_areas_proj = ign_areas.to_crs(src.crs)
                # Crear máscara rasterizada
                try:
                    ign_water_mask_raw, _ = mask(src, ign_areas_proj.geometry, invert=False, filled=True)
                    # Convertir a boolean mask (si el raster tiene múltiples bandas, usamos la primera)
                    ign_water_mask = (ign_water_mask_raw[0] > 0)
                except Exception as e:
                    print(f"⚠️ No se pudo rasterizar la hidrología del IGN: {e}")
                    
    # Inundación limpia = Inundación filtrada por DEM - Cuerpos de agua permanentes del IGN
    clean_inundation = filtered_inundation & (~ign_water_mask)
    
    with rasterio.open(IMG_FEB) as src:
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.uint8, nodata=0, compress='DEFLATE')
        with rasterio.open(DATA_DIR / "inundacion_limpia_final.tif", "w", **profile) as dst:
            dst.write(clean_inundation.astype(rasterio.uint8), 1)

    # 6. Calcular Hectáreas afectadas
    # Cada píxel de 20x20m = 400 m²
    pixel_area_ha = 400.0 / 10000.0 # 0.04 ha por píxel
    pixels_inundated = np.sum(clean_inundation)
    hectares_affected = pixels_inundated * pixel_area_ha
    
    # 7. Cargar raster de población y estimar afectados
    pop_path = DATA_DIR / "worldpop_clip.tif"
    with rasterio.open(pop_path) as src:
        pop_density = src.read(1)
        # Nodata en WorldPop suele ser negativo o NaN
        pop_density = np.where(pop_density < 0, 0, pop_density)
        
    # La población afectada es la densidad de población sumada en las celdas inundadas.
    # Dado que WorldPop está remuestreado a 20m, la densidad es la cantidad de personas por celda de 20m.
    # Nota: Si el raster de población original de 1km representa "personas por píxel de 1km (1,000,000 m²)", 
    # y lo remuestreamos a 20m (400 m²), el método de remuestreo (bilinear) distribuye los valores,
    # por lo que debemos multiplicar el valor interpolado por la proporción de áreas (400 / 1,000,000) 
    # para no sobreestimar la población si el raster original representaba recuento absoluto de población.
    # Verificamos si arg_ppp es de recuento de población. Sí, ppp = "population per pixel".
    # Así que la suma del raster remuestreado debe corregirse por la proporción de áreas: 400 / 1,000,000 = 0.0004
    poblacion_afectada = np.sum(pop_density[clean_inundation]) * 0.0004
    
    print("\n📊 --- RESULTADOS FINALES ---")
    print(f"Hectáreas afectadas por la inundación: {hectares_affected:.2f} ha")
    print(f"Población estimada afectada: {int(poblacion_afectada)} personas")
    print("--------------------------------\n")
    
    # Guardar resumen en un archivo txt
    resumen_path = DATA_DIR / "resumen_resultados.txt"
    with open(resumen_path, "w") as f:
        f.write("RESUMEN DE RESULTADOS - TRABAJO PRÁCTICO N° 2\n")
        f.write("=============================================\n\n")
        f.write(f"Hectáreas afectadas por la inundación: {hectares_affected:.2f} ha\n")
        f.write(f"Población estimada afectada: {int(poblacion_afectada)} personas\n")
        f.write(f"Píxeles totales inundados (20m): {pixels_inundated}\n")
        f.write(f"Cuerpos de agua permanentes IGN descontados: {np.sum(ign_water_mask) * pixel_area_ha:.2f} ha\n")
        
    print(f"✔️ Resumen de resultados guardado en: {resumen_path.name}")

if __name__ == "__main__":
    download_dem_and_pop()
    download_ign_hydrology()
    preprocess_rasters()
    calculate_change_and_impact()
