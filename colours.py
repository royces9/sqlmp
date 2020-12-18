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

class Default_pair:
    def __init__(self, colour):
        self.colour = colour

class Palette:
    def __init__(self):
        self.colour_pairs = []

    def __getitem__(self, ind):
        return self.colour_pairs[ind].colour

    def append(self, new):
        self.colour_pairs.append(new)
        
    def mix(self, a, b, enum):
        new = Colour_pair(self.colour_pairs[a].fg, self.colour_pairs[b].bg, enum)
        self.append(new)
    
