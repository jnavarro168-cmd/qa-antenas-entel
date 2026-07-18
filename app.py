import streamlit as st
import pandas as pd
import json

# Configuración de la página para móviles
st.set_page_config(
    page_title="Entel QA - Buscador de Azimut",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector de Antenas")
st.write("Herramienta MVP para verificación de Azimut y Tilt en tiempo real.")

# 1. Cargar y limpiar base de datos de Entel
@st.cache_data
def cargar_datos():
    try:
        # Cargamos el archivo Excel
        df = pd.read_excel("Azimt teorico.xlsx")
        # Limpiamos los espacios en blanco que tienen los encabezados en tu archivo
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
    
    # Filtrar sectores según el sitio seleccionado
    df_filtrado_sitio = df_antenas[df_antenas['ID_Sitio'] == id_sitio]
    sectores_disponibles = sorted(df_filtrado_sitio['Sector'].dropna().unique())
    sector = st.selectbox("2. Seleccione el Sector:", sectores_disponibles)
    
    # Extraer los valores teóricos correspondientes
    registro = df_filtrado_sitio[df_filtrado_sitio['Sector'] == sector].iloc[0]
    azimut_teorico = float(registro['Azimut_Teorico'])
    tilt_teorico = float(registro['Tilt_Mecanico_Teorico'])
    
    # Definir tolerancias dadas por el usuario
    TOL_AZIMUT = 5.0
    TOL_TILT = 2.0
    
    # Mostrar KPI Teórico
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🎯 Azimut Teórico", value=f"{azimut_teorico}°")
    with col2:
        st.metric(label="📐 Tilt Teórico", value=f"{tilt_teorico}°")
        
    st.info("💡 Coloque el celular de espaldas paralelo al panel de la antena usando el sistema de pinza.")

    # 3. Componente de Realidad Aumentada y Sensores en JavaScript (HTML5)
    # Se inyecta código JS para activar la cámara trasera y los sensores AbsoluteOrientationSensor / DeviceOrientation
    js_camera_and_sensors = f"""
    <div style="position: relative; width: 100%; max-width: 500px; margin: auto;">
        <!-- Video de la cámara en vivo -->
        <video id="webcam" autoplay playsinline style="width: 100%; border-radius: 10px; transform: scaleX(1); background: #000;"></video>
        
        <!-- Capa superpuesta (HUD de Información) -->
        <div id="hud-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 8px solid gray; border-radius: 10px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; padding: 15px; font-family: sans-serif; color: white; text-shadow: 2px 2px 4px #000; background: rgba(0,0,0,0.1);">
            
            <div style="display: flex; justify-content: space-between; font-size: 16px; font-weight: bold;">
                <div>SITIO: {id_sitio}</div>
                <div>SECTOR: {sector}</div>
            </div>
            
            <!-- Datos en Tiempo Real -->
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
            
            <!-- Estado de Validación -->
            <div id="lbl-status" style="text-align: center; font-size: 22px; font-weight: bold; padding: 8px; border-radius: 5px; background: rgba(128,128,128,0.8);">
                ESPERANDO SENSORES
            </div>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 15px;">
        <button id="btn-permisos" style="padding: 12px 24px; font-size: 16px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🔄 Activar Sensores y Cámara
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

        // 1. Inicializar Cámara Trasera sin espejo
        async function initCamera() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: {{ exact: "environment" }} }}, // Fuerza cámara trasera
                    audio: false
                }});
                video.srcObject = stream;
            }} catch (err) {{
                // Fallback si "exact environment" falla en computadoras de prueba
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
                    video.srcObject = stream;
                }} catch (e) {{
                    console.error("Error de cámara: ", e);
                }}
            }}
        }}

        // 2. Procesar Orientación del Dispositivo
        function handleOrientation(event) {{
            // alpha: rotación en torno al eje Z (Brújula 0 a 360)
            // beta: inclinación adelante/atrás (-180 a 180) -> Para medir Tilt mecánico
            let alpha = event.alpha;
            let beta = event.beta;

            if (alpha === null) return;

            // En dispositivos Android, alpha suele requerir corrección dependiendo de la orientación
            // Convertir a rumbo de brújula estándar de 0 a 360 grados
            let azimutReal = Math.round(alpha);
            let tiltReal = Math.round(beta);

            // Calcular desviaciones aritméticas
            let desvAzimut = azimutReal - tAzimut;
            if (desvAzimut > 180) desvAzimut -= 360;
            if (desvAzimut < -180) desvAzimut += 360;
            
            let desvTilt = tiltReal - tTilt;

            // Actualizar etiquetas en pantalla
            document.getElementById('lbl-azimut-real').innerText = azimutReal;
            document.getElementById('lbl-tilt-real').innerText = tiltReal;
            
            document.getElementById('lbl-azimut-desv').innerText = (desvAzimut > 0 ? "+" : "") + desvAzimut;
            document.getElementById('lbl-tilt-desv').innerText = (desvTilt > 0 ? "+" : "") + desvTilt;

            // Logica de validación de tolerancias (Condición de Aceptación de QA)
            const azimutOk = Math.abs(desvAzimut) <= tolAzimut;
            const tiltOk = Math.abs(desvTilt) <= tolTilt;

            if (azimutOk && tiltOk) {{
                hud.style.border = "8px solid #28a745"; // Verde
                document.getElementById('lbl-status').innerText = "✅ INSPECCIÓN CONFORME";
                document.getElementById('lbl-status').style.background = "rgba(40, 167, 69, 0.9)";
            }} else {{
                hud.style.border = "8px solid #dc3545"; // Rojo
                document.getElementById('lbl-status').innerText = "❌ FUERA DE TOLERANCIA";
                document.getElementById('lbl-status').style.background = "rgba(220, 53, 69, 0.9)";
            }}
        }}

        // Manejador del botón para activar permisos (Requerido en iOS modernos y navegadores seguros)
        btnPermisos.addEventListener('click', async () => {{
            await initCamera();
            
            if (typeof DeviceOrientationEvent.requestPermission === 'function') {{
                // Flujo para iOS (si aplica en el futuro)
                DeviceOrientationEvent.requestPermission()
                    .then(permissionState => {{
                        if (permissionState === 'granted') {{
                            window.addEventListener('deviceorientation', handleOrientation, true);
                        }}
                    }})
                    .catch(console.error);
            }} else {{
                // Flujo estándar Android (Samsung A14)
                window.addEventListener('deviceorientation', handleOrientation, true);
            }}
            btnPermisos.style.display = 'none'; // Esconder botón tras activar
        }});
    </script>
    """
    
    # Desplegar el componente HTML/JS dentro de la app de Streamlit
    st.components.v1.html(js_camera_and_sensors, height=600, scrolling=False)

st.caption("Desarrollado como MVP de Innovación para Procesos de Calidad y SST Entel.")
