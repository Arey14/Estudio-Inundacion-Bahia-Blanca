import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap
from pathlib import Path

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
    ["📊 Resumen de Resultados", "🛰️ Comparación Sentinel-2", "🎬 Evolución Temporal & Simulación", "🧭 Datos de Soporte (DEM & Pop)", "🗺️ Mapa Interactivo IGN"]
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

elif menu == "🎬 Evolución Temporal & Simulación":
    st.markdown("<h3 class='section-title'>Evolución Temporal y Simulación de Crecida</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🌧️ Evolución Temporal Real (S2/DEM)", "⛰️ Simulación Teórica de Crecida (DEM)"])
    
    with tab1:
        st.write("Esta sección presenta la evolución reconstruida del anegamiento desde la situación base (19 de febrero) al pico de la inundación (11 de marzo). Se utiliza el modelo de elevación digital (Copernicus DEM) para guiar la secuencia temporal física (el agua inunda primero las cotas más bajas).")
        
        dates_desc = [
            "Paso 0: 19 de Febrero (Cuerpos de agua preexistentes)",
            "Paso 1: Evolución (Inundación en cotas <= 1.0m)",
            "Paso 2: Evolución (Inundación en cotas <= 2.0m)",
            "Paso 3: Evolución (Inundación en cotas <= 3.0m)",
            "Paso 4: Evolución (Inundación en cotas <= 4.0m)",
            "Paso 5: Evolución (Inundación en cotas <= 5.0m)",
            "Paso 6: Evolución (Inundación en cotas <= 7.0m)",
            "Paso 7: Evolución (Inundación en cotas <= 10.0m)",
            "Paso 8: Evolución (Inundación en cotas <= 15.0m)",
            "Paso 9: 11 de Marzo (Pico de inundación registrado)"
        ]
        
        col_ctrl, col_display = st.columns([1, 2])
        
        with col_ctrl:
            st.info("💡 **Cómo usar:** Desplazá el control deslizante para avanzar paso a paso o activá la reproducción automática para ver la secuencia animada en vivo.")
            
            # Autoplay control
            play_real = st.checkbox("▶️ Reproducción Automática (Bucle)", value=False, key="play_real")
            
            if play_real:
                import time
                # Inicializar o recuperar estado del paso actual
                if "step_real" not in st.session_state:
                    st.session_state.step_real = 0
                else:
                    st.session_state.step_real = (st.session_state.step_real + 1) % 10
                
                step = st.slider("Paso de Evolución:", 0, 9, st.session_state.step_real, key="slider_real_disabled", disabled=True)
                # Forzar re-ejecución periódica para la animación
                time.sleep(0.8)
                st.rerun()
            else:
                step = st.slider("Paso de Evolución:", 0, 9, 0, key="slider_real_active")
                
            st.write(f"**Estado actual:** {dates_desc[step]}")
            
        with col_display:
            frame_path = IMG_DIR / "animacion_real" / f"frame_{step}.png"
            if frame_path.exists():
                st.image(str(frame_path), caption=dates_desc[step], width='stretch')
            else:
                st.warning(f"No se encontró el fotograma en {frame_path.name}")
                
    with tab2:
        st.write("Esta simulación permite evaluar de forma teórica qué áreas se verían afectadas si el agua subiera a una altitud determinada (cota sobre el nivel del mar), considerando exclusivamente el relieve (pendientes <= 5 grados).")
        
        alturas = [0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30]
        
        col_ctrl2, col_display2 = st.columns([1, 2])
        
        with col_ctrl2:
            st.info("💡 **Análisis de Vulnerabilidad**: Las cuencas bajas del este y los humedales del sur se inundan de forma masiva por debajo de la cota de 6m. La zona urbana central alta está resguardada por su altitud (cota > 20m).")
            
            play_dem = st.checkbox("▶️ Reproducción Automática (Bucle)", value=False, key="play_dem")
            
            if play_dem:
                import time
                if "step_dem" not in st.session_state:
                    st.session_state.step_dem = 0
                else:
                    st.session_state.step_dem = (st.session_state.step_dem + 1) % len(alturas)
                
                h_idx = st.slider("Cota de agua (m.s.n.m.):", 0, len(alturas)-1, st.session_state.step_dem, key="slider_dem_disabled", disabled=True)
                h_val = alturas[h_idx]
                time.sleep(0.8)
                st.rerun()
            else:
                h_idx = st.slider("Seleccionar cota:", 0, len(alturas)-1, 0, key="slider_dem_active")
                h_val = alturas[h_idx]
                
            st.write(f"**Cota de agua simulada:** {h_val} m.s.n.m.")
            
        with col_display2:
            frame_path = IMG_DIR / "animacion_dem" / f"frame_{h_val}.png"
            if frame_path.exists():
                st.image(str(frame_path), caption=f"Simulación topográfica a cota {h_val} m.s.n.m.", width='stretch')
            else:
                st.warning(f"No se encontró el fotograma para la cota {h_val}")

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
