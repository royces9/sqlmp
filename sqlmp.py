#!/usr/bin/python

import atexit
import curses
import os
import signal
import sys

import menu
import musicdb
import player_disp
import playlist
import socket_thread

import config
import debug


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

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    return player_disp.Player_disp([leftwin, rightwin, botwin], stdscr, db)


def main_loop(disp):
    remote = socket_thread.Remote(disp, config.SOCKET)
    while True:
        disp.refresh()
        key = disp.getkey()

        if key in disp.actions:
            disp.actions[key]()

        while not remote.empty():
            pl, fn = remote.get_nowait()
            for p in pl:
                for f in fn:
                    if os.path.isdir(f):
                        disp.adddir((f, p))
                    else:
                        disp.addfile((f, p))
"""
def __inp(disp, qq):
    while True:
        key = disp.getkey()
        if key in disp.actions:
            qq.put_nowait((key))

import threading
def main_loop(disp):
    remote = socket_thread.Remote(disp)
    inp_thread = threading.Thread(target=__inp, args=(disp,remote,), daemon=True)
    inp_thread.start()

    while True:
        disp.refresh()
        item = remote.get()
            
        if item in disp.actions:
            disp.actions[item]()            
        else:
            pl, fn = item
            for p in pl:
                for f in fn:
                    if os.path.isdir(f):
                        disp.adddir((f, p))
                    else:
                        disp.addfile((f, p))
"""


def cleanup(stdscr):
    curses.echo()
    curses.nocbreak()
    stdscr.keypad(0)

    if os.path.exists(config.SOCKET):
        os.remove(config.SOCKET)

    curses.endwin()
    

def main(stdscr):
    db = musicdb.Musicdb(config.DBPATH, config.LIBPATH)

    disp = init_windows(db, stdscr)

    main_loop(disp)


if __name__ == "__main__":
    if os.path.exists(config.SOCKET):
        sys.exit('sqlmp socket already open')

    try:
        stdscr = curses.initscr()

        atexit.register(cleanup, stdscr)
        signal.signal(signal.SIGTERM, lambda: cleanup(stdscr))

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        if curses.has_colors():
            init_colours()

        stdscr.keypad(True)
        main(stdscr)

    except Exception as e:
        cleanup(stdscr)
        import traceback
        print(traceback.format_exc())

        print("Error: " + str(e))
        sys.exit()
