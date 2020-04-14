import curses
import sys

import menu
import player_disp
import playlist

from loadconf import config as config


def colours():
    curses.start_color()
    curses.use_default_colors()

    colours = [config.FOCUSED, config.CURSOR, config.HIGHLIGHT_COLOUR, config.NORMAL]

    for i, c in enumerate(colours, 1):
        if c[0] is None:
            curses.init_pair(i, c[1], c[2])
            c[0] = curses.color_pair(i)


def ncurses():
    stdscr = curses.initscr()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(1)

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    if curses.has_colors():
        colours()

    return stdscr


def windows(db, stdscr):
    hh, ww, bottom_bar, cc = config.set_size(stdscr)

    leftwin = menu.Menu(0, 0, ww, hh,
                        data=[playlist.Playlist(name=pl, db=db) for pl in db.list_pl()],
                        form=lambda x: ((x.name, 1),),
                        cursor_colour=config.FOCUSED[0],
                        highlight_colour=config.FOCUSED[0],
                        normal_colour=config.NORMAL[0])

    rightwin = menu.Menu(ww, 0, cc - ww, hh,
                         data=leftwin.data[0].data,
                         form=config.SONG_DISP,
                         cursor_colour=config.CURSOR[0],
                         highlight_colour=config.HIGHLIGHT_COLOUR[0],
                         normal_colour=config.NORMAL[0])

    botwin = menu.Window(0, hh, cc, bottom_bar)

    return player_disp.Player_disp([leftwin, rightwin, botwin], stdscr, db)
