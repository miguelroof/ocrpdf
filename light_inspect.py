#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        light_inspect.py
# Purpose:     Light inspect utils for pdf files
#
# Author:      tejada.miguel@gmail.com
#
# Created:     09/10/2023
# Licence:     GPL
import os

# -------------------------------------------------------------------------------
# __all__ = ['project', 'qApp', 'unit', 'settings','tempDir']

from PyPDF2 import PdfFileReader, PdfFileWriter


def read_data_type(pdf_path, page_num):
    with open(pdf_path, 'rb') as pdf_file:
        pdf = PdfFileReader(pdf_file, strict=False)
        page = pdf.getPage(page_num)
        objs = []
        for anot in page['/Annots']:
            obj = anot.getObject()
            if 'AutoCAD' in obj.values():
                objs.append(obj)
                print(obj.values())



if __name__ == '__main__':
    pdf_path = os.path.join('.', '2023_08_15_2483 Control Bldg Makkah - 08 - PRECAST ELEVATIONS I.pdf')
    read_data_type(pdf_path, 0)
