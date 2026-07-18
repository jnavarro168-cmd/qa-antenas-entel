import streamlit as st
import pandas as pd

# Configuración de la página para móviles
st.set_page_config(
    page_title="Entel QA - Buscador de Azimut",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector de Antenas")
st.write("Herramienta para verificación de Azimut y Tilt en tiempo real.")

# 1. Cargar y limpiar base de datos de Entel
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Azimt teorico.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar 'Azimt teorico.xlsx': {e}")
        return None

df_antenas = cargar_datos()

if df_antenas is not None:
    # 2. Selectores de Filtro en Terreno
    sitios_disponibles = sorted(df_antenas['ID_Sitio'].dropna().unique())
    id_sitio = st.selectbox("1. Seleccione el ID_Sitio del Nodo:", sitios_disponibles)
    
    df_filtrado_sitio = df_antenas[df_antenas['ID_Sitio'] == id_sitio]
    sectores_disponibles = sorted(df_filtrado_sitio['Sector'].dropna().unique())
    sector = st.selectbox("2. Seleccione el Sector:", sectores_disponibles)
    
    registro = df_filtrado_sitio[df_filtrado_sitio['Sector'] == sector].iloc[0]
    azimut_teorico = float(registro['Azimut_Teorico'])
    tilt_teorico = float(registro['Tilt_Mecanico_Teorico'])
    
    TOL_AZIMUT = 5.0
    TOL_TILT = 2.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🎯 Azimut Teórico", value=f"{azimut_teorico}°")
    with col2:
        st.metric(label="📐 Tilt Teórico", value=f"{tilt_teorico}°")
        
    st.info("💡 Coloque el celular de espaldas paralelo al panel de la antena usando el sistema de pinza.")

    # 3. Componente con bypass de permisos para Android/Chrome e iframes
    js_camera_and_sensors = f"""
    <div style="position: relative; width: 100%; max-width: 500px; margin: auto;">
        <video id="webcam" autoplay playsinline style="width: 100%; border-radius: 10px; background: #000;"></video>
        
        <div id="hud-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 8px solid gray; border-radius: 10px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; padding: 15px; font-family: sans-serif; color: white; text-shadow: 2px 2px 4px #000; background: rgba(0,0,0,0.1);">
            
            <div style="display: flex; justify-content: space-between; font-size: 16px; font-weight: bold;">
                <div>SITIO: {id_sitio}</div>
                <div>SECTOR: {sector}</div>
            </div>
            
            <div style="text-align: center; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                    AZIMUT REAL: <span id="lbl-azimut-real">--</span>°
                </div>
                <div style="font-size: 18px; margin-bottom: 5px;">
                    Desviación: <span id="lbl-azimut-desv">--</span>°
                </div>
                <div style="font-size: 20px; font-weight: bold; border-top: 1px solid #fff; padding-top: 5px; margin-top: 5px;">
                    TILT REAL: <span id="lbl-tilt-real">--</span>°
                </div>
                <div style="font-size: 16px;">
                    Desviación: <span id="lbl-tilt-desv">--</span>°
                </div>
            </div>
            
            <div id="lbl-status" style="text-align: center; font-size: 22px; font-weight: bold; padding: 8px; border-radius: 5px; background: rgba(128,128,128,0.8);">
                ESPERANDO SENSORES
            </div>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 15px;">
        <button id="btn-permisos" style="padding: 12px 24px; font-size: 16px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%;">
            🔄 SOLICITAR ACCESO COMPLETO (SENSORES Y CÁMARA)
        </button>
    </div>

    <script>
        const video = document.getElementById('webcam');
        const hud = document.getElementById('hud-overlay');
        const btnPermisos = document.getElementById('btn-permisos');
        
        const tAzimut = {azimut_teorico};
        const tTilt = {tilt_teorico};
        const tolAzimut = {TOL_AZIMUT};
        const tolTilt = {TOL_TILT};

        async function iniciarCamara() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "environment" }},
                    audio: false
                }});
                video.srcObject = stream;
            }} catch (err) {{
                console.error("Error al acceder a la cámara trasera: ", err);
            }}
        }}

        function procesarOrientacion(event) {{
            // Forzar detección tanto de brújula corregida como absoluta por acelerómetro diferencial
            let heading = event.webkitCompassHeading || event.alpha;
            
            // Si el evento arroja coordenadas absolutas de Android
            if (event.absolute === true && event.alpha !== null) {{
                heading = 360 - event.alpha;
            }}

            let beta = event.beta; 

            if (heading === null || heading === undefined || beta === null) return;

            let azimutReal = Math.round(heading);
            let tiltReal = Math.round(beta);

            if (azimutReal < 0) azimutReal += 360;
            if (azimutReal >= 360) azimutReal -= 360;

            let desvAzimut = azimutReal - tAzimut;
            if (desvAzimut > 180) desvAzimut -= 360;
            if (desvAzimut < -180) desvAzimut += 360;
            
            let desvTilt = tiltReal - tTilt;

            document.getElementById('lbl-azimut-real').innerText = azimutReal;
            document.getElementById('lbl-tilt-real').innerText = tiltReal;
            document.getElementById('lbl-azimut-desv').innerText = (desvAzimut > 0 ? "+" : "") + desvAzimut;
            document.getElementById('lbl-tilt-desv').innerText = (desvTilt > 0 ? "+" : "") + desvTilt;

            const azimutOk = Math.abs(desvAzimut) <= tolAzimut;
            const tiltOk = Math.abs(desvTilt) <= tolTilt;

            if (azimutOk && tiltOk) {{
                hud.style.border = "8px solid #28a745";
                document.getElementById('lbl-status').innerText = "✅ INSPECCIÓN CONFORME";
                document.getElementById('lbl-status').style.background = "rgba(40, 167, 69, 0.9)";
            }} else {{
                hud.style.border = "8px solid #dc3545";
                document.getElementById('lbl-status').innerText = "❌ FUERA DE TOLERANCIA";
                document.getElementById('lbl-status').style.background = "rgba(220, 53, 69, 0.9)";
            }}
        }}

        btnPermisos.addEventListener('click', async () => {{
            // Inicializar la cámara
            await iniciarCamara();
            
            // Forzar escucha activa rompiendo la política restrictiva de origen
            if (window.DeviceOrientationEvent) {{
                // Intentar capturar evento estándar
                window.addEventListener('deviceorientation', procesarOrientacion, true);
                // Intentar capturar evento absoluto obligatorio en Chrome Mobile moderno
                window.addEventListener('deviceorientationabsolute', procesarOrientacion, true);
                
                document.getElementById('lbl-status').innerText = "CONECTANDO CON SENSORES...";
            }} else {{
                alert("Tu dispositivo o navegador no expone la API de orientación.");
            }}
            
            btnPermisos.style.display = 'none';
        }});
    </script>
    """
    # Se añade explícitamente una altura cómoda para evitar cortes en pantallas pequeñas
    st.components.v1.html(js_camera_and_sensors, height=620, scrolling=False)

st.caption("Desarrollado como MVP de Innovación para Procesos de Calidad y SST Entel.")
