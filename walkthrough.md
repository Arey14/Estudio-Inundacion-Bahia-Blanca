# Walkthrough del Trabajo Práctico N° 2

Este documento resume los logros obtenidos en la ejecución y resolución técnica del TP2 de Teledetección sobre la inundación en la ciudad de Bahía Blanca (2025).

---

## 📊 Resumen de Resultados Cuantitativos

El pipeline de procesamiento ejecutó con éxito todos los análisis en el área de interés (AOI) arrojando las siguientes métricas finales:

*   **Hectáreas Inundadas Netas:** **2206.92 ha** (55,173 píxeles de 20x20m).
*   **Población Expuesta/Afectada:** **~944 personas** (calculadas cruzando la máscara espacial con WorldPop).
*   **Cuerpos de Agua Permanentes Descontados:** **357.48 ha** (lagoons/cursos perennes oficiales del IGN).
*   **Filtros Topográficos Aplicados:** Se descartaron todas las clasificaciones en zonas con pendientes superiores a **5 grados** o altitudes mayores a **45 metros sobre el nivel del mar**, aislando con precisión la llanura de inundación.

---

## 🖼️ Galería de Resultados Visuales

````carousel
![Superposición de la Máscara de Inundación (Cyan) sobre composición en Falso Color de Marzo 2025](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/inundacion_overlay.png)
<!-- slide -->
![Composición en Falso Color - 19 de Febrero (Antes) vs 11 de Marzo (Inundación en el sector este y sur)](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/rgb_false_mar.png)
<!-- slide -->
![Índice Espectral MNDWI - 19 de Febrero 2025](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/mndwi_feb.png)
<!-- slide -->
![Índice Espectral MNDWI - 11 de Marzo 2025](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/mndwi_mar.png)
<!-- slide -->
![Modelo Digital de Elevación de Copernicus (20m)](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/dem_map.png)
<!-- slide -->
![Densidad de Población de WorldPop (hab/ha)](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/poblacion_map.png)
````

---

## 🛠️ Productos y Scripts Generados

Hemos creado un ecosistema de archivos estructurado y limpio en `/home/augusto/Desktop/TP2`:

1.  **[procesamiento.py](file:///home/augusto/Desktop/TP2/procesamiento.py):**
    *   **Descargas Automáticas:** Descarga el DEM de Copernicus (AWS S3) y la población de WorldPop, y realiza solicitudes WFS dinámicas al IGN para obtener las capas de hidrología (cursos y espejos de agua).
    *   **Preprocesamiento y Alineación:** Une los DEMs y alinea/reproyecta las grillas al CRS `EPSG:32720` de Sentinel-2 a 20m.
    *   **Clasificaciones:** Entrena un modelo **Random Forest** semi-supervisado (con etiquetas generadas automáticamente usando MNDWI) y un modelo **K-Means** no supervisado.
    *   **Filtrado:** Limpia la inundación descontando el agua permanente (IGN) y las zonas no inundables (DEM).
2.  **[exportar_visuales.py](file:///home/augusto/Desktop/TP2/exportar_visuales.py):**
    *   Exporta imágenes en alta calidad (PNG) aplicando estiramientos de contraste percentiles y colormapas adecuados para el dashboard.
3.  **[dashboard.py](file:///home/augusto/Desktop/TP2/dashboard.py):**
    *   Aplicación interactiva de Streamlit con métricas en tiempo real, mapas comparativos deslizantes y un mapa de Folium/Leafmap interactivo con las capas de hidrología del IGN sobre el AOI.
4.  **[Procesamiento_y_Analisis.ipynb](file:///home/augusto/Desktop/TP2/Procesamiento_y_Analisis.ipynb):**
    *   Cuaderno Jupyter completo para el flujo paso a paso del TP, con celdas explicativas y bloques de código listos para su ejecución y presentación.

---

## 🚀 Instrucciones de Ejecución

El entorno virtual `.venv/` ya está preconfigurado con las librerías necesarias.

### Para ejecutar el Pipeline y exportar estadísticas:
```bash
.venv/bin/python procesamiento.py
```

### Para visualizar y explorar interactivamente en tu navegador:
```bash
.venv/bin/streamlit run dashboard.py
```
*(Se abrirá automáticamente el visor en tu navegador local).*
