import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap
from pathlib import Path
import json
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Inundación Bahía Blanca 2025 - Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para estética premium
st.markdown("""
<style>
    .main-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #4B5563;
        text-align: center;
        margin-bottom: 30px;
        font-size: 1.1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 12px;
        padding: 15px 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        border-left: 5px solid #3B82F6;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #4B5563;
        font-weight: 600;
    }
    .section-title {
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 8px;
        margin-top: 50px;
        margin-bottom: 15px;
        color: #1E3A8A;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Rutas de datos
BASE_DIR = Path("/home/augusto/Desktop/TP2")
DATA_DIR = BASE_DIR / "data-Sentinel-2"
IMG_DIR = BASE_DIR / "img"
RESUMEN_FILE = DATA_DIR / "resumen_resultados.txt"

# Leer resumen de resultados
results = {
    "hectareas": 2206.92,
    "poblacion": 944,
    "pixeles": 55173,
    "descontado": 357.48
}

if RESUMEN_FILE.exists():
    try:
        with open(RESUMEN_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Hectáreas afectadas" in line:
                    results["hectareas"] = float(line.split(":")[1].replace("ha", "").strip())
                elif "Población estimada afectada" in line:
                    results["poblacion"] = int(line.split(":")[1].replace("personas", "").strip())
                elif "Píxeles totales inundados" in line:
                    results["pixeles"] = int(line.split(":")[1].strip())
                elif "Cuerpos de agua permanentes" in line:
                    results["descontado"] = float(line.split(":")[1].replace("ha", "").strip())
    except Exception as e:
        pass

# Sidebar
st.sidebar.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🌊 Navegación</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio(
    "Ir a la sección:",
    ["📊 Resumen de Resultados", "🤖 Comparación de Modelos", "🛰️ Comparación Sentinel-2", "🎬 Simulación de Crecida (DEM)", "🧭 Datos de Soporte (DEM & Pop)", "🗺️ Mapa Interactivo IGN"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Proyecto:**  
Trabajo Práctico N° 2  
**Materia:**  
Sistemas de Información Geográfica  
**Docentes:**  
Federico Bayle y Carolina S. Ramos  
**Estudiantes:**  
Yair Barnatan  
German Samartino  
Augusto Rey  
""")

# Título Principal
st.markdown("<h1 class='main-header'>Clasificación de Imágenes Satelitales y Detección de Inundaciones</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Caso de Estudio: Inundación en la Ciudad de Bahía Blanca en 2025</p>", unsafe_allow_html=True)

if menu == "📊 Resumen de Resultados":
    st.markdown("<h3 class='section-title'>Métricas de Impacto de la Inundación</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-val'>{results["hectareas"]:.2f} ha</div>
            <div class='metric-label'>Área Inundada Detectada</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #EF4444;'>
            <div class='metric-val'>{results["poblacion"]}</div>
            <div class='metric-label'>Población Afectada Estimada</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #10B981;'>
            <div class='metric-val'>{results["descontado"]:.2f} ha</div>
            <div class='metric-label'>Agua Permanente Descontada</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #8B5CF6;'>
            <div class='metric-val'>{results["pixeles"]}</div>
            <div class='metric-label'>Píxeles Detectados (20m)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h3 class='section-title'>Visualización de la Inundación sobre Bahía Blanca</h3>", unsafe_allow_html=True)
    col_img, col_info = st.columns([2, 1])
    
    with col_img:
        overlay_img = IMG_DIR / "inundacion_overlay.png"
        if overlay_img.exists():
            st.image(str(overlay_img), caption="Máscara de inundación final (azul) sobre composición en falso color (Marzo 2025).", width='stretch')
        else:
            st.warning("Imagen de superposición no encontrada. Corra scripts/exportar_visuales.py.")
            
    with col_info:
        st.info("""
        **Resumen de la Metodología:**
        - **Detección Satelital:** Se procesaron dos imágenes Sentinel-2 correspondientes al **19 de febrero de 2025** (pre-inundación) y el **11 de marzo de 2025** (post-inundación).
        - **Algoritmo de Machine Learning:** Se entrenó un clasificador **Random Forest** de forma semi-supervisada. Las etiquetas de entrenamiento se generaron automáticamente mediante umbrales robustos de los índices **MNDWI** y **NDWI**.
        - **Filtro Topográfico (DEM):** Se eliminaron falsos positivos urbanos y sombras aplicando restricciones del Modelo de Elevación Digital de Copernicus (pendientes ≤ 5° y altitud ≤ 45 m.s.n.m.).
        - **Cuerpos de Agua del IGN:** Se descontaron los cursos y espejos de agua permanentes del IGN descargados mediante WFS.
        """)

elif menu == "🤖 Comparación de Modelos":
    st.markdown("<h3 class='section-title'>Comparación Cuantitativa de Modelos y Embeddings</h3>", unsafe_allow_html=True)
    st.write("En esta sección se evalúa la eficacia de diferentes aproximaciones espectrales y espaciales, incluyendo el uso de componentes principales (PCA), embeddings geoespaciales (BetaEarth / AlphaEarth de Google DeepMind) y modelos fundacionales (Prithvi-EO-2.0 de IBM/NASA), comparados contra una U-Net convolucional entrenada localmente por destilación supervisada.")
    
    metricas_path = DATA_DIR / "metricas_modelos.json"
    if metricas_path.exists():
        try:
            with open(metricas_path, "r") as f:
                metricas = json.load(f)
            # Convertir a DataFrame y calcular diferencia
            df = pd.DataFrame.from_dict(metricas, orient='index')
            df["Diferencia Hectáreas (ha)"] = (df["hectareas_sin_dem"] - df["hectareas"]).round(2)
            
            # Reordenar y renombrar
            df = df.rename(columns={
                "nombre": "Modelo de Clasificación",
                "hectareas": "Hectáreas (Con DEM)",
                "hectareas_sin_dem": "Hectáreas (Sin DEM)",
                "iou_consenso": "Jaccard IoU (Consenso)",
                "dice_consenso": "Dice Coefficient (Consenso)",
                "poblacion": "Población (Con DEM)",
                "poblacion_sin_dem": "Población (Sin DEM)"
            })
            
            # Seleccionar columnas a mostrar
            cols_to_show = [
                "Modelo de Clasificación", 
                "Hectáreas (Con DEM)", 
                "Hectáreas (Sin DEM)", 
                "Diferencia Hectáreas (ha)",
                "Jaccard IoU (Consenso)",
                "Dice Coefficient (Consenso)",
                "Población (Con DEM)",
                "Población (Sin DEM)"
            ]
            
            # Mostrar tabla interactiva
            st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
            
            # Mostrar gráfico comparativo
            chart_path = IMG_DIR / "comparacion_metricas_modelos.png"
            if chart_path.exists():
                st.image(str(chart_path), caption="Comparación de hectáreas inundadas (con y sin DEM) y población afectada por modelo.", width='stretch')
                
            # Selector de visualización de máscaras
            st.markdown("<h3 class='section-title'>Visualización Interactiva de Máscaras</h3>", unsafe_allow_html=True)
            st.write("Selecciona una máscara de inundación (azul/verde) para superponerla sobre la composición en falso color de Marzo 2025:")
            
            opciones = {metricas[k]["nombre"]: k for k in metricas}
            modelo_sel = st.selectbox("Seleccionar modelo para visualizar:", list(opciones.keys()))
            modelo_key = opciones[modelo_sel]
            
            overlay_model_path = IMG_DIR / f"inundacion_overlay_{modelo_key}.png"
            if overlay_model_path.exists():
                st.image(str(overlay_model_path), caption=f"Máscara de inundación estimada por {modelo_sel}.", width='stretch')
            else:
                st.warning(f"No se encontró la imagen de superposición para {modelo_sel}.")
                
            # Discusión técnica y defensas de los modelos
            st.markdown("<h3 class='section-title'>Análisis Técnico y Lecciones Aprendidas</h3>", unsafe_allow_html=True)
            
            with st.expander("🛡️ Defensa y Explicación de los Modelos (¿Qué hace cada uno?)"):
                st.write("""
                - **RF (Base):** Clasificador tradicional pixel-a-pixel. Se entrena con reflectancia multiespectral básica y dos índices de agua. Es rápido pero muy susceptible al ruido del suelo y las sombras (sal y pimienta) porque no analiza la estructura espacial de los píxeles adyacentes.
                - **RF (3 PCA):** Reduce la dimensionalidad del dataset multiespectral de 7 bandas a 3 componentes principales (capturando el 98.97% de la varianza). Al remover ruido y componentes de correlación mutua, genera mapas de inundación más compactos pero pierde píxeles húmedos marginales.
                - **RF (BetaEarth):** Emplea representaciones latentes geoespaciales de 64 dimensiones. Dado que los embeddings provienen de un codificador espacial pre-entrenado, capturan el contexto de vecindad de cada píxel, logrando delimitar zonas de inundación con excelente cohesión geográfica.
                - **U-Net (Distilación):** Red convolucional entrenada para replicar el output de Random Forest base. Actúa como un filtro de regularización convolucional (campo receptivo de 256x256), rellenando lagunas y suavizando bordes ruidosos.
                - **U-Net (Ajuste Fino):** Red convolucional entrenada desde cero con parches locales y pseudo-etiquetas de alta confianza. Logra generalizar de forma sobresaliente las formas y estructuras de canales fluviales y valles de inundación.
                - **Prithvi-EO-2.0:** Modelo fundacional transformador de 300M de parámetros pre-entrenado por IBM/NASA en inundaciones generales (Sen1Floods11). Posee un umbral espacial/espectral muy genérico y sensible al agua, logrando alta exhaustividad pero también falsos positivos.
                - **Prithvi (Ajuste Fino):** El transformador fundacional adaptado con congelamiento de encoder (backbone ViT) y pesos balanceados (47.83x para agua) sobre parches locales. Especializa su decodificador en la reflectancia y geomorfología específica del suelo de Bahía Blanca.
                """)
                
            with st.expander("📊 Explicación Física de las Discrepancias (¿Por qué difieren tanto?)"):
                st.write("""
                Las diferencias métricas (desde las 1,441 ha de RF-PCA hasta las 8,966 ha de Prithvi Zero-Shot) tienen explicaciones físicas e ingenieriles claras:
                1. **La sobreestimación de Prithvi Zero-Shot (8,966 ha):** Al ser un modelo fundacional entrenado a escala global, confunde la alta reflectancia húmeda de los suelos arcillosos y costeros planos de Bahía Blanca con agua estancada inundada. Al no tener calibración local, el modelo clasifica cualquier zona con alta humedad en el suelo como inundación.
                2. **El colapso por desbalance de clases:** En los primeros intentos de ajuste fino, los modelos colapsaban a clasificar todo como tierra (dando 355 ha) porque el agua representa menos del 3% de los píxeles totales de la zona. Al aplicar **pesos de clase balanceados (47.83x)** en Prithvi y una pérdida combinada Dice+BCE en U-Net, los modelos aprendieron a optimizar la detección del agua sin dejarse engañar por la clase mayoritaria (tierra).
                3. **Efecto del Filtro DEM:** El Modelo Digital de Elevación (DEM) de Copernicus remueve de forma contundente sombras de nubes, laderas empinadas orientadas al sur y falsos positivos en zonas urbanas elevadas, reduciendo el área a su llanura de inundación fluvial real.
                """)
                
            with st.expander("🌍 BetaEarth vs. AlphaEarth (Google DeepMind)"):
                st.write("""
                - **AlphaEarth Foundations (AEF):** Es un modelo cerrado y propietario desarrollado por Google DeepMind que genera embeddings geoespaciales de 64 dimensiones para cualquier ubicación terrestre a 10m de resolución. Dado que el modelo no ha sido liberado al público y solo sus embeddings precalculados en Google Earth Engine están disponibles, no es posible ejecutarlo de forma local o directa en nuestro pipeline offline.
                - **BetaEarth (Asterisk Labs):** Es un emulador e interpolador de código abierto entrenado de forma supervisada para imitar los embeddings de AlphaEarth a partir de imágenes Sentinel-1 y Sentinel-2 estándares. Nos permite generar embeddings locales de 64D en nuestra máquina para las fechas específicas del evento (**Febrero y Marzo de 2025**) y entrenar clasificadores de Machine Learning sobre ellos de forma autónoma.
                """)
        except Exception as e:
            st.error(f"Error al cargar las métricas: {e}")
    else:
        st.warning("El archivo de métricas de comparación no ha sido generado aún. Corra scripts/comparar_modelos.py primero.")

elif menu == "🛰️ Comparación Sentinel-2":
    st.markdown("<h3 class='section-title'>Composición en Falso Color Compuesto (SWIR, NIR, Verde)</h3>", unsafe_allow_html=True)
    st.write("Esta combinación de bandas espectrales facilita enormemente la visualización del agua (que se observa en color azul profundo o negro) frente a la vegetación (verde brillante) y el suelo (tonos marrones).")
    
    col_fc1, col_fc2 = st.columns(2)
    with col_fc1:
        img_feb = IMG_DIR / "rgb_false_feb.png"
        if img_feb.exists():
            st.image(str(img_feb), caption="19 de Febrero 2025 - Antes de la Inundación", width='stretch')
    with col_fc2:
        img_mar = IMG_DIR / "rgb_false_mar.png"
        if img_mar.exists():
            st.image(str(img_mar), caption="11 de Marzo 2025 - Después de la Inundación (Inundación visible en el sector este y sur)", width='stretch')
            
    st.markdown("<h3 class='section-title'>Índice Espectral de Agua Modificado (MNDWI)</h3>", unsafe_allow_html=True)
    st.write("El MNDWI aprovecha la banda verde y la banda SWIR1. Los valores positivos y cercanos a 1 (rojo/azul según la paleta) representan agua pura, mientras que los valores negativos representan suelo y edificación.")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        mndwi_feb = IMG_DIR / "mndwi_feb.png"
        if mndwi_feb.exists():
            st.image(str(mndwi_feb), caption="MNDWI - 19 de Febrero 2025", width='stretch')
    with col_m2:
        mndwi_mar = IMG_DIR / "mndwi_mar.png"
        if mndwi_mar.exists():
            st.image(str(mndwi_mar), caption="MNDWI - 11 de Marzo 2025", width='stretch')

elif menu == "🎬 Simulación de Crecida (DEM)":
    st.markdown("<h3 class='section-title'>Simulación Teórica de Crecida (DEM)</h3>", unsafe_allow_html=True)
    with st.expander("ℹ️ ¿Cómo funciona esta simulación de crecida topográfica?"):
        st.write(r"""
        *   **¿Qué es lo que hace?**  
            Esta simulación calcula de forma teórica e interactiva qué celdas de terreno quedarían sumergidas si el nivel del agua se elevara uniformemente a una altura determinada (cota).
        *   **¿Qué métrica se está moviendo?**  
            La métrica móvil es la **cota de elevación topográfica** (altitud en metros sobre el nivel del mar, m.s.n.m.). Al arrastrar el slider, el modelo clasifica como "inundados" a todos los píxeles cuyo relieve en el DEM sea menor o igual a la cota seleccionada, y que además pertenezcan a llanuras y cuencas bajas (pendiente $\le 5^{\circ}$).
        *   **Fuente de los datos de relieve:**  
            Los datos provienen del **Modelo de Elevación Digital de Copernicus (Copernicus DEM GLO-30)** de 30m de resolución original, interpolado y remuestreado a 20m de grilla espacial para alinearse exactamente con las imágenes multiespectrales de Sentinel-2.
        """)
    
    alturas = [0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30]
    
    col_ctrl, col_display = st.columns([1, 3])
    
    with col_ctrl:
        st.info("💡 **Análisis de Vulnerabilidad**: Las cuencas bajas del este y los humedales del sur se inundan de forma masiva por debajo de la cota de 6m. La zona urbana central alta está resguardada por su altitud (cota > 20m).")
        
        # Slider de cota
        h_val = st.select_slider("Seleccionar cota de agua (m.s.n.m.):", options=alturas, value=0)
        
        # Botón para iniciar animación automática
        play_anim = st.button("▶️ Reproducir Crecida Completa")
        
    with col_display:
        image_placeholder = st.empty()
        
        # Si se hace click en reproducir animación
        if play_anim:
            import time
            for val in alturas:
                frame_path = IMG_DIR / "animacion_dem" / f"frame_{val}.png"
                if frame_path.exists():
                    image_placeholder.image(str(frame_path), caption=f"Simulación topográfica a cota {val} m.s.n.m.", width='stretch')
                time.sleep(0.4)
            # Al finalizar, volver a mostrar el valor seleccionado en el slider
            frame_path = IMG_DIR / "animacion_dem" / f"frame_{h_val}.png"
            if frame_path.exists():
                image_placeholder.image(str(frame_path), caption=f"Simulación topográfica a cota {h_val} m.s.n.m.", width='stretch')
        else:
            frame_path = IMG_DIR / "animacion_dem" / f"frame_{h_val}.png"
            if frame_path.exists():
                image_placeholder.image(str(frame_path), caption=f"Simulación topográfica a cota {h_val} m.s.n.m.", width='stretch')

elif menu == "🧭 Datos de Soporte (DEM & Pop)":
    st.markdown("<h3 class='section-title'>Topografía y Elevación (Copernicus DEM GLO-30)</h3>", unsafe_allow_html=True)
    st.write("El modelo digital de elevación nos permite verificar si el agua se acumula físicamente en llanuras bajas o zonas deprimidas.")
    
    col_dem, col_dem_info = st.columns([2, 1])
    with col_dem:
        dem_img = IMG_DIR / "dem_map.png"
        if dem_img.exists():
            st.image(str(dem_img), caption="Mapa de Elevación de Bahía Blanca (Copernicus GLO-30, resolución de 20m tras interpolación).", width='stretch')
    with col_dem_info:
        st.info("""
        **Análisis de Elevaciones:**
        - La ciudad de Bahía Blanca se asienta sobre una pendiente que desciende de norte a sur hacia el estuario.
        - Las zonas inundadas detectadas se concentran predominantemente en alturas **inferiores a los 25 metros sobre el nivel del mar** y llanuras con pendiente prácticamente nula (≤ 2°).
        - El filtro topográfico implementado eliminó falsos positivos ubicados en las mesetas altas al norte de la ciudad.
        """)
        
    st.markdown("<h3 class='section-title'>Distribución de la Población (WorldPop 1km)</h3>", unsafe_allow_html=True)
    st.write("Utilizando los datos de distribución espacial de la población mundial de WorldPop (2020), cruzamos la máscara de inundación para calcular el número de personas expuestas directamente.")
    
    col_pop, col_pop_info = st.columns([2, 1])
    with col_pop:
        pop_img = IMG_DIR / "poblacion_map.png"
        if pop_img.exists():
            st.image(str(pop_img), caption="Mapa de Densidad Poblacional (hab/ha) de WorldPop alineado al AOI.", width='stretch')
    with col_pop_info:
        st.info(f"""
        **Análisis Demográfico:**
        - Población estimada expuesta: **{results["poblacion"]} personas**.
        - La mayor concentración de la inundación ocurrió en áreas agrícolas, de humedales y periféricas, lo que limitó significativamente el impacto sobre las zonas urbanas de alta densidad.
        """)

elif menu == "🗺️ Mapa Interactivo IGN":
    st.markdown("<h3 class='section-title'>Mapa Interactivo de Hidrología Oficial del IGN</h3>", unsafe_allow_html=True)
    st.write("Este mapa interactivo carga el polígono de referencia (AOI) y las capas vectoriales oficiales del Instituto Geográfico Nacional (IGN) correspondientes a Bahía Blanca, descargadas de forma dinámica mediante WFS.")
    
    aoi_path = DATA_DIR / "aoi.geojson"
    ign_path = DATA_DIR / "ign_hydrology.geojson"
    
    if aoi_path.exists():
        # Crear Mapa Leafmap/Folium
        m = leafmap.Map(center=[-38.72, -62.27], zoom=11, draw_control=False, measure_control=False)
        
        # Cargar AOI
        aoi_gdf = gpd.read_file(aoi_path)
        m.add_gdf(aoi_gdf, layer_name="Polígono AOI de Referencia", style={'color': 'red', 'fillOpacity': 0.1})
        
        # Cargar IGN
        if ign_path.exists():
            ign_gdf = gpd.read_file(ign_path)
            
            # Cargar áreas perennes
            perennes_areas = ign_gdf[ign_gdf['layer'] == 'ign:areas_de_aguas_continentales_perenne']
            if len(perennes_areas) > 0:
                m.add_gdf(perennes_areas, layer_name="IGN - Espejos de Agua (Perenne)", style={'color': 'blue', 'fillColor': 'blue', 'fillOpacity': 0.5})
                
            # Cargar líneas perennes
            perennes_lineas = ign_gdf[ign_gdf['layer'] == 'ign:lineas_de_aguas_continentales_perenne']
            if len(perennes_lineas) > 0:
                m.add_gdf(perennes_lineas, layer_name="IGN - Cursos de Agua (Perenne)", style={'color': '#1E40AF', 'weight': 2.5})
                
            # Cargar líneas intermitentes
            interm_lineas = ign_gdf[ign_gdf['layer'] == 'ign:lineas_de_aguas_continentales_intermitentes']
            if len(interm_lineas) > 0:
                m.add_gdf(interm_lineas, layer_name="IGN - Cursos de Agua (Intermitente)", style={'color': '#60A5FA', 'weight': 1.5, 'dashArray': '5, 5'})
                
        # Renderizar en Streamlit
        m.to_streamlit(height=600)
    else:
        st.error("No se encontró el polígono AOI de referencia (aoi.geojson).")
