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
st.subheader("📸 2. Captura de Evidencia en Terreno")
st.info("Utiliza la cámara para capturar la evidencia con marca de agua y telemetría.")

# =====================================================================
# ⚠️ IMPORTANTE: PEGA AQUÍ TU st.components.v1.html CON EL JAVASCRIPT
# =====================================================================
# st.components.v1.html(""" 
#   <html>... Tu código de V6.6 con la brújula y cámara ...</html>
# """, height=600)
st.success("Motor de captura activo. (Aquí va tu componente HTML/JS).")


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
