import curses

import window
import wchar
from colours import Colour_types as ct

import debug


class Menu(window.Window):
    def __init__(self, x=0, y=0, w=0, h=0, win=None, data=None,
                 palette=None
                 ):
        super().__init__(x, y, w, h, win)

        #the coordinate of the cursor on the screen
        self.cursor = 0

        #the number of items the top item
        #of the list is offset from the top
        self.offset = 0

        self.data = data
        self.palette = palette

        self.highlight_list = []

        self.paint_cursor()

        self.win.idlok(True)
        self.win.scrollok(True)


    def disp(self):
        self.win.erase()
        diff = len(self.data) - self.offset
        smaller = self.h if diff > self.h else diff

        for ii in range(smaller):
            self.print_line(str(self.data[ii + self.offset]), ii, 0)

        self.paint()
        self.refresh()
        
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

    def highlighted(self):
        if self.data:
            return self[self.highlighted_ind()]
        else:
            return None


    def highlighted_ind(self):
        return self.cursor + self.offset


    def up(self):
        if self.cursor >= 1:
            self.cursor -= 1

        elif self.offset > 0:
            self.offset -= 1
            self.win.scroll(-1)

        self.paint()


    def down(self):
        if (self.offset + self.cursor) < (len(self.data) - 1):
            if self.cursor >= (self.h - 1):
                self.offset += 1
                self.win.scroll(1)

            else:
                self.cursor += 1

        self.paint()


    def jump_up(self, n):
        self.cursor -= n

        if self.cursor < 0:
            if self.offset < -self.cursor:
                self.win.scroll(self.offset)
                self.offset = 0
            else:
                self.offset += self.cursor
                self.win.scroll(self.cursor)
            self.cursor = 0

        self.paint()


    def jump_down(self, n):
        self.cursor += n

        if (self.offset + self.cursor) >= (len(self.data) - 1):
            self.cursor = (len(self.data) - 1) - self.offset

        if self.cursor > (self.h - 1):
            self.offset += (self.cursor - (self.h - 1))
            self.win.scroll(self.cursor - (self.h - 1))
            self.cursor = self.h - 1

        self.paint()


    def chgat(self, y, x, width, colour):
        self.win.chgat(y, x, self.w - x, self.palette[colour])


    def paint(self):
        if not self.data:
            return
        else:
            #paint cursor
            self.chgat(self.cursor, 0, self.w - 1, ct.cursor)

        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            colour = ct.highlight
            if 0 <= newind < self.h:
                if newind == self.cursor:
                    colour |= ct.cursor
                self.chgat(newind, 0, self.w - 1, colour)

        self.win.touchwin()

    def paint_cursor(self):
        if self.data:
            self.chgat(self.cursor, 0, self.w - 1, 1)


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

            
class Music_menu(Menu):
    def __init__(self, x=0, y=0, w=0, h=0, win=None, data=None,
                 form=lambda w, h, addnstr, x, y, ll: self.win.addnstr(y, x, ll['title'], w),
                 palette=None, ui=None
                 ):
        super().__init__(x, y, w, h, win, data,
                         palette=palette)

        self.form=form
        
        self.ui = ui

    def disp(self):
        self.win.erase()
        diff = len(self.data) - self.offset
        smaller = self.h if diff > self.h else diff
        for ii in range(smaller):
            self.form(self.w, self.h, self.win.addnstr, 0, ii, self.data[ii + self.offset])

        self.paint()
        self.refresh()

    def default_print_col(self, w, h, addnstr, x, y, datas):
        for string, fraction, flag in datas:
            width = int(self.w * fraction)
            s = wchar.set_width(string, width)
            if flag:
                s = s.rjust(width)
            self.win.addnstr(y, x, s, width)
            x += width

        
        

    def paint(self):
        #check that playlist to be displayed has both be true:
        #the currently playing playlist is the currently displayed playlist
        #the currently playing song is in the playlist
        if self.data == self.ui.cur_pl and self.ui.player.cur_song['path'] in self.data:
            cur_song_ind = self.data.index(self.ui.player.cur_song) - self.offset
        else:
            cur_song_ind = -1
            
        if self.data:
            self.chgat(self.cursor, 0, self.w - 1, ct.cursor)

        if 0 <= cur_song_ind < self.h:
            if cur_song_ind == self.cursor:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.cursor | ct.playing)
            else:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.playing)

        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            colour = ct.highlight
            if 0 <= newind < self.h:
                if newind == cur_song_ind:
                    colour |= ct.playing
                if newind == self.cursor:
                    colour |= ct.cursor
                self.chgat(newind, 0, self.w - 1, colour)

        self.ui.leftwin.win.touchwin()


