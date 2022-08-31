import curses
import os
import signal
import sys

import colours
import loadconf
import init
import musicdb
import player_ui
import remote
            
import config
import debug

def cleanup(exit_f=False):
    if os.path.exists(config.SOCKET):
        os.remove(config.SOCKET)
    
    curses.echo()
    curses.nocbreak()

    colours.reset_colours()
    curses.resetty()
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
        signal.signal(signal.SIGINT, lambda a, b: cleanup(True))

        #init the ui
        ui = player_ui.Player_ui(stdscr, palette, db)

        #init remote
        remote.Remote(ui, config.SOCKET)

        #start mainloop
        ui.mainloop()

        #cleanup curses
        cleanup()

    except Exception as e:
        cleanup()
        debug.print_error('error:', e)
