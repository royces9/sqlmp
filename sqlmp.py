#!/usr/bin/python

import curses
import os
import sys

import menu
import musicdb
import player
import player_disp
import playlist
import socket_thread

import keys
import debug


def init_colours():
    curses.start_color()
    curses.use_default_colors()

    colours = [keys.FOCUSED, keys.CURSOR, keys.HIGHLIGHT_COLOUR, keys.NORMAL]

    for i, c in enumerate(colours, 1):
        if c[0] is None:
            curses.init_pair(i, c[1], c[2])
            c[0] = curses.color_pair(i)


def init_windows(db, play, stdscr):
    hh, ww, bottom_bar, ll, cc = keys.set_size(stdscr)

    leftwin = menu.Menu(0, 0, ww, hh,
                        data=[playlist.Playlist(name=pl, db=db) for pl in db.list_pl()],
                        form=lambda x: ((x.name, 1),), 
                        cursor_colour=keys.FOCUSED[0],
                        highlight_colour=keys.FOCUSED[0],
                        normal_colour=keys.NORMAL[0])

    rightwin = menu.Menu(ww, 0, cc - ww, hh,
                         data=leftwin.data[0].data,
                         form=keys.SONG_DISP,
                         cursor_colour=keys.CURSOR[0],
                         highlight_colour=keys.HIGHLIGHT_COLOUR[0],
                         normal_colour=keys.NORMAL[0])

    botwin = menu.Window(0, hh, cc, bottom_bar)

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    return player_disp.Player_disp([leftwin, rightwin, botwin], stdscr, db, play)


def main(stdscr):
    db = musicdb.Musicdb(keys.DBPATH, keys.LIBPATH)

    play = player.Player()
    disp = init_windows(db, play, stdscr)

    socket_thread.start_socket(disp)

    disp.main_loop()

    
if __name__ == "__main__":
    if os.path.exists(keys.SOCKET):
        sys.exit('sqlmp socket already open')
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        if curses.has_colors():
            init_colours()

        stdscr.keypad(True)
        main(stdscr)

    finally:
        curses.echo()
        curses.nocbreak()
        stdscr.keypad(0)
        
        os.remove(keys.SOCKET)
        curses.endwin()
