import streamlit as st

# Configuración de la página para dispositivos móviles
st.set_page_config(
    page_title="Entel QA - Medidor Ultra Estable V6.1",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector Profesional V6.1")
st.write("Medición de Azimut (Norte Verdadero / GPS) con Filtrado de Alta Estabilidad.")

# --- PARÁMETROS DE INSPECCIÓN ---
st.subheader("1. Identificación y Datos del Sitio")

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

# --- CALIBRACIÓN Y DECLINACIÓN ---
st.subheader("2. Ajustes Finitos de Campo")
st.caption("La app calcula la declinación magnética por GPS automáticamente. Usa este campo solo para corrección manual si lo deseas.")

compensacion_manual = st.number_input(
    "Ajuste Fino Manual (°):",
    min_value=-90.0,
    max_value=90.0,
    value=0.0,
    step=0.5,
    help="Sume o reste grados para ajustar la aguja si está muy cerca de masas metálicas."
)

TOL_AZIMUT = 5.0
TOL_TILT = 2.0

texto_identificacion = f"{sitio_nemonico} - {sector_seleccionado.upper()}"
nombre_archivo_sector = f"{sitio_nemonico}_{sector_seleccionado.replace(' ', '-')}"

# --- COMPONENTE HTML5 / JS INTEGRADO V6.1 ULTRA ESTABLE ---
js_v61_engine = f"""
<div id="capture-area" style="width: 100%; max-width: 500px; margin: auto; font-family: system-ui, -apple-system, sans-serif; background: #0f172a; padding: 12px; border-radius: 16px;">
    
    <!-- CÁMARA Y OVERLAY -->
    <div style="position: relative; width: 100%; border-radius: 12px; overflow: hidden; background: #000; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
        <video id="webcam" autoplay playsinline style="width: 100%; display: block;"></video>
        <canvas id="snapshot" style="display: none; width: 100%; border-radius: 12px;"></canvas>
        
        <!-- INSIGNIA SUPERIOR CON DATOS DE UBICACIÓN -->
        <div style="position: absolute; top: 12px; left: 12px; background: rgba(15, 23, 42, 0.85); color: #38bdf8; padding: 6px 12px; border-radius: 8px; font-weight: bold; font-size: 12px; border: 1px solid rgba(56, 189, 248, 0.3); backdrop-filter: blur(4px);">
            {texto_identificacion} | Dec GPS: <span id="lbl-dec-gps">Calculando...</span>
        </div>
        
        <div style="position: absolute; top: 20px; left: 20px; right: 20px; bottom: 20px; border: 1px dashed rgba(255,255,255,0.25); pointer-events: none; border-radius: 8px;"></div>
    </div>
    
    <!-- PANEL PRINCIPAL DE LECTURAS -->
    <div id="data-panel" style="margin-top: 12px; background: #1e293b; color: white; padding: 14px; border-radius: 12px; border: 3px solid #ef4444; transition: all 0.3s ease;">
        
        <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 6px;">
            <div>NORTE VERDADERO (GPS + FILTRO HEAVY)</div>
            <div>TOL: Az±5° | Tlt±2°</div>
        </div>

        <div style="display: flex; gap: 10px; justify-content: space-between; text-align: center;">
            <div style="flex: 1; background: #0f172a; padding: 10px; border-radius: 8px;">
                <div style="font-size: 10px; color: #38bdf8; font-weight: bold; letter-spacing: 0.5px;">AZIMUT REAL</div>
                <div style="font-size: 28px; font-weight: 800; margin: 2px 0;"><span id="lbl-azimut-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-azimut-desv">--</span>°</div>
            </div>
            
            <div style="flex: 1; background: #0f172a; padding: 10px; border-radius: 8px;">
                <div style="font-size: 10px; color: #38bdf8; font-weight: bold; letter-spacing: 0.5px;">TILT REAL</div>
                <div style="font-size: 28px; font-weight: 800; margin: 2px 0;"><span id="lbl-tilt-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-tilt-desv">--</span>°</div>
            </div>
        </div>
        
        <div id="lbl-status" style="margin-top: 10px; text-align: center; font-size: 15px; font-weight: bold; padding: 8px; border-radius: 8px; background: #ef4444; letter-spacing: 0.5px;">
            INICIALIZANDO SENSORES...
        </div>
    </div>
</div>

<!-- INSTRUCCIÓN DE CALIBRACIÓN DE SENSOR -->
<div id="calib-box" style="max-width: 500px; margin: 10px auto; background: #0284c7; color: white; padding: 10px 14px; border-radius: 10px; font-size: 12px; display: flex; align-items: center; justify-content: space-between;">
    <div>
        <strong>🔄 ¿Lectura desfasada?</strong> Mueva el teléfono dibujando un <strong>"8"</strong> en el aire para calibrar el magnetómetro.
    </div>
</div>

<!-- BOTONES DE ACCIÓN -->
<div style="max-width: 500px; margin: 10px auto 0 auto; display: flex; flex-direction: column; gap: 10px;">
    <button id="btn-permisos" style="padding: 14px 24px; font-size: 15px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
        📡 ACTIVAR CÁMARA, GPS Y SENSORES V6.1
    </button>
    
    <button id="btn-capturar" style="display: none; padding: 14px 24px; font-size: 15px; font-weight: bold; background-color: #e11d48; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
        📸 CAPTURAR EVIDENCIA QA
    </button>
</div>

<a id="download-link" style="display: none;"></a>

<script>
    const video = document.getElementById('webcam');
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
    
    // VARIABLES DE AMORTIGUACIÓN HEAVY (Mismo algoritmo estable de la V5.7)
    let azimutSuave = null;
    let tiltSuave = null;
    let ultimoAzimutRenderizado = null;

    // Factores ajustados para máxima firmeza
    const FACTOR_SUAVIDAD_AZIMUT = 0.004; // Súper pesado, elimina el parpadeo de micro-vibración
    const FACTOR_SUAVIDAD_TILT = 0.015;
    const UMBRAL_ZONA_MUERTA = 1.2;      // Zona muerta: Ignora oscilaciones menores a 1.2 grados

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

    function filtrarAzimutEstable(nuevoHeading) {{
        if (azimutSuave === null) {{
            azimutSuave = nuevoHeading;
            ultimoAzimutRenderizado = Math.round(azimutSuave);
            return azimutSuave;
        }}
        
        let diferencia = nuevoHeading - azimutSuave;
        if (diferencia > 180) diferencia -= 360;
        if (diferencia < -180) diferencia += 360;
        
        // Amortiguación exponencial pesada
        azimutSuave += diferencia * FACTOR_SUAVIDAD_AZIMUT;
        
        if (azimutSuave < 0) azimutSuave += 360;
        if (azimutSuave >= 360) azimutSuave -= 360;
        
        let candidatoRedondeado = Math.round(azimutSuave);
        let deltaDisplay = candidatoRedondeado - ultimoAzimutRenderizado;
        if (deltaDisplay > 180) deltaDisplay -= 360;
        if (deltaDisplay < -180) deltaDisplay += 360;

        // Zona Muerta: Solo actualiza el número en pantalla si supera el umbral
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
                video: {{ facingMode: "environment" }},
                audio: false
            }});
            video.srcObject = stream;
            btnCapturar.style.display = 'block';
        }} catch (err) {{
            console.error("Error al iniciar cámara: ", err);
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

        // 1. Filtrar con amortiguador suave + zona muerta
        let azimutBrutoEstable = filtrarAzimutEstable(heading);
        
        // 2. Aplicar Declinación GPS + Offset Manual
        let azimutVerdadero = azimutBrutoEstable + declinacionCalculadaGPS + offsetManual;
        
        if (azimutVerdadero < 0) azimutVerdadero += 360;
        if (azimutVerdadero >= 360) azimutVerdadero -= 360;

        let tiltReal = filtrarTiltEstable(beta);

        // 3. Calcule desviaciones
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
        const statusElement = document.getElementById('lbl-status');

        if (azimutOk && tiltOk) {{
            dataPanel.style.borderColor = "#22c55e";
            statusElement.innerText = "✅ INSPECCIÓN CONFORME";
            statusElement.style.background = "#22c55e";
        }} else {{
            dataPanel.style.borderColor = "#ef4444";
            statusElement.innerText = "❌ FUERA DE TOLERANCIA";
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
        
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Estampado superior
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(20, 20, 360, 45);
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 15px sans-serif";
        ctx.fillText(tIdentificacion + " (Dec GPS: " + declinacionCalculadaGPS + "°)", 35, 48);
        
        // Estampado inferior de datos
        ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
        ctx.fillRect(0, canvas.height - 180, canvas.width, 180);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 22px sans-serif";
        ctx.fillText("EVIDENCIA DE INSPECCIÓN QA - V6.1", 30, canvas.height - 130);
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        ctx.font = "17px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("AZIMUT VERDADERO: " + azReal + "° (Teórico: " + tAzimut + "°)", 30, canvas.height - 95);
        ctx.fillText("TILT REAL: " + tltReal + "° (Teórico: " + tTilt + "°)", 30, canvas.height - 65);
        
        ctx.font = "bold 18px sans-serif";
        ctx.fillStyle = status.includes("CONFORME") ? "#22c55e" : "#ef4444";
        ctx.fillText("ESTADO: " + status, 30, canvas.height - 25);
        
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

st.components.v1.html(js_v61_engine, height=780, scrolling=False)
st.caption("Desarrollado como MVP de Innovación para Procesos de Calidad Entel - V6.1 Ultra Estable.")
