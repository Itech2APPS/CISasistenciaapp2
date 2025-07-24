import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import zipfile
import re
import calendar
import io

# Diccionario de meses en español
MESES_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

def extraer_mes(texto):
    match = re.search(r"Periodo desde\s+(\d{2})/(\d{2})/(\d{4})", texto)
    if match:
        numero_mes = int(match.group(2))
        return MESES_ES.get(numero_mes, "MES")
    return "MES"

def extraer_rut(texto):
    ruts = re.findall(r"\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]", texto)
    for rut in ruts:
        if not rut.startswith("65.191"):
            return rut.replace(".", "")
    return "RUT_NO_ENCONTRADO"

def extraer_nombre(texto):
    match = re.search(r"(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])\s*-\s*([A-ZÑÁÉÍÓÚ ]+)", texto)
    if match:
        return match.group(2).strip()
    # Fallback si no encuentra con guión
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if re.match(r"\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]", linea.strip()):
            if not linea.strip().startswith("65.191") and i + 1 < len(lineas):
                return lineas[i + 1].strip()
    return "NOMBRE_NO_ENCONTRADO"

def generar_pdfs_desde_pares(pdf_file):
    reader = PdfReader(pdf_file)
    archivos = []

    for i in range(0, len(reader.pages), 2):  # Solo páginas impares
        page = reader.pages[i]
        texto = page.extract_text()

        mes = extraer_mes(texto)
        rut = extraer_rut(texto)
        nombre = extraer_nombre(texto)

        nombre_archivo = f"ASISTENCIA_{mes}_{rut}_{nombre}".replace(" ", "_") + ".pdf"

        buffer = io.BytesIO()
        writer = PdfWriter()
        writer.add_page(page)
        writer.write(buffer)
        archivos.append((nombre_archivo, buffer.getvalue()))

    return archivos

def crear_zip(archivos_pdf):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for nombre, contenido in archivos_pdf:
            zipf.writestr(nombre, contenido)
    return zip_buffer.getvalue()

# === Interfaz de Streamlit ===
st.set_page_config(page_title="Generador de Asistencias", layout="centered")
st.title("📄 Generador de archivos de Asistencia")
st.markdown("Sube un archivo PDF con múltiples asistencias. Se generarán archivos individuales por empleado (páginas impares) y podrás descargar todo en un `.zip`.")

archivo = st.file_uploader("📤 Sube tu archivo PDF", type=["pdf"])

if archivo:
    with st.spinner("Procesando el archivo..."):
        archivos_generados = generar_pdfs_desde_pares(archivo)
        if not archivos_generados:
            st.error("No se encontraron páginas impares válidas.")
        else:
            zip_data = crear_zip(archivos_generados)
            st.success(f"{len(archivos_generados)} archivos generados correctamente.")

            st.download_button(
                label="📦 Descargar ZIP",
                data=zip_data,
                file_name="asistencias_generadas.zip",
                mime="application/zip"
            )
