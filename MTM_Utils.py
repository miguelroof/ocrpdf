#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        MTM_Utils
# Purpose:     Utiles matematicos y otros
#
# Author:      tejada.miguel@gmail.com
#
# Created:     17/03/2014
# Licence:     GPL

# -------------------------------------------------------------------------------
__all__ = ['MyDecoder', 'MyEncoder', 'OrderedSet', 'OrderedWeakrefSet', 'SmartDict', 'is_number', 'parentDir',
           'importDataFromCSV']

import json, sys
import os
from pathlib import Path
from json.encoder import (_make_iterencode, JSONEncoder,
                          encode_basestring_ascii, INFINITY,
                          c_make_encoder, encode_basestring)

from json.decoder import JSONDecoder
import pickle, base64
import datetime
import weakref
from collections import OrderedDict
from collections.abc import MutableSet

__version__ = "1.0"
__versionHistory__ = [["0.0", "171227", "MTEJADA", "Inicio"],
                      ["1.0", "220907", "MTEJADA", "Migracion a python 3.10"]]

# -----------------------------CODIFICADORES PARA JSON---------------------------
#
parentDir = Path(__file__).parent
# if parentDir.name == 'modulos':
#     parentDir = parentDir.parent
# parentDir = str(parentDir)
# os.chdir(parentDir)


class MyEncoder(JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        # Force the use of _make_iterencode instead of c_make_encoder
        # Force the use of _make_iterencode instead of c_make_encoder
        _one_shot = False
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=float.__repr__, _inf=INFINITY, _neginf=-INFINITY):
            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        if False:  # (_one_shot and c_make_encoder is not None and self.indent is None):
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot, isinstance=self.isinstance)
        return _iterencode(o, 0)

    def isinstance(self, obj, cls):
        cls = (cls,) if not isinstance(cls, tuple) else cls
        if type(obj) in cls:
            return True
        return False

    def default(self, obj):
        """
        Defines custom serialization.

        To avoid circular references, any object that will always fail
        self.isinstance must be converted to something that is
        deserializable here.
        """
        if type(obj) == datetime.datetime:
            return {"__class__": "datetime.datetime", "data": obj.isoformat()}
        elif type(obj) == set:
            return {"__class__": "set", "data": list(obj)}
        elif type(obj) == OrderedSet:
            return {"__class__": "MTM_Utils.OrderedSet", "data": list(obj)}
        elif type(obj) == OrderedDict:
            return {"__class__": "collections.OrderedDict", "data": list(zip(obj.keys(), obj.values()))}
        elif hasattr(obj, '__json__'):
            return obj.__json__()
        else:
            try:
                # print(obj)
                return {"__pickle__": True, "data": base64.b64encode(pickle.dumps(obj)).decode('ascii')}
            except:
                raise IOError("Bad object ", obj)


class MyDecoder(JSONDecoder):
    def __init__(self, project=None, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        self.project = project

    def object_hook(self, obj):
        if isinstance(obj, dict):
            if '__jsoncls__' in obj:
                modname, mymethod = obj['__jsoncls__'].split(":", 1)
                __import__(modname)
                objlist = mymethod.split(".")
                jobj = getattr(sys.modules[modname], objlist[0])
                for oob in objlist[1:-1]:
                    jobj = getattr(jobj, oob)
                createdObj = getattr(jobj, objlist[-1])(obj)
                if hasattr(createdObj, '_proxyProject') and self.project:
                    createdObj._proxyProject = weakref.ref(self.project)
                return createdObj
            elif '__class__' in obj:
                if obj['__class__'] == "datetime.datetime":
                    return datetime.datetime.strptime(obj['data'], "%Y-%m-%dT%H:%M:%S.%f")
                elif obj['__class__'] == 'set':
                    return set(obj['data'])
                else:
                    if "." in obj['__class__']:
                        modname, clase = obj['__class__'].split('.')
                        __import__(modname)
                        jobj = getattr(sys.modules[modname], clase)
                    return jobj(obj['data'])

            elif '__pickle__' in obj:
                valor = pickle.loads(base64.b64decode(obj['data'].encode('ascii')))
                return valor
        return obj


# SMART CLASES
class OrderedSet(OrderedDict, MutableSet):
    def __init__(self, lista=None):
        super(OrderedSet, self).__init__()
        if not lista is None:
            self.update(lista)

    def update(self, *args, **kwargs):
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                self.add(e)

    def add(self, elem):
        self[elem] = None

    def discard(self, elem):
        self.pop(elem, None)

    def reorder(self, lista):
        self.clear()
        self.update(lista)

    def __le__(self, other):
        return all(e in other for e in self)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(e in self for e in other)

    def __gt__(self, other):
        return self >= other and self != other

    def __repr__(self):
        return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))

    def __str__(self):
        return '{%s}' % (', '.join(map(repr, self.keys())))

    difference = property(lambda self: self.__sub__)
    difference_update = property(lambda self: self.__isub__)
    intersection = property(lambda self: self.__and__)
    intersection_update = property(lambda self: self.__iand__)
    issubset = property(lambda self: self.__le__)
    issuperset = property(lambda self: self.__ge__)
    symmetric_difference = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union = property(lambda self: self.__or__)


class OrderedWeakrefSet(weakref.WeakSet):
    def __init__(self, values=()):
        super(OrderedWeakrefSet, self).__init__()
        self.data = OrderedSet()
        for elem in values:
            self.add(elem)

    def add(self, elem):
        super(OrderedWeakrefSet, self).add(elem)


class SmartDict():
    "Clase que define un diccionario acumulativo inteligente y ordenado"

    def __init__(self, dic=None, autoFill=False):
        self.autoFill = autoFill
        if not dic:
            self._keys = []
            self._values = []
        elif isinstance(dic, (dict, OrderedDict)):
            self._keys = list(dic.keys())
            self._values = list(dic.values())
        elif isinstance(dic, (list, tuple)):
            key, value = zip(*dic)
            self._keys, self._values = list(key), list(value)

    def __setitem__(self, key, value):
        if key not in self._keys:
            self._keys.append(key)
            self._values.append(None)
        self._values[self._keys.index(key)] = value

    def __getitem__(self, key):
        if key not in self._keys and self.autoFill:
            self._keys.append(key)
            self._values.append(SmartDict())
        return self._values[self._keys.index(key)]

    def __len__(self):
        return len(self._keys)

    def __nonzero__(self):
        return bool(self._keys)

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def __delitem__(self, key):
        if self.has_key(key):
            indice = self._keys.index(key)
            self._keys.pop(indice)
            self._values.pop(indice)

    def has_key(self, key):
        return key in self._keys

    def get(self, key):
        if self.has_key(key):
            return self.__getitem__(key)
        else:
            return None

    def index(self, key):
        return self._keys.index(key)

    def insert(self, index, key, value):
        "inserta en el indice pasado el par llave valor"
        if key in self._keys:
            raise IOError(" %s already exists in dictionary" % key)
            return
        self._keys.insert(index, key)
        self._values.insert(index, value)

    def replaceKey(self, oldkey, newkey):
        if not self.has_key(oldkey):
            raise IOError(" %s not found in dictionary" % oldkey)
            return
        if newkey != oldkey and newkey in self._keys:
            raise IOError(" %s arlready exists in dictionary" % newkey)
            return
        self._keys[self._keys.index(oldkey)] = newkey

    def __repr__(self):
        return "SmartDict(" + str(zip(self._keys, self._values)) + ")"

    def __iter__(self):
        return iter(zip(self._keys, self._values))

    def pop(self, key):
        if self.has_key(key):
            indice = self._keys.index(key)
            self._keys.pop(indice)
            return self._values.pop(indice)
        else:
            return None

    def items(self):
        return iter(zip(self._keys, self._values))

    def copy(self):
        from copy import deepcopy
        return SmartDict(zip(deepcopy(self._keys), deepcopy(self._values)), autoFill=self.autoFill)

    def clear(self):
        self._keys = []
        self._values = []


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def importDataFromCSV(filename, asDict=False):
    import csv
    data = []
    for endode in ['utf-8-sig', 'latin1', 'utf-8']:
        try:
            with open(os.path.join(parentDir, 'data', filename), mode='r', encoding=endode) as csv_file:
                if asDict:
                    csv_reader = csv.DictReader(csv_file, delimiter=";")
                else:
                    csv_reader = csv.reader(csv_file, delimiter=";")
                data = list(csv_reader)
            return data
        except:
            continue
    return data


if __name__ == '__main__':
    import math
