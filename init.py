import curses
import sys

import colours

from loadconf import config


def init_colours():
    curses.start_color()
    curses.use_default_colors()

    config_colours = [config.FOCUSED,
               config.CURSOR,
               config.HIGHLIGHT_COLOUR,
               config.NORMAL,
               config.PLAYING_HIGHLIGHT]
 
    palette = colours.Palette()
    j = 1
    for i, c in enumerate(config_colours, 10):
        if len(c) > 1:
            fg, bg = c
            palette.append(colours.Colour_pair(colours.Colour(*fg, j), colours.Colour(*bg, j + 1), i))
            j += 2
        else:
            palette.append(colours.Default_pair(c[0]))
        
    return palette

def ncurses():
    stdscr = curses.initscr()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(1)

    sys.stdout.write("\x1b]2;sqlmp\x07")
    sys.stdout.flush()

    if curses.has_colors():
        if curses.can_change_color():
            palette = init_colours()
        else:
            colours()

    return stdscr, palette
