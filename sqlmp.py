#!/usr/bin/python

import curses
import signal
import sqlite3
import sys

import db_pl
import display
import libdb
import menu
import music
import playlist

import keys

def exitpl(*args):
    sys.exit();

    
def init_dict(disp, player):
    out = dict();
    out.update(dict.fromkeys(keys.UP, disp.up));
    out.update(dict.fromkeys(keys.DOWN, disp.down));
    out.update(dict.fromkeys(keys.VOLUP, player.vol_up));
    out.update(dict.fromkeys(keys.VOLDOWN, player.vol_down));
    out.update(dict.fromkeys(keys.PLAYPAUSE, player.play_pause));
    out.update(dict.fromkeys(keys.QUIT, exitpl));
    out.update(dict.fromkeys(keys.SWITCH, disp.switch_view));
    out.update(dict.fromkeys(keys.COMMAND, disp.grab_input));
    out.update(dict.fromkeys(keys.SELECT, disp.select));

    return out;


def run(conn, curs, disp, player):
    action = init_dict(disp, player);

    while(True):
        disp.refresh()
        key = disp.getkey()
        
        if key in action:
            action[key](disp, curs, player);
            
 
def init_windows(curs):
    bottom_bar = 5
    hh = curses.LINES - bottom_bar + 1;
    ww = curses.COLS // 6;
    
    leftwin = menu.Menu(0, 0, ww, hh, form=lambda x: x.name);
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
    
    return display.Player_disp(leftwin, rightwin, botwin)


def main(stdscr):
    curses.use_default_colors()

    curses.curs_set(False);
    
    stdscr.clear();

    db = "lib.db";
    conn = sqlite3.connect(db);
    curs = conn.cursor();

    disp = init_windows(curs);

    player = music.init_music();

    disp.refresh();
    run(conn, curs, disp, player);

if __name__ == "__main__":
    curses.wrapper(main);
