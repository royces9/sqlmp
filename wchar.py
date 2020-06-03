import ctypes
import os

import debug

libc = ctypes.CDLL(None)
wide = ctypes.CDLL(os.path.dirname(__file__) + '/wide.so')
wide.set_width.restype = ctypes.c_wchar_p


def wcwidth(c):
    """
    return width of character, if string inputted, only the first character
    """
    inp = ctypes.c_wchar(c[0])
    return libc.wcwidth(inp)


def wcswidth(s):
    """
    return width and length of string
    """
    n = len(s)
    inp = ctypes.c_wchar_p(s)
    return libc.wcswidth(inp, n), n


def set_width(s, n):
    inp = ctypes.c_wchar_p(s)
    return wide.set_width(inp, n)



