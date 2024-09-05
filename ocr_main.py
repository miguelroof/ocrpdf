#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        
# Purpose:     
#
# Author:      tejada.miguel@gmail.com
#
# Created:     06/12/2021
# Licence:     GPL

# -------------------------------------------------------------------------------
# __all__ = ['project', 'qApp', 'unit', 'settings','tempDir']
__author__ = "Miguel Tejada"
__version__ = "0.0"
__email__ = "tejada.miguel@gmail.com"
__license__ = "tejada.miguel@gmail.com"
__versionHistory__ = [
    ["0.0", "231009", "MTEJADA", "START"]]

import os
# Requires Python 3.6 or higher due to f-strings

# Import libraries
import platform
from PIL import Image
from tempfile import TemporaryDirectory
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2

if platform.system() == "Windows":
    # We may need to do some additional downloading and setup...
    # Windows needs a PyTesseract Download
    # https://github.com/UB-Mannheim/tesseract/wiki/Downloading-Tesseract-OCR-Engine

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    # Windows also needs poppler_exe
    # agrego
    path_to_poppler_exe = Path(r'.\poppler\Library\bin')

    # Put our output files in a sane place...
    out_directory = Path(r"~\Desktop").expanduser()
else:
    out_directory = Path("~").expanduser()

# Path of the Input pdf
PDF_file = Path(r"./PILBT001.pdf")

# Store all the pages of the PDF in a variable
image_file_list = []

text_file = Path("./out_text.txt")


def pdf_ocr(pdf_file):
    ''' Main execution point of the program'''
    PDF_file = Path(pdf_file)
    dpi = 500
    with TemporaryDirectory() as tempdir:
        # Create a temporary directory to hold our temporary images.

        """
        Part #1 : Converting PDF to images
        """

        if platform.system() == "Windows":
            pdf_pages = convert_from_path(
                PDF_file, dpi)#, poppler_path=path_to_poppler_exe)
        else:
            pdf_pages = convert_from_path(PDF_file, dpi)
        # Read in the PDF file at 500 DPI

        # Iterate through all the pages stored above
        for page_enumeration, page in enumerate(pdf_pages, start=1):
            # enumerate() "counts" the pages for us.

            # Create a file name to store the image
            filename = f"{tempdir}\page_{page_enumeration:03}.jpg"

            # Declaring filename for each page of PDF as JPG
            # For each page, filename will be:
            # PDF page 1 -> page_001.jpg
            # PDF page 2 -> page_002.jpg
            # PDF page 3 -> page_003.jpg
            # ....
            # PDF page n -> page_00n.jpg

            # Save the image of the page in system
            page.save(filename, "JPEG")
            image_file_list.append(filename)

        """
        Part #2 - Recognizing text from the images using OCR
        """

        with open(text_file, "a") as output_file:
            for image_file in image_file_list:

                # img = Image.open(image_file)
                img = cv2.imread(image_file)
                img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = cv2.GaussianBlur(img, (5,5), 0)
                # ret, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

                img_height = img.shape[0]
                config = "--oem 3 --psm 12"
                data = pytesseract.image_to_data(img,lang='eng', output_type='dict')
                i = len(data['level'])-1
                while i >= 0:
                    dt_txt = data['text'][i]
                    if dt_txt in ('', ' ', '  '):
                        for k in data.keys():
                            data[k].pop(i)
                    i -= 1

                boxes = len(data['level'])
                code_pos = None
                for i in range(boxes):
                    if data['text'][i] == "CODE":
                        code_pos = (data['left'][i], data['top'][i] + data['height'][i])
                        break
                # obtengo ahora las posiciones en la misma linea
                if not code_pos:
                    return
                vert_range = 2.5*(img_height-code_pos[1])/19
                for i in range(boxes):
                    txt_pos = (data['left'][i], data['top'][i] + data['height'][i])
                    if -0.5*vert_range < (txt_pos[1]-code_pos[1]) < vert_range and txt_pos[0] > code_pos[0]:
                        print(data['text'][i], txt_pos)




def searchable_shx(pdf_name, page_num):
    from PyPDF2 import PdfFileReader, PdfFileWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape, A3
    from datetime import date, time, datetime, timedelta
    import io, os
    with open(pdf_name, 'rb') as pdf_file:
        pdf = PdfFileReader(pdf_file, strict=False)
        page = pdf.getPage(page_num)
        objs = []
        for annot in page['/Annots']:
            obj = annot.getObject()
            if 'AutoCAD SHX Text' in obj.values():
                # print(obj['/Contents'], obj['/Rect'])
                objs.append(obj)

        page_size = pdf.getPage(page_num).mediaBox.upperRight
        w, h = page_size
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=landscape(A3))
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(colors.grey)
        for obj in objs:
            if '/Contents' in obj:
                xy = tuple(obj['/Rect'])  # get
                llx, lly, urx, ury = xy  # LowerLeftX,LowerLeftY,UpperRightX, UpperRightY
                text = obj['/Contents']
                x1 = int(urx)
                y1 = int(lly)
                c.drawString(x1, y1, text)
        c.save()
        # buffer start from 0
        packet.seek(0)
        new_pdf = PdfFileReader(packet)
        page = None
        new_pdf_file_name = None
        # read existing pdf
        output = PdfFileWriter()
        page = pdf.getPage(page_num)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        # Finally output new pdf
        new_pdf_file_name = os.path.splitext(pdf_name)[0] + ".annot.pdf"
        outputStream = open(new_pdf_file_name, "wb")
        output.write(outputStream)
        outputStream.close()
        return new_pdf_file_name
        # os.startfile(new_pdf_file_name, 'open')

if __name__ == "__main__":
    # We only want to run this if it's directly executed!
    pdf_name = searchable_shx(os.path.join('.', 'PILBT001.pdf'), 0)
    print("--------------------------------")
    pdf_ocr(pdf_name)

