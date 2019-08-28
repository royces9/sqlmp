#!/usr/bin/python

import curses
import sqlite3
import sys
import threading

import menu
import musicdb
import player
import player_disp

import keys

def info_print(disp):
    while True:
        fn = disp.player.curplay()
        disp[2].print_line(0, 0, disp[2].blank)
        if fn:
            line = fn['title'] + ' - ' + fn['artist'] + ' - ' + fn['album']
            disp[2].print_line(0, 0, line)

        disp[2].refresh()

        
def run(disp, stdscr):
    action = init_dict(disp)

    infothread = threading.Thread(target=info_print, args=(disp,), daemon=True)
    infothread.start()

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

    if not keys.FOCUSED:
        curses.init_pair(1, keys.FOCUSED_FG, keys.FOCUSED_BG)
        keys.FOCUSED=curses.color_pair(1)

    if not keys.HIGHLIGHTED:
        curses.init_pair(2, keys.HIGHLIGHTED_FG, keys.HIGHLIGHTED_BG)
        keys.HIGHLIGHTED=curses.color_pair(2)

    if not keys.NORMAL:
        curses.init_pair(3, keys.NORMAL_FG, keys.NORMAL_BG)
        keys.NORMAL=curses.color_pair(3)

        
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
    ]

    assert len(_keys) == len(vals)

    for key, val in zip(_keys, vals):
        out.update(dict.fromkeys(key, val))

    return out;


def init_windows(db, play, stdscr):
    hh, ww, bottom_bar, ll, cc = keys.set_size(stdscr)
    
    leftwin = menu.Menu(0, 0, ww, hh, form=lambda x: (x.name, 0),
                        highlight_colour=keys.FOCUSED, normal_colour=keys.NORMAL)
    rightwin = menu.Menu(ww, 0, cc - ww, hh, form=keys.SONG_DISP,
                         highlight_colour=keys.HIGHLIGHTED, normal_colour=keys.NORMAL)
    botwin = menu.Window(0, hh, cc, bottom_bar)

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    return player_disp.Player_disp([leftwin, rightwin, botwin], db, play)


def main(stdscr):
    curses.curs_set(False)
    stdscr.clear()
    init_colours()

    db = musicdb.Musicdb(keys.LIBPATH)

    play = player.Player()
    disp = init_windows(db, play, stdscr)
    disp[2].print_line(0, 0, "Nothing currently playing")

    run(disp, stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
