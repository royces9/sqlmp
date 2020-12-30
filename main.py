import curses
import os
import signal
import sys

import loadconf
import init
import musicdb
import player_ui
import remote
            
import config
import debug

def cleanup(stdscr, exit_f=False):
    if os.path.exists(config.SOCKET):
        os.remove(config.SOCKET)
    
    curses.echo()
    curses.nocbreak()
    stdscr.keypad(0)

    curses.endwin()

    if exit_f:
        sys.exit()


def main():
    if os.path.exists(config.SOCKET):
        sys.exit('sqlmp socket already open')
    
    stdscr, palette = init.ncurses()

    try:
        db = musicdb.Musicdb(config.DBPATH, config.LIBPATH)
    except Exception as e:
        debug.print_error('db error:', e)

    try:
        signal.signal(signal.SIGINT, lambda a, b: cleanup(stdscr, True))

        #init the ui
        ui = player_ui.Player_ui(stdscr, palette, db)

        #init remote
        remote.Remote(ui, config.SOCKET)

        #start mainloop
        ui.mainloop()

        #cleanup curses
        cleanup(stdscr)

    except Exception as e:
        cleanup(stdscr)
        debug.print_error('error:', e)
