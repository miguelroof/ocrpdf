#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        inspect_shpdwg.py
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


def load_family_filehead():
    "Funcion que carga el encabezado de las famililas desde el sistema"


def get_shpdwg_info(pdf_path):

    with open(pdf_path, 'rb') as pdf_file:
        pdf = PdfFileReader(pdf_file, strict=False)
        page = pdf.getPage(0)
        objs = []
        for annot in page['/Annots']:
            obj = annot.getObject()
            if 'AutoCAD SHX Text' in obj.values():
                objs.append(obj)
    # ahora inspecciono todos los objetos
    file_name = os.path.basename(pdf_path)


    data_dict = {'filename': os.path.basename(pdf_path),
                 'shp_data': '',
                 'revision': [],
                 'code': [],
                 'type': [],
                 'units': 0,
                 'volume': 0.0,
                 'weight': 0.0,
                 'steel': 0.0,
                 'mesh': 0.0,
                 'wire': 0.0,
                 'length': 0.0,
                 'width': 0.0,
                 'height': 0.0,
                 'date': '',
                 'strands': 0,
                 'work_number': [],
                 'work_title': [],
                 'by': ''
                 }
    top_left = None
    bot_right = [0,10000]

    # busco las esquinas del cajetin
    for obj in objs:
        obj_rect = obj.get('/Rect', (0,1000,0,1000)) # max_x, min_y, min_x, max_y
        bot_right[0] = max(bot_right[0], obj_rect[0])
        bot_right[1] = min(bot_right[1], obj_rect[1])
        if obj.get('/Contents', '').startswith('THIS PLAN'):
            top_left = [obj_rect[2],obj_rect[1]]

    if not top_left:
        return data_dict
    # proporcion del cajetin: 100 x 40, sin incluir la tabla de armado
    caj_width = bot_right[0] - top_left[0]
    caj_height = caj_width*40/100
    area_cajetin = [(top_left[0],bot_right[1]+caj_height), (bot_right[0],bot_right[1])]
    area_tabla = [(top_left[0],top_left[1]), (bot_right[0], bot_right[1]+caj_height)]

    def is_in_area(point, area):
        return area[0][0] <= point[0] <= area[1][0] and area[0][1] >= point[1] >= area[1][1]

    region_tabla = {'code': None,
                    'type': None,
                    'units': None,
                    'volume': None,
                    'weight': None,
                    'steel': None,
                    'mesh': None,
                    'wire': None,
                    'truss': None}

    region_cajetin = {'work:': None,
                      'location:': None,
                      'max.length:':None,
                      'strands:':None,
                      'n':None,
                      'date:':None,
                      'by:':None,
                      'rev':None}

    i = 0
    h_text_type = caj_height/15
    datos_tabla = []
    datos_cajetin = []
    for obj in objs:
        contenido = obj.get('/Contents', '').lower()
        rectangle = obj.get('/Rect') # max_x, min_y, min_x, max_y: bot_right, top_left
        if not contenido or not rectangle:
            continue
        if is_in_area((rectangle[2],rectangle[3]), area_tabla):
            founded = False
            for k in region_tabla.keys():
                if contenido.startswith(k) and region_tabla[k] is None:
                    region_tabla[k] = rectangle
                    founded = True
                    break
            if not founded:
                if contenido.startswith('('):
                    continue
                elif 0.5*(rectangle[1]+rectangle[3]) > (0.5*(area_tabla[0][1]+area_tabla[1][1])): # si el punto superior no esta en la mitad inferior, quita
                    continue
                elif abs(rectangle[1]-rectangle[3]) < 0.7*h_text_type:
                    continue
                else:
                    datos_tabla.append(obj)
        elif is_in_area((rectangle[2],rectangle[3]), area_cajetin):
            founded = False
            for k in region_cajetin.keys():
                if contenido.startswith(k) and region_cajetin[k] is None:
                    if k == 'n' and len(contenido) == 2:
                        region_cajetin[k] = obj['/Rect']
                        founded = True
                    else:
                        region_cajetin[k] = obj['/Rect']
                        founded = True
                    if founded:
                        break
            if not founded:
                datos_cajetin.append(obj)

    # LA TABLA SE DIVIDIRA EN 8 COLUMNAS MAS O MENOS REGULARES

    min_x_tabla = region_tabla['code'][2] if region_tabla['code'] else area_tabla[0][0]
    if region_tabla['wire']:
        max_x_tabla = region_tabla['wire'][0]
    elif region_tabla['truss']:
        max_x_tabla = region_tabla['truss'][0]
    else:
        max_x_tabla = area_tabla[1][0]
    col_width = (max_x_tabla - min_x_tabla)/8
    col_dict = {0: 'code', 1:'type', 2:'units', 3:'volume', 4:'weight', 5:'steel', 6:'mesh', 7:'wire'}
    col_dict_inv = {'code':0,  'type':1, 'units':2, 'volume':3, 'weight':4, 'steel':5, 'mesh':6, 'wire':7}
    for obj in datos_tabla:
        rectangle  = obj.get('/Rect')
        contenido = obj.get('/Contents','')
        if is_number(contenido):
            contenido = float(contenido)

        elif contenido in ('-','_'):
            contenido = 0.0
        centro_x = (rectangle[0]*0.7+rectangle[2]*0.3)
        indice_by_position = int((centro_x-min_x_tabla)/col_width)
        # indice_by_region = None
        # for k_name, k_rect in region_tabla.items():
        #     if k_rect[2] - 0.5*h_text_type <= centro_x <= k_rect[0]+0.5*h_text_type:
        #         indice_by_region = col_dict_inv[k_name if k_name != 'truss' else 'wire']
        #         break
        if indice_by_position == 1 and isinstance(contenido, str) and 'T' in contenido:
            contenido = contenido.rsplit('T',1)[-1]
            if is_number(contenido):
                contenido = int(contenido)
        elif indice_by_position == 2 and isinstance(contenido, float):
            contenido = int(round(contenido, 0))
        if indice_by_position > 1 and not isinstance(contenido, (int,float)):
            contenido = 0.0
        if indice_by_position == 3 and obj.get('/Contents') == '3':
            contenido = 0.0
        if indice_by_position == 7 and contenido != 0.0 and region_tabla['truss']: # es un panel y el hierro tiene que ir al
            data_dict['steel'] += contenido
        elif indice_by_position > 1:
            data_dict[col_dict[indice_by_position]] += contenido







    return data_dict




if __name__ == '__main__':
    pdf_path = os.path.join('.', 'JL50T161.pdf')
    print(get_shpdwg_info(pdf_path))

