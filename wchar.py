import ctypes

libc = ctypes.CDLL(None)

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
    """
    return s truncated to n wide
    if the width of s is less than n, return s
    """
    wid, _len = wcswidth(s)
    if wid == -1:
        return ""
    if wid >= n:
        for i, c in enumerate(reversed(s)):
            cw = wcwidth(c)
            if cw == -1:
                return ""
            wid -= cw
            if wid < n:
                return s[:_len - i - 1]

    return s
