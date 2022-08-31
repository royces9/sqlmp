import curses
import enum
import functools

import debug

import config

class Colour_types(enum.IntFlag):
    normal = 0
    cursor = 1
    highlight = 2
    playing = 4


global_colour = []
global_pair = []

def reset_colours():
    for colour in global_colour:
        curses.init_color(*colour)

    for pair in global_pair:
        curses.init_pair(*pair)

class Colour:
    __enum = 3
    def __init__(self, r, g, b):
        self.r = int(r * 1000 / 255)
        self.g = int(g * 1000 / 255)
        self.b = int(b * 1000 / 255)
        self.enum = type(self).__enum

        self.init_color(type(self).__enum, self.r, self.g, self. b)
        type(self).__enum += 1

    def init_color(self, num, r, g, b):
        orig_colour = curses.color_content(num)
        global_colour.append((num, *orig_colour))
        curses.init_color(num, r, g, b)

class Colour_pair:
    __enum = 2

    def __init__(self, fg, bg):
        self.fg = fg
        self.bg = bg

        self.init_pair(type(self).__enum, fg.enum, bg.enum)
        self.colour = curses.color_pair(type(self).__enum)

        type(self).__enum += 1

    def init_pair(self, num, fg, bg):
        orig_pair = curses.pair_content(num)
        global_pair.append((num, *orig_pair))
        curses.init_pair(num, fg, bg)


class Palette:
    def __init__(self):
        self.colour_pairs = {}

    def __setitem__(self, ind, item):
        self.colour_pairs[ind] = item

    def __getitem__(self, ind):
        return self.colour_pairs[ind].colour

    def find(self, value):
        for key in self.colour_pairs:
            if self[key] == value:
                return key
        return None

    def mix(self, *args):
        """
        mix any amount of colours in the palette together
        the first argument will be the foreground (text) colour
        the second will be the background colour
        """
        if len(args) < 2:
            return
        fg = args[0]
        bg = args[1]
        enum = functools.reduce(lambda a, b: a | b, args)
        self[enum] = Colour_pair(self.colour_pairs[fg].fg, self.colour_pairs[bg].bg)
