import curses
import sys

import colours
from colours import Colour_types as ct

import config
import debug

def init_palette():
    curses.start_color()
    curses.use_default_colors()

    config_colours = [config.CURSOR,
                      config.FOCUSED,
                      config.HIGHLIGHT_COLOUR,
                      config.NORMAL,
                      config.PLAYING_HIGHLIGHT,
                      ]
    focus_palette = colours.Palette()
    cursor_palette = colours.Palette()

    colour_list = [colours.Colour_pair(colours.Colour(*c[0]), colours.Colour(*c[1]))
                   for i, c in enumerate(config_colours)]

    cursor_palette[ct.normal] = colour_list[3]
    cursor_palette[ct.cursor] = colour_list[0]
    cursor_palette[ct.highlight] = colour_list[2]
    cursor_palette[ct.playing] = colour_list[4]
    cursor_palette.mix(ct.highlight, ct.cursor)
    cursor_palette.mix(ct.playing, ct.cursor)
    cursor_palette.mix(ct.playing, ct.highlight)
    cursor_palette.mix(ct.playing, ct.cursor, ct.highlight)


    focus_palette[ct.normal] = colour_list[3]
    focus_palette[ct.cursor] = colour_list[1]
    focus_palette[ct.highlight] = colour_list[2]
    focus_palette[ct.playing] = colour_list[4]
    focus_palette.mix(ct.highlight, ct.cursor)
    focus_palette.mix(ct.playing, ct.cursor)
    focus_palette.mix(ct.playing, ct.highlight)
    focus_palette.mix(ct.playing, ct.cursor, ct.highlight)

    return [cursor_palette, focus_palette]


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
            palette = init_palette()

    return stdscr, palette
