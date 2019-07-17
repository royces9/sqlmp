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
    data = [];


    def __init__(self, x, y, w, h, data = []):
        self.loc = Coord(x, y);
        self.size = Coord(w, h);
        self.win = curses.newwin(h, w, y, x);

        self.data = data;

        #index of the list member at y=0
        self.pos = 0;

        #y location of cursor
        self.cursor = 0;
        self.blank = " " * self.size.x;
        
    def refresh(self):
        self.win.refresh();
        
    def print_list(self):
        for ii, item in enumerate(self.data[self.pos:]):
            if ii > (self.size.y - 2):
                break;
            self.print_line(0, ii, item);

        self.win.refresh();

    def scroll_up(self):
        at_top = self.cursor < 0;

        if self.cursor > 0:
            self.cursor -= 1;

        if self.pos > 0:
            self.pos -= 1;

        self.win.chgat(self.cursor + 1, 0, curses.A_NORMAL);
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);

        self.print_list();

    def scroll_down(self):
        if self.cursor >= (self.size.y - 1):
            if self.pos < len(self.data):
                self.pos += 1;
        else:
            self.cursor += 1;


        self.win.chgat(self.cursor - 1, 0, curses.A_NORMAL);
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);
            
        self.print_list();

    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.size.x);
        self.win.addstr(y, x, line);
        self.win.refresh();

    def curr_highlighted(self):
        return self.pos + self.cursor;
        

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
            win.refresh();


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
        for songstr in curs.execute(f"SELECT title, artist FROM library WHERE path='{song}';"):
            out.append(songstr[0] + ' -  ' + songstr[1]);
            
    return out;
        

def run(conn, curs, disp):
    playlists = libdb.list_playlists(curs);
    for i, playlist in enumerate(playlists):
        disp.wins[0].win.addstr(i, 0, playlist);

    if playlists:
        disp.wins[0].data = playlists;
        disp.wins[1].data = get_songs_playlist(playlists[0], disp.wins[1], curs);
        disp.wins[1].print_list();

    disp.wins[0].win.chgat(0, 0, curses.A_STANDOUT);
    disp.wins[1].win.chgat(0, 0, curses.A_STANDOUT);
    
    pos = [0, 0];
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
            disp.wins[2].refresh();
            inp = grab_input(disp.wins[2].win);
            exec_inp(inp);
            
        elif key == 'KEY_UP':
            disp.wins[win].scroll_up();
            disp.wins[2].print_line(0, 2, disp.wins[win].data[disp.wins[win].curr_highlighted()]);
            if win == 0:
                disp.wins[1].cursor = 0;
                disp.wins[1].pos = 0;
                disp.wins[1].win.clear();
                disp.wins[1].data = get_songs_playlist(disp.wins[0].data[disp.wins[0].curr_highlighted()], disp.wins[1], curs);
                disp.wins[1].win.chgat(0, 0, curses.A_STANDOUT);
                disp.wins[1].print_list()

        elif key == 'KEY_DOWN':
            disp.wins[win].scroll_down();
            disp.wins[2].print_line(0, 2, disp.wins[win].data[disp.wins[win].curr_highlighted()]);
            if win == 0:
                disp.wins[1].cursor = 0;
                disp.wins[1].pos = 0;
                disp.wins[1].data = get_songs_playlist(disp.wins[0].data[disp.wins[0].curr_highlighted()], disp.wins[1], curs);
                disp.wins[1].print_list()
 
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
