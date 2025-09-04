import streamlit as st
import pandas as pd
import json
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
import re 
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A4  # ← ESTA LÍNEA FALTABA
from PIL import Image
import qrcode
from io import BytesIO
import random
import string
import io
from reportlab.pdfgen import canvas
import textwrap
import string, random
import base64
import pytz
import uuid
import os
import time

from PyPDF2 import PdfReader, PdfWriter, PdfMerger

from reportlab.lib.pagesizes import letter

###########################  PROCESO PDF FISCALES #############################################################################################
def generar_pdf(datos_sat, idcif, rfc):

    # Extraer datos del diccionario para facilitar lectura
    datos = {k.strip().lower().replace(" ", "_"): v for k, v in datos_sat.items()}

    
    curp = datos.get("curp", "")
    nombre_completo = datos.get("nombre_completo", "")
    nombre = datos.get("nombre", "")
    apellido_paterno = datos.get("apellido_paterno", "")
    apellido_materno = datos.get("apellido_materno", "")
    fecha_inicio_operaciones = datos.get("fecha_de_inicio_de_operaciones", "")
    situacion_contribuyente = datos.get("situación_del_contribuyente", "")
    fecha_ultimo_cambio = datos.get("fecha_del_ultimo_cambio_de_situacion", "")
    cp = datos.get("cp", "")
    nombre_vialidad = datos.get("nombre_de_la_vialidad", "")
    numero_interior = datos.get("número_interior", "")
    municipio = datos.get("municipio_o_delegación", "")
    entidad_federativa = datos.get("entidad_federativa", "")
    tipo_vialidad = datos.get("tipo_de_vialidad", "")
    numero_exterior = datos.get("número_exterior", "")
    colonia = datos.get("colonia", "")
    resultado_fecha_actual = datos.get("fecha_actual", "")
    #regimen = datos.get("régimen", "")
    regimen = "22222222 222222222222222 2222222222222 222222222222 22222222222222 22222222222 22222222 222222222 222222222222 22222222222 2222222222"
    regimen2 = None
    fecha_alta = datos.get("fecha_de_alta", "")
    #regimen2 = datos.get("régimen2", "")
    fecha_alta2 = datos.get("fecha_de_alta2", "")
    rfc = rfc.upper()
    if regimen2 and regimen in regimen2:
        regimen2 = None
        fecha_alta2 = None
    
    #st.write("Estatus:", datos)
    #st.write("Estatus:", datos_sat)
    #st.write("Estatus:", regimen2)
    #st.write("Estatus:", fecha_alta2)
    
    #st.write("Estatus:", "Generado")
    if apellido_materno == None:
        apellido_materno = ""
    
    # Descargar plantilla PDF desde GitHub
    if regimen2 == None:
        url_plantilla = "https://raw.githubusercontent.com/userprogram331/archivo/main/SAT4.pdf"
    else:
    #url_plantilla = "https://raw.githubusercontent.com/userprogram331/program/main/SAT4.pdf"
        url_plantilla = "https://raw.githubusercontent.com/userprogram331/archivo/main/SAT2.pdf"
    
    respuesta = requests.get(url_plantilla)
    if respuesta.status_code != 200:
        raise Exception(f"No se pudo descargar la plantilla, status: {respuesta.status_code}")

    buffer_plantilla = BytesIO(respuesta.content)
    pdf_plantilla = PdfReader(buffer_plantilla)

    # Generar código QR en memoria
    qr_data = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    #qr_data = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3="
    qr_img = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Crear buffer para contenido dinámico (capa superior)
    buffer_contenido = BytesIO()
    c = canvas.Canvas(buffer_contenido, pagesize=letter)
    width, height = letter

    def safe_text(text):
        if text is None:
            return ""
        return str(text)

    # Abrir la imagen QR con PIL para que ReportLab la acepte
    qr_buffer.seek(0)
    img_pil = Image.open(qr_buffer)

    # Insertar la imagen QR en la posición deseada con tamaño 100x100
    c.drawInlineImage(img_pil, 40, 550, width=100, height=100)

    # Dibujo de textos (tu código original resumido y corregido)
    text_width = c.stringWidth(rfc.upper(), "Helvetica", 8)
    x = (153 + 280 - text_width) / 2
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(130/255.0, 130/255.0, 130/255.0)
    c.drawString(x, 634, safe_text(rfc))

    c.drawString(205, 555, safe_text(idcif))

    text_width = c.stringWidth(rfc, "Helvetica", 7)
    x = (578 + 308 - text_width) / 2
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(412, 528, safe_text(rfc))

    # Nombre completo en máximo 3 líneas centrado
    x1 = 153
    x2 = 280
    y_last_line = 595
    max_width = x2 - x1
    font_name = "Helvetica"
    font_size = 8
    line_spacing = font_size + 2
    c.setFont(font_name, font_size)
    c.setFillColorRGB(130/255.0, 130/255.0, 130/255.0)
    nombre_completo = f"{nombre} {apellido_paterno} {apellido_materno}".strip()
    nombre_completo = safe_text(nombre_completo)
    text_width = c.stringWidth(nombre_completo, font_name, font_size)
    avg_char_width = text_width / max(len(nombre_completo), 1)
    if avg_char_width == 0:
        avg_char_width = 1  # evitar división por cero
    chars_per_line = int(max_width / avg_char_width)

    lines = textwrap.wrap(nombre_completo, width=chars_per_line)[:3]
    for i, line in enumerate(reversed(lines)):
        line_width = c.stringWidth(line, font_name, font_size)
        x = (x1 + x2 - line_width) / 2
        y = y_last_line + (i * line_spacing)
        c.drawString(x, y, line)

    def dibujar_texto(texto, x, y, font="Helvetica", size=8, color=(0,0,0)):
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        c.drawString(x, y, safe_text(texto))

    dibujar_texto(rfc, 236, 478)
    dibujar_texto(curp, 236, 457)
    dibujar_texto(nombre, 236, 435)
    dibujar_texto(apellido_paterno, 236, 413)
    dibujar_texto(apellido_materno, 236, 391)

    def formatear_fecha(fecha_str):
        try:
            fecha = time.strptime(fecha_str, "%d-%m-%Y")
            meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                     "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            return f"{fecha.tm_mday:02d} DE {meses[fecha.tm_mon - 1]} DE {fecha.tm_year}"
        except Exception:
            return fecha_str

    dibujar_texto(formatear_fecha(fecha_inicio_operaciones), 236, 369)
    dibujar_texto(situacion_contribuyente, 236, 347)
    dibujar_texto(formatear_fecha(fecha_inicio_operaciones), 236, 325)

    dibujar_texto(cp, 95, 249)
    dibujar_texto(nombre_vialidad, 115, 227)
    dibujar_texto(numero_interior, 100, 205)

    x1 = 130
    x2 = 300
    y_last_line = 178
    y_single_line = 183
    max_width = x2 - x1
    font_name = "Helvetica"
    font_size = 8
    line_spacing = font_size + 2

    municipio_text = safe_text(municipio)
    text_width = c.stringWidth(municipio_text, font_name, font_size)
    avg_char_width = text_width / max(len(municipio_text), 1)
    if avg_char_width == 0:
        avg_char_width = 1
    chars_per_line = int(max_width / avg_char_width)
    lines = textwrap.wrap(municipio_text, width=chars_per_line)[:2]

    if len(lines) == 1:
        c.drawString(x1, y_single_line, lines[0])
    else:
        for i, line in enumerate(reversed(lines)):
            line_width = c.stringWidth(line, font_name, font_size)
            x = (x1 + x2 - line_width) / 2
            y = y_last_line + (i * line_spacing)
            c.drawString(x, y, line)

##################################

    x = 165
    x_max = 300
    max_width = x_max - x
    font_name = "Helvetica"
    font_size = 8
    
    # Procesar el texto
    entidad_text = safe_text(entidad_federativa)
    
    # Medir ancho promedio de caracteres
    text_width = c.stringWidth(entidad_text, font_name, font_size)
    avg_char_width = text_width / max(len(entidad_text), 1)
    if avg_char_width == 0:
        avg_char_width = 1
    
    # Calcular cuántos caracteres caben por línea
    chars_per_line = int(max_width / avg_char_width)
    
    # Dividir en líneas
    lines = textwrap.wrap(entidad_text, width=chars_per_line)
    
    # Dibujar texto según cantidad de líneas
    if len(lines) == 1:
        c.drawString(x, 161, lines[0])
    else:
        # Solo usar las primeras dos líneas si hay más
        if len(lines) > 0:
            c.drawString(x, 166, lines[0])
        if len(lines) > 1:
            c.drawString(x, 156, lines[1])
################################

    
    #dibujar_texto(entidad_federativa, 165, 161)
    #dibujar_texto("|", 300, 165)
    dibujar_texto(tipo_vialidad, 378, 249)
    dibujar_texto(numero_exterior, 378, 227)
    dibujar_texto(colonia, 397, 205)

    x1 = 498
    x2 = 578
    y_last_line = 178
    y_single_line = 183
    max_width = x2 - x1

    municipio_text = safe_text(municipio)
    text_width = c.stringWidth(municipio_text, font_name, font_size)
    avg_char_width = text_width / max(len(municipio_text), 1)
    if avg_char_width == 0:
        avg_char_width = 1
    chars_per_line = int(max_width / avg_char_width)
    lines = textwrap.wrap(municipio_text, width=chars_per_line)[:2]

    if len(lines) == 1:
        c.drawString(x1, y_single_line, lines[0])
    else:
        for i, line in enumerate(reversed(lines)):
            line_width = c.stringWidth(line, font_name, font_size)
            x = (x1 + x2 - line_width) / 2
            y = y_last_line + (i * line_spacing)
            c.drawString(x, y, line)

    #dibujar_texto(entidad_federativa, 535, 161)
    # Crear imagen de código de barras tipo Code128
    codigo_barras = code128.Code128(
        rfc,                 # Texto codificado
        barHeight=24,        # Altura de las barras
        barWidth=0.6         # Grosor de las barras
    )
    
    # Calcular el ancho del código de barras
    barcode_width = codigo_barras.width
    
    # Rango horizontal entre el que quieres centrar el código
    x1_barcode = 308
    x2_barcode = 578
    
    # Calcular posición X para centrar
    x_barcode = (x1_barcode + x2_barcode - barcode_width) / 2
    
    # Dibujar el código de barras centrado
    codigo_barras.drawOn(c, x=x_barcode, y=535)  # Y = altura desde la base
    #dibujar_texto(formatear_fecha(resultado_fecha_actual), 490, 631)

    # Área del campo resultado_fecha_actual
    x1 = 308
    x2 = 578
    max_width = x2 - x1
    
    # Texto seguro y formateado
    resultado_fecha_actual = safe_text(formatear_fecha(resultado_fecha_actual))
    
    # Intentar con fuente tamaño 10
    font_name = "Helvetica-Bold"
    font_size_try = 9
    c.setFont(font_name, font_size_try)
    text_width = c.stringWidth(resultado_fecha_actual, font_name, font_size_try)
    
    if text_width <= max_width:
        # Cabe con tamaño 10, centrar en y = 580
        line_width = text_width
        x = (x1 + x2 - line_width) / 2
        y = 580
        c.setFillColorRGB(0.0, 0.0, 0.0)
        c.drawString(x, y, resultado_fecha_actual)
    else:
        # No cabe, reducir tamaño a 8 y dividir en 2 líneas
        font_size = 8
        line_spacing = font_size + 2
        y_last_line = 573
    
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.0, 0.0, 0.0)
    
        text_width = c.stringWidth(resultado_fecha_actual, font_name, font_size)
        avg_char_width = text_width / max(len(resultado_fecha_actual), 1)
        chars_per_line = int(max_width / avg_char_width)
    
        lines = textwrap.wrap(resultado_fecha_actual, width=chars_per_line)[:2]
    
        for i, line in enumerate(reversed(lines)):
            line_width = c.stringWidth(line, font_name, font_size)
            x = (x1 + x2 - line_width) / 2
            y = y_last_line + (i * line_spacing)
            c.drawString(x, y, line)


    ############################
    c.showPage()
####################################################################################################################
    if regimen2 == None:
        if situacion_contribuyente == "SUSPENDIDO":
            regimen = None

        regimen = safe_text(regimen)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 33
        y_inicio = 555
        ancho_maximo = 370 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen, font, size)
        avg_char_width = text_width / max(len(regimen), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)

        
     # Régimen Fiscal en la segunda página
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(33, 555, safe_text(regimen))

        regimen = safe_text(regimen)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 78
        y_inicio = 628
        ancho_maximo = 445 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen, font, size)
        avg_char_width = text_width / max(len(regimen), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)
        
         # Régimen Fiscal en la segunda página
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(78, 628, safe_text(regimen))
    
    
     # Régimen Fiscal fecha inicio
        if situacion_contribuyente == "SUSPENDIDO":
            fecha_alta = None
        else:
            if fecha_alta and fecha_alta.strip():
                fecha_alta = fecha_alta.replace("-", "/")
            elif fecha_inicio_operaciones and fecha_inicio_operaciones.strip():
                fecha_alta = fecha_inicio_operaciones.replace("-", "/")
            else:
                fecha_alta = None
        #fecha_alta = fecha_alta.replace("-", "/")
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(455, 555, safe_text(fecha_alta))
        if situacion_contribuyente == "SUSPENDIDO":
            porcentaje = None
        else:
            porcentaje = "100"
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(380, 628, safe_text(porcentaje))  
     # Régimen Fiscal fecha inicio
        
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(455, 628, safe_text(fecha_alta))
        
        zona_mexico = pytz.timezone("America/Mexico_City")
        
        # Fecha actual en Ciudad de México
        fecha_actual = datetime.now(zona_mexico).strftime("%Y/%m/%d")
        caracteres = string.ascii_letters + string.digits + '/+'
        longitud = 88
        longitud2 = 4
    
        cadena_aleatoria = ''.join(random.choices(caracteres, k=longitud))
        cadena_aleatoria2 = ''.join(random.choices(caracteres, k=longitud))
        cadena_aleatoria3 = ''.join(random.choices(caracteres, k=longitud2))
    
        sello_1 = f"||{fecha_actual}|{rfc}|CONSTANCIA DE SITUACIÓN FISCAL|200001088888800000031||"
        sello_2 = cadena_aleatoria
        sello_3 = cadena_aleatoria2
        sello_4 = cadena_aleatoria3
        #sello_full = sello_2 + sello_3 + sello_4
        sello_full="https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=0&D2=1&D3=%7C%7C2025%2F02%2F04%7C%7CCONSTANCIA+DE+SITUACI%D3N+FISCAL%7C200001088888800000031%7C%7C_aixL43%2BlaHcEhTqh2j2Nl%2FPUVLD0dNN7wGUAjCbcoqjcjKLjJMs5KRrC%2B%2B4hLtBPIqhCS%2F05Z9iGM7MaOpZwnAdhcRpy5H8%2BflESHLHJySP3LmhSbIliaGRjgWjT4k62%2BL6pwOOCk0Yjp69%2BX5Bsnl6n6M48by%2Bee5JionpQE3w%3D"

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(155, 420, sello_1)
        c.drawString(155, 410, sello_2)
        c.drawString(155, 400, sello_3)
        c.drawString(155, 390, sello_4)
        x_q = 290

    #################################################################
    else:
        if situacion_contribuyente == "SUSPENDIDO":
            regimen = None

        regimen = safe_text(regimen)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 78
        y_inicio = 628
        ancho_maximo = 370 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen, font, size)
        avg_char_width = text_width / max(len(regimen), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)

        
            
        # Régimen Fiscal en la segunda página
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(78, 628, safe_text(regimen))


        regimen2 = safe_text(regimen2)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 78
        y_inicio = 605
        ancho_maximo = 370 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen2, font, size)
        avg_char_width = text_width / max(len(regimen2), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen2, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)

        # Régimen Fiscal en la segunda página
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(78, 605, safe_text(regimen2))

        regimen = safe_text(regimen)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 33
        y_inicio = 535
        ancho_maximo = 445 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen, font, size)
        avg_char_width = text_width / max(len(regimen), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)

        
     # Régimen Fiscal en la segunda página
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(33, 535, safe_text(regimen))

        regimen2 = safe_text(regimen2)
        font = "Helvetica"
        size = 8
        color = (0, 0, 0)
        x_inicio = 33
        y_inicio = 512
        ancho_maximo = 445 - x_inicio
        line_spacing = size + 2
        
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        
        text_width = c.stringWidth(regimen2, font, size)
        avg_char_width = text_width / max(len(regimen2), 1)
        if avg_char_width == 0:
            avg_char_width = 1
        
        chars_per_line = int(ancho_maximo / avg_char_width)
        lines = textwrap.wrap(regimen2, width=chars_per_line)[:2]
        
        for i, line in enumerate(lines):
            y = y_inicio - (i * line_spacing)
            c.drawString(x_inicio, y, line)
        
        
        #c.setFont("Helvetica", 8)
        #c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        #c.drawString(33, 512, safe_text(regimen2))
    

    
    
     # Régimen Fiscal fecha inicio
        if situacion_contribuyente == "SUSPENDIDO":
            fecha_alta = None
        else:
            if fecha_alta and fecha_alta.strip():
                fecha_alta = fecha_alta.replace("-", "/")
            elif fecha_inicio_operaciones and fecha_inicio_operaciones.strip():
                fecha_alta = fecha_inicio_operaciones.replace("-", "/")
            else:
                fecha_alta = None
        #fecha_alta = fecha_alta.replace("-", "/")
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(455, 535, safe_text(fecha_alta))
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        fecha_alta2 = fecha_alta2.replace("-", "/")
        c.drawString(455, 512, safe_text(fecha_alta2))
        if situacion_contribuyente == "SUSPENDIDO":
            porcentaje = None
        else:
            porcentaje = "50"
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(380, 628, safe_text("50"))  
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(380, 605, safe_text("50")) 
     # Régimen Fiscal fecha inicio
        
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(455, 628, safe_text(fecha_alta))

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(455, 605, safe_text(fecha_alta2))
        
        zona_mexico = pytz.timezone("America/Mexico_City")
        
        # Fecha actual en Ciudad de México
        fecha_actual = datetime.now(zona_mexico).strftime("%Y/%m/%d")
        caracteres = string.ascii_letters + string.digits + '/+'
        longitud = 88
        longitud2 = 4
    
        cadena_aleatoria = ''.join(random.choices(caracteres, k=longitud))
        cadena_aleatoria2 = ''.join(random.choices(caracteres, k=longitud))
        cadena_aleatoria3 = ''.join(random.choices(caracteres, k=longitud2))
    
        sello_1 = f"||{fecha_actual}|{rfc}|CONSTANCIA DE SITUACIÓN FISCAL|200001088888800000031||"
        sello_2 = cadena_aleatoria
        sello_3 = cadena_aleatoria2
        sello_4 = cadena_aleatoria3
        #sello_full = sello_2 + sello_3 + sello_4
        sello_full="https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=0&D2=1&D3=%7C%7C2025%2F02%2F04%7C%7CCONSTANCIA+DE+SITUACI%D3N+FISCAL%7C200001088888800000031%7C%7C_aixL43%2BlaHcEhTqh2j2Nl%2FPUVLD0dNN7wGUAjCbcoqjcjKLjJMs5KRrC%2B%2B4hLtBPIqhCS%2F05Z9iGM7MaOpZwnAdhcRpy5H8%2BflESHLHJySP3LmhSbIliaGRjgWjT4k62%2BL6pwOOCk0Yjp69%2BX5Bsnl6n6M48by%2Bee5JionpQE3w%3D"

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
        c.drawString(155, 376, sello_1)
        c.drawString(155, 366, sello_2)
        c.drawString(155, 356, sello_3)
        c.drawString(155, 346, sello_4)
        x_q = 246
################################################################################################################


    # Generar QR en memoria
    qr_denso = qrcode.QRCode(
        version=10,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=6,
        border=1
    )
    qr_denso.add_data(sello_full)
    qr_denso.make(fit=True)
    qr_img_denso = qr_denso.make_image(fill_color="black", back_color="white")

    qr_buffer_denso = BytesIO()
    qr_img_denso.save(qr_buffer_denso, format="PNG")
    qr_buffer_denso.seek(0)
    img_pil_denso = Image.open(qr_buffer_denso)
    c.drawInlineImage(img_pil_denso, x=440, y=x_q, width=100, height=100)

    
    c.showPage()
    c.save()
    buffer_contenido.seek(0)

 # Leer el PDF dinámico que creaste (con 2 páginas)
    pdf_dinamico = PdfReader(buffer_contenido)
    pdf_salida = PdfWriter()

    # Página 1 de plantilla y contenido dinámico
    pagina_plantilla_1 = pdf_plantilla.pages[0]
    pagina_dinamica_1 = pdf_dinamico.pages[0]
    pagina_plantilla_1.merge_page(pagina_dinamica_1)
    pdf_salida.add_page(pagina_plantilla_1)

    # Página 2 de plantilla y contenido dinámico
    pagina_plantilla_2 = pdf_plantilla.pages[1]
    pagina_dinamica_2 = pdf_dinamico.pages[1]
    pagina_plantilla_2.merge_page(pagina_dinamica_2)
    pdf_salida.add_page(pagina_plantilla_2)

    # Escribir salida a buffer
    output_buffer = BytesIO()
    pdf_salida.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer  # o lo que uses para devolver el PDF
######################################### FIN PDF FISCALES ###########################################################################################################

######################################## PROCESO PDF MORALES ############################################################################################################
def generar_pdf_morales(datos_sat, idcif, rfc):

    # Extraer datos del diccionario para facilitar lectura
    datos = {k.strip().lower().replace(" ", "_"): v for k, v in datos_sat.items()}

    
    denominacion = datos.get("denominacion", "")
    regimen_capital = datos.get("regimen_capital", "")
    fecha_constitucion = datos.get("fecha_constitucion", "")
    situacion_contribuyente = datos.get("situacion_contribuyente", "")
    fecha_ultimo_cambio = datos.get("fecha_ultimo_cambio", "")
    fecha_inicio_operaciones = datos.get("fecha_de_inicio_de_operaciones", "")
    entidad_federativa = datos.get("entidad_federativa", "")
    cp = datos.get("cp", "")
    nombre_vialidad = datos.get("nombre_de_la_vialidad", "")
    numero_interior = datos.get("número_interior", "")
    municipio = datos.get("municipio_o_delegación", "")
    entidad_federativa = datos.get("entidad_federativa", "")
    tipo_vialidad = datos.get("tipo_de_vialidad", "")
    numero_exterior = datos.get("número_exterior", "")
    colonia = datos.get("colonia", "")
    resultado_fecha_actual = datos.get("fecha_actual", "")
    regimen = datos.get("régimen", "")
    fecha_alta = datos.get("fecha_de_alta", "")
    fecha_inicio = datos.get("fecha_inicio", "")
    nombre_completo = datos.get("nombre_completo", "")
    rfc = rfc.upper()
    
    
    
    #st.write("Estatus:", "Generado")
    
    # Descargar plantilla PDF desde GitHub
    #url_plantilla = "https://raw.githubusercontent.com/userprogram331/program/main/SAT4.pdf"
    url_plantilla = "https://raw.githubusercontent.com/userprogram331/archivo/main/moral.pdf"

    
    respuesta = requests.get(url_plantilla)
    if respuesta.status_code != 200:
        raise Exception(f"No se pudo descargar la plantilla, status: {respuesta.status_code}")

    buffer_plantilla = BytesIO(respuesta.content)
    pdf_plantilla = PdfReader(buffer_plantilla)

    # Generar código QR en memoria
    qr_data = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    #qr_data = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3="
    qr_img = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Crear buffer para contenido dinámico (capa superior)
    buffer_contenido = BytesIO()
    c = canvas.Canvas(buffer_contenido, pagesize=letter)
    width, height = letter

    def safe_text(text):
        if text is None:
            return ""
        return str(text)

    # Abrir la imagen QR con PIL para que ReportLab la acepte
    qr_buffer.seek(0)
    img_pil = Image.open(qr_buffer)

    # Insertar la imagen QR en la posición deseada con tamaño 100x100
    c.drawInlineImage(img_pil, 40, 550, width=100, height=100)

    # Dibujo de textos (tu código original resumido y corregido)
    text_width = c.stringWidth(rfc.upper(), "Helvetica", 8)
    x = (153 + 280 - text_width) / 2
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(130/255.0, 130/255.0, 130/255.0)
    c.drawString(x, 636, safe_text(rfc))

    c.drawString(205, 556, safe_text(idcif))

    text_width = c.stringWidth(rfc, "Helvetica", 7)
    x = (578 + 308 - text_width) / 2
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x, 528, safe_text(rfc))

    # Nombre completo en máximo 3 líneas centrado
    x1 = 153
    x2 = 280
    y_last_line = 591
    max_width = x2 - x1
    font_name = "Helvetica"
    font_size = 8
    line_spacing = font_size + 2
    c.setFont(font_name, font_size)
    c.setFillColorRGB(130/255.0, 130/255.0, 130/255.0)
    nombre_completo = denominacion 
    nombre_completo = safe_text(nombre_completo)
    text_width = c.stringWidth(nombre_completo, font_name, font_size)
    avg_char_width = text_width / max(len(nombre_completo), 1)
    if avg_char_width == 0:
        avg_char_width = 1  # evitar división por cero
    chars_per_line = int(max_width / avg_char_width)

    lines = textwrap.wrap(nombre_completo, width=chars_per_line)[:3]
    for i, line in enumerate(reversed(lines)):
        line_width = c.stringWidth(line, font_name, font_size)
        x = (x1 + x2 - line_width) / 2
        y = y_last_line + (i * line_spacing)
        c.drawString(x, y, line)

    def dibujar_texto(texto, x, y, font="Helvetica", size=8, color=(0,0,0)):
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        c.drawString(x, y, safe_text(texto))

    dibujar_texto(rfc, 231, 478)
    dibujar_texto(denominacion, 231, 457)
    dibujar_texto(regimen_capital, 231, 435)
    dibujar_texto(denominacion, 231, 413)
    #dibujar_texto(apellido_materno, 231, 391)

    def formatear_fecha(fecha_str):
        try:
            fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
            meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                     "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            return f"{fecha.day} DE {meses[fecha.month - 1]} DE {fecha.year}"
        except Exception:
            return fecha_str

    dibujar_texto(formatear_fecha(fecha_inicio), 231, 391)
    dibujar_texto(situacion_contribuyente, 231, 369)
    # Usar fecha_inicio si fecha_ultimo_cambio está vacío
    fecha_a_usar = fecha_ultimo_cambio if fecha_ultimo_cambio else fecha_inicio
    dibujar_texto(formatear_fecha(fecha_a_usar), 231, 347)

    dibujar_texto(cp, 95, 291)
    dibujar_texto(nombre_vialidad, 115, 269)
    dibujar_texto(numero_interior, 100, 247)

    dibujar_texto(municipio, 38, 220)
    dibujar_texto(municipio, 315, 220)
    dibujar_texto(entidad_federativa, 166, 203)
    dibujar_texto(tipo_vialidad, 378, 290)
    dibujar_texto(numero_exterior, 378, 269)
    dibujar_texto(colonia, 397, 247)

    x1 = 498
    x2 = 578
    y_last_line = 178
    y_single_line = 183
    max_width = x2 - x1



    #dibujar_texto(entidad_federativa, 535, 161)
    # Crear imagen de código de barras tipo Code128
    codigo_barras = code128.Code128(
        rfc,                 # Texto codificado
        barHeight=24,        # Altura de las barras
        barWidth=0.6         # Grosor de las barras
    )
    
    # Calcular el ancho del código de barras
    barcode_width = codigo_barras.width
    
    # Rango horizontal entre el que quieres centrar el código
    x1_barcode = 308
    x2_barcode = 578
    
    # Calcular posición X para centrar
    x_barcode = (x1_barcode + x2_barcode - barcode_width) / 2
    
    # Dibujar el código de barras centrado
    codigo_barras.drawOn(c, x=x_barcode, y=535)  # Y = altura desde la base
    #dibujar_texto(formatear_fecha(resultado_fecha_actual), 490, 631)

    # Área del campo resultado_fecha_actual
    x1 = 308
    x2 = 578
    max_width = x2 - x1
    
    # Texto seguro y formateado
    resultado_fecha_actual = safe_text(formatear_fecha(resultado_fecha_actual))
    
    # Intentar con fuente tamaño 10
    font_name = "Helvetica-Bold"
    font_size_try = 9
    c.setFont(font_name, font_size_try)
    text_width = c.stringWidth(resultado_fecha_actual, font_name, font_size_try)
    
    if text_width <= max_width:
        # Cabe con tamaño 10, centrar en y = 580
        line_width = text_width
        x = (x1 + x2 - line_width) / 2
        y = 580
        c.setFillColorRGB(0.0, 0.0, 0.0)
        c.drawString(x, y, resultado_fecha_actual)
    else:
        # No cabe, reducir tamaño a 8 y dividir en 2 líneas
        font_size = 8
        line_spacing = font_size + 2
        y_last_line = 573
    
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.0, 0.0, 0.0)
    
        text_width = c.stringWidth(resultado_fecha_actual, font_name, font_size)
        avg_char_width = text_width / max(len(resultado_fecha_actual), 1)
        chars_per_line = int(max_width / avg_char_width)
    
        lines = textwrap.wrap(resultado_fecha_actual, width=chars_per_line)[:2]
    
        for i, line in enumerate(reversed(lines)):
            line_width = c.stringWidth(line, font_name, font_size)
            x = (x1 + x2 - line_width) / 2
            y = y_last_line + (i * line_spacing)
            c.drawString(x, y, line)


    ############################
    c.showPage()
    if situacion_contribuyente == "SUSPENDIDO":
        regimen = None



     # Régimen Fiscal en la segunda página
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
    c.drawString(38, 648, safe_text(regimen))


 # Régimen Fiscal fecha inicio
    if situacion_contribuyente == "SUSPENDIDO":
        fecha_alta = None
    else:
        if fecha_alta and fecha_alta.strip():
            fecha_alta = fecha_alta.replace("-", "/")
        elif fecha_inicio_operaciones and fecha_inicio_operaciones.strip():
            fecha_alta = fecha_inicio_operaciones.replace("-", "/")
        else:
            fecha_alta = None
    #fecha_alta = fecha_alta.replace("-", "/")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
   
    
 # Régimen Fiscal fecha inicio
    
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
    c.drawString(455, 648, safe_text(fecha_alta))
    zona_mexico = pytz.timezone("America/Mexico_City")
    fecha_actual = datetime.now(zona_mexico).strftime("%Y/%m/%d")
    caracteres = string.ascii_letters + string.digits + '/+'
    longitud = 88
    longitud2 = 4

    cadena_aleatoria = ''.join(random.choices(caracteres, k=longitud))
    cadena_aleatoria2 = ''.join(random.choices(caracteres, k=longitud))
    cadena_aleatoria3 = ''.join(random.choices(caracteres, k=longitud2))

    sello_1 = f"||{fecha_actual}|{rfc}|CONSTANCIA DE SITUACIÓN FISCAL|200001088888800000031||"
    sello_2 = cadena_aleatoria
    sello_3 = cadena_aleatoria2
    sello_4 = cadena_aleatoria3
    #sello_full = sello_2 + sello_3 + sello_4
    sello_full="https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=0&D2=1&D3=%7C%7C2025%2F02%2F04%7C%7CCONSTANCIA+DE+SITUACI%D3N+FISCAL%7C200001088888800000031%7C%7C_aixL43%2BlaHcEhTqh2j2Nl%2FPUVLD0dNN7wGUAjCbcoqjcjKLjJMs5KRrC%2B%2B4hLtBPIqhCS%2F05Z9iGM7MaOpZwnAdhcRpy5H8%2BflESHLHJySP3LmhSbIliaGRjgWjT4k62%2BL6pwOOCk0Yjp69%2BX5Bsnl6n6M48by%2Bee5JionpQE3w%3D"

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.0, 0.0, 0.0)  # Negro
    c.drawString(155, 420, sello_1)
    c.drawString(155, 410, sello_2)
    c.drawString(155, 400, sello_3)
    c.drawString(155, 390, sello_4)


    # Generar QR en memoria
    qr_denso = qrcode.QRCode(
        version=10,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=6,
        border=1
    )
    qr_denso.add_data(sello_full)
    qr_denso.make(fit=True)
    qr_img_denso = qr_denso.make_image(fill_color="black", back_color="white")

    qr_buffer_denso = BytesIO()
    qr_img_denso.save(qr_buffer_denso, format="PNG")
    qr_buffer_denso.seek(0)
    img_pil_denso = Image.open(qr_buffer_denso)
    c.drawInlineImage(img_pil_denso, x=440, y=290, width=100, height=100)

    
    c.showPage()
    c.save()
    buffer_contenido.seek(0)

 # Leer el PDF dinámico que creaste (con 2 páginas)
    pdf_dinamico = PdfReader(buffer_contenido)
    pdf_salida = PdfWriter()

    # Página 1 de plantilla y contenido dinámico
    pagina_plantilla_1 = pdf_plantilla.pages[0]
    pagina_dinamica_1 = pdf_dinamico.pages[0]
    pagina_plantilla_1.merge_page(pagina_dinamica_1)
    pdf_salida.add_page(pagina_plantilla_1)

    # Página 2 de plantilla y contenido dinámico
    pagina_plantilla_2 = pdf_plantilla.pages[1]
    pagina_dinamica_2 = pdf_dinamico.pages[1]
    pagina_plantilla_2.merge_page(pagina_dinamica_2)
    pdf_salida.add_page(pagina_plantilla_2)

    # Escribir salida a buffer
    output_buffer = BytesIO()
    pdf_salida.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer  # o lo que uses para devolver el PDF
######################################### FIN PDF MORALES #################################################################################################################
# JSON con credenciales Google Sheets (reemplaza con tus datos si quieres)
#json_str = """
#{
#  "type": "service_account",
#  "project_id": "fifth-marker-459819-k2",
#  "private_key_id": "9ffd0aeeca59a53126ffce5aa0a5314cb9169d99",
#  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCEV8oZru3izghz\\n8Pv4xfTPh765kMEc4clOpc0n7nqyAxYbNqNMsRa95Jm7+z6iaT2LyrxYd3mMz2uf\\nfYjCxxdOUYv/f1iKkH2fJqTjLoWTkmphREkwTtrdpUACZ2hXS3n62kQCnPTzT98V\\nalN7/oAU01iSZQ/Jl0rgzuRjuXosL1rE/FG7/yUMWrhyBOrLkgvFiaaYqIxf4KJO\\nJLI5bHpcqS2wuvE2EBUwWQFN4tfAPubaZKTErFqHVNlNB5JvG9vjqxLchmrW/6z0\\nXnfxg0dLAaiutCqM2/4kmh+AIVHd51ZfBl4U6aZ0objboVp6Ya/zn85ugNOC1/r0\\nkMP5NUfBAgMBAAECggEAF73cDsF4AaEumQYZXea9ZWGX0JhsXG8Q+x/5bvl0X2z4\\nUUd7Ai4ew1A4WCXZda9lkCd9pG1CjAVF7GXL3A11W+J7OAmza6BCOQPovqzA39l7\\nZhmm+5iZ4PtdQVElwctThbIUU1evBdtFTQU3Ft5wQcwsbo7cxzByCWR0SoOirDxM\\ng9vbTiK5wZJxU23NEbyUR5D34eAKuxVgU9XSYO2i9LPBV98qta+5e3rOTuC30Sar\\nTWSApyVDTm0AkD7rBbKq1N/TO8sDtjman9DjMB57LAnrMi09I9EoSUeyQD3X3K24\\nDA4veCJmO7YRKaTu12KvCfnbritm2RNCWYa534TaNQKBgQC58vvAsewHlP+ObB3y\\nkI/zzBeyWlWS3KIsBvDtuSm2d5nJja940/YG9Ubtpnn4bZqki+5ktuownw7ooY7/\\nGtFBuaogMri3oi/VE1128IFTculk2nfNTxTBwBA+UwKvOULYe+zGWV8pQyr73e1a\\nflmyUUNtM+RkFCbqmlLMoSbUDwKBgQC2Mv+a3BY1m38/D05SO8y5fiHQpVyQXK3v\\n8rb/FEgq8enJOJyrjlDblFEpU4NKislwiCr/U5cgv0P7DPzIce7VfLW3KZzvu8ie\\nFLTnHTv5fn3hXR8BcJfJnG76EMoP1GcSkRI+THkrpW1QD4i+5PBmZcl/hC88qov5\\nGi429okXLwKBgEFhWPlY1beYwP5Pr3vxLlw3P4G7V2lK4E6Apke/mhYJGW6PvcnL\\nJS8vIKBAr5QU3ZHLjael1NQBqRlMbN3vjPICGPo3O1F92jmeFHfUenRf7AZE9mie\\nzJqPMGbpgwEfLgy2DftzwwzcDAoA7wqpcFpNTlrgKwaxOzmzxzch1mgrAoGAX7Ar\\nA7bAx0iyLHkqZg/X9jdjJQQjuAGkrBcpuo95U2yXnsFnrsXge2HKukyM8HIxVzN8\\neXn6Lg2lc00f2VnU2DRV7ysgq9tQgo1XcOWuoNqo29ofNY9feFf7BMQaivO/akXc\\ncfGR1bVc0qZF6BOumeitSZYvhMoBF0ODsAQMfasCgYEAjZfTx0nIE/iT2QT7GYZ+\\neq2j7VpmTFLWU4ciA1GULodlTLH+cei630Eva12yPm+MKKszdBR4eUTCR7IZqVRb\\nMzjAda2nboeHc9fR9ERzND79Gtxw5YufD0hjGmA42PpmtzSBtntXe4whzjy4PIqZ\\ndv4o4AI3UVFVhs+IFPAqHgk=\\n-----END PRIVATE KEY-----\\n",
#  "client_email": "usuarios@fifth-marker-459819-k2.iam.gserviceaccount.com",
#  "client_id": "106520291494181522144",
#  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#  "token_uri": "https://oauth2.googleapis.com/token",
#  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/usuarios%40fifth-marker-459819-k2.iam.gserviceaccount.com",
#  "universe_domain": "googleapis.com"
#}
#"""

#creds_dict = json.loads(json_str)
#scope = [
#    "https://spreadsheets.google.com/feeds",
#    "https://www.googleapis.com/auth/drive"
#]

#creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#client = gspread.authorize(creds)
#spreadsheet_id = "1ZK6axry0iM_V8hypIijSeZJsTWNC0QuzmOCzxlNr1CI"
#spreadsheet_id = "1D-AOOzfHLSTSyoFEgkx-fwMg0cjyBWFBbnIrNjNgfy4"
#sheet = client.open_by_key(spreadsheet_id).sheet1

@st.cache_data(ttl=600)
def cargar_datos():
    records = [
        {"correo": "NA", "usuario": "rr92", "contrasena": "rr92", "saldo": 9225, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
        {"correo": "NA", "usuario": "er94", "contrasena": "er94", "saldo": 10000, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
        {"correo": "NA", "usuario": "mr97", "contrasena": "mr97", "saldo": 10000, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
        {"correo": "NA", "usuario": "as90", "contrasena": "as90", "saldo": 10000, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
        {"correo": "NA", "usuario": "admin", "contrasena": "admin10", "saldo": 10000, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
        {"correo": "NA", "usuario": "nr98", "contrasena": "nr98", "saldo": 10000, "precio original": 25, "precio ficticia": 25, "precio manual": 25, "sesion": "cerrado", "error": "", "caducidad": "2025-11-02"},
    ]

    df_local = pd.DataFrame(records)
    df_local['usuario'] = df_local['usuario'].astype(str).str.strip()
    df_local['contrasena'] = df_local['contrasena'].astype(str).str.strip()
    #df_local['sesion'] = df_local['sesion'].astype(str).str.strip().str.lower()
    return df_local

#def actualizar_estado_sesion(usuario, nuevo_estado):
  
#    df = cargar_datos()
#    try:
#        idx = df.index[df['usuario'] == usuario][0]
#        fila_google_sheets = idx + 2
#        col_sesion = df.columns.get_loc('sesion') + 1
#        sheet.update_cell(fila_google_sheets, col_sesion, "cerrado")
#        return True
#    except Exception as e:
#        st.error(f"Error al actualizar sesión: {e}")
#        return False

class UnsafeAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs['ssl_context'] = ctx
        self.poolmanager = PoolManager(*args, **kwargs)
####################################################### PROCESO CONSULTA SAT FISCALES ###############################################################################
def consulta_sat(idcif, rfc, usuario):
    import socket
    from datetime import datetime
    import traceback

    session = requests.Session()
    session.mount("https://", UnsafeAdapter())

    url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    response = session.get(url)

    if response.status_code != 200:
        return None, f"Error HTTP {response.status_code}"

    soup = BeautifulSoup(response.text, "html.parser")
    celdas = soup.find_all("td")
    if not celdas:
        return None, "No se encontraron datos en la página SAT."

    datos_extraidos = {}
    for i in range(0, len(celdas) - 1, 2):
        clave = celdas[i].get_text(strip=True)
        valor = celdas[i+1].get_text(strip=True)
        datos_extraidos[clave] = valor

    # Guardar en Google Sheets
    #try:
    #    spreadsheet = client.open_by_key(spreadsheet_id)
    #    hoja_rfc = spreadsheet.worksheet("sheet3")
    #    zona_mexico = pytz.timezone("America/Mexico_City")
    

     #   fecha_hora = datetime.now(zona_mexico).strftime("%Y-%m-%d")
     #   fecha_hora2 = datetime.now(zona_mexico).strftime("%H:%M:%S")
     #   nombre_equipo = socket.gethostname()
     #   nueva_fila = [rfc, usuario, fecha_hora, fecha_hora2, nombre_equipo,idcif]

      #  hoja_rfc.append_row(nueva_fila, value_input_option='USER_ENTERED')
      #  print(f"RFC '{rfc}' y usuario '{usuario}' y fecha '{fecha_hora}' guardados exitosamente en sheet3.")
    #except Exception as e:
    #    print("Error al guardar en sheet3:", e)
    #    traceback.print_exc()

    return datos_extraidos, None


import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
def extraer_regimenes_de_datos(texto):
    regimenes = []
    # Aquí buscamos dentro de todo el texto el bloque con régimen + fecha de alta repetido
    # Ajusto regex para que encuentre todos los matches en el texto completo
    matches = re.findall(
        r'Régimen:\s*(.*?)\s*Fecha de alta:\s*(\d{2}-\d{2}-\d{4})', texto)
    for regimen, fecha in matches:
        regimenes.append({
            'Régimen': regimen.strip(),
            'Fecha de alta': fecha.strip()
        })

    # Variables por si no hay dos regimenes
    regimen1 = regimenes[0]['Régimen'] if len(regimenes) > 0 else None
    fecha1 = regimenes[0]['Fecha de alta'] if len(regimenes) > 0 else None
    regimen2 = regimenes[1]['Régimen'] if len(regimenes) > 1 else None
    fecha2 = regimenes[1]['Fecha de alta'] if len(regimenes) > 1 else None

    return regimen1, fecha1, regimen2, fecha2
############################################# FIN CONSULTA SAT FISCALES ##################################################################

############################################# CONSULTA SAT MORALES ########################################################################
def consulta_sat_morales(idcif, rfc, usuario):
    import socket
    from datetime import datetime
    import traceback

    session = requests.Session()
    session.mount("https://", UnsafeAdapter())

    url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    response = session.get(url)

    if response.status_code != 200:
        return None, f"Error HTTP {response.status_code}"

    soup = BeautifulSoup(response.text, "html.parser")
    celdas = soup.find_all("td")
    if not celdas:
        return None, "No se encontraron datos en la página SAT."

    datos_extraidos = {}
    for i in range(0, len(celdas) - 1, 2):
        clave = celdas[i].get_text(strip=True)
        valor = celdas[i+1].get_text(strip=True)
        datos_extraidos[clave] = valor

    # Guardar en Google Sheets
    #try:
    #    spreadsheet = client.open_by_key(spreadsheet_id)
    #    hoja_rfc = spreadsheet.worksheet("sheet3")
    #    zona_mexico = pytz.timezone("America/Mexico_City")
    #    fecha_hora = datetime.now(zona_mexico).strftime("%Y-%m-%d")
    #    fecha_hora2 = datetime.now(zona_mexico).strftime("%H:%M:%S")
    #    nombre_equipo = socket.gethostname()
    #    nueva_fila = [rfc, usuario, fecha_hora, fecha_hora2, nombre_equipo,idcif]

    #    hoja_rfc.append_row(nueva_fila, value_input_option='USER_ENTERED')
    #    print(f"RFC '{rfc}' y usuario '{usuario}' y fecha '{fecha_hora}' guardados exitosamente en sheet3.")
    #except Exception as e:
    #    print("Error al guardar en sheet3:", e)
    #    traceback.print_exc()

    return datos_extraidos, None


import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
def extraer_regimenes_de_datos_morales(texto):
    regimenes = []
    # Aquí buscamos dentro de todo el texto el bloque con régimen + fecha de alta repetido
    # Ajusto regex para que encuentre todos los matches en el texto completo
    matches = re.findall(
        r'Régimen:\s*(.*?)\s*Fecha de alta:\s*(\d{2}-\d{2}-\d{4})', texto)
    for regimen, fecha in matches:
        regimenes.append({
            'Régimen': regimen.strip(),
            'Fecha de alta': fecha.strip()
        })

    # Variables por si no hay dos regimenes
    regimen1 = regimenes[0]['Régimen'] if len(regimenes) > 0 else None
    fecha1 = regimenes[0]['Fecha de alta'] if len(regimenes) > 0 else None
    regimen2 = regimenes[1]['Régimen'] if len(regimenes) > 1 else None
    fecha2 = regimenes[1]['Fecha de alta'] if len(regimenes) > 1 else None

    return regimen1, fecha1, regimen2, fecha2
############################################ FIN CONSULTA SAT MORALES #######################################################################
########################################### ORDENAR DATOS FISCALES ######################################################################
def ordenar_datos(texto):
    limpio = texto  # Puedes limpiar el texto aquí si quieres
    resultado = {}

    # CURP
    curp = None
    coincidencias = list(re.finditer(r'CURP:\s*(.{1,50}?)\s*(Nombre:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            curp = posible_valor
            break
    resultado['CURP'] = curp

    # Nombre
    nombre = None
    coincidencias = list(re.finditer(r'Nombre:\s*(.{1,50}?)\s*(Apellido Paterno:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            nombre = posible_valor
            break
    resultado['Nombre'] = nombre

    # Apellido Paterno
    apellido_paterno = None
    coincidencias = list(re.finditer(r'Apellido Paterno:\s*(.{1,50}?)\s*(Apellido Materno:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            apellido_paterno = posible_valor
            break
    resultado['Apellido Paterno'] = apellido_paterno

    # NUEVAS VARIABLES AÑADIDAS

    apellido_materno = None
    coincidencias = list(re.finditer(r'Apellido Materno:\s*(.{1,50}?)\s*(Fecha Nacimiento:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            apellido_materno = posible_valor
            break
    resultado['Apellido Materno'] = apellido_materno

    fecha_nacimiento = None
    coincidencias = list(re.finditer(r'Fecha Nacimiento:\s*(.{1,50}?)\s*(Fecha de Inicio de operaciones:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_nacimiento = posible_valor
            break
    resultado['Fecha Nacimiento'] = fecha_nacimiento

    fecha_inicio_operaciones = None
    coincidencias = list(re.finditer(r'Fecha de Inicio de operaciones:\s*(.{1,50}?)\s*(Situación del contribuyente:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_inicio_operaciones = posible_valor
            break
    # Si no hay fecha de inicio, usar fecha nacimiento + 18 años
    if (not fecha_inicio_operaciones or fecha_inicio_operaciones == '') and fecha_nacimiento:
        try:
            fecha_nac = datetime.strptime(fecha_nacimiento, "%d/%m/%Y")  # Ajustar formato si es otro
            fecha_inicio_operaciones = fecha_nac.replace(year=fecha_nac.year + 18).strftime("%d/%m/%Y")
        except Exception as e:
            print("Error al convertir fecha de nacimiento:", e)
    resultado['Fecha de Inicio de operaciones'] = fecha_inicio_operaciones

    situacion_contribuyente = None
    coincidencias = list(re.finditer(r'Situación del contribuyente:\s*(.{1,50}?)\s*(Fecha del último cambio de situación:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            situacion_contribuyente = posible_valor
            break
    resultado['Situación del contribuyente'] = situacion_contribuyente

    fecha_ultimo_cambio = None
    
    # Regex para detectar fecha en formato dd-mm-yyyy o dd/mm/yyyy
    patron_fecha = re.compile(r"^\d{2}[-/]\d{2}[-/]\d{4}$")
    
    # Buscar todas las ocurrencias de "Fecha del último cambio de situación:"
    inicio_busqueda = 0
    while True:
        idx = limpio.find("Fecha del último cambio de situación:", inicio_busqueda)
        if idx == -1:
            break  # Ya no hay más coincidencias
    
        # Avanzar hasta después de la etiqueta
        idx_fecha = idx + len("Fecha del último cambio de situación:")
        posible_fecha = limpio[idx_fecha:idx_fecha + 10].strip()
    
        # Validar formato
        if patron_fecha.match(posible_fecha):
            fecha_ultimo_cambio = posible_fecha
            break  # ✅ Fecha válida encontrada, ya no seguimos buscando
    
        # Si no es fecha válida, seguir buscando después de esta posición
        inicio_busqueda = idx_fecha
    
    resultado['Fecha del último cambio de situación'] = fecha_ultimo_cambio
    
   
    entidad_federativa = None
    coincidencias = list(re.finditer(r'Entidad Federativa:\s*(.{1,50}?)\s*(Municipio o delegación:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            entidad_federativa = posible_valor
            break
    resultado['Entidad Federativa'] = entidad_federativa

    municipio = None
    coincidencias = list(re.finditer(r'Municipio o delegación:\s*(.{1,50}?)\s*(Colonia:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            municipio = posible_valor
            break
    resultado['Municipio o delegación'] = municipio

    colonia = None
    coincidencias = list(re.finditer(r'Colonia:\s*(.{1,50}?)\s*(Tipo de vialidad:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            colonia = posible_valor
            break
    resultado['Colonia'] = colonia

    tipo_vialidad = None
    coincidencias = list(re.finditer(r'Tipo de vialidad:\s*(.{1,50}?)\s*(Nombre de la vialidad:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            tipo_vialidad = posible_valor
            break
    resultado['Tipo de vialidad'] = tipo_vialidad

    nombre_vialidad = None
    coincidencias = list(re.finditer(r'Nombre de la vialidad:\s*(.{1,50}?)\s*(Número exterior:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            nombre_vialidad = posible_valor
            break
    resultado['Nombre de la vialidad'] = nombre_vialidad

    numero_exterior = None
    coincidencias = list(re.finditer(r'Número exterior:\s*(.{1,50}?)\s*(Número interior:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            numero_exterior = posible_valor
            break
    resultado['Número exterior'] = numero_exterior

    numero_interior = None
    coincidencias = list(re.finditer(r'Número interior:\s*(.{1,50}?)\s*(CP:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            numero_interior = posible_valor
            break
    resultado['Número interior'] = numero_interior

    cp = None
    coincidencias = list(re.finditer(r'CP:\s*(.{1,50}?)\s*(Correo electrónico:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            cp = posible_valor
            break
    resultado['CP'] = cp

    correo_electronico = None
    coincidencias = list(re.finditer(r'Correo electrónico:\s*(.{1,50}?)\s*(AL:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            correo_electronico = posible_valor
            break
    resultado['Correo electrónico'] = correo_electronico

    AL_al = None
    coincidencias = list(re.finditer(r'AL:\s*(.{1,50}?)\s*(Entidad Federativa:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            AL_al = posible_valor
            break
    resultado['AL'] = AL_al
########################################################################################
    regimen1, fecha1, regimen2, fecha2 = extraer_regimenes_de_datos(limpio)

    # Guardar en resultado
    resultado['Régimen'] = regimen1
    resultado['Fecha de alta'] = fecha1
    resultado['Régimen2'] = regimen2
    resultado['Fecha de alta2'] = fecha2
##########################################################################################
    #regimen = None
    #coincidencias = list(re.finditer(r'Régimen:\s*(.{1,50}?)\s*(Fecha de alta:|$)', limpio))
    #for match in coincidencias:
    #    posible_valor = match.group(1).strip()
    #    if posible_valor and not any(c in posible_valor for c in [':', '\n']):
    #        regimen = posible_valor
    #        break
    #if not regimen:
    #    regimen = "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios"
    #resultado['Régimen'] = regimen

    #fecha_alta = None
    #coincidencias = list(re.finditer(r'Fecha de alta:\s*(.{10})', limpio))
    #for match in coincidencias:
    #    posible_valor = match.group(1).strip()
    #    # Validación para evitar caracteres no deseados si quieres
    #    if posible_valor and not any(c in posible_valor for c in [':', '\n']):
    #        fecha_alta = posible_valor
    #        break
    #resultado['Fecha de alta'] = fecha_alta

    # Nombre completo concatenado
    nombre_completo = f"{safe_text(nombre)} {safe_text(apellido_paterno)} {safe_text(apellido_materno)}"
    resultado['Nombre completo'] = nombre_completo

    # Obtener fecha actual formateada
    def obtener_fecha_formato_largo():
        meses = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
            5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
            9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        zona_mexico = pytz.timezone("America/Mexico_City")
        hoy = datetime.now(zona_mexico)
        return f"{hoy.day:02d} DE {meses[hoy.month]} DE {hoy.year}"

    fecha_actual = obtener_fecha_formato_largo()
    resultado_fecha_actual = f"GUADALAJARA , JALISCO A {fecha_actual}"
    resultado['Fecha actual'] = resultado_fecha_actual
    # Suponiendo que texto_extraido se genera antes (por OCR, scraping, etc.)
    texto_extraido = resultado

    return resultado
############################################# FIN ORDENAR DATOS FISCALES ########################################################

############################################# ORDENAR DATOS MORALES ###############################################################
def ordenar_datos_morales(texto):
    limpio = texto  # Puedes limpiar el texto aquí si quieres
    resultado = {}

    # CURP
    denominacion = None
    coincidencias = list(re.finditer(r'Denominación o Razón Social:\s*(.{1,100}?)\s*(Régimen de capital:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            denominacion = posible_valor
            break
    resultado['denominacion'] = denominacion

    # Nombre
    regimen_capital = None
    coincidencias = list(re.finditer(r'Régimen de capital:\s*(.{1,50}?)\s*(Fecha de constitución:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            regimen_capital = posible_valor
            break
    resultado['regimen_capital'] = regimen_capital

    # Apellido Paterno
    fecha_constitucion = None
    coincidencias = list(re.finditer(r'Fecha de constitución:\s*(.{1,50}?)\s*(Fecha de Inicio de operaciones:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_constitucion = posible_valor
            break
    resultado['fecha_constitucion'] = fecha_constitucion

        # Apellido Paterno
    fecha_inicio = None
    coincidencias = list(re.finditer(r'Fecha de Inicio de operaciones:\s*(.{1,50}?)\s*(Situación del contribuyente:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_inicio = posible_valor
            break
    resultado['fecha_inicio'] = fecha_inicio
    # NUEVAS VARIABLES AÑADIDAS

    situacion_contribuyente = None
    coincidencias = list(re.finditer(r'Situación del contribuyente:\s*(.{1,50}?)\s*(Fecha del último cambio de situación:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            situacion_contribuyente = posible_valor
            break
    resultado['situacion_contribuyente'] = situacion_contribuyente

    fecha_ultimo_cambio = None
    coincidencias = list(re.finditer(r"Fecha del último cambio de situación:\s*(.{1,50}?)\s*(': 'Denominación o Razón Social:'|$)", limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_ultimo_cambio = posible_valor
            break
    resultado['fecha_ultimo_cambio'] = fecha_ultimo_cambio


    entidad_federativa = None
    coincidencias = list(re.finditer(r'Entidad Federativa:\s*(.{1,50}?)\s*(Municipio o delegación:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            entidad_federativa = posible_valor
            break
    resultado['entidad_federativa'] = entidad_federativa

   # fecha_ultimo_cambio = None
   # coincidencias = list(re.finditer(r'Fecha del último cambio de situación:\s*(.{1,50}?)\s*(CURP:|$)', limpio))
   # for match in coincidencias:
   #     posible_valor = match.group(1).strip()
   #     if posible_valor and not any(c in posible_valor for c in [':', '\n']):
   #         fecha_ultimo_cambio = posible_valor
   #         break
   # # Si no hay fecha último cambio, calcular fecha_nacimiento + 18 años + 2 meses
   # if (not fecha_ultimo_cambio or fecha_ultimo_cambio == '') and fecha_nacimiento:
   #     try:
   #         fecha_nac = datetime.strptime(fecha_nacimiento, "%d/%m/%Y")
   #         fecha_ultimo_cambio = (fecha_nac + relativedelta(years=18, months=2)).strftime("%d/%m/%Y")
   #     except Exception as e:
   #         print("Error al calcular fecha_ultimo_cambio:", e)
   # resultado['Fecha del último cambio de situación'] = fecha_ultimo_cambio


    municipio = None
    coincidencias = list(re.finditer(r'Municipio o delegación:\s*(.{1,50}?)\s*(Colonia:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            municipio = posible_valor
            break
    resultado['Municipio o delegación'] = municipio

    colonia = None
    coincidencias = list(re.finditer(r'Colonia:\s*(.{1,50}?)\s*(Tipo de vialidad:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            colonia = posible_valor
            break
    resultado['Colonia'] = colonia

    tipo_vialidad = None
    coincidencias = list(re.finditer(r'Tipo de vialidad:\s*(.{1,50}?)\s*(Nombre de la vialidad:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            tipo_vialidad = posible_valor
            break
    resultado['Tipo de vialidad'] = tipo_vialidad

    nombre_vialidad = None
    coincidencias = list(re.finditer(r'Nombre de la vialidad:\s*(.{1,50}?)\s*(Número exterior:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            nombre_vialidad = posible_valor
            break
    resultado['Nombre de la vialidad'] = nombre_vialidad

    numero_exterior = None
    coincidencias = list(re.finditer(r'Número exterior:\s*(.{1,50}?)\s*(Número interior:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            numero_exterior = posible_valor
            break
    resultado['Número exterior'] = numero_exterior

    numero_interior = None
    coincidencias = list(re.finditer(r'Número interior:\s*(.{1,50}?)\s*(CP:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            numero_interior = posible_valor
            break
    resultado['Número interior'] = numero_interior

    cp = None
    coincidencias = list(re.finditer(r'CP:\s*(.{1,50}?)\s*(Correo electrónico:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            cp = posible_valor
            break
    resultado['CP'] = cp

    correo_electronico = None
    coincidencias = list(re.finditer(r'Correo electrónico:\s*(.{1,50}?)\s*(AL:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            correo_electronico = posible_valor
            break
    resultado['Correo electrónico'] = correo_electronico

    fecha_inicio_operaciones = None
    coincidencias = list(re.finditer(r'Fecha de Inicio de operaciones:\s*(.{1,50}?)\s*(Situación del contribuyente:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            fecha_inicio_operaciones = posible_valor
            break
    # Si no hay fecha de inicio, usar fecha nacimiento + 18 años
    if (not fecha_inicio_operaciones or fecha_inicio_operaciones == '') and fecha_nacimiento:
        try:
            fecha_nac = datetime.strptime(fecha_nacimiento, "%d/%m/%Y")  # Ajustar formato si es otro
            fecha_inicio_operaciones = fecha_nac.replace(year=fecha_nac.year + 18).strftime("%d/%m/%Y")
        except Exception as e:
            print("Error al convertir fecha de nacimiento:", e)
    resultado['Fecha de Inicio de operaciones'] = fecha_inicio_operaciones
    
    
    AL_al = None
    coincidencias = list(re.finditer(r'AL:\s*(.{1,50}?)\s*(Entidad Federativa:|$)', limpio))
    for match in coincidencias:
        posible_valor = match.group(1).strip()
        if posible_valor and not any(c in posible_valor for c in [':', '\n']):
            AL_al = posible_valor
            break
    resultado['AL'] = AL_al

########################################################################################
    regimen1, fecha1, regimen2, fecha2 = extraer_regimenes_de_datos_morales(limpio)

    # Guardar en resultado
    resultado['Régimen'] = regimen1
    resultado['Fecha de alta'] = fecha1
    resultado['Régimen2'] = regimen2
    resultado['Fecha de alta2'] = fecha2
##########################################################################################
  #  regimen = None
  #  coincidencias = list(re.finditer(r'Régimen:\s*(.{1,50}?)\s*(Fecha de alta:|$)', limpio))
  #  for match in coincidencias:
  #      posible_valor = match.group(1).strip()
  #      if posible_valor and not any(c in posible_valor for c in [':', '\n']):
  #          regimen = posible_valor
  #          break
  #  if not regimen:
  #      regimen = "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios"
  #  resultado['Régimen'] = regimen

   # fecha_alta = None
   # coincidencias = list(re.finditer(r'Fecha de alta:\s*(.{10})', limpio))
   # for match in coincidencias:
   #     posible_valor = match.group(1).strip()
   #     # Validación para evitar caracteres no deseados si quieres
   #     if posible_valor and not any(c in posible_valor for c in [':', '\n']):
   #         fecha_alta = posible_valor
   #         break
    #resultado['Fecha de alta'] = fecha_alta

    # Nombre completo concatenado
    nombre_completo = denominacion
    resultado['Nombre_completo'] = nombre_completo

    # Obtener fecha actual formateada
    def obtener_fecha_formato_largo():
        meses = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
            5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
            9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        zona_mexico = pytz.timezone("America/Mexico_City")
        hoy = datetime.now(zona_mexico)
        return f"{hoy.day:02d} DE {meses[hoy.month]} DE {hoy.year}"

    fecha_actual = obtener_fecha_formato_largo()
    resultado_fecha_actual = f"GUADALAJARA , JALISCO A {fecha_actual}"
    resultado['Fecha actual'] = resultado_fecha_actual
    # Suponiendo que texto_extraido se genera antes (por OCR, scraping, etc.)
    texto_extraido = resultado

    return resultado

############################################ FIN ORDENAR DATOS MORALES ####################################################################
def safe_text(text):
    return str(text) if text is not None else ""

# ---------- CONFIGURACIÓN DE SESIONES ----------

SESION_FILE = "sesiones_activas.json"

def generar_sesion_id():
    return str(uuid.uuid4())

def cargar_sesiones():
    if not os.path.exists(SESION_FILE):
        return {}
    with open(SESION_FILE, "r") as f:
        return json.load(f)

def guardar_sesiones(sesiones):
    with open(SESION_FILE, "w") as f:
        json.dump(sesiones, f)

def registrar_sesion(usuario, sesion_id):
    sesiones = cargar_sesiones()
    sesiones[usuario] = {"sesion_id": sesion_id, "timestamp": time.time()}
    guardar_sesiones(sesiones)

def validar_sesion_activa(usuario, sesion_id):
    sesiones = cargar_sesiones()
    datos = sesiones.get(usuario)
    if not datos:
        return False
    return datos["sesion_id"] == sesion_id

def cerrar_sesion(usuario):
    sesiones = cargar_sesiones()
    if usuario in sesiones:
        del sesiones[usuario]
        guardar_sesiones(sesiones)

# ---------- LÓGICA DE LA APLICACIÓN ----------
###################################################### APP SALDO #########################################################################
def app_saldo(usuario, contrasena):
    # Validar que la sesión aún es válida
    if not validar_sesion_activa(usuario, st.session_state.get("sesion_id", "")):
        st.warning("Tu sesión ha sido cerrada porque fue iniciada en otro dispositivo.")
        st.session_state.clear()
        st.stop()

    df = cargar_datos()
    fila = df[(df['usuario'] == usuario) & (df['contrasena'] == contrasena)]
    
    if fila.empty:
        st.error("Usuario o contraseña incorrectos.")
        return False

    if fila.iloc[0]['sesion'] == 'activo':
        st.warning("Ya hay una sesión activa para este usuario. Cierre sesión antes de iniciar otra.")
        return False

   # if not actualizar_estado_sesion(usuario, "activo"):
    #    return False

    st.success(f"¡Bienvenido, {usuario}!")

    # Inicializar estados separados
    st.session_state.setdefault("consultado_fiscal", False)
    st.session_state.setdefault("datos_sat_fiscal", None)
    st.session_state.setdefault("error_sat_fiscal", None)

    st.session_state.setdefault("consultado_moral", False)
    st.session_state.setdefault("datos_sat_moral", None)
    st.session_state.setdefault("error_sat_moral", None)

    with st.form("form_sat"):
        rfc = st.text_input("RFC", max_chars=13, key="rfc_input")
        idcif = st.text_input("ID CIF", max_chars=11, key="idcif_input")
        
        col1, col2 = st.columns(2)
        with col1:
            enviar = st.form_submit_button("Consultar Fiscal")
        with col2:
            enviar_moral = st.form_submit_button("Consultar Moral")

    ################### CONSULTA FISCAL ###################
    if enviar:
        st.session_state.consultado_moral = False  # Evita mostrar moral si fiscal fue llamado

        if not idcif or not rfc:
            st.error("Debe ingresar ID CIF y RFC.")
        elif len(idcif.strip()) != 11:
            st.error("El ID CIF debe tener exactamente 11 caracteres.")
        elif len(rfc.strip()) != 13:
            st.error("El RFC Fiscal debe tener exactamente 13 caracteres.")
        else:
            datos_raw, error = consulta_sat(idcif.strip(), rfc.strip(), usuario)
            if datos_raw:
                texto_para_ordenar = "\n".join(f"{k}: {v}" for k, v in datos_raw.items())
                datos = ordenar_datos(texto_para_ordenar)
            else:
                datos = None

            st.session_state.consultado_fiscal = True
            st.session_state.datos_sat_fiscal = datos
            st.session_state.error_sat_fiscal = error

    if st.session_state.consultado_fiscal:
        if st.session_state.error_sat_fiscal:
            st.error(f"Error: {st.session_state.error_sat_fiscal}")
        elif st.session_state.datos_sat_fiscal:
            st.success("Estatus: Generado")
            pdf_bytes = generar_pdf(st.session_state.datos_sat_fiscal, idcif, rfc)

            if st.download_button(
                label="Descargar PDF",
                data=pdf_bytes.getvalue(),
                file_name=f"{rfc.upper()}.pdf",
                mime="application/pdf",
                key="download_fiscal_pdf"
            ):
                for key in ["consultado_fiscal", "datos_sat_fiscal", "error_sat_fiscal", "rfc_input", "idcif_input"]:
                    st.session_state.pop(key, None)

    ################### CONSULTA MORAL ###################
    if enviar_moral:
        st.session_state.consultado_fiscal = False  # Evita mostrar fiscal si moral fue llamado

        if not idcif or not rfc:
            st.error("Debe ingresar ID CIF y RFC.")
        elif len(idcif.strip()) != 11:
            st.error("El ID CIF debe tener exactamente 11 caracteres.")
        elif len(rfc.strip()) != 12:
            st.error("El RFC Moral debe tener exactamente 12 caracteres.")
        else:
            datos_raw, error = consulta_sat_morales(idcif.strip(), rfc.strip(), usuario)
            if datos_raw:
                texto_para_ordenar = "\n".join(f"{k}: {v}" for k, v in datos_raw.items())
                datos = ordenar_datos_morales(texto_para_ordenar)
            else:
                datos = None

            st.session_state.consultado_moral = True
            st.session_state.datos_sat_moral = datos
            st.session_state.error_sat_moral = error

    if st.session_state.consultado_moral:
        if st.session_state.error_sat_moral:
            st.error(f"Error: {st.session_state.error_sat_moral}")
        elif st.session_state.datos_sat_moral:
            st.success("Estatus: Generado")
            pdf_bytes = generar_pdf_morales(st.session_state.datos_sat_moral, idcif, rfc)

            if st.download_button(
                label="Descargar PDF",
                data=pdf_bytes.getvalue(),
                file_name=f"{rfc.upper()}.pdf",
                mime="application/pdf",
                key="download_moral_pdf"
            ):
                for key in ["consultado_moral", "datos_sat_moral", "error_sat_moral", "rfc_input", "idcif_input"]:
                    st.session_state.pop(key, None)

    ################### CERRAR SESIÓN ###################
    if st.button("Cerrar sesión"):
        cerrar_sesion(usuario)
       # actualizar_estado_sesion(usuario, "inactivo")
        st.session_state.clear()

        
    return True

def main():
    st.title("Sistema de Inicio de Sesión")

    if "logueado" not in st.session_state:
        st.session_state.logueado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = ""
    if "contrasena" not in st.session_state:
        st.session_state.contrasena = ""

    if not st.session_state.logueado:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("Iniciar sesión")

        if submit_login:
            if not usuario or not contrasena:
                st.error("Por favor ingrese usuario y contraseña.")
            else:
                df = cargar_datos()
                fila = df[(df['usuario'] == usuario.strip()) & (df['contrasena'] == contrasena.strip())]
                if fila.empty:
                    st.error("Usuario o contraseña incorrectos.")
                else:
                    fecha_caducidad_str = fila.iloc[0]['caducidad']
                    try:
                        fecha_caducidad = datetime.strptime(fecha_caducidad_str, "%Y-%m-%d").date()
                        zona_mexico = pytz.timezone("America/Mexico_City")
                        hoy = datetime.now(zona_mexico).date()
                
                        if fecha_caducidad >= hoy:
                            st.session_state.logueado = True
                            st.session_state.usuario = usuario.strip()
                            st.session_state.contrasena = contrasena.strip()
                            st.session_state.sesion_id = generar_sesion_id()
                            registrar_sesion(usuario.strip(), st.session_state.sesion_id)
                            return
                        else:
                            st.error("Licencia expirada. Contacte al administrador.")
                    except Exception as e:
                        st.error(f"Error al verificar la fecha de caducidad: {e}")
    else:
        app_saldo(st.session_state.usuario, st.session_state.contrasena)

if __name__ == "__main__":
    main()
