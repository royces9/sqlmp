import curses
import sys

import player_ui

from loadconf import config

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
    return player_ui.Player_ui(stdscr, db)
