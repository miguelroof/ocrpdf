#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        read_concise_pdf.py
# Purpose:     Search important info from DM2M shopdrawings
#
# Author:      tejada.miguel@gmail.com
#
# Created:     10/10/2023
# Licence:     GPL

# -------------------------------------------------------------------------------
# __all__ = ['project', 'qApp', 'unit', 'settings','tempDir']
__author__ = "Miguel Tejada"
__version__ = "0.0"
__email__ = "tejada.miguel@gmail.com"
__license__ = "tejada.miguel@gmail.com"
__versionHistory__ = [
    ["0.0", "231010", "MTEJADA", "START"]]

import os

from PyPDF2 import PdfFileReader, PdfFileWriter
from pathlib import Path
from MTM_Utils import is_number
from MTM_html import loadTextToWebbrowser


def pdf_to_html(pdf_path):
    if False:
        from pymupdf4llm import to_markdown
        import markdown
        md_text = to_markdown(pdf_path)
        html_text = markdown.markdown(md_text)
        loadTextToWebbrowser(html_text, filepath='test.html')

    else:
        import pypdf2htmlEX
        PDF = pypdf2htmlEX.PDF(str(pdf_path))
        PDF.to_html()



if __name__ == '__main__':
    pdf_path = Path(os.path.abspath('.'), 'concise.pdf')
    pdf_to_html(pdf_path)