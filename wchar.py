import ctypes
import os

import debug

#no need to import clib because wchar.h is #included in wide.c
wide = ctypes.CDLL(os.path.dirname(__file__) + '/wide.so')
wide.set_width.restype = ctypes.c_wchar_p


def wcwidth(c):
    """
    return width of character, if string inputted, only the first character
    """
    inp = ctypes.c_wchar(c[0])
    return wide.wcwidth(inp)


def wcswidth(s):
    """
    return width and length of string
    """
    n = len(s)
    inp = ctypes.c_wchar_p(s)
    return wide.wcswidth(inp, n), n


def set_width(s, n):
    inp = ctypes.c_wchar_p(s)
    return wide.set_width(inp, n)
