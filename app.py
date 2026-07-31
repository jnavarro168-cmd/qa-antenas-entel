import base64
from datetime import datetime
import os
import time
import google.generativeai as genai
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Entel QA - Target V6.7 AI",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("📡 Entel QA - Inspector Target V6.7 (con IA)")
st.markdown(
    "**Sistema de Inspección, Alineación y Auditoría con Inteligencia Artificial**"
)

# --- 1. DATOS DEL SITIO (INPUTS) ---
with st.expander("📝 1. Ingresar Datos del Sitio y Parámetros", expanded=True):
    col_id1, col_id2 = st.columns([2, 1])

    with col_id1:
        sitio_nemonico = (
            st.text_input(
                "Nemónico del Sitio / Nodo:", value="SA542", max_chars=20
            )
            .strip()
            .upper()
        )

    with col_id2:
        sector_seleccionado = st.selectbox(
            "Sector:",
            options=["Sector 1", "Sector 2", "Sector 3", "Sector 4"],
            index=0,
        )

    col_input1, col_input2 = st.columns(2)

    with col_input1:
        azimut_teorico = st.number_input(
            "Azimut Teórico (°)",
            min_value=0.0,
            max_value=360.0,
            value=300.0,
            step=1.0,
        )

    with col_input2:
        tilt_teorico = st.number_input(
            "Tilt Teórico (°)",
            min_value=-90.0,
            max_value=90.0,
            value=85.0,
            step=0.5,
        )

    compensacion_manual = st.number_input(
        "Ajuste Fino Manual (°):",
        min_value=-90.0,
        max_value=90.0,
        value=0.0,
        step=0.5,
    )

TOL_AZIMUT = 5.0
TOL_TILT = 2.0

texto_identificacion = f"{sitio_nemonico} - {sector_seleccionado.upper()}"
nombre_archivo_sector = (
    f"{sitio_nemonico}_{sector_seleccionado.replace(' ', '-')}"
)

st.markdown("---")

# --- 2. MOTOR DE CÁMARA Y SENSORES ---
st.subheader("📸 2. Captura de Evidencia en Terreno")
st.info("Utiliza la cámara para alinear la antena y capturar la evidencia.")

HTML_TEMPLATE = r"""
<div id="capture-area" style="width: 100%; max-width: 500px; margin: auto; font-family: system-ui, -apple-system, sans-serif; background: #0f172a; padding: 8px; border-radius: 12px;">
    
    <div style="position: relative; width: 100%; border-radius: 10px; overflow: hidden; background: #000;">
        <video id="webcam" autoplay playsinline style="width: 100%; display: block; max-height: 280px; object-fit: cover;"></video>
        <canvas id="target-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
        <canvas id="snapshot" style="display: none; width: 100%; border-radius: 10px;"></canvas>
        
        <div style="position: absolute; top: 8px; left: 8px; background: rgba(15, 23, 42, 0.85); color: #38bdf8; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; border: 1px solid rgba(56, 189, 248, 0.3);">
            __TEXTO_IDENTIFICACION__ | Dec GPS: <span id="lbl-dec-gps">Calculando...</span>
        </div>

        <div id="badge-accuracy" style="position: absolute; top: 8px; right: 8px; background: rgba(15, 23, 42, 0.85); color: #22c55e; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; border: 1px solid rgba(34, 197, 94, 0.3);">
            🟢 Sensor Listo
        </div>
    </div>
    
    <div id="data-panel" style="margin-top: 8px; background: #1e293b; color: white; padding: 10px; border-radius: 10px; border: 2px solid #ef4444;">
        
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #94a3b8; font-weight: bold; margin-bottom: 6px;">
            <div>ALINEACIÓN DE OBJETIVO (TARGET)</div>
            <div>TOL: Az±5° | Tlt±2°</div>
        </div>

        <div style="display: flex; gap: 8px; justify-content: space-between; text-align: center;">
            <div style="flex: 1; background: #0f172a; padding: 6px; border-radius: 6px;">
                <div style="font-size: 9px; color: #38bdf8; font-weight: bold;">AZIMUT REAL</div>
                <div style="font-size: 22px; font-weight: 800; margin: 0;"><span id="lbl-azimut-real">--</span>°</div>
                <div style="font-size: 10px; color: #cbd5e1;">Desv: <span id="lbl-azimut-desv">--</span>°</div>
            </div>
            
            <div style="flex: 1; background: #0f172a; padding: 6px; border-radius: 6px;">
                <div style="font-size: 9px; color: #38bdf8; font-weight: bold;">TILT REAL</div>
                <div style="font-size: 22px; font-weight: 800; margin: 0;"><span id="lbl-tilt-real">--</span>°</div>
                <div style="font-size: 10px; color: #cbd5e1;">Desv: <span id="lbl-tilt-desv">--</span>°</div>
            </div>
        </div>
        
        <div id="lbl-status" style="margin-top: 6px; text-align: center; font-size: 13px; font-weight: bold; padding: 6px; border-radius: 6px; background: #ef4444;">
            INICIALIZANDO ALINEADOR...
        </div>
    </div>
</div>

<div style="max-width: 500px; margin: 6px auto 0 auto; display: flex; flex-direction: column; gap: 6px;">
    <button id="btn-permisos" style="padding: 12px; font-size: 14px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%;">
        📡 ACTIVAR CÁMARA Y MIRA TARGET V6.7
    </button>
    
    <button id="btn-capturar" style="display: none; padding: 14px; font-size: 15px; font-weight: bold; background-color: #e11d48; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%;">
        📸 CAPTURAR EVIDENCIA CON TARGET
    </button>
</div>

<a id="download-link" style="display: none;"></a>

<script>
    const video = document.getElementById('webcam');
    const overlayCanvas = document.getElementById('target-overlay');
    const oCtx = overlayCanvas.getContext('2d');
    const canvas = document.getElementById('snapshot');
    const dataPanel = document.getElementById('data-panel');
    const btnPermisos = document.getElementById('btn-permisos');
    const btnCapturar = document.getElementById('btn-capturar');
    const downloadLink = document.getElementById('download-link');
    const lblDecGps = document.getElementById('lbl-dec-gps');
    
    const tIdentificacion = "__TEXTO_IDENTIFICACION__";
    const tNombreArchivo = "__NOMBRE_ARCHIVO_SECTOR__";
    const tAzimut = __AZIMUT_TEORICO__;
    const tTilt = __TILT_TEORICO__;
    const tolAzimut = __TOL_AZIMUT__;
    const tolTilt = __TOL_TILT__;
    const offsetManual = __COMPENSACION_MANUAL__;

    let declinacionCalculadaGPS = 0.0;
    let latitudActual = "Buscando...";
    let longitudActual = "Buscando...";

    function redimensionarCanvasOverlay() {
        overlayCanvas.width = video.clientWidth || 350;
        overlayCanvas.height = video.clientHeight || 220;
    }

    async function iniciarCamara() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" },
                audio: false
            });
            video.srcObject = stream;
            video.onloadedmetadata = () => { video.play(); };
            btnCapturar.style.display = 'block';
        } catch (err) {
            alert("Error al acceder a la cámara.");
        }
    }

    btnPermisos.addEventListener('click', async () => {
        await iniciarCamara();
        btnPermisos.style.display = 'none';
    });

    btnCapturar.addEventListener('click', () => {
        canvas.width = video.videoWidth || 1280;
        canvas.height = video.videoHeight || 720;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const imageUri = canvas.toDataURL('image/jpeg', 0.95);
        downloadLink.href = imageUri;
        downloadLink.download = tNombreArchivo + "_evidencia.jpg";
        downloadLink.click();
    });
</script>
"""

js_v66_engine = (
    HTML_TEMPLATE
    .replace("__TEXTO_IDENTIFICACION__", texto_identificacion)
    .replace("__NOMBRE_ARCHIVO_SECTOR__", nombre_archivo_sector)
    .replace("__AZIMUT_TEORICO__", str(azimut_teorico))
    .replace("__TILT_TEORICO__", str(tilt_teorico))
    .replace("__TOL_AZIMUT__", str(TOL_AZIMUT))
    .replace("__TOL_TILT__", str(TOL_TILT))
    .replace("__COMPENSACION_MANUAL__", str(compensacion_manual))
)

components.html(js_v66_engine, height=520, scrolling=True)

st.markdown("---")

# --- 3. ANÁLISIS AUDITORÍA CON IA (GEMINI) ---
st.subheader("🤖 3. Configuración de IA Gemini")

api_key = st.text_input("Ingresa tu API Key de Google Gemini:", type="password")

if api_key and not api_key.startswith("AIzaSy"):
    st.warning("⚠️ Recuerda que las claves oficiales de Google AI Studio comienzan con 'AIzaSy'.")

uploaded_file = st.file_uploader(
    "Carga la captura de evidencia descargada (JPG/PNG):",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    image = Image.open(uploaded_file)
    st.image(image, caption="Evidencia Cargada", use_column_width=True)

    if st.button("🚀 Iniciar Análisis con IA"):
        with st.spinner("Analizando la evidencia con Gemini IA..."):
            # Lista de modelos compatibles en orden de preferencia
            modelos_disponibles = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            respuesta_exitosa = False

            for nombre_modelo in modelos_disponibles:
                try:
                    model = genai.GenerativeModel(nombre_modelo)
                    prompt = (
                        f"Actúa como un auditor senior QA. Analiza la imagen para el sitio {sitio_nemonico}, sector {sector_seleccionado}.\n"
                        f"Verifica el azimut teórico ({azimut_teorico}°) y tilt teórico ({tilt_teorico}°).\n"
                        f"Indica claramente si la alineación cumple con los parámetros requeridos."
                    )
                    response = model.generate_content([prompt, image])
                    st.success(f"✅ Análisis Completado (Modelo utilizado: {nombre_modelo})")
                    st.markdown("### Resultado de la Auditoría IA:")
                    st.write(response.text)
                    respuesta_exitosa = True
                    break
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "Quota" in err_msg:
                        st.error("⏳ Límites de velocidad/cuota alcanzados. Por favor espera 1 minuto antes de presionar el botón nuevamente.")
                        respuesta_exitosa = True
                        break
                    continue

            if not respuesta_exitosa:
                st.error("❌ No se pudo conectar con los modelos de Gemini. Revisa que tu API Key sea correcta y esté activa en Google AI Studio.")
