# Walkthrough del Trabajo Práctico N° 2

Este documento resume los logros obtenidos en la ejecución y resolución técnica del TP2 de Teledetección sobre la inundación en la ciudad de Bahía Blanca (2025).

---

## 📽️ Demostración del Dashboard en Vivo

A continuación se muestra una grabación animada del visualizador de Streamlit interactivo en funcionamiento:

![Grabación del Dashboard de Streamlit interactivo](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/dashboard_demo.webp)

---

## 📊 Resumen de Resultados Cuantitativos

El pipeline de procesamiento ejecutó con éxito todos los análisis en el área de interés (AOI) arrojando las siguientes métricas finales:

*   **Hectáreas Inundadas Netas:** **2206.92 ha** (55,173 píxeles de 20x20m).
*   **Población Expuesta/Afectada:** **~944 personas** (calculadas cruzando la máscara espacial con WorldPop).
*   **Cuerpos de Agua Permanentes Descontados:** **357.48 ha** (lagoons/cursos perennes oficiales del IGN).
*   **Filtros Topográficos Aplicados:** Se descartaron todas las clasificaciones en zonas con pendientes superiores a **5 grados** o altitudes mayores a **45 metros sobre el nivel del mar**, aislando con precisión la llanura de inundación.

---

## 🖼️ Capturas de la Interfaz del Dashboard

````carousel
![Página de Resumen de Resultados y Métricas de Impacto](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/screenshot_resumen.png)
<!-- slide -->
![Comparación de Imágenes en Falso Color y MNDWI (Feb vs Mar)](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/screenshot_comparacion.png)
<!-- slide -->
![Mapas de Soporte del DEM de Copernicus y WorldPop](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/screenshot_soporte.png)
<!-- slide -->
![Mapa Interactivo con Hidrología Dinámica del IGN](/home/augusto/.gemini/antigravity-ide/brain/f832c0be-1379-4890-98cf-754c40e7ff8d/screenshot_mapa.png)
````

---

## 🖼️ Galería de Gráficos Procesados

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

## 🤖 Comparación Avanzada de Modelos y Embeddings (Punto 2)

Hemos completado el análisis comparativo entrenando y evaluando **7 aproximaciones distintas** para delimitar la inundación y medir el impacto demográfico, incluyendo versiones pre-entrenadas (Zero-Shot) y ajustadas localmente mediante **Fine-Tuning** en la GPU **RTX 3090**:

1. **Random Forest Base (9 features)**: Clasificación tradicional pixel-a-pixel. Detecta **2219.32 ha** de inundación y **960** personas afectadas. Sirve de baseline.
2. **Random Forest con PCA (3 Componentes)**: Reduce el espacio de 7 bandas a 3 componentes principales (explicando **98.97%** de la varianza). Al corregir el domain shift (escalador y PCA ajustados en Marzo y aplicados a ambas fechas), detecta **1441.00 ha** y **337** personas afectadas, logrando una clasificación más compacta y veloz.
3. **Random Forest con BetaEarth (embeddings de 64D)**: Extracción de representaciones espaciales latentes mediante el emulador local de DeepMind AlphaEarth (con interpolación lineal para recrear las bandas Red Edge `B05`, `B06`, `B07`). Detecta **2479.12 ha** y **1306** personas afectadas, mostrando una excelente cohesión espacial en llanuras inundadas.
4. **U-Net (ResNet34 - Distilación Supervisada)**: Modelo convolucional entrenado localmente en PyTorch utilizando la máscara del Random Forest base como etiqueta. Destila el conocimiento reduciendo el ruido espacial y regularizando los contornos. Detecta **1448.36 ha** y **83** personas afectadas.
5. **U-Net (Ajuste Fino Local)**: La misma arquitectura U-Net entrenada directamente sobre parches espectrales locales de Sentinel-2 utilizando una pérdida combinada de Dice + BCE. Detecta **4583.60 ha** y **159** personas afectadas.
6. **Prithvi-EO-2.0 (Zero-Shot)**: Inferencia directa usando el modelo fundacional de 300M de parámetros de IBM/NASA (finetuneado en Sen1Floods11). Identifica una zona de afectación mucho mayor (**8966.56 ha** y **1874** personas afectadas) al incluir áreas húmedas periféricas de llanuras de pendiente nula.
7. **Prithvi (Ajuste Fino Local)**: El modelo fundacional Prithvi ajustado localmente congelando su encoder (backbone ViT) y entrenando solo su decodificador (UperNetDecoder) en la GPU. Al especializarse en la geografía local, reduce drásticamente la sobreestimación del modelo zero-shot, bajando de 8966 ha a **355.16 ha** y **32** personas afectadas, logrando clasificar con precisión quirúrgica el agua estancada acumulada.

El gráfico comparativo consolidado se guardó en [comparacion_metricas_modelos.png](file:///home/augusto/Desktop/TP2/img/comparacion_metricas_modelos.png):

![Gráfico Comparativo de Modelos y Embeddings](/home/augusto/Desktop/TP2/img/comparacion_metricas_modelos.png)


---

## 🛠️ Productos y Scripts Generados

Hemos creado un ecosistema de archivos estructurado y limpio en `/home/augusto/Desktop/TP2`:

1.  **[procesamiento.py](file:///home/augusto/Desktop/TP2/scripts/procesamiento.py):**
    *   **Descargas Automáticas:** Descarga el DEM de Copernicus (AWS S3) y la población de WorldPop, y realiza solicitudes WFS dinámicas al IGN para obtener las capas de hidrología (cursos y espejos de agua).
    *   **Preprocesamiento y Alineación:** Une los DEMs y alinea/reproyecta las grillas al CRS `EPSG:32720` de Sentinel-2 a 20m.
    *   **Clasificaciones:** Entrena un modelo **Random Forest** semi-supervisado (con etiquetas generadas automáticamente usando MNDWI) y un modelo **K-Means** no supervisado.
    *   **Filtrado:** Limpia la inundación descontando el agua permanente (IGN) y las zonas no inundables (DEM).
2.  **[exportar_visuales.py](file:///home/augusto/Desktop/TP2/scripts/exportar_visuales.py):**
    *   Exporta imágenes en alta calidad (PNG) aplicando estiramientos de contraste percentiles y colormapas adecuados para el dashboard.
    *   **Módulo de Animación**: Renderiza de manera eficiente los fotogramas para la simulación física por DEM.
3.  **[dashboard.py](file:///home/augusto/Desktop/TP2/scripts/dashboard.py):**
    *   Aplicación interactiva de Streamlit con métricas en tiempo real, mapas comparativos deslizantes, mapas del IGN y un **simulador de crecida interactivo por DEM** con soporte para reproducción automática fluida.
4.  **[Procesamiento_y_Analisis.ipynb](file:///home/augusto/Desktop/TP2/notebooks/Procesamiento_y_Analisis.ipynb):**
    *   Cuaderno Jupyter completo para el flujo paso a paso del TP, con celdas explicativas y bloques de código listos para su ejecución y presentación.

---

## 🚀 Instrucciones de Ejecución

El entorno virtual `.venv/` ya está preconfigurado con las librerías necesarias.

### Para ejecutar el Pipeline y exportar estadísticas:
```bash
.venv/bin/python scripts/procesamiento.py
```

### Para visualizar y explorar interactivamente en tu navegador:
```bash
.venv/bin/streamlit run scripts/dashboard.py
```
*(Se abrirá automáticamente el visor en tu navegador local).*
