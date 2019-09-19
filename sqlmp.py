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
        
def run(disp, stdscr):
    action = init_dict(disp)

    while True:
        disp.refresh()

        key = disp.getkey()

        if key in action:
            action[key](disp)
        elif key == 'KEY_RESIZE':
            disp.resize(stdscr)

def init_colours():
    curses.start_color()
    curses.use_default_colors()

    colours = [keys.FOCUSED, keys.CURSOR, keys.HIGHLIGHT_COLOUR, keys.NORMAL]

    for i, c in enumerate(list(range(len(colours))), 1):
        aa = colours[c]
        if aa[0] is None:
            curses.init_pair(i, aa[1], aa[2])
            aa[0] = curses.color_pair(i)

        
def init_dict(disp):
    out = dict()

    def exitpl(*args):
        sys.exit()

    _keys = [
        keys.UP,
        keys.DOWN,
        keys.VOLUP,
        keys.VOLDOWN,
        keys.PLAYPAUSE,
        keys.QUIT,
        keys.SWITCH,
        keys.COMMAND,
        keys.SELECT,
        keys.HIGHLIGHT,
        keys.TRANSFER,
        keys.DELETE,
    ]

    vals = [
        disp.up,
        disp.down,
        disp.player.vol_up,
        disp.player.vol_down,
        disp.player.play_pause,
        exitpl,
        disp.switch_view,
        disp.grab_input,
        disp.select,
        disp.highlight,
        disp.transfer,
        disp.delete,
    ]

    assert len(_keys) == len(vals)

    for key, val in zip(_keys, vals):
        out.update(dict.fromkeys(key, val))

    return out;


def init_windows(db, play, stdscr):
    hh, ww, bottom_bar, ll, cc = keys.set_size(stdscr)
    
    leftdata = [playlist.Playlist(name=pl, db=db) for pl in db.list_pl()]
    plname = lambda x: ((x.name, 1),)
    leftwin = menu.Menu(0, 0, ww, hh, data=leftdata, form=plname, 
                        cursor_colour=keys.FOCUSED[0],
                        highlight_colour=keys.FOCUSED[0],
                        normal_colour=keys.NORMAL[0])

    #set data for the first playlist
    rightdata = leftdata[0].data
    rightwin = menu.Menu(ww, 0, cc - ww, hh, data=rightdata, form=keys.SONG_DISP,
                         cursor_colour=keys.CURSOR[0],
                         highlight_colour=keys.HIGHLIGHT_COLOUR[0],
                         normal_colour=keys.NORMAL[0])
    botwin = menu.Window(0, hh, cc, bottom_bar)

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    return player_disp.Player_disp([leftwin, rightwin, botwin], db, play)


def main(stdscr):
    curses.curs_set(False)
    stdscr.clear()

    if curses.has_colors():
        init_colours()

    db = musicdb.Musicdb(keys.DBPATH, keys.LIBPATH)

    play = player.Player()
    disp = init_windows(db, play, stdscr)
    disp[2].print_line(0, 0, "Nothing currently playing")

    run(disp, stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
