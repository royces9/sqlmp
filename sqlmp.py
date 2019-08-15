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

def exec_inp(inp):
    return inp;


def grab_input(win):
    curses.echo();
    out = win.getstr(2, 1, curses.COLS - 2);
    curses.noecho()

    win.addnstr(2, 0, " " * curses.COLS, curses.COLS);
    win.refresh();

    return out;

def get_songs_playlist(pl, curs):
    songs = db_pl.list_pl_songs(pl, curs)
    out = []

    tags = ['path', 'title', 'artist', 'album', 'length', 'bitrate', 'playcount']
    joined_tag = ", ".join(tags);
        
    for i, song in enumerate(songs):
        song = song.replace("'", r"''");
        for queries in curs.execute(f"SELECT {joined_tag} FROM library WHERE path='{song}';"):
            newd = dict()
            for tag, query in zip(tags, queries):
                newd[tag] = query
            
            out.append(newd);
            
    return out;


def scroll_up(*args):
    disp = args[0]
    curs = args[1];
    
    curwin = disp.curwin();
    curwin.up();
    disp.wins[2].print_line(0, 2, curwin.form(curwin.selected()));
    if disp.cur == 0:
        disp.wins[1].data = disp.wins[0].selected();
        disp.wins[1].cursor = 0;
        disp.wins[1].offset = 0;
        disp.wins[1].disp()


def scroll_down(*args):
    disp = args[0]
    curs = args[1];

    curwin = disp.curwin();
    curwin.down();
    disp.wins[2].print_line(0, 2, curwin.form(curwin.selected()));
    if disp.cur == 0:
        disp.wins[1].data = disp.wins[0].selected();
        disp.wins[1].cursor = 0;
        disp.wins[1].offset = 0;
        disp.wins[1].disp()


def exec_command(disp, curs, player):
    disp.wins[2].win.addstr(2, 0, disp.wins[2].blank);
    disp.wins[2].win.addstr(2, 0, ":");
    disp.wins[2].refresh();
    inp = grab_input(disp.wins[2].win);
    exec_inp(inp);

    
def switch_view(*args):
    disp = args[0]
    if disp.cur == 1:
        disp.cur = 0;
    else:
        disp.cur = 1;
        

def select(*args):
    disp = args[0];
    player = args[2];

    curpl = disp.wins[1];

    disp.wins[2].print_line(0, 2, "Play: " + curpl.form(curpl.selected()));
    player.play(curpl.selected());

    for i in range(len(curpl.data)):
        newsong = disp.wins[0].data[disp.wins[0].cursor]._next()
        player.append(newsong)

       

def exitpl(*args):
    sys.exit();

    
def init_dict(disp, player):
    out = dict();
    out.update(dict.fromkeys(keys.UP, scroll_up));
    out.update(dict.fromkeys(keys.DOWN, scroll_down));
    out.update(dict.fromkeys(keys.VOLUP, player.vol_up));
    out.update(dict.fromkeys(keys.VOLDOWN, player.vol_down));
    out.update(dict.fromkeys(keys.PLAYPAUSE, player.play_pause));
    out.update(dict.fromkeys(keys.QUIT, exitpl));
    out.update(dict.fromkeys(keys.SWITCH, switch_view));
    out.update(dict.fromkeys(keys.COMMAND, exec_command));
    out.update(dict.fromkeys(keys.SELECT, select));

    return out;


def run(conn, curs, disp, player):
    action = init_dict(disp, player);

    while(True):
        disp.refresh()
        key = disp.curwin().win.getkey()
        
        if key in action:
            action[key](disp, curs, player);
            
 
def init_windows(curs):
    bottom_bar = 4;
    hh = curses.LINES - bottom_bar;
    ww = curses.COLS // 6;
    
    leftwin = menu.Menu(0, 0, ww, hh, form=lambda x: x.name);
    rightwin = menu.Menu(ww, 0, curses.COLS - ww, hh, form=keys.SONG_DISP)
    botwin = menu.Window(0, hh, curses.COLS, bottom_bar)
    
    str_pl = libdb.list_playlists(curs)
    playlists = []

    for i, pl in enumerate(str_pl):
        leftwin.win.addstr(i, 0, pl);
        playlists.append(playlist.Playlist(
            name=pl, data=get_songs_playlist(pl, curs),)
        )

    leftwin.data = playlists;
    rightwin.data = leftwin.data[0].data
    rightwin.disp();

    leftwin.win.chgat(0, 0, curses.A_STANDOUT);
    rightwin.win.chgat(0, 0, curses.A_STANDOUT);
    
    return display.Disp(leftwin, rightwin, botwin);


def main(stdscr):
    curses.use_default_colors()

    curses.curs_set(False);
    
    stdscr.clear();

    db = "lib.db";
    conn = sqlite3.connect(db);
    curs = conn.cursor();

    global disp
    disp = init_windows(curs);

    global player
    player = music.init_music();

    disp.refresh();
    run(conn, curs, disp, player);

if __name__ == "__main__":
    curses.wrapper(main);
