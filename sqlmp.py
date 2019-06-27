#!/usr/bin/python

import curses
import sqlite3
import pl
import libdb


def run(conn, curs, rightwin, leftwin, botwin):
    playlists = libdb.list_playlists(curs);
    
    for i, playlist in enumerate(playlists):
        leftwin.addstr(i, 0, playlist);

    leftwin.chgat(0, 0, curses.A_STANDOUT);

    songs = pl.list_pl_songs(playlists[0], curs);
    for i, song in enumerate(songs):
        if i >= hh - 1:
            break;

        for songstr in curs.execute(f"SELECT title, artist FROM library WHERE path='{song}';"):
            rightwin.addstr(i, 0, songstr[0]);
            
    pos = [0, 0, 0];
    curr_win = [leftwin, rightwin, botwin];
    win = 0;

    while(True):
        leftwin.refresh();
        rightwin.refresh();
        botwin.refresh();

        key = curr_win[win].getkey();

        if key == '\t':
            if win == 1:
                win = 0;
            else:
                win = 1;
        elif key == ':':
            win = 2;
        elif key == 'KEY_UP':
            pos[win] -= 1;
            curr_win[win].chgat(pos[win], 0, curses.A_STANDOUT);
            curr_win[win].chgat(pos[win] + 1, 0, curses.A_NORMAL);
        elif key == 'KEY_DOWN':
            pos[win] += 1;
            curr_win[win].chgat(pos[win], 0, curses.A_STANDOUT);
            curr_win[win].chgat(pos[win] - 1, 0, curses.A_NORMAL);


def main(stdscr):
    stdscr.clear();

    bottom_bar = 4;
    hh = curses.LINES - bottom_bar;
    ww = curses.COLS * 1 // 6;
    leftwin = curses.newwin(hh, ww, 0, 0);
    rightwin = curses.newwin(hh, curses.COLS - ww - 1, 0, ww + 1);
    botwin = curses.newwin(bottom_bar, curses.COLS - 1, hh - 1, 0);

    leftwin.keypad(True);
    rightwin.keypad(True);
    botwin.keypad(True);
    
    db = "lib.db";
    conn = sqlite3.connect(db);
    curs = conn.cursor();

    leftwin.refresh();
    rightwin.refresh();
    botwin.refresh();

    run(conn, curs, rightwin, leftwin, botwin);

if __name__ == "__main__":
    curses.wrapper(main);
