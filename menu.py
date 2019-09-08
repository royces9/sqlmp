import curses

import wchar

class Window:
    def __init__(self, x = 0, y = 0, w = 0, h = 0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.win = curses.newwin(h, w, y, x)
        self.win.keypad(True)

        self.blank = " " * (self.w - 1)

        self.cursor = 0
        self.offset = 0
        
    def print_blank(self, y):
        self.win.addnstr(y, 0, self.blank, self.w)

    def print_line(self, x, y, line):
        self.print_blank(y)
        self.win.addnstr(y, x, line, self.w)

    def refresh(self):
        self.win.refresh()


class Menu(Window):
    def __init__(self, x = 0, y = 0, w = 0, h = 0, data = [],
                 form = lambda ll: (str(ll), 0),
                 cursor_colour=curses.A_STANDOUT,
                 highlight_colour=curses.A_REVERSE,
                 normal_colour=curses.A_NORMAL):
        super().__init__(x, y, w, h)
        self.data = data
        self.form = form
        self.cursor_colour = cursor_colour
        self.highlight_colour = highlight_colour
        self.normal_colour = normal_colour

        self.highlight_list = []

        self.paint_cursor(self.highlight_colour)

    def __getitem__(self, ind):
        return self.data[ind]


    def highlight(self):
        newitem = self.highlighted_ind()

        if newitem not in self.highlight_list:
            self.highlight_list.append(newitem)
        else:
            self.highlight_list.remove(newitem)

        self.paint_highlight(self.highlight_colour)

    def highlighted(self):
        return self[self.highlighted_ind()]

    def highlighted_ind(self):
        return self.cursor + self.offset
    
    def up(self):
        self.paint_cursor(self.normal_colour)
        
        at_top = self.cursor < 1;
        if not at_top:
            self.cursor -= 1
        elif self.offset > 0:
            self.offset -= 1

        self.disp();


    def down(self):
        self.paint_cursor(self.normal_colour)

        if (self.offset + self.cursor) < (len(self.data) - 1):
            at_bot = self.cursor >= (self.h - 1)
            if at_bot:
                self.offset += 1
            else:
                self.cursor += 1

        self.disp();
        
    def disp(self):
        for ii in range(self.h):
            self.print_blank(ii)
            if not ((ii + self.offset) > (len(self.data) - 1)):
                formatted_list, flag = self.form(self.data[ii + self.offset])

                if flag:
                    self.print_col(ii, formatted_list)
                else:
                    self.print_line(0, ii, formatted_list)

        self.paint_highlight(self.highlight_colour)
        self.paint_cursor(self.cursor_colour)

    def paint_highlight(self, colour):
        for hl in self.highlight_list:
            newind = hl - self.offset
            if 0 <= newind <= self.w:
                self.win.chgat(newind, 0, self.w - 1, colour)

    def paint_cursor(self, colour):
        self.win.chgat(self.cursor, 0, self.w - 1, colour)

    def print_line(self, x, y, line):
        self.print_blank(y)
        self.win.addstr(y, x, line);

        
    def print_col(self, y, datas):
        previous = 0
        for string, fraction in datas:
            ind = previous
            width = int(self.w * fraction)
            previous += width
            self.win.addstr(y, ind, wchar.set_width(string, width))
