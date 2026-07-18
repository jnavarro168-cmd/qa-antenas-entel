import streamlit as st

# Configuración de la página para móviles
st.set_page_config(
    page_title="Entel QA - Medidor en Terreno",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector de Antenas")
st.write("Verificación de Azimut y Tilt con calibración magnética.")

# --- PARÁMETROS, IDENTIFICACIÓN Y COMPENSACIÓN ---
st.subheader("1. Identificación y Parámetros Teóricos")

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

# --- NUEVO: COMPENSACIÓN POR DECLINACIÓN O INTERFERENCIA ---
st.subheader("🔧 Calibración de Brújula")
compensacion_azimut = st.number_input(
    "Ajuste / Offset de Azimut (°):",
    min_value=-180.0,
    max_value=180.0,
    value=0.0,
    step=1.0,
    help="Sume o reste grados para emparejar la app con su brújula Suunto (Ej: si la app marca 315 y la Suunto 338, ingrese 23)."
)

TOL_AZIMUT = 5.0
TOL_TILT = 2.0

texto_identificacion = f"{sitio_nemonico} - {sector_seleccionado.upper()}"
nombre_archivo_sector = f"{sitio_nemonico}_{sector_seleccionado.replace(' ', '-')}"

# --- COMPONENTE INTEGRADO CON COMPENSACIÓN V5.6 ---
js_camera_and_sensors = f"""
<div id="capture-area" style="width: 100%; max-width: 500px; margin: auto; font-family: sans-serif; background: #0f172a; padding: 10px; border-radius: 16px;">
    
    <div style="position: relative; width: 100%; border-radius: 12px; overflow: hidden; background: #000; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <video id="webcam" autoplay playsinline style="width: 100%; display: block;"></video>
        <canvas id="snapshot" style="display: none; width: 100%; border-radius: 12px;"></canvas>
        
        <div style="position: absolute; top: 15px; left: 15px; background: rgba(15, 23, 42, 0.75); color: #38bdf8; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; border: 1px solid rgba(56, 189, 248, 0.4);">
            {texto_identificacion} (Cal: {compensacion_azimut}°)
        </div>
        
        <div style="position: absolute; top: 20px; left: 20px; right: 20px; bottom: 20px; border: 1px dashed rgba(255,255,255,0.3); pointer-events: none; border-radius: 6px;"></div>
    </div>
    
    <div id="data-panel" style="margin-top: 15px; background: #1e293b; color: white; padding: 15px; border-radius: 12px; border: 4px solid #ef4444; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: border-color 0.3s ease;">
        
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px;">
            <div>ID: {texto_identificacion} | AZ {azimut_teorico}° | TLT {tilt_teorico}°</div>
            <div>TOL: Az±5° | Tlt±2°</div>
        </div>

        <div style="display: flex; gap: 10px; justify-content: space-between; text-align: center;">
            <div style="flex: 1; background: #0f172a; padding: 8px; border-radius: 8px;">
                <div style="font-size: 11px; color: #38bdf8; font-weight: bold;">AZIMUT COMPENSADO</div>
                <div style="font-size: 26px; font-weight: bold; margin: 2px 0;"><span id="lbl-azimut-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-azimut-desv">--</span>°</div>
            </div>
            
            <div style="flex: 1; background: #0f172a; padding: 8px; border-radius: 8px;">
                <div style="font-size: 11px; color: #38bdf8; font-weight: bold;">TILT REAL</div>
                <div style="font-size: 26px; font-weight: bold; margin: 2px 0;"><span id="lbl-tilt-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-tilt-desv">--</span>°</div>
            </div>
        </div>
        
        <div id="lbl-status" style="margin-top: 12px; text-align: center; font-size: 16px; font-weight: bold; padding: 10px; border-radius: 8px; background: #ef4444; letter-spacing: 1px;">
            FUERA DE TOLERANCIA
        </div>
    </div>
</div>

<div style="max-width: 500px; margin: 15px auto 0 auto; display: flex; flex-direction: column; gap: 10px;">
    <button id="btn-permisos" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
        🔄 SOLICITAR ACCESO (SENSORES Y CÁMARA)
    </button>
    
    <button id="btn-capturar" style="display: none; padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #e11d48; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
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
    
    const tIdentificacion = "{texto_identificacion}";
    const tNombreArchivo = "{nombre_archivo_sector}";
    const tAzimut = {azimut_teorico};
    const tTilt = {tilt_teorico};
    const tolAzimut = {TOL_AZIMUT};
    const tolTilt = {TOL_TILT};
    
    // Traemos el offset definido en Streamlit
    const offsetAzimut = {compensacion_azimut};

    let azimutSuave = null;
    let tiltSuave = null;
    let ultimoAzimutRenderizado = null;

    const FACTOR_SUAVIDAD_AZIMUT = 0.005; 
    const FACTOR_SUAVIDAD_TILT = 0.02;
    const UMBRAL_ZONA_MUERTA = 1.0; 

    function filtrarAzimutAvanzado(nuevoHeading) {{
        if (azimutSuave === null) {{
            azimutSuave = nuevoHeading;
            ultimoAzimutRenderizado = Math.round(azimutSuave);
            return azimutSuave;
        }}
        
        let diferencia = nuevoHeading - azimutSuave;
        if (diferencia > 180) diferencia -= 360;
        if (diferencia < -180) diferencia += 360;
        
        azimutSuave += diferencia * FACTOR_SUAVISAD_AZIMUT;
        
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

    function filtrarTiltExponencial(nuevoBeta) {{
        if (tiltSuave === null) {{
            tiltSuave = nuevoBeta;
            return tiltSuave;
        }}
        tiltSuave += (nuevoBeta - tiltSuave) * FACTOR_SUAVIDAD_TILT;
        return tiltSuave;
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
            console.error("Error: ", err);
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

        // 1. Obtener azimut base filtrado
        let azimutBase = filtrarAzimutAvanzado(heading);
        
        // 2. APLICAR COMPENSACIÓN MANUAL
        let azimutReal = azimutBase + offsetAzimut;
        
        // Normalizar para que se mantenga entre 0 y 359 grados
        if (azimutReal < 0) azimutReal += 360;
        if (azimutReal >= 360) azimutReal -= 360;

        let tiltReal = Math.round(filtrarTiltExponencial(beta));

        // Calcular desviaciones contra el teórico
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
        if (window.DeviceOrientationEvent) {{
            window.addEventListener('deviceorientation', procesarOrientacion, true);
            window.addEventListener('deviceorientationabsolute', procesarOrientacion, true);
            document.getElementById('lbl-status').innerText = "CONECTANDO SENSORES...";
        }} else {{
            alert("Sensores no disponibles.");
        }}
        btnPermisos.style.display = 'none';
    }});

    btnCapturar.addEventListener('click', () => {{
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(20, 20, 310, 45);
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 15px sans-serif";
        ctx.fillText(tIdentificacion + " (Cal: " + offsetAzimut + "°)", 35, 48);
        
        ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
        ctx.fillRect(0, canvas.height - 180, canvas.width, 180);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 22px sans-serif";
        ctx.fillText("EVIDENCIA DE INSPECCIÓN - " + tIdentificacion, 30, canvas.height - 130);
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        ctx.font = "17px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("AZIMUT REAL: " + azReal + "° (Teórico: " + tAzimut + "°)", 30, canvas.height - 95);
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
            alert("Use la captura nativa.");
        }}
    }});
</script>
"""

st.components.v1.html(js_camera_and_sensors, height=760, scrolling=False)
st.caption("Desarrollado como MVP de Innovación para Procesos de Calidad y SST Entel.")
