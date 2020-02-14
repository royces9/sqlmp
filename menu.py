import curses
import threadwin

import wchar


class Window:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.win = threadwin.Threadwin(h, w, y, x)

        self.blank = ' ' * (self.w - 1)


    def print_blank(self, y=0, x=0):
        self.win.addnstr(y, x, self.blank, self.w - x)


    def print_line(self, line, y=0, x=0):
        self.print_blank(y, x)
        trunc_line = wchar.set_width(line, self.w - x)
        self.win.addnstr(y, x, trunc_line, self.w - x)


    def print_right_justified(self, line, y=0):
        length = wchar.wcswidth(line)[0]
        self.win.addnstr(y, self.w - length, line, length)


    def refresh(self):
        self.win.refresh()



class Menu(Window):
    def __init__(self, x=0, y=0, w=0, h=0, data=None,
                 form=lambda ll: ((str(ll), 1),),
                 cursor_colour=curses.A_STANDOUT,
                 highlight_colour=curses.A_REVERSE,
                 normal_colour=curses.A_NORMAL):
        super().__init__(x, y, w, h)

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

        self.paint_cursor(self.cursor_colour)

        self.win.idlok(True)
        self.win.scrollok(True)


    def __contains__(self, item):
        return item in self.data


    def __getitem__(self, ind):
        return self.data[ind]


    def highlight(self):
        newitem = self.highlighted()

        if newitem not in self.highlight_list:
            self.highlight_list.append(newitem)
        else:
            self.highlight_list.remove(newitem)

        self.paint_highlight(self.highlight_colour)


    def highlighted(self):
        if self.data:
            return self[self.highlighted_ind()]
        else:
            return None


    def highlighted_ind(self):
        return self.cursor + self.offset


    def up(self):
        self.paint_cursor(self.normal_colour)

        at_top = self.cursor < 1

        if not at_top:
            self.cursor -= 1
        elif self.offset > 0:
            self.offset -= 1
            self.win.scroll(-1)

            if self.offset < len(self.data):
                formatted_list = self.form(self.data[self.offset])
                self.print_col(0, 0, formatted_list)

        self.paint_highlight(self.highlight_colour)
        self.paint_cursor(self.cursor_colour)


    def down(self):
        self.paint_cursor(self.normal_colour)

        if (self.offset + self.cursor) < (len(self.data) - 1):
            at_bot = self.cursor >= (self.h - 1)
            if at_bot:
                self.offset += 1
                self.win.scroll(1)

                if (self.h - 1 + self.offset) < len(self.data):
                    formatted_list = self.form(self.data[(self.h - 1) + self.offset])
                    self.print_col(0, self.h - 1, formatted_list)

            else:
                self.cursor += 1

        self.paint_highlight(self.highlight_colour)
        self.paint_cursor(self.cursor_colour)


    def disp(self):
        for ii in range(self.h):
            self.print_blank(ii)
            if (ii + self.offset) < len(self.data):
                formatted_list = self.form(self.data[ii + self.offset])
                self.print_col(0, ii, formatted_list)

        self.paint_highlight(self.highlight_colour)
        self.paint_cursor(self.cursor_colour)


    def paint_highlight(self, colour):
        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            if 0 <= newind < self.w:
                self.win.chgat(newind, 0, self.w - 1, colour)


    def paint_cursor(self, colour):
        if self.data:
            self.win.chgat(self.cursor, 0, self.w - 1, colour)


    def print_col(self, x, y, datas):
        for string, fraction in datas:
            width = int(self.w * fraction)
            self.win.addnstr(y, x, wchar.set_width(string, width), self.w)
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
