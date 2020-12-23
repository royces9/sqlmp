import curses
import sys

import colours
import debug

from loadconf import config


def init_palette():
    curses.start_color()
    curses.use_default_colors()

    colour_list = [0, 0, 0, 0, 0]
    config_colours = [(config.CURSOR, 3, 10),
                      (config.FOCUSED, 5, 11),
                      (config.HIGHLIGHT_COLOUR, 7, 12),
                      (config.NORMAL, 9, 13),
                      (config.PLAYING_HIGHLIGHT, 11, 14),
        ]
    focus_palette = colours.Palette()
    cursor_palette = colours.Palette()

    for i, c in enumerate(config_colours):
        if len(c[0]) > 1:
            fg, bg = c[0]
            colour_list[i] = colours.Colour_pair(
                colours.Colour(*fg, c[1]),
                colours.Colour(*bg, c[1] + 1),
                c[2]
            )
        else:
            colour_list[i] = colours.Default_pair(c[0][0])
            
    cursor_palette[0] = colour_list[3]
    cursor_palette[1] = colour_list[0]
    cursor_palette[2] = colour_list[2]
    cursor_palette[4] = colour_list[4]
    cursor_palette.mix(2, 1, 3)
    cursor_palette.mix(4, 1, 5)
    cursor_palette.mix(4, 2, 6)
    cursor_palette.mix(4, 1, 7)

    focus_palette[0] = colour_list[3]
    focus_palette[1] = colour_list[1]
    focus_palette[2] = colour_list[2]
    focus_palette[4] = colour_list[4]
    focus_palette.mix(2, 1, 3)
    focus_palette.mix(4, 1, 5)
    focus_palette.mix(4, 2, 6)
    focus_palette.mix(4, 1, 7)

    """
    cursor_palette.append(colour_list[0])
    cursor_palette.append(colour_list[2])
    cursor_palette.append(colour_list[3])
    cursor_palette.append(colour_list[4])

    focus_palette.append(colour_list[1])
    focus_palette.append(colour_list[2])
    focus_palette.append(colour_list[3])
    focus_palette.append(colour_list[4])
    """
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
        else:
            colours()

    return stdscr, palette
