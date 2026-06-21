import json
from pathlib import Path

# Rutas
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
AOI_GEOJSON = DATA_DIR / "aoi.geojson"
IGN_GEOJSON = DATA_DIR / "ign_hydrology.geojson"

# Salidas JS
AOI_JS = DATA_DIR / "aoi.js"
IGN_JS = DATA_DIR / "ign_hydrology.js"

def convert_to_js():
    # 1. AOI
    if AOI_GEOJSON.exists():
        with open(AOI_GEOJSON, 'r') as f:
            data = json.load(f)
        with open(AOI_JS, 'w') as f:
            f.write(f"window.aoiData = {json.dumps(data)};\n")
        print(f"✔️ {AOI_JS.name} generado.")
    else:
        print(f"⚠️ {AOI_GEOJSON.name} no encontrado.")
        
    # 2. IGN Hydrology
    if IGN_GEOJSON.exists():
        with open(IGN_GEOJSON, 'r') as f:
            data = json.load(f)
        with open(IGN_JS, 'w') as f:
            f.write(f"window.ignHydrologyData = {json.dumps(data)};\n")
        print(f"✔️ {IGN_JS.name} generado.")
    else:
        print(f"⚠️ {IGN_GEOJSON.name} no encontrado.")

if __name__ == "__main__":
    convert_to_js()
