import curses

from loadconf import config

class Colour:
    def __init__(self, r, g, b, enum):
        self.r = int(r * 1000 / 255)
        self.g = int(g * 1000 / 255)
        self.b = int(b * 1000 / 255)
        self.enum = enum

        curses.init_color(self.enum, self.r, self.g, self. b)

class Colour_pair:
    def __init__(self, fg, bg, enum):
        self.fg = fg
        self.bg = bg
        self.enum = enum

        curses.init_pair(self.enum, fg.enum, bg.enum)
        self.colour = curses.color_pair(self.enum)


class Default_colour:
    def __init__(self, enum):
        self.enum = enum

        
class Default_pair:
    def __init__(self, colour):
        self.colour = colour
        fg_enum, bg_enum = curses.pair_content(curses.pair_number(self.colour))
        self.fg = Default_colour(fg_enum)
        self.bg = Default_colour(bg_enum)


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

    def mix(self, a, b, enum):
        self[enum] = Colour_pair(self.colour_pairs[a].fg, self.colour_pairs[b].bg, enum)
    
