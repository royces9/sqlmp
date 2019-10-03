#!/usr/bin/python

import curses
import sqlite3
import sys

import menu
import musicdb
import player
import player_disp
import playlist

import keys
import debug

def main_loop(disp):
    action = init_dict(disp)
    debug.debug('Start')

    while True:
        disp.refresh()

        curses.flushinp()
        key = disp.getkey()

        if key not in {'k', 'l'}:
            debug.debug(key)

        if key in action:
            action[key]()

            
def init_colours():
    curses.start_color()
    curses.use_default_colors()

    colours = [keys.FOCUSED, keys.CURSOR, keys.HIGHLIGHT_COLOUR, keys.NORMAL]

    for i, c in enumerate(colours, 1):
        if c[0] is None:
            curses.init_pair(i, c[1], c[2])
            c[0] = curses.color_pair(i)

        
def init_dict(disp):
    out = dict()

    pairs = [
        [keys.UP, disp.up],
        [keys.DOWN, disp.down],
        [keys.LEFT, disp.player.seek_backward],
        [keys.RIGHT, disp.player.seek_forward],
        [keys.VOLUP, disp.player.vol_up],
        [keys.VOLDOWN, disp.player.vol_down],
        [keys.PLAYPAUSE, disp.player.play_pause],
        [keys.QUIT, sys.exit],
        [keys.SWITCH, disp.switch_view],
        [keys.COMMAND, disp.grab_input],
        [keys.SELECT, disp.select],
        [keys.HIGHLIGHT, disp.highlight],
        [keys.TRANSFER, disp.transfer],
        [keys.DELETE, disp.delete],
        [['KEY_RESIZE'], disp.resize],
    ]
    
    for key, val in pairs:
        out.update(dict.fromkeys(key, val))

    return out


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
    main_loop(disp)

if __name__ == "__main__":
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

        curses.endwin()
