import curses
import threading

global_lock = threading.Lock()

def decorator(func):
    def inner(*args, **kwargs):
        global_lock.acquire()
        out = func(*args, **kwargs)
        global_lock.release()
        return out

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
