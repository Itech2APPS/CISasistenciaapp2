import streamlit as st
import zipfile
import io
import re
import unicodedata
import calendar
import locale
import pdfplumber
from PyPDF2 import PdfWriter
from pathlib import Path

# Configura español para el nombre del mes
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "es_CL.UTF-8")
    except:
        pass

# Normaliza texto (elimina acentos)
def normalizar_nombre(nombre):
    return unicodedata.normalize("NFKD", nombre).encode("ASCII", "ignore").decode()

# Extrae mes, rut, nombre
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

def procesar_pdf(pdf_file):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file, pdfplumber.open(pdf_file) as pdf:
        for i in range(0, len(pdf.pages), 2):  # páginas impares
            page = pdf.pages[i]
            texto = page.extract_text()

            if not texto:
                continue

            mes, rut, nombre = extraer_datos(texto)
            if not all([mes, rut, nombre]):
                continue

            nombre_limpio = normalizar_nombre(nombre)
            filename = f"ASISTENCIA_{mes.upper()}_{rut}_{nombre_limpio.upper()}.pdf"

            # Crear PDF individual
            writer = PdfWriter()
            writer.add_page(pdf.pages[i].to_pdf().pages[0])

            buffer_pdf = io.BytesIO()
            writer.write(buffer_pdf)
            buffer_pdf.seek(0)
            zip_file.writestr(filename, buffer_pdf.read())

    zip_buffer.seek(0)
    return zip_buffer

# Streamlit UI
st.title("App para Separar Páginas Impares del PDF de Asistencia")
st.write("Sube el PDF y descarga los archivos individuales de asistencia por empleado.")

uploaded_file = st.file_uploader("📄 Subir PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Procesando archivo..."):
        zip_resultado = procesar_pdf(uploaded_file)

    st.success("¡PDFs generados correctamente!")
    st.download_button(
        label="📦 Descargar ZIP con PDFs",
        data=zip_resultado,
        file_name="asistencias.zip",
        mime="application/zip"
    )
