import streamlit as st
import zipfile
import io
import re
import unicodedata
import calendar
import locale
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

# Configurar locale en español
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "es_CL.UTF-8")
    except:
        pass

def normalizar_nombre(nombre):
    return unicodedata.normalize("NFKD", nombre).encode("ASCII", "ignore").decode()

def extraer_datos(texto):
    match_fecha = re.search(r"Periodo desde\s+(\d{2})/\d{2}/\d{4}", texto)
    mes_num = int(match_fecha.group(1)) if match_fecha else None
    mes_nombre = calendar.month_name[mes_num].capitalize() if mes_num else "Desconocido"

    match_rut = re.search(r"(\d{1,2}\.\d{3}\.\d{3}-\d)", texto)
    if match_rut:
        rut = match_rut.group(1)
        if rut.startswith("65.191"):
            return None, None, None
    else:
        rut = "RUT_NO_ENCONTRADO"

    match_nombre = re.search(r"\d{1,2}\.\d{3}\.\d{3}-\d\s+([A-ZÑÁÉÍÓÚ\s]+)", texto)
    nombre = (
        match_nombre.group(1).strip().title().replace("  ", " ")
        if match_nombre
        else "NOMBRE_NO_ENCONTRADO"
    )

    return mes_nombre, rut, nombre

def procesar_pdf(uploaded_file):
    zip_buffer = io.BytesIO()
    reader = PdfReader(uploaded_file)
    uploaded_file.seek(0)  # volver al inicio
    with pdfplumber.open(uploaded_file) as pdf, zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(0, len(reader.pages), 2):  # páginas impares
            texto = pdf.pages[i].extract_text()
            if not texto:
                continue

            mes, rut, nombre = extraer_datos(texto)
            if not all([mes, rut, nombre]):
                continue

            nombre_limpio = normalizar_nombre(nombre)
            filename = f"ASISTENCIA_{mes.upper()}_{rut}_{nombre_limpio.upper()}.pdf"

            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            output_pdf = io.BytesIO()
            writer.write(output_pdf)
            zip_file.writestr(filename, output_pdf.getvalue())

    zip_buffer.seek(0)
    return zip_buffer

# Interfaz de Streamlit
st.title("📄 Generador de PDFs de Asistencia por Empleado")
st.write("Sube un PDF con asistencia mensual. Se generarán archivos PDF individuales por página impar con el nombre del trabajador.")

uploaded_file = st.file_uploader("Sube tu archivo PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Procesando PDF..."):
        zip_file = procesar_pdf(uploaded_file)

    st.success("¡Listo! Descarga el archivo ZIP con los PDFs.")
    st.download_button(
        label="📦 Descargar ZIP",
        data=zip_file,
        file_name="asistencias_individuales.zip",
        mime="application/zip"
    )
