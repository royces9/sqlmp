import curses
import threadwin

import wchar

import debug

class Window:
    def __init__(self, x=0, y=0, w=0, h=0, win=None):
        self.win = win if win else threadwin.Threadwin(h, w, y, x)

    @property
    def x(self):
        return self.win.getbegyx()[1]

    @property
    def y(self):
        return self.win.getbegyx()[0]

    @property
    def w(self):
        return self.win.getmaxyx()[1]

    @property
    def h(self):
        return self.win.getmaxyx()[0]


    def print_blank(self, y=0, x=0):
        self.win.move(y, x)
        self.win.clrtoeol()


    def print_line(self, line, y=0, x=0):
        self.print_blank(y, x)
        trunc_line = wchar.set_width(line, self.w - x)
        self.win.addnstr(y, x, trunc_line, self.w - x)


    def print_right_justified(self, line, y=0):
        length = wchar.wcswidth(line)[0]
        self.win.addnstr(y, self.w - length, line, length)


    def refresh(self):
        self.win.noutrefresh()


class Menu(Window):
    def __init__(self, x=0, y=0, w=0, h=0, win=None, data=None,
                 form=lambda ll: ((str(ll), 1, 0),),
                 cursor_colour=curses.A_STANDOUT,
                 highlight_colour=curses.A_REVERSE,
                 normal_colour=curses.A_NORMAL):
        super().__init__(x, y, w, h, win)

        #the coordinate of the cursor on the screen
        self.cursor = 0

        #the number of items the top item
        #of the list is offset from the top
        self.offset = 0

        self.data = data
        self.form = form
        self.cursor_colour = cursor_colour
        self.highlight_colour = highlight_colour
        self.normal_colour = normal_colour

        self.highlight_list = []

        self.paint_cursor(self.cursor_colour, self.cursor)

        self.win.idlok(True)
        self.win.scrollok(True)


    def __contains__(self, item):
        return item in self.data


    def __getitem__(self, ind):
        return self.data[ind]


    def __str__(self):
        return str(self.data)


    def highlight(self):
        newitem = self.highlighted()

        if newitem not in self.highlight_list:
            self.highlight_list.append(newitem)
        else:
            self.highlight_list.remove(newitem)

        self.paint_highlight(self.highlight_colour, self.offset)


    def highlighted(self):
        if self.data:
            return self[self.highlighted_ind()]
        else:
            return None


    def highlighted_ind(self):
        return self.cursor + self.offset


    def up(self):
        if not self.cursor < 1:
            self.cursor -= 1

        elif self.offset > 0:
            self.offset -= 1
            self.win.scroll(-1)

            if self.offset < len(self.data):
                formatted_list = self.form(self.data[self.offset])
                self.print_col(0, 0, formatted_list)

        self.paint_cursor(self.normal_colour, self.cursor + 1)
        self.paint_cursor(self.cursor_colour, self.cursor)

        self.paint_highlight(self.highlight_colour, self.offset)


    def down(self):
        if (self.offset + self.cursor) < (len(self.data) - 1):
            if self.cursor >= (self.h - 1):
                self.offset += 1
                self.win.scroll(1)

                if (self.h - 1 + self.offset) < len(self.data):
                    formatted_list = self.form(self.data[(self.h - 1) + self.offset])
                    self.print_col(0, self.h - 1, formatted_list)

            else:
                self.cursor += 1

            self.paint_cursor(self.normal_colour, self.cursor - 1)
            self.paint_cursor(self.cursor_colour, self.cursor)

            self.paint_highlight(self.highlight_colour, self.offset)


    def disp(self):
        self.win.erase()
        diff = len(self.data) - self.offset
        smaller = self.h if diff > self.h else diff

        for ii in range(smaller):
            #self.print_line(str(self.data[ii + self.offset]), ii, 0)
            formatted_list = self.form(self.data[ii + self.offset])
            self.print_col(0, ii, formatted_list)

        self.paint_highlight(self.highlight_colour, self.offset)
        self.paint_cursor(self.cursor_colour, self.cursor)

        self.win.noutrefresh()


    def paint_highlight(self, colour, offset):
        for hl in self.highlight_list:
            newind = self.data.index(hl) - offset
            if 0 <= newind < self.w:
                self.win.chgat(newind, 0, self.w - 1, colour)


    def paint_cursor(self, colour, cursor):
        if self.data:
            self.win.chgat(cursor, 0, self.w - 1, colour)


    def print_col(self, x, y, datas):
        for string, fraction, flag in datas:
            width = int(self.w * fraction)
            s = wchar.set_width(string, width)
            if flag:
                s = s.rjust(width)
            self.win.addnstr(y, x, s, width)

            x += width


    def insert(self, items):
        if isinstance(items, list):
            self.data += items
        else:
            self.data += [items]


    def delete(self, item):
        if item in self:
            self.data.remove(item)

        if item in self.highlight_list:
            self.highlight_list.remove(item)

        if self.highlighted_ind() >= len(self.data):
            self.up()
