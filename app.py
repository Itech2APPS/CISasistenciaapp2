import streamlit as st
import zipfile
import io
import re
import unicodedata
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

# Meses en español (índice 1-12)
MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Normaliza nombres eliminando acentos
def normalizar_nombre(nombre):
    return unicodedata.normalize("NFKD", nombre).encode("ASCII", "ignore").decode()

# Extrae mes, RUT y nombre completo desde el texto
def extraer_datos(texto):
    # Extraer mes en número
    match_fecha = re.search(r"Periodo desde\s+(\d{2})/\d{2}/\d{4}", texto)
    mes_num = int(match_fecha.group(1)) if match_fecha else None
    mes_nombre = MESES_ES[mes_num] if mes_num and mes_num <= 12 else "Desconocido"

    # Extraer RUT y nombre completo
    match_rut_nombre = re.search(r"\d+\s+(\d{1,2}\.\d{3}\.\d{3}-\d)\s+([A-ZÑÁÉÍÓÚ]+(?:\s+[A-ZÑÁÉÍÓÚ]+)+)", texto)

    if not match_rut_nombre:
        return None, None, None

    rut = match_rut_nombre.group(1)
    nombre = match_rut_nombre.group(2).strip().title()

    if rut.startswith("65.191"):
        return None, None, None

    return mes_nombre, rut, nombre

# Procesa el PDF y genera los archivos individuales comprimidos en ZIP
def procesar_pdf(uploaded_file):
    zip_buffer = io.BytesIO()
    reader = PdfReader(uploaded_file)
    uploaded_file.seek(0)  # Reiniciar para pdfplumber

    with pdfplumber.open(uploaded_file) as pdf, zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(0, len(reader.pages), 2):  # Solo páginas impares
            texto = pdf.pages[i].extract_text()
            if not texto:
                continue

            mes, rut, nombre = extraer_datos(texto)
            if not all([mes, rut, nombre]):
                continue

            nombre_limpio = normalizar_nombre(nombre)
            nombre_archivo = f"ASISTENCIA_{mes.upper()}_{rut}_{nombre_limpio.upper()}.pdf"

            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            zip_file.writestr(nombre_archivo, pdf_output.getvalue())

    zip_buffer.seek(0)
    return zip_buffer

# Interfaz de Streamlit
st.set_page_config(page_title="Divisor de Asistencia por Empleado", layout="centered")
st.title("📄 Dividir PDF de Asistencia por Empleado")
st.write("Sube un archivo PDF con asistencia mensual. Esta app separa las páginas impares y genera un archivo PDF individual por trabajador.")

uploaded_file = st.file_uploader("📎 Sube el archivo PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("⏳ Procesando archivo..."):
        zip_resultado = procesar_pdf(uploaded_file)

    st.success("✅ ¡Proceso completado! Descarga el archivo ZIP con los PDFs individuales.")
    st.download_button(
        label="📦 Descargar ZIP",
        data=zip_resultado,
        file_name="asistencias_individuales.zip",
        mime="application/zip"
    )
