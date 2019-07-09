#!/usr/bin/python

import curses
import sqlite3
import pl
import libdb


class Coord:
    x = 0;
    y = 0;

    def __init__(self, x = 0, y = 0):
        self.x = x;
        self.y = y;

class Window:
    loc = Coord(0, 0);
    size = Coord(0, 0);

    def __init__(self, x, y, w, h):
        self.loc = Coord(x, y);
        self.size = Coord(w, h);
        self.win = curses.newwin(h, w, y, x);
    

class Disp:
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
            win.win.refresh();


def exec_inp(inp):
    return inp;


def grab_input(win):
    curses.echo();
    out = win.getstr(2, 1, curses.COLS - 2);
    curses.noecho()

    win.addnstr(2, 0, " " * curses.COLS, curses.COLS);
    win.refresh();

    return out;

def run(conn, curs, disp):
    playlists = libdb.list_playlists(curs);
    
    for i, playlist in enumerate(playlists):
        disp.wins[0].win.addstr(i, 0, playlist);

    disp.wins[0].win.chgat(0, 0, curses.A_STANDOUT);

    songs = pl.list_pl_songs(playlists[0], curs);
    for i, song in enumerate(songs):
        if i >= disp.wins[0].size.y - 1:
            break;

        song = song.replace("'", r"''");
        for songstr in curs.execute(f"SELECT title, artist FROM library WHERE path='{song}';"):
            disp.wins[1].win.addstr(i, 0, songstr[0]);
            
    pos = [0, 0, 0];
    win = 0;

    prev = -1;

    while(True):
        disp.refresh()

        key = disp.wins[win].win.getkey();

        if key == '\t':
            if win == 1:
                win = 0;
            else:
                win = 1;
        elif key == ':':
            disp.wins[2].win.addstr(2, 0, ":");
            disp.wins[2].win.refresh();
            inp = grab_input(disp.wins[2].win);
            exec_inp(inp);
            
        elif key == 'KEY_UP':
            pos[win] -= 1;
            if pos[win] < 0:
                pos[win] = 0;
            disp.wins[win].win.chgat(pos[win], 0, curses.A_STANDOUT);
            disp.wins[win].win.chgat(pos[win] + 1, 0, curses.A_NORMAL);
        elif key == 'KEY_DOWN':
            pos[win] += 1;
            if pos[win] > (disp.wins[win].size.y - 1):
                pos[win] = disp.wins[win].size.y - 1;
                
            disp.wins[win].win.chgat(pos[win], 0, curses.A_STANDOUT);
            disp.wins[win].win.chgat(pos[win] - 1, 0, curses.A_NORMAL);


def init_windows():
    bottom_bar = 4;
    hh = curses.LINES - bottom_bar;
    ww = curses.COLS // 6;

    leftwin = Window(0, 0, ww, hh);
    rightwin = Window(ww, 0, curses.COLS - ww, hh);
    botwin = Window(0, hh, curses.COLS, bottom_bar);

    return leftwin, rightwin, botwin;

def main(stdscr):
    curses.curs_set(False);

    stdscr.clear();

    leftwin, rightwin, botwin = init_windows();

    leftwin.win.keypad(True);
    rightwin.win.keypad(True);
    botwin.win.keypad(True);
 
    disp = Disp(leftwin, rightwin, botwin);    
    disp.refresh();
    
    db = "lib.db";
    conn = sqlite3.connect(db);
    curs = conn.cursor();

    run(conn, curs, disp);

if __name__ == "__main__":
    curses.wrapper(main);
