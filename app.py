import streamlit as st
import pandas as pd

# Configuración de la página para móviles
st.set_page_config(
    page_title="Entel QA - Medidor en Terreno",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📡 Entel QA - Inspector de Antenas")
st.write("Verificación de Azimut y Tilt en tiempo real con captura de evidencia.")

# --- MEJORA 1: INGRESAR VALORES MANUALMENTE DESDE LA APP ---
st.subheader("1. Parámetros Teóricos del Sector")
col_input1, col_input2 = st.columns(2)

with col_input1:
    azimut_teorico = st.number_input(
        "Azimut Teórico (°)", 
        min_value=0.0, 
        max_value=360.0, 
        value=120.0, 
        step=1.0,
        help="Ingrese el azimut teórico de diseño para el sector."
    )

with col_input2:
    tilt_teorico = st.number_input(
        "Tilt Teórico (°)", 
        min_value=-90.0, 
        max_value=90.0, 
        value=-5.0, 
        step=0.5,
        help="Ingrese el tilt mecánico teórico de diseño para el sector."
    )

TOL_AZIMUT = 5.0
TOL_TILT = 2.0

st.info("💡 Coloque el celular de espaldas paralelo al panel de la antena usando el sistema de pinza.")

# --- COMPONENTE COMPLETO: CÁMARA, SENSORES ESTABILIZADOS Y CAPTURA ---
js_camera_and_sensors = f"""
<div id="capture-area" style="width: 100%; max-width: 500px; margin: auto; font-family: sans-serif; background: #0f172a; padding: 10px; border-radius: 16px;">
    
    <!-- Contenedor de video limpio sin textos encima -->
    <div style="position: relative; width: 100%; border-radius: 12px; overflow: hidden; background: #000; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <video id="webcam" autoplay playsinline style="width: 100%; display: block;"></video>
        <canvas id="snapshot" style="display: none; width: 100%; border-radius: 12px;"></canvas>
        <div style="position: absolute; top: 20px; left: 20px; right: 20px; bottom: 20px; border: 1px dashed rgba(255,255,255,0.4); pointer-events: none; border-radius: 6px;"></div>
    </div>
    
    <!-- Panel de datos ubicado ABAJO del video -->
    <div id="data-panel" style="margin-top: 15px; background: #1e293b; color: white; padding: 15px; border-radius: 12px; border: 4px solid #64748b; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        
        <div style="display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px;">
            <div>TEÓRICOS: AZ {azimut_teorico}° | TLT {tilt_teorico}°</div>
            <div>TOLERANCIA: Az±5° | Tlt±2°</div>
        </div>

        <div style="display: flex; gap: 10px; justify-content: space-between; text-align: center;">
            <div style="flex: 1; background: #0f172a; padding: 8px; border-radius: 8px;">
                <div style="font-size: 11px; color: #38bdf8; font-weight: bold;">AZIMUT REAL</div>
                <div style="font-size: 26px; font-weight: bold; margin: 2px 0;"><span id="lbl-azimut-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-azimut-desv">--</span>°</div>
            </div>
            
            <div style="flex: 1; background: #0f172a; padding: 8px; border-radius: 8px;">
                <div style="font-size: 11px; color: #38bdf8; font-weight: bold;">TILT REAL</div>
                <div style="font-size: 26px; font-weight: bold; margin: 2px 0;"><span id="lbl-tilt-real">--</span>°</div>
                <div style="font-size: 11px; color: #cbd5e1;">Desv: <span id="lbl-tilt-desv">--</span>°</div>
            </div>
        </div>
        
        <div id="lbl-status" style="margin-top: 12px; text-align: center; font-size: 16px; font-weight: bold; padding: 10px; border-radius: 8px; background: #475569; letter-spacing: 1px;">
            ESPERANDO SENSORES
        </div>
    </div>
</div>

<!-- Controles del Sistema -->
<div style="max-width: 500px; margin: 15px auto 0 auto; display: flex; flex-direction: column; gap: 10px;">
    <button id="btn-permisos" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #005A9C; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
        🔄 SOLICITAR ACCESO (SENSORES Y CÁMARA)
    </button>
    
    <button id="btn-capturar" style="display: none; padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #e11d48; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
        📸 CAPTURAR EVIDENCIA QA
    </button>
</div>

<!-- Elemento oculto para descarga automática de imagen -->
<a id="download-link" style="display: none;"></a>

<script>
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('snapshot');
    const dataPanel = document.getElementById('data-panel');
    const btnPermisos = document.getElementById('btn-permisos');
    const btnCapturar = document.getElementById('btn-capturar');
    const downloadLink = document.getElementById('download-link');
    
    const tAzimut = {azimut_teorico};
    const tTilt = {tilt_teorico};
    const tolAzimut = {TOL_AZIMUT};
    const tolTilt = {TOL_TILT};

    // --- FILTRO ESTABILIZADOR (MEDIA MÓVIL) ---
    const TAMANO_FILTRO = 15;
    let lecturasAzimut = [];

    function filtrarAzimut(nuevoValor) {{
        lecturasAzimut.push(nuevoValor);
        if (lecturasAzimut.length > TAMANO_FILTRO) {{
            lecturasAzimut.shift();
        }}
        
        let sumSin = 0;
        let sumCos = 0;
        for (let i = 0; i < lecturasAzimut.length; i++) {{
            let rad = lecturasAzimut[i] * Math.PI / 180;
            sumSin += Math.sin(rad);
            sumCos += Math.cos(rad);
        }}
        
        let avgRad = Math.atan2(sumSin, sumCos);
        let avgDeg = avgRad * 180 / Math.PI;
        if (avgDeg < 0) avgDeg += 360;
        
        return avgDeg;
    }}

    async function iniciarCamara() {{
        try {{
            const stream = await navigator.mediaDevices.getUserMedia({{
                video: {{ facingMode: "environment" }},
                audio: false
            }});
            video.srcObject = stream;
            btnCapturar.style.display = 'block'; // Mostrar botón de captura al iniciar cámara
        }} catch (err) {{
            console.error("Error cámara trasera: ", err);
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

        let azimutEstabilizado = filtrarAzimut(heading);

        let azimutReal = Math.round(azimutEstabilizado);
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
            dataPanel.style.borderColor = "#22c55e";
            document.getElementById('lbl-status').innerText = "✅ INSPECCIÓN CONFORME";
            document.getElementById('lbl-status').style.background = "#22c55e";
        }} else {{
            dataPanel.style.borderColor = "#ef4444";
            document.getElementById('lbl-status').innerText = "❌ FUERA DE TOLERANCIA";
            document.getElementById('lbl-status').style.background = "#ef4444";
        }}
    }}

    btnPermisos.addEventListener('click', async () => {{
        await iniciarCamara();
        if (window.DeviceOrientationEvent) {{
            window.addEventListener('deviceorientation', procesarOrientacion, true);
            window.addEventListener('deviceorientationabsolute', procesarOrientacion, true);
            document.getElementById('lbl-status').innerText = "CONECTANDO SENSORES...";
        }} else {{
            alert("No se detectan sensores.");
        }}
        btnPermisos.style.display = 'none';
    }});

    // --- NUEVA LÓGICA: CAPTURA DE PANTALLA PROCESADA ---
    btnCapturar.addEventListener('click', () => {{
        // Dimensionar canvas al tamaño del video real en ejecución
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        
        // 1. Dibujar el cuadro exacto del video
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // 2. Renderizar marcas de agua informativas directo en la foto capturada
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(0, canvas.height - 160, canvas.width, 160);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 24px sans-serif";
        ctx.fillText("EVIDENCIA DE INSPECCIÓN - ENTEL QA", 30, canvas.height - 110);
        
        const azReal = document.getElementById('lbl-azimut-real').innerText;
        const tltReal = document.getElementById('lbl-tilt-real').innerText;
        const status = document.getElementById('lbl-status').innerText;
        
        ctx.font = "20px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText(`AZIMUT REAL: ${{azReal}}° (Teo: ${{tAzimut}}°)  |  TILT REAL: ${{tltReal}}° (Teo: ${{tTilt}}°)`, 30, canvas.height - 70);
        
        ctx.font = "bold 20px sans-serif";
        ctx.fillStyle = status.includes("CONFORME") ? "#22c55e" : "#ef4444";
        ctx.fillText(`ESTADO: ${{status}}`, 30, canvas.height - 30);
        
        // 3. Disparar la descarga automática del archivo PNG en el teléfono
        try {{
            const dataURL = canvas.toDataURL('image/png');
            downloadLink.href = dataURL;
            
            // Nombre del archivo ordenado por fecha aproximada
            const timestamp = new Date().getTime();
            downloadLink.download = `Evidencia_QA_AZ${{azReal}}_TLT${{tltReal}}_${{timestamp}}.png`;
            downloadLink.click();
        }} catch(e) {{
            alert("Para guardar el registro, por favor toma una captura de pantalla normal (Botón de encendido + bajar volumen).");
        }}
    }});
</script>
"""

st.components.v1.html(js_camera_and_sensors, height=750, scrolling=False)
st.caption("Desarrollado como MVP de Innovación para Procesos de Calidad y SST Entel.")
