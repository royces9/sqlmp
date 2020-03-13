import curses
import threading

global_lock = threading.Lock()

def decorator(func):
    def inner(*args, **kwargs):
        with global_lock:
            out = func(*args, **kwargs)

        return out

    return inner


def exception_deco(func):
    def inner(*args, **kwargs):
        try:
            out = func(*args, **kwargs)
            return out
        except:
            pass
        
    return inner


class Threadwin:
    def __init__(self, *args, **kwargs):
        self.__win = curses.newwin(*args, **kwargs)

        #grab all the callable things from curses window and put it into this class
        for attr in dir(self.__win):
            if not attr.startswith('__'):
                if callable(getattr(self.__win, attr)):
                    setattr(self, attr, decorator(getattr(self.__win, attr)))
                else:
                    setattr(self, attr, getattr(self.__win, attr))

        setattr(self, 'addnstr', exception_deco(getattr(self.__win, 'addnstr')))
        
