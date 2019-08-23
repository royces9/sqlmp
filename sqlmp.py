#!/usr/bin/python

import curses
import sqlite3
import sys
import threading

import menu
import music
import musicdb
import player_disp

import keys

def exitpl(*args):
    sys.exit()

    
def init_dict(disp, player):
    out = dict()
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
        player.vol_up,
        player.vol_down,
        player.play_pause,
        exitpl,
        disp.switch_view,
        disp.grab_input,
        disp.select,
    ]

    assert len(_keys) == len(vals)

    for key, val in zip(_keys, vals):
        out.update(dict.fromkeys(key, val))

    return out;

def info_print(disp, player):
    disp[2].print_line(0, 0, "Nothing currently playing")
    while True:
        fn = player.curplay()
        disp[2].print_line(0, 0, disp[2].blank)
        if fn:
            line = fn['title'] + ' - ' + fn['artist'] + ' - ' + fn['album']
            disp[2].print_line(0, 0, line)

        disp[2].refresh()

def run(conn, curs, disp, player, stdscr):
    action = init_dict(disp, player)

    yolothread = threading.Thread(target=info_print, args=(disp,player,))
    yolothread.daemon = True
    yolothread.start()

    while True:
        disp.refresh()

        key = disp.getkey()
        if key in action:
            action[key](disp, curs, player)
        elif key == 'KEY_RESIZE':
            disp.resize(stdscr)
 
def init_windows(conn, curs):
    bottom_bar = 5
    hh = curses.LINES - bottom_bar + 1
    ww = curses.COLS // 6
    
    leftwin = menu.Menu(0, 0, ww, hh, form=lambda x: (x.name, 0), highlight_colour=keys.FOCUSED, normal_colour=keys.NORMAL)
    rightwin = menu.Menu(ww, 0, curses.COLS - ww, hh, form=keys.SONG_DISP, highlight_colour=keys.HIGHLIGHTED, normal_colour=keys.NORMAL)
    botwin = menu.Window(0, hh - 1, curses.COLS, bottom_bar)
    
    return player_disp.Player_disp([leftwin, rightwin, botwin], conn, curs)


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


def main(stdscr):
    curses.curs_set(False);
    stdscr.clear();
    
    init_colours()

    conn = sqlite3.connect(keys.LIBPATH);
    curs = conn.cursor();

    disp = init_windows(conn, curs);
    player = music.init_music();

    run(conn, curs, disp, player, stdscr);

if __name__ == "__main__":
    curses.wrapper(main);
