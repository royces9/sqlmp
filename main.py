import curses
import os
import signal
import sys

import debug
import init
import musicdb
import remote
            
from loadconf import config

def cleanup(stdscr, exit_f=False):
    if os.path.exists(config.SOCKET):
        os.remove(config.SOCKET)
    
    curses.echo()
    curses.nocbreak()
    stdscr.keypad(0)

    curses.endwin()

    if exit_f:
        sys.exit()


def mainloop(ui):
    while not ui.die:
        #check input queue for any new things to do
        item = ui.inpq.get()

        #do something based off of type of item
        item[0](item, ui)


def main():
    if os.path.exists(config.SOCKET):
        sys.exit('sqlmp socket already open')
    
    stdscr = init.ncurses()

    try:
        db = musicdb.Musicdb(config.DBPATH, config.LIBPATH)
    except Exception as e:
        debug.print_error('db error:', e)

    try:
        signal.signal(signal.SIGINT, lambda a, b: cleanup(stdscr, True))

        #init the ui
        ui = init.windows(db, stdscr)

        #init remote
        remote.Remote(ui, config.SOCKET)

        #start mainloop
        mainloop(ui)

        #cleanup curses
        cleanup(stdscr)

    except Exception as e:
        cleanup(stdscr)
        debug.print_error('error:', e)
