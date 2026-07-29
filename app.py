import streamlit as st

# Configuración de la página para dispositivos móviles
st.set_page_config(
    page_title="Entel QA - Target V6.5",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector Target V6.5")

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

# --- COMPONENTE HTML5 / JS INTEGRADO V6.5 CON MIRA Y TARGET ---
js_v65_engine = f"""
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
        📡 ACTIVAR CÁMARA Y MIRA TARGET V6.5
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
                declinacionCalculadaGPS = calcularDeclinacionAproximada(lat, lon);
                lblDecGps.innerText = (declinacionCalculadaGPS > 0 ? "+" : "") + declinacionCalculadaGPS + "°";
            }}, (err) => {{
                lblDecGps.innerText = "Std (-4.5°)";
                declinacionCalculadaGPS = -4.5;
            }});
        }} else {{
            lblDecGps.innerText = "Sin GPS (-4.5°)";
            declinacionCalculadaGPS = -4.5;
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
        // Escalado: 1 grado de desviación = 5 píxeles en pantalla
        const escalaPx = 5;
        let posX = cX + (desvAz * escalaPx);
        let posY = cY + (desvTlt * escalaPx);

        // Clampear para no salir de la pantalla de la cámara
        posX = Math.max(15, Math.min(w - 15, posX));
        posY = Math.max(15, Math.min(h - 15, posY));

        // Dibujar Punto Móvil (Target Dot)
        oCtx.beginPath();
        oCtx.arc(posX, posY, 10, 0, 2 * Math.PI);
        oCtx.fillStyle = estaConforme ? "#22c55e" : "#facc15";
        oCtx.fill();
        oCtx.lineWidth = 2;
        oCtx.strokeStyle = "#ffffff";
        oCtx.stroke();

        // Línea conector entre centro y punto
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
            // Pedimos al navegador la resolución más alta posible
            const stream = await navigator.mediaDevices.getUserMedia({{
                video: {{ 
                    facingMode: "environment",
                    width: {{ ideal: 1920, max: 3840 }},
                    height: {{ ideal: 1080, max: 2160 }}
                }},
                audio: false
            }});
            
            // Configurar el video
            video.srcObject = stream;
            
            // Ajustamos la calidad interna de reproducción
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

        // 3. Estampado superior (Identificación del sitio)
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(10 * esc, 10 * esc, 380 * esc, 28 * esc);
        
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold " + Math.floor(12 * esc) + "px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(tIdentificacion + " (Dec GPS: " + declinacionCalculadaGPS + "°)", 18 * esc, 28 * esc);
        
        // 4. Panel inferior de datos (Reorganizado en filas independientes)
        const altoCaja = 135 * esc;
        const yBase = canvas.height - altoCaja;

        // Fondo oscuro translúcido
        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        ctx.fillRect(0, yBase, canvas.width, altoCaja);
        
        // Título de la evidencia
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold " + Math.floor(14 * esc) + "px sans-serif";
        ctx.fillText("EVIDENCIA QA - TARGET V6.5", 15 * esc, yBase + (24 * esc));
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        // Lecturas de Azimut y Tilt en filas separadas
        ctx.font = Math.floor(12.5 * esc) + "px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("AZIMUT VERD: " + azReal + "° (Teórico: " + tAzimut + "°)", 15 * esc, yBase + (48 * esc));
        ctx.fillText("TILT REAL: " + tltReal + "° (Teórico: " + tTilt + "°)", 15 * esc, yBase + (70 * esc));
        
        // 5. Banner de Estado destacado (En su propia franja inferior para 0% traslape)
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

st.components.v1.html(js_v65_engine, height=880, scrolling=False)
st.caption("Desarrollado para Procesos de Calidad Entel - V6.5 Target Alignment System.")
