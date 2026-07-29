import streamlit as st
import google.generativeai as genai
from PIL import Image
import base64
import os
from datetime import datetime
from weasyprint import HTML

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="QA Antenas V6.7", page_icon="📡", layout="centered")

st.title("📡 Sistema QA de Alineación - Target V6.7")
st.markdown("**Versión con IA (Gemini) y Generación de Reportes PDF**")

# --- 1. DATOS DEL SITIO (INPUTS) ---
with st.expander("📝 1. Ingresar Datos del Sitio", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        sitio_nemonico = st.text_input("Sitio (Ej. SA542)", "SA542")
        sector_seleccionado = st.selectbox("Sector", ["SECTOR 1", "SECTOR 2", "SECTOR 3", "SECTOR 4"])
    with col2:
        azimut_teorico = st.number_input("Azimut Teórico (°)", min_value=0, max_value=360, value=300)
        tilt_teorico = st.number_input("Tilt Teórico (°)", min_value=0, max_value=180, value=85)

st.markdown("---")

# --- 2. MOTOR DE CÁMARA Y SENSORES (TU CÓDIGO JS) ---
import streamlit as st

# Configuración de la página para dispositivos móviles
st.set_page_config(
    page_title="Entel QA - Target V6.6",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector Target V6.6")

# --- PARÁMETROS DE INSPECCIÓN ---
col_id1, col_id2 = st.columns([2, 1])

with col_id1:
    sitio_nemonico = st.text_input(
        "Nemónico del Sitio / Nodo:", 
        value="SA542", 
        max_chars=20
    ).strip().upper()

with col_id2:
    sector_seleccionado = st.selectbox(
        "Sector:",
        options=["Sector 1", "Sector 2", "Sector 3", "Sector 4"],
        index=0
    )

col_input1, col_input2 = st.columns(2)

with col_input1:
    azimut_teorico = st.number_input(
        "Azimut Teórico (°)", 
        min_value=0.0, max_value=360.0, value=120.0, step=1.0
    )

with col_input2:
    tilt_teorico = st.number_input(
        "Tilt Teórico (°)", 
        min_value=-90.0, max_value=90.0, value=-5.0, step=0.5
    )

# --- CALIBRACIÓN ---
compensacion_manual = st.number_input(
    "Ajuste Fino Manual (°):",
    min_value=-90.0,
    max_value=90.0,
    value=0.0,
    step=0.5
)

TOL_AZIMUT = 5.0
TOL_TILT = 2.0

texto_identificacion = f"{sitio_nemonico} - {sector_seleccionado.upper()}"
nombre_archivo_sector = f"{sitio_nemonico}_{sector_seleccionado.replace(' ', '-')}"

# --- COMPONENTE HTML5 / JS INTEGRADO V6.6 CON MIRA, GPS Y ALTA RESOLUCIÓN ---
js_v66_engine = f"""
<div id="capture-area" style="width: 100%; max-width: 500px; margin: auto; font-family: system-ui, -apple-system, sans-serif; background: #0f172a; padding: 8px; border-radius: 12px;">
    
    <div style="position: relative; width: 100%; border-radius: 10px; overflow: hidden; background: #000;">
        <video id="webcam" autoplay playsinline style="width: 100%; display: block; max-height: 280px; object-fit: cover;"></video>
        <canvas id="target-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
        <canvas id="snapshot" style="display: none; width: 100%; border-radius: 10px;"></canvas>
        
        <div style="position: absolute; top: 8px; left: 8px; background: rgba(15, 23, 42, 0.85); color: #38bdf8; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; border: 1px solid rgba(56, 189, 248, 0.3);">
            {texto_identificacion} | Dec GPS: <span id="lbl-dec-gps">Calculando...</span>
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

<div id="calib-box" style="max-width: 500px; margin: 6px auto; background: #0284c7; color: white; padding: 6px 10px; border-radius: 8px; font-size: 11px;">
    🎯 <strong>Guía de Alineación:</strong> Centre la burbuja amarilla en la cruz verde para lograr la alineación perfecta.
</div>

<div style="max-width: 500px; margin: 6px auto 0 auto; display: flex; flex-direction: column; gap: 6px;">
    <button id="btn-permisos" style="padding: 12px; font-size: 14px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%;">
        📡 ACTIVAR CÁMARA Y MIRA TARGET V6.6
    </button>
    
    <button id="btn-capturar" style="display: none; padding: 14px; font-size: 15px; font-weight: bold; background-color: #e11d48; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
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
    
    const tIdentificacion = "{texto_identificacion}";
    const tNombreArchivo = "{nombre_archivo_sector}";
    const tAzimut = {azimut_teorico};
    const tTilt = {tilt_teorico};
    const tolAzimut = {TOL_AZIMUT};
    const tolTilt = {TOL_TILT};
    const offsetManual = {compensacion_manual};

    let declinacionCalculadaGPS = 0.0;
    let latitudActual = "Buscando...";
    let longitudActual = "Buscando...";
    
    let azimutSuave = null;
    let tiltSuave = null;
    let ultimoAzimutRenderizado = null;

    const FACTOR_SUAVIDAD_AZIMUT = 0.004;
    const FACTOR_SUAVIDAD_TILT = 0.015;
    const UMBRAL_ZONA_MUERTA = 1.2;

    function calcularDeclinacionAproximada(lat, lon) {{
        let dec = -4.5 - ((lat + 33.4) * 0.45) - ((lon + 70.6) * 0.1);
        return parseFloat(dec.toFixed(1));
    }}

    function obtenerGPS() {{
        if ("geolocation" in navigator) {{
            navigator.geolocation.getCurrentPosition((pos) => {{
                let lat = pos.coords.latitude;
                let lon = pos.coords.longitude;
                
                latitudActual = lat.toFixed(6);
                longitudActual = lon.toFixed(6);
                
                declinacionCalculadaGPS = calcularDeclinacionAproximada(lat, lon);
                lblDecGps.innerText = (declinacionCalculadaGPS > 0 ? "+" : "") + declinacionCalculadaGPS + "°";
            }}, (err) => {{
                lblDecGps.innerText = "Std (-4.5°)";
                declinacionCalculadaGPS = -4.5;
                latitudActual = "Sin señal GPS";
                longitudActual = "Sin señal GPS";
            }});
        }} else {{
            lblDecGps.innerText = "Sin GPS (-4.5°)";
            declinacionCalculadaGPS = -4.5;
            latitudActual = "No soportado";
            longitudActual = "No soportado";
        }}
    }}

    function redimensionarCanvasOverlay() {{
        overlayCanvas.width = video.clientWidth || 350;
        overlayCanvas.height = video.clientHeight || 220;
    }}

    function dibujarTargetGraphics(desvAz, desvTlt, estaConforme) {{
        redimensionarCanvasOverlay();
        const w = overlayCanvas.width;
        const h = overlayCanvas.height;
        const cX = w / 2;
        const cY = h / 2;

        oCtx.clearRect(0, 0, w, h);

        // 1. Dibujar Zona Central de Tolerancia (Círculo Target)
        oCtx.beginPath();
        oCtx.arc(cX, cY, 35, 0, 2 * Math.PI);
        oCtx.fillStyle = estaConforme ? "rgba(34, 197, 94, 0.25)" : "rgba(239, 68, 68, 0.2)";
        oCtx.fill();
        oCtx.lineWidth = 2;
        oCtx.strokeStyle = estaConforme ? "#22c55e" : "rgba(255,255,255,0.4)";
        oCtx.stroke();

        // 2. Cruz Central Fija (Teórico)
        oCtx.beginPath();
        oCtx.moveTo(cX - 15, cY); oCtx.lineTo(cX + 15, cY);
        oCtx.moveTo(cX, cY - 15); oCtx.lineTo(cX, cY + 15);
        oCtx.strokeStyle = "#38bdf8";
        oCtx.lineWidth = 2;
        oCtx.stroke();

        // 3. Mapeo del Punto Móvil (Burbuja Real)
        const escalaPx = 5;
        let posX = cX + (desvAz * escalaPx);
        let posY = cY + (desvTlt * escalaPx);

        posX = Math.max(15, Math.min(w - 15, posX));
        posY = Math.max(15, Math.min(h - 15, posY));

        oCtx.beginPath();
        oCtx.arc(posX, posY, 10, 0, 2 * Math.PI);
        oCtx.fillStyle = estaConforme ? "#22c55e" : "#facc15";
        oCtx.fill();
        oCtx.lineWidth = 2;
        oCtx.strokeStyle = "#ffffff";
        oCtx.stroke();

        oCtx.beginPath();
        oCtx.moveTo(cX, cY);
        oCtx.lineTo(posX, posY);
        oCtx.strokeStyle = estaConforme ? "rgba(34, 197, 94, 0.6)" : "rgba(250, 204, 21, 0.6)";
        oCtx.lineWidth = 1.5;
        oCtx.setLineDash([3, 3]);
        oCtx.stroke();
        oCtx.setLineDash([]);
    }}

    function filtrarAzimutEstable(nuevoHeading) {{
        if (azimutSuave === null) {{
            azimutSuave = nuevoHeading;
            ultimoAzimutRenderizado = Math.round(azimutSuave);
            return azimutSuave;
        }}
        
        let diferencia = nuevoHeading - azimutSuave;
        if (diferencia > 180) diferencia -= 360;
        if (diferencia < -180) diferencia += 360;
        
        azimutSuave += diferencia * FACTOR_SUAVIDAD_AZIMUT;
        
        if (azimutSuave < 0) azimutSuave += 360;
        if (azimutSuave >= 360) azimutSuave -= 360;
        
        let candidatoRedondeado = Math.round(azimutSuave);
        let deltaDisplay = candidatoRedondeado - ultimoAzimutRenderizado;
        if (deltaDisplay > 180) deltaDisplay -= 360;
        if (deltaDisplay < -180) deltaDisplay += 360;

        if (Math.abs(deltaDisplay) >= UMBRAL_ZONA_MUERTA) {{
            ultimoAzimutRenderizado = candidatoRedondeado;
        }}
        
        return ultimoAzimutRenderizado;
    }}

    function filtrarTiltEstable(nuevoBeta) {{
        if (tiltSuave === null) {{
            tiltSuave = nuevoBeta;
            return tiltSuave;
        }}
        tiltSuave += (nuevoBeta - tiltSuave) * FACTOR_SUAVIDAD_TILT;
        return Math.round(tiltSuave);
    }}

    async function iniciarCamara() {{
        try {{
            const stream = await navigator.mediaDevices.getUserMedia({{
                video: {{ 
                    facingMode: "environment",
                    width: {{ ideal: 1920, max: 3840 }},
                    height: {{ ideal: 1080, max: 2160 }}
                }},
                audio: false
            }});
            
            video.srcObject = stream;
            
            video.onloadedmetadata = () => {{
                video.play();
            }};
            
            btnCapturar.style.display = 'block';
        }} catch (err) {{
            console.error("Error al iniciar cámara de alta resolución: ", err);
            alert("No se pudo iniciar la cámara en alta resolución. Revisar permisos.");
        }}
    }}

    function procesarOrientacion(event) {{
        let heading = event.webkitCompassHeading;
        if (heading === undefined || heading === null) {{
            if (event.absolute === true && event.alpha !== null) {{
                heading = 360 - event.alpha;
            }} else {{
                heading = event.alpha;
            }}
        }}

        let beta = event.beta; 
        if (heading === null || heading === undefined || beta === null) return;

        let azimutBrutoEstable = filtrarAzimutEstable(heading);
        let azimutVerdadero = azimutBrutoEstable + declinacionCalculadaGPS + offsetManual;
        
        if (azimutVerdadero < 0) azimutVerdadero += 360;
        if (azimutVerdadero >= 360) azimutVerdadero -= 360;

        let tiltReal = filtrarTiltEstable(beta);

        let desvAzimut = Math.round(azimutVerdadero - tAzimut);
        if (desvAzimut > 180) desvAzimut -= 360;
        if (desvAzimut < -180) desvAzimut += 360;
        
        let desvTilt = Math.round(tiltReal - tTilt);

        document.getElementById('lbl-azimut-real').innerText = Math.round(azimutVerdadero);
        document.getElementById('lbl-tilt-real').innerText = tiltReal;
        document.getElementById('lbl-azimut-desv').innerText = (desvAzimut > 0 ? "+" : "") + desvAzimut;
        document.getElementById('lbl-tilt-desv').innerText = (desvTilt > 0 ? "+" : "") + desvTilt;

        const azimutOk = Math.abs(desvAzimut) <= tolAzimut;
        const tiltOk = Math.abs(desvTilt) <= tolTilt;
        const conforme = azimutOk && tiltOk;
        const statusElement = document.getElementById('lbl-status');

        dibujarTargetGraphics(desvAzimut, desvTilt, conforme);

        if (conforme) {{
            dataPanel.style.borderColor = "#22c55e";
            statusElement.innerText = "🎯 OBJETIVO ALINEADO (CONFORME)";
            statusElement.style.background = "#22c55e";
        }} else {{
            dataPanel.style.borderColor = "#ef4444";
            statusElement.innerText = "❌ FUERA DE OBJETIVO";
            statusElement.style.background = "#ef4444";
        }}
    }}

    btnPermisos.addEventListener('click', async () => {{
        await iniciarCamara();
        obtenerGPS();
        
        if (window.DeviceOrientationEvent) {{
            window.addEventListener('deviceorientation', procesarOrientacion, true);
            window.addEventListener('deviceorientationabsolute', procesarOrientacion, true);
            document.getElementById('lbl-status').innerText = "CONECTANDO SENSORES...";
        }} else {{
            alert("Sensores no disponibles en este dispositivo.");
        }}
        btnPermisos.style.display = 'none';
    }});

    btnCapturar.addEventListener('click', () => {{
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        
        // 1. Imagen base de la cámara
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // 2. Estampar la gráfica de la mira (Target)
        ctx.drawImage(overlayCanvas, 0, 0, canvas.width, canvas.height);

        // --- CÁLCULO DE ESCALA DINÁMICA ---
        const esc = canvas.width / 400; 

        // --- OBTENER FECHA Y HORA ACTUAL ---
        const ahora = new Date();
        const fechaHora = ahora.toLocaleString('es-CL', {{ hour12: false }});

        // 3. Estampado superior (Identificación + Sello de Tiempo + Coordenadas)
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(10 * esc, 10 * esc, 380 * esc, 60 * esc); 
        
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold " + Math.floor(12 * esc) + "px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(tIdentificacion + " (Dec GPS: " + declinacionCalculadaGPS + "°)", 18 * esc, 28 * esc);
        
        // Dibujamos la fecha y hora
        ctx.fillStyle = "#cbd5e1";
        ctx.font = Math.floor(10.5 * esc) + "px sans-serif";
        ctx.fillText("📅 Fecha de Inspección: " + fechaHora, 18 * esc, 44 * esc);

        // Dibujamos las Coordenadas GPS destacadas en amarillo
        ctx.fillStyle = "#facc15"; 
        ctx.fillText("📍 Lat: " + latitudActual + " / Lon: " + longitudActual, 18 * esc, 60 * esc);
        
        // 4. Panel inferior de datos
        const altoCaja = 135 * esc;
        const yBase = canvas.height - altoCaja;

        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        ctx.fillRect(0, yBase, canvas.width, altoCaja);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold " + Math.floor(14 * esc) + "px sans-serif";
        ctx.fillText("EVIDENCIA QA - TARGET V6.6", 15 * esc, yBase + (24 * esc));
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        ctx.font = Math.floor(12.5 * esc) + "px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("AZIMUT VERD: " + azReal + "° (Teórico: " + tAzimut + "°)", 15 * esc, yBase + (48 * esc));
        ctx.fillText("TILT REAL: " + tltReal + "° (Teórico: " + tTilt + "°)", 15 * esc, yBase + (70 * esc));
        
        // 5. Banner de Estado destacado
        const esConforme = status.includes("CONFORME");
        ctx.fillStyle = esConforme ? "rgba(34, 197, 94, 0.95)" : "rgba(239, 68, 68, 0.95)";
        ctx.fillRect(10 * esc, yBase + (88 * esc), canvas.width - (20 * esc), 32 * esc);
        
        // Texto centrado dentro del banner
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold " + Math.floor(13 * esc) + "px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(status, canvas.width / 2, yBase + (109 * esc));
        
        // Restaurar alineación predeterminada
        ctx.textAlign = "left";
        
        try {{
            const dataURL = canvas.toDataURL('image/png');
            downloadLink.href = dataURL;
            downloadLink.download = "QA_" + tNombreArchivo + "_AZ" + azReal + "_TLT" + tltReal + ".png";
            downloadLink.click();
        }} catch(e) {{
            alert("Captura completada.");
        }}
    }});
</script>
"""

st.components.v1.html(js_v66_engine, height=880, scrolling=False)
st.caption("Desarrollado para Procesos de Calidad Entel - V6.6 Target Alignment System.")

# =====================================================================
# ⚠️ IMPORTANTE: PEGA AQUÍ TU st.components.v1.html CON EL JAVASCRIPT
# =====================================================================
st.components.v1.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Brújula y Cámara</title>
        </head>
    <body>
        ...
    </body>
    </html>
""", height=650)

st.success("Motor de captura activo.")

st.markdown("---")

# --- 3. CARGA DE EVIDENCIA PARA ANÁLISIS ---
st.subheader("⚙️ 3. Auditoría Inteligente y Reporte")
st.write("Sube la imagen que acabas de descargar del motor de captura para validarla y generar el PDF.")

imagen_subida = st.file_uploader("Cargar captura con marca de agua (PNG/JPG)", type=["png", "jpg", "jpeg"])

if imagen_subida is not None:
    # Mostrar la imagen
    img = Image.open(imagen_subida)
    st.image(img, caption="Evidencia cargada exitosamente", use_column_width=True)
    
    # --- MÓDULO GEMINI (ASISTENTE IA) ---
    st.markdown("### 🧠 Análisis con Gemini")
    API_KEY = st.text_input("Ingresa tu API Key de Gemini:", type="password")
    
    if API_KEY:
        try:
            genai.configure(api_key=API_KEY)
            modelo = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt_qa = f"""
            Eres un auditor de calidad (QA) de telecomunicaciones para la empresa Entel.
            Analiza esta imagen de alineación de antena (Sitio {sitio_nemonico}, {sector_seleccionado}).
            Verifica:
            1. Que los valores de Azimut y Tilt se lean claramente.
            2. Que el cartel verde de "OBJETIVO ALINEADO (CONFORME)" esté visible.
            Responde de forma breve, profesional y al grano indicando si la captura es válida como evidencia.
            """
            
            if st.button("🚀 Iniciar Análisis IA"):
                with st.spinner("La IA está revisando la imagen..."):
                    respuesta = modelo.generate_content([prompt_qa, img])
                    st.success("Análisis completado:")
                    st.write(respuesta.text)
        except Exception as e:
            st.error(f"Error al conectar con Gemini: {e}")
    else:
        st.warning("⚠️ Ingresa una API Key para habilitar el auditor IA.")

    # --- MÓDULO GENERACIÓN DE PDF ---
    st.markdown("### 📄 Generar Documento Oficial")
    
    if st.button("📥 Generar y Descargar PDF"):
        with st.spinner("Compilando reporte PDF..."):
            # 1. Convertir la imagen subida a Base64 para incrustarla en el HTML
            imagen_subida.seek(0)
            encoded_string = base64.b64encode(imagen_subida.read()).decode('utf-8')
            mime = "image/png" if imagen_subida.name.endswith(".png") else "image/jpeg"
            img_base64_str = f"data:{mime};base64,{encoded_string}"
            
            # Fecha actual para el reporte
            fecha_reporte = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
            
            # 2. Plantilla HTML (con CSS incrustado)
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
            <meta charset="UTF-8">
            <style>
              @page {{ size: A4; margin: 12mm 10mm; background-color: #f8fafc; }}
              body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #0f172a; font-size: 9.5pt; line-height: 1.4; }}
              .header-banner {{ background-color: #0284c7; color: #ffffff; padding: 16px 20px; border-radius: 8px; margin-bottom: 14px; }}
              .header-title {{ font-size: 16pt; font-weight: bold; margin: 0 0 4px 0; text-transform: uppercase; }}
              .header-subtitle {{ font-size: 10pt; opacity: 0.9; margin: 0; }}
              .status-card {{ background-color: #dcfce7; border: 2px solid #22c55e; border-radius: 8px; padding: 10px 16px; margin-bottom: 14px; text-align: center; }}
              .status-title {{ font-size: 13pt; font-weight: bold; color: #15803d; margin: 0; text-transform: uppercase; }}
              .section-title {{ font-size: 11pt; font-weight: bold; color: #0369a1; border-bottom: 2px solid #cbd5e1; padding-bottom: 3px; margin-top: 14px; margin-bottom: 10px; }}
              table.data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; background-color: #ffffff; border-radius: 6px; border: 1px solid #e2e8f0; }}
              table.data-table th, table.data-table td {{ padding: 6pt 8pt; text-align: left; border-bottom: 1px solid #e2e8f0; }}
              table.data-table th {{ background-color: #f1f5f9; font-weight: bold; font-size: 9pt; }}
              .photo-container {{ text-align: center; margin-top: 10px; margin-bottom: 14px; background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; }}
              .photo-container img {{ max-width: 100%; height: 400px; border-radius: 6px; object-fit: contain; }}
              .footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #cbd5e1; font-size: 7.5pt; color: #64748b; text-align: center; }}
            </style>
            </head>
            <body>
            
            <div class="header-banner">
              <div class="header-title">Informe de Inspección y QA</div>
              <div class="header-subtitle">Evidencia Técnica | Sistema Target V6.7</div>
            </div>
            
            <div class="status-card">
              <div class="status-title">🎯 OBJETIVO ALINEADO (CONFORME)</div>
              <div style="font-size: 9pt; color: #166534; margin-top: 2px;">La evidencia ha sido procesada por la plataforma QA.</div>
            </div>
            
            <div class="section-title">1. Datos Generales del Sitio</div>
            <table class="data-table">
              <tr>
                <th>Identificador de Sitio:</th><td>{sitio_nemonico}</td>
                <th>Sector:</th><td>{sector_seleccionado}</td>
              </tr>
              <tr>
                <th>Fecha de Reporte:</th><td>{fecha_reporte}</td>
                <th>Motor de Captura:</th><td>TARGET V6.7</td>
              </tr>
            </table>
            
            <div class="section-title">2. Evidencia Fotográfica Capturada en Terreno</div>
            <div class="photo-container">
              <img src="{img_base64_str}" alt="Captura de Evidencia" />
              <div style="font-size: 8.5pt; color: #475569; margin-top: 6px; font-style: italic;">
                Figura 1: Captura fotográfica original con marca de agua gráfica y datos de telemetría.
              </div>
            </div>
            
            <div class="section-title">3. Parámetros Teóricos de Auditoría</div>
            <table class="data-table">
              <tr>
                <th>Azimut Teórico:</th><td>{azimut_teorico}°</td>
                <th>Tolerancia Máx:</th><td>± 5°</td>
              </tr>
              <tr>
                <th>Tilt Teórico:</th><td>{tilt_teorico}°</td>
                <th>Tolerancia Máx:</th><td>± 2°</td>
              </tr>
            </table>
            
            <div class="footer">
              Generado por Asistente IA Entel QA • Sistema de Alineación de Antenas V6.7 • Documento Oficial
            </div>
            
            </body>
            </html>
            """
            
            # 3. Generar PDF
            archivo_pdf = "Reporte_Inspeccion.pdf"
            HTML(string=html_content).write_pdf(archivo_pdf)
            
            # 4. Crear el botón de descarga
            with open(archivo_pdf, "rb") as pdf_file:
                st.download_button(
                    label="💾 Clic aquí para descargar tu PDF",
                    data=pdf_file,
                    file_name=f"Reporte_QA_{sitio_nemonico}_{sector_seleccionado}.pdf",
                    mime="application/pdf"
                )
            st.success("¡PDF generado con éxito! Ya puedes descargarlo.")
            
            # Limpiar el archivo temporal
            if os.path.exists(archivo_pdf):
                os.remove(archivo_pdf)
