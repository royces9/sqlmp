#!/usr/bin/python

import curses
import os
import queue
import signal
import sys
import threading
import time
import traceback

import menu
import musicdb
import player_disp
import playlist
import socket_thread
            
from loadconf import config as config
import debug

import locale
locale.setlocale(locale.LC_ALL, '')

def init_colours():
    curses.start_color()
    curses.use_default_colors()

    colours = [config.FOCUSED, config.CURSOR, config.HIGHLIGHT_COLOUR, config.NORMAL]

    for i, c in enumerate(colours, 1):
        if c[0] is None:
            curses.init_pair(i, c[1], c[2])
            c[0] = curses.color_pair(i)


def init_windows(db, stdscr):
    hh, ww, bottom_bar, cc = config.set_size(stdscr)

    leftwin = menu.Menu(0, 0, ww, hh,
                        data=[playlist.Playlist(name=pl, db=db) for pl in db.list_pl()],
                        form=lambda x: ((x.name, 1),),
                        cursor_colour=config.FOCUSED[0],
                        highlight_colour=config.FOCUSED[0],
                        normal_colour=config.NORMAL[0])

    rightwin = menu.Menu(ww, 0, cc - ww, hh,
                         data=leftwin.data[0].data,
                         form=config.SONG_DISP,
                         cursor_colour=config.CURSOR[0],
                         highlight_colour=config.HIGHLIGHT_COLOUR[0],
                         normal_colour=config.NORMAL[0])

    botwin = menu.Window(0, hh, cc, bottom_bar)


    return player_disp.Player_disp([leftwin, rightwin, botwin], stdscr, db)


def __inp(disp, qq):
    while True:
        key = disp.getkey()
        if key in disp.actions:
            qq.put_nowait((key))



def main_loop(disp):
    remote = socket_thread.Remote(disp, config.SOCKET)

    inp_thread = threading.Thread(target=__inp, args=(disp,remote,), daemon=True)
    inp_thread.start()

    while not disp.die:
        start = time.time()
        item = remote.get_nowait() if not remote.empty() else None

        if item in disp.actions:
            disp.actions[item]()
        elif item:
            pl, fn = item
            for p in pl:
                for f in fn:
                    if os.path.isdir(f):
                        disp.adddir((f, p))
                    else:
                        disp.addfile((f, p))

        disp.draw()
        diff = time.time() - start

        if diff < disp.frame_time:
            time.sleep(disp.frame_time - diff)


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
    
    try:
        stdscr = curses.initscr()

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        stdscr.keypad(1)

        sys.stdout.write("\x1b]2;sqlmp\x07")
        sys.stdout.flush()

        if curses.has_colors():
            init_colours()
    except:
        cleanup(stdscr)
        print('curses error:')
        print(traceback.format_exc())
        return

    try:
        db = musicdb.Musicdb(config.DBPATH, config.LIBPATH)
    except Exception as e:
        print('db error:')
        print(e)
        print(traceback.format_exc())

    try:
        signal.signal(signal.SIGINT, lambda a, b: cleanup(stdscr, True))
        disp = init_windows(db, stdscr)
        main_loop(disp)
        cleanup(stdscr)

    except Exception as e:
        cleanup(stdscr)
        print('error: ')
        print(traceback.format_exc())



if __name__ == "__main__":
    main()

