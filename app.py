import streamlit as st
import zipfile
import io
import re
import unicodedata
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import calendar
import locale

# Forzar español para nombre de meses
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "es_CL.UTF-8")
    except:
        pass  # fallback a inglés si no disponible

def extraer_datos(texto):
    # Mes desde "Periodo desde"
    match_periodo = re.search(r"Periodo desde\s+(\d{2})/\d{2}/\d{4}", texto)
    mes_num = match_periodo.group(1) if match_periodo else None
    mes_nombre = (
        calendar.month_name[int(mes_num)].capitalize() if mes_num else "DESCONOCIDO"
    )

    # RUT (evita el de la empresa)
    rut_match = re.search(r"(\d{1,2}\.\d{3}\.\d{3}-\d)", texto)
    if rut_match and rut_match.group(1).startswith("65.191"):
        return None, None, None

    rut = rut_match.group(1) if rut_match else "RUT_NO_ENCONTRADO"

    # Nombre completo justo después del RUT
    nombre_match = re.search(r"\d{1,2}\.\d{3}\.\d{3}-\d\s+([A-ZÑÁÉÍÓÚ\s]+)", texto)
    nombre = (
        nombre_match.group(1).strip().title().replace("  ", " ")
        if nombre_match
        else "NOMBRE_NO_ENCONTRADO"
    )

    return mes_nombre, rut, nombre

def normalizar_nombre(nombre):
    return unicodedata.normalize("NFKD", nombre).encode("ASCII", "ignore").decode()

def procesar_pdf(pdf_subido):
    reader = PdfReader(pdf_subido)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(0, len(reader.pages), 2):  # páginas impares
            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            texto = reader.pages[i].extract_text()
            mes, rut, nombre = extraer_datos(texto)

            if not all([mes, rut, nombre]):
                continue

            nombre_normalizado = normalizar_nombre(nombre)
            filename = f"ASISTENCIA_{mes.upper()}_{rut}_{nombre_normalizado.upper()}.pdf"

            pdf_buffer = io.BytesIO()
            writer.write(pdf_buffer)
            zip_file.writestr(filename, pdf_buffer.getvalue())

    zip_buffer.seek(0)
    return zip_buffer

# Interfaz Streamlit
st.title("Separador de PDF por Empleado (Páginas Impares)")
st.write("Sube un archivo PDF de asistencia y descarga los archivos individuales por empleado.")

pdf_file = st.file_uploader("Sube tu PDF", type=["pdf"])

if pdf_file is not None:
    with st.spinner("Procesando..."):
        zip_resultado = procesar_pdf(pdf_file)
    st.success("¡Listo! Descarga el ZIP con los archivos generados.")
    st.download_button(
        label="📦 Descargar ZIP",
        data=zip_resultado,
        file_name="asistencias_separadas.zip",
        mime="application/zip",
    )
