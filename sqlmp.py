#!/usr/bin/python

import curses
import sqlite3
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame.mixer as pgm
import sys

import libdb
import menu
import music
import pl

import keys

class Disp:
    cur = 0;
    wins = [];

    def __init__(self, *argv):
        for arg in argv:
            self.wins.append(arg);
    def append(self, arg):
        self.wins.append(arg);
    
    def len(self):
        return len(self.wins);

    def refresh(self):
        for win in self.wins:
            win.refresh();

    def curwin(self):
        return self.wins[self.cur];


def exec_inp(inp):
    return inp;


def grab_input(win):
    curses.echo();
    out = win.getstr(2, 1, curses.COLS - 2);
    curses.noecho()

    win.addnstr(2, 0, " " * curses.COLS, curses.COLS);
    win.refresh();

    return out;

def get_songs_playlist(playlist, win, curs):
    songs = pl.list_pl_songs(playlist, curs);
    out = [];
    for i, song in enumerate(songs):
        song = song.replace("'", r"''");
        for songstr in curs.execute(f"SELECT title, artist, path FROM library WHERE path='{song}';"):
            out.append([songstr[0], songstr[1], songstr[2]]);
            
    return out;

def scroll_up(disp, curs):
    curwin = disp.curwin();
    curwin.up();
    disp.wins[2].print_line(0, 2, curwin.form(curwin.selected()));
    if disp.cur == 0:
        listwin = disp.wins[0];
        plwin = disp.wins[1];
        plwin.cursor = 0;
        plwin.offset = 0;
        plwin.data = get_songs_playlist(listwin.selected(), disp.wins[1], curs);
        plwin.disp()

def scroll_down(disp, curs):
    curwin = disp.curwin();
    curwin.down();
    disp.wins[2].print_line(0, 2, curwin.form(curwin.selected()));
    if disp.cur == 0:
        listwin = disp.wins[0];
        plwin = disp.wins[1];
        plwin.cursor = 0;
        plwin.offset = 0;
        plwin.data = get_songs_playlist(listwin.selected(), disp.wins[1], curs);
        plwin.disp()



def exec_command(disp, curs):
    disp.wins[2].win.addstr(2, 0, disp.wins[2].blank);
    disp.wins[2].win.addstr(2, 0, ":");
    disp.wins[2].refresh();
    inp = grab_input(disp.wins[2].win);
    exec_inp(inp);

def switch_view(disp, curs):
    if disp.cur == 1:
        disp.cur = 0;
    else:
        disp.cur = 1;
        

def select(disp, curs):
    curpl = disp.wins[1];
    disp.wins[2].print_line(0, 2, "Play: " + curpl.form(curpl.selected()));
    music.play(curpl.selected());


def exitpl(disp, curs):
    sys.exit();

def init_dict():
    out = dict();
    out.update(dict.fromkeys(keys.UP, scroll_up));
    out.update(dict.fromkeys(keys.DOWN, scroll_down));
    out.update(dict.fromkeys(keys.VOLUP, music.vol_up));
    out.update(dict.fromkeys(keys.VOLDOWN, music.vol_down));
    out.update(dict.fromkeys(keys.PLAYPAUSE, music.play_pause));
    out.update(dict.fromkeys(keys.QUIT, exitpl));
    out.update(dict.fromkeys(keys.SWITCH, switch_view));
    out.update(dict.fromkeys(keys.COMMAND, exec_command));
    out.update(dict.fromkeys(keys.SELECT, select));

    return out;


def run(conn, curs, disp):
    playlists = libdb.list_playlists(curs);
    for i, playlist in enumerate(playlists):
        disp.wins[0].win.addstr(i, 0, playlist);

    if playlists:
        disp.wins[0].data = playlists;
        disp.wins[1].data = get_songs_playlist(playlists[0], disp.wins[1], curs);
        disp.wins[1].disp();

    disp.wins[0].win.chgat(0, 0, curses.A_STANDOUT);
    disp.wins[1].win.chgat(0, 0, curses.A_STANDOUT);
    
    action = init_dict();

    while(True):
        disp.refresh()

        key = disp.curwin().win.getkey();
        if key in action:
            action[key](disp, curs);
            
 
def init_windows():
    bottom_bar = 4;
    hh = curses.LINES - bottom_bar;
    ww = curses.COLS // 6;

    
    leftwin = menu.Menu(0, 0, ww, hh);

    songname = lambda ll: str(ll[0] + ' - ' + ll[1]);
    rightwin = menu.Menu(ww, 0, curses.COLS - ww, hh, form=songname);
    botwin = menu.Window(0, hh, curses.COLS, bottom_bar);
    
    return leftwin, rightwin, botwin;

def main(stdscr):
    curses.curs_set(False);
    
    stdscr.clear();

    leftwin, rightwin, botwin = init_windows();
    music.init_music();

    disp = Disp(leftwin, rightwin, botwin);    
    disp.refresh();
    
    db = "lib.db";
    conn = sqlite3.connect(db);
    curs = conn.cursor();

    run(conn, curs, disp);

if __name__ == "__main__":
    curses.wrapper(main);
