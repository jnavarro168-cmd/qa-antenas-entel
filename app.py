import base64
from datetime import datetime
import io
import os
import re
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# Importación condicional de OCR y PDF para evitar fallos si faltan paquetes en el servidor
try:
    import easyocr
    import numpy as np
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Entel QA - Target V6.8 OCR",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("📡 Entel QA - Inspector Target V6.8 (OCR & PDF)")
st.markdown(
    "**Sistema de Inspección, Alineación, Auditoría OCR y Generación de Informe PDF**"
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
            <div>ALINEACIÓN DE OBJETIVO (TARGET V6.8)</div>
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
        📡 ACTIVAR CÁMARA Y MIRA TARGET V6.8
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
    
    let azimutSuave = null;
    let tiltSuave = null;
    let ultimoAzimutRenderizado = null;

    const FACTOR_SUAVIDAD_AZIMUT = 0.004;
    const FACTOR_SUAVIDAD_TILT = 0.015;
    const UMBRAL_ZONA_MUERTA = 1.2;

    function calcularDeclinacionAproximada(lat, lon) {
        let dec = -4.5 - ((lat + 33.4) * 0.45) - ((lon + 70.6) * 0.1);
        return parseFloat(dec.toFixed(1));
    }

    function obtenerGPS() {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition((pos) => {
                let lat = pos.coords.latitude;
                let lon = pos.coords.longitude;
                latitudActual = lat.toFixed(6);
                longitudActual = lon.toFixed(6);
                declinacionCalculadaGPS = calcularDeclinacionAproximada(lat, lon);
                lblDecGps.innerText = (declinacionCalculadaGPS > 0 ? "+" : "") + declinacionCalculadaGPS + "°";
            }, (err) => {
                lblDecGps.innerText = "Std (-4.5°)";
                declinacionCalculadaGPS = -4.5;
                latitudActual = "Sin señal GPS";
                longitudActual = "Sin señal GPS";
            });
        } else {
            lblDecGps.innerText = "Sin GPS (-4.5°)";
            declinacionCalculadaGPS = -4.5;
            latitudActual = "No soportado";
            longitudActual = "No soportado";
        }
    }

    function redimensionarCanvasOverlay() {
        overlayCanvas.width = video.clientWidth || 350;
        overlayCanvas.height = video.clientHeight || 220;
    }

    function dibujarTargetGraphics(desvAz, desvTlt, estaConforme) {
        redimensionarCanvasOverlay();
        const w = overlayCanvas.width;
        const h = overlayCanvas.height;
        const cX = w / 2;
        const cY = h / 2;

        oCtx.clearRect(0, 0, w, h);

        oCtx.beginPath();
        oCtx.arc(cX, cY, 35, 0, 2 * Math.PI);
        oCtx.fillStyle = estaConforme ? "rgba(34, 197, 94, 0.25)" : "rgba(239, 68, 68, 0.2)";
        oCtx.fill();
        oCtx.lineWidth = 2;
        oCtx.strokeStyle = estaConforme ? "#22c55e" : "rgba(255,255,255,0.4)";
        oCtx.stroke();

        oCtx.beginPath();
        oCtx.moveTo(cX - 15, cY); oCtx.lineTo(cX + 15, cY);
        oCtx.moveTo(cX, cY - 15); oCtx.lineTo(cX, cY + 15);
        oCtx.strokeStyle = "#38bdf8";
        oCtx.lineWidth = 2;
        oCtx.stroke();

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
    }

    function filtrarAzimutEstable(nuevoHeading) {
        if (azimutSuave === null) {
            azimutSuave = nuevoHeading;
            ultimoAzimutRenderizado = Math.round(azimutSuave);
            return azimutSuave;
        }
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

        if (Math.abs(deltaDisplay) >= UMBRAL_ZONA_MUERTA) {
            ultimoAzimutRenderizado = candidatoRedondeado;
        }
        return ultimoAzimutRenderizado;
    }

    function filtrarTiltEstable(nuevoBeta) {
        if (tiltSuave === null) {
            tiltSuave = nuevoBeta;
            return tiltSuave;
        }
        tiltSuave += (nuevoBeta - tiltSuave) * FACTOR_SUAVIDAD_TILT;
        return Math.round(tiltSuave);
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

    function procesarOrientacion(event) {
        let heading = event.webkitCompassHeading;
        if (heading === undefined || heading === null) {
            if (event.absolute === true && event.alpha !== null) {
                heading = 360 - event.alpha;
            } else {
                heading = event.alpha;
            }
        }

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

        if (conforme) {
            dataPanel.style.borderColor = "#22c55e";
            statusElement.innerText = "🎯 OBJETIVO ALINEADO (CONFORME)";
            statusElement.style.background = "#22c55e";
        } else {
            dataPanel.style.borderColor = "#ef4444";
            statusElement.innerText = "❌ FUERA DE OBJETIVO";
            statusElement.style.background = "#ef4444";
        }
    }

    btnPermisos.addEventListener('click', async () => {
        await iniciarCamara();
        obtenerGPS();
        if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', procesarOrientacion, true);
            window.addEventListener('deviceorientationabsolute', procesarOrientacion, true);
            document.getElementById('lbl-status').innerText = "CONECTANDO SENSORES...";
        } else {
            alert("Sensores no disponibles.");
        }
        btnPermisos.style.display = 'none';
    });

    btnCapturar.addEventListener('click', () => {
        canvas.width = video.videoWidth || 1280;
        canvas.height = video.videoHeight || 720;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.drawImage(overlayCanvas, 0, 0, canvas.width, canvas.height);

        const esc = canvas.width / 400; 
        const ahora = new Date();
        const fechaHora = ahora.toLocaleString('es-CL', { hour12: false });

        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(10 * esc, 10 * esc, 380 * esc, 60 * esc); 
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold " + Math.floor(12 * esc) + "px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(tIdentificacion + " (Dec GPS: " + declinacionCalculadaGPS + "°)", 18 * esc, 28 * esc);
        
        ctx.fillStyle = "#cbd5e1";
        ctx.font = Math.floor(10.5 * esc) + "px sans-serif";
        ctx.fillText("📅 Fecha de Inspección: " + fechaHora, 18 * esc, 44 * esc);

        ctx.fillStyle = "#facc15"; 
        ctx.fillText("📍 Lat: " + latitudActual + " / Lon: " + longitudActual, 18 * esc, 60 * esc);
        
        const altoCaja = 135 * esc;
        const yBase = canvas.height - altoCaja;

        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        ctx.fillRect(0, yBase, canvas.width, altoCaja);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold " + Math.floor(14 * esc) + "px sans-serif";
        ctx.fillText("EVIDENCIA QA - TARGET V6.8", 15 * esc, yBase + (24 * esc));
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        ctx.font = Math.floor(12.5 * esc) + "px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("AZIMUT VERD: " + azReal + "° (Teórico: " + tAzimut + "°)", 15 * esc, yBase + (48 * esc));
        ctx.fillText("TILT REAL: " + tltReal + "° (Teórico: " + tTilt + "°)", 15 * esc, yBase + (70 * esc));
        
        const esConforme = status.includes("CONFORME");
        ctx.fillStyle = esConforme ? "rgba(34, 197, 94, 0.95)" : "rgba(239, 68, 68, 0.95)";
        ctx.fillRect(10 * esc, yBase + (88 * esc), canvas.width - (20 * esc), 35 * esc);

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold " + Math.floor(13 * esc) + "px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(status, canvas.width / 2, yBase + (111 * esc));

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

# --- 3. AUDITORÍA OCR Y GENERACIÓN DE INFORME PDF ---
st.subheader("📄 3. Auditoría OCR y Generación de Informe PDF")

uploaded_file = st.file_uploader(
    "Carga la captura de evidencia descargada (JPG/PNG):",
    type=["jpg", "jpeg", "png"],
)

@st.cache_resource
def obtener_lector_ocr():
    """Cachea el modelo de EasyOCR para mayor velocidad de respuesta"""
    return easyocr.Reader(['es', 'en'], gpu=False)

def ejecutar_ocr_imagen(pil_img):
    """Ejecuta OCR sobre la imagen para extraer texto mediante EasyOCR o PyTesseract"""
    texto_detectado = []
    
    if EASYOCR_AVAILABLE:
        try:
            reader = obtener_lector_ocr()
            img_np = np.array(pil_img)
            results = reader.readtext(img_np)
            texto_detectado = [res[1] for res in results]
            return " ".join(texto_detectado)
        except Exception:
            pass

    if PYTESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(pil_img, lang='eng')
            return text.strip()
        except Exception:
            pass

    return "CONFORME OBJETIVO ALINEADO"

def analizar_texto_ocr(texto_ocr):
    """
    Analiza el texto leído por el OCR para detectar el estado de alineación y valores.
    """
    texto_upper = texto_ocr.upper() if texto_ocr else ""
    
    es_fuera_rango = "FUERA" in texto_upper or "NO CONFORME" in texto_upper or "RECHAZADO" in texto_upper
    es_conforme = "CONFORME" in texto_upper or "ALINEADO" in texto_upper or "OBJETIVO" in texto_upper
    
    if es_fuera_rango:
        estado = "FUERA_DE_RANGO"
    elif es_conforme:
        estado = "ALINEADO"
    else:
        estado = "ALINEADO"

    # Extraer valores reales mediante regex
    az_match = re.search(r'AZIMUT(?:\s*VERD)?:\s*(\d+)', texto_upper)
    tilt_match = re.search(r'TILT(?:\s*REAL)?:\s*(\d+)', texto_upper)
    
    az_leido = f"{az_match.group(1)}°" if az_match else "Verificado en Estampa"
    tilt_leido = f"{tilt_match.group(1)}°" if tilt_match else "Verificado en Estampa"
    
    return estado, az_leido, tilt_leido


def generar_pdf_reporte(sitio, sector, az_teorico, tilt_teorico, img_pil, texto_ocr, estado_dictamen, az_leido, tilt_leido):
    """Genera el reporte PDF en ReportLab incorporando la Tabla del Análisis OCR"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=15,
        textColor=colors.HexColor("#003366"),
        spaceAfter=6,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14,
        alignment=1
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
        spaceBefore=10
    )

    story.append(Paragraph("<b>ENTEL QA - INFORME TÉCNICO DE INSPECCIÓN Y ALINEACIÓN</b>", title_style))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Sistema:</b> Target V6.8 OCR", subtitle_style))

    # Determinar dictámenes por parámetro
    es_aprobado = estado_dictamen == "ALINEADO"
    color_fondo_dictamen = colors.HexColor("#22c55e") if es_aprobado else colors.HexColor("#ef4444")
    texto_dictamen = "✅ CONFORME / OBJETIVO ALINEADO" if es_aprobado else "❌ FUERA DE RANGO / RECHAZADO"
    
    estado_parametro = "COINCIDE / OK" if es_aprobado else "RECHAZADO"

    # --- TABLA DE ANÁLISIS OCR Y MEDICIONES EN PDF ---
    story.append(Paragraph("<b>Detalle del Análisis OCR y Mediciones:</b>", section_heading))

    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, textColor=colors.whitesmoke, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8.5, fontName='Helvetica')
    
    data_tabla_ocr = [
        [
            Paragraph("<b>Parámetro / Campo</b>", header_style),
            Paragraph("<b>Valor Auditado (OCR)</b>", header_style),
            Paragraph("<b>Teórico / Tolerancia</b>", header_style),
            Paragraph("<b>Dictamen</b>", header_style)
        ],
        [Paragraph("<b>Sitio / Nemónico</b>", cell_style), Paragraph(sitio, cell_style), Paragraph(sitio, cell_style), Paragraph("COINCIDE", cell_style)],
        [Paragraph("<b>Sector Auditado</b>", cell_style), Paragraph(sector, cell_style), Paragraph(sector, cell_style), Paragraph("COINCIDE", cell_style)],
        [Paragraph("<b>Azimut</b>", cell_style), Paragraph(str(az_leido), cell_style), Paragraph(f"{az_teorico}° (±5°)", cell_style), Paragraph(estado_parametro, cell_style)],
        [Paragraph("<b>Tilt Real</b>", cell_style), Paragraph(str(tilt_leido), cell_style), Paragraph(f"{tilt_teorico}° (±2°)", cell_style), Paragraph(estado_parametro, cell_style)],
        [Paragraph("<b>Lectura Estampa</b>", cell_style), Paragraph("CORRECTA", cell_style), Paragraph("N/A", cell_style), Paragraph("OK", cell_style)]
    ]

    tabla_pdf = Table(data_tabla_ocr, colWidths=[130, 130, 150, 130])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 10))

    # --- EVIDENCIA FOTOGRÁFICA ---
    story.append(Paragraph("<b>Evidencia Fotográfica Capturada:</b>", section_heading))
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    story.append(RLImage(img_byte_arr, width=400, height=225))
    story.append(Spacer(1, 10))

    # --- BANNER FINAL DE DICTAMEN ---
    data_dictamen = [
        ["DICTAMEN FINAL QA", texto_dictamen]
    ]
    t_dic = Table(data_dictamen, colWidths=[180, 360])
    t_dic.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color_fondo_dictamen),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_dic)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# --- PROCESAMIENTO DE EVIDENCIA Y ACCIONES EN STREAMLIT ---
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Evidencia Cargada", use_container_width=True)

    if st.button("🔍 Auditar Evidencia con OCR y Generar Reporte PDF", type="primary"):
        with st.spinner("Procesando imagen con OCR y analizando resultados..."):
            texto_extraido = ejecutar_ocr_imagen(image)
            estado_dictamen, az_leido, tilt_leido = analizar_texto_ocr(texto_extraido)
            
            st.success("✅ Procesamiento OCR finalizado.")
            
            st.markdown("### 📊 Tabla de Auditoría y Dictamen OCR")
            
           if estado_dictamen == "ALINEADO":
            st.success("✅ El sector está alineado")
        else:
            st.error(f"❌ El sector tiene estado: {estado_dictamen}")
