# Clasificación de Imágenes Satelitales y Detección de Inundaciones - Bahía Blanca 2025

Este repositorio contiene la resolución técnica del **Trabajo Práctico N° 2** de la materia **Sistemas de Información Geográfica** de la *Maestría en Explotación de Datos y Descubrimiento del Conocimiento (UBA)*. 

El proyecto implementa un flujo completo de teledetección utilizando imágenes de **Sentinel-2**, modelos de elevación (**Copernicus DEM**), distribución espacial de población (**WorldPop**) y capas de hidrología oficial (**IGN**) para mapear y cuantificar la inundación ocurrida en la ciudad de **Bahía Blanca** en **2025**.

---

## 👥 Integrantes
*   Yair Barnatan
*   German Samartino
*   Augusto Rey

---

## 📊 Resumen de Resultados
*   **Hectáreas Inundadas Netas:** **2206.92 ha** (55,173 píxeles de 20x20m).
*   **Cuerpos de Agua Preexistentes Descontados:** **357.48 ha** (lagoons/cursos permanentes oficiales del IGN).
*   **Población Afectada Estimada:** **~944 habitantes** (expuestos espacialmente en zonas anegadas según WorldPop).
*   **Filtros Topográficos:** Exclusión de anegamientos en pendientes > 5° y alturas > 45 m.s.n.m. mediante el DEM de Copernicus.

---

## 🗂️ Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

*   `scripts/`:
    *   `procesamiento.py`: Script principal de Python que ejecuta el pipeline completo (descargas, mosaicos, ML, filtrados y cálculos).
    *   `dashboard.py`: Aplicación interactiva de Streamlit para el análisis y exploración de los mapas y métricas.
    *   `exportar_visuales.py`: Utilidad para exportar mapas y contrastes en PNG para el dashboard.
    *   `convert_geojson_to_js.py`: Convierte vectores GeoJSON a JavaScript para evitar bloqueos de CORS locales.
*   `notebooks/`:
    *   `Procesamiento_y_Analisis.ipynb`: Cuaderno Jupyter interactivo con el paso a paso del estudio detallado y comentado.
    *   `Descarga de imágenes.ipynb`: Cuaderno original de descarga.
*   `index.html`: Versión del dashboard interactivo en HTML estático, autocompletada y optimizada para ser hosteada en **GitHub Pages** (utiliza Leaflet.js).
*   `consignas/`: Enunciados y pautas originales del TP.
*   `docs/`:
    *   `informe_final.md`: Informe científico formal redactado en español con formato paper académico.
    *   `plan_presentacion.md`: Guion y estructura diapositiva por diapositiva para la ponencia oral de 15 minutos.
*   `img/`: Gráficos y composiciones en falso color generadas en alta resolución.
*   `data-Sentinel-2/`: Capas vectoriales (`aoi.geojson`, `ign_hydrology.geojson`) y capas raster alineadas.

---

## 🚀 Guía de Uso y Ejecución

### 1. Requisitos Previos y Entorno
El proyecto requiere Python 3.10+ y las librerías científicas geoespaciales instaladas. Si ya creaste el entorno virtual `.venv` en la carpeta raíz, recordá activarlo:
```bash
source .venv/bin/activate
```
*(De no tenerlas instaladas, podés instalar las dependencias con `.venv/bin/pip install scikit-learn requests geopandas rasterio matplotlib shapely streamlit leafmap streamlit-folium`)*.

### 2. Ejecutar el Pipeline de Procesamiento
Para correr las clasificaciones (Random Forest y K-Means), descargar los datos externos y calcular el impacto:
```bash
python scripts/procesamiento.py
```
Este script creará los rasters en `data-Sentinel-2/` y guardará un resumen en `data-Sentinel-2/resumen_resultados.txt`.

### 3. Generar las Imágenes Visuales
Para exportar los gráficos del DEM, población y falso color que alimentan la interfaz gráfica:
```bash
python scripts/exportar_visuales.py
```

### 4. Lanzar el Dashboard Interactivo (Streamlit)
Para correr el servidor local interactivo y explorar los resultados desde el navegador:
```bash
streamlit run scripts/dashboard.py
```
*(Se abrirá por defecto en `http://localhost:8501`)*.

### 5. Ver el Visor Estático (GitHub Pages / Local)
Si querés ver el dashboard en formato HTML estático sin necesidad de un backend de Python:
- Podés abrir directamente el archivo `index.html` en tu navegador (haciéndole doble clic).
- O podés correr un servidor HTTP simple de Python:
  ```bash
  python3 -m http.server 8000
  ```
  Y abrir `http://localhost:8000`.
- Para subirlo a GitHub Pages, simplemente subí estos archivos a tu repo y activá GitHub Pages en los ajustes (`Settings -> Pages`) seleccionando la rama de producción (`main`).
