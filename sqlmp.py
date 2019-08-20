#!/usr/bin/python

import curses
import signal
import sqlite3
import sys
import threading

import db_pl
import display
import libdb
import menu
import music
import playlist

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

def info_print():
    while True:
        fn = player.curplay()
        disp[2].print_line(0, 0, disp[2].blank)
        if fn:
            line = fn['title'] + ' - ' + fn['artist'] + ' - ' + fn['album']
            disp[2].print_line(0, 0, line)

        disp[2].refresh()

def run(conn, curs, disp, player):
    action = init_dict(disp, player)

    yolothread = threading.Thread(target=info_print)
    yolothread.daemon = True
    yolothread.start()

    while True:
        disp.refresh()
        try:
            key = disp.getkey()
        except:
            key = None
            pass
        if key in action:
            action[key](disp, curs, player)
            
 
def init_windows(curs):
    bottom_bar = 5
    hh = curses.LINES - bottom_bar + 1;
    ww = curses.COLS // 6;
    
    leftwin = menu.Menu(0, 0, ww, hh, form=lambda x: (x.name, 0));
    rightwin = menu.Menu(ww, 0, curses.COLS - ww, hh, form=keys.SONG_DISP)
    botwin = menu.Window(0, hh - 1, curses.COLS, bottom_bar)
    
    str_pl = libdb.list_playlists(curs)
    playlists = []

    for i, pl in enumerate(str_pl):
        leftwin.win.addstr(i, 0, pl);
        playlists.append(playlist.Playlist(name=pl, curs=curs))


    leftwin.data = playlists
    rightwin.data = leftwin.data[0].data
    rightwin.disp()

    leftwin.win.chgat(0, 0, curses.A_STANDOUT)
    rightwin.win.chgat(0, 0, curses.A_STANDOUT)

    leftwin.win.syncok(True)
    rightwin.win.syncok(True)
    botwin.win.syncok(True)
    
    return display.Player_disp(leftwin, rightwin, botwin)


def main(stdscr):
    curses.use_default_colors()

    curses.curs_set(False);
    
    stdscr.clear();

    conn = sqlite3.connect(keys.LIBPATH);
    curs = conn.cursor();
    global disp
    disp = init_windows(curs);
    global player
    player = music.init_music();

    disp.refresh();
    run(conn, curs, disp, player);

if __name__ == "__main__":
    curses.wrapper(main);
