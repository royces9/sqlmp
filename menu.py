import curses

import window
import wchar
from colours import Colour_types as ct

import debug


class Menu_item:
    def __init__(self, data):
        self.data = data
        self.highlighted = False

    def __str__(self):
        return str(self.data)

    
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

        if data:
            self.data = [Menu_item(d) for d in data]
        else:
            self.data = []
        self.palette = palette

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
        return any(filter(lambda x: x.data == item, self.data))


    def __getitem__(self, ind):
        return self.data[ind]


    def __str__(self):
        return str(self.data)


    def highlight(self):
        newitem = self.highlighted()
        newitem.highlighted = not newitem.highlighted
            

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

        for i, d in enumerate(self.data[self.offset:self.offset+self.h]):
            if d.highlighted:
                colour = ct.highlight
                if i == self.cursor:
                    colour |= ct.cursor
                self.chgat(i, 0, self.w - 1, colour)

        self.win.touchwin()


    def insert(self, items):
        if isinstance(items, list):
            self.data += [Menu_item(d) for d in items]
        else:
            self.data += [Menu_item(items)]


    def delete(self, item):
        if item in self:
            self.data.remove(item)

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
            self.form(self.w, self.h, self.win.addnstr, 0, ii, self.data[ii + self.offset].data)
        
        self.paint()
        self.refresh()


    def paint(self):
        #check that playlist to be displayed has both be true:
        #the currently playing playlist is the currently displayed playlist
        #the currently playing song is in the playlist
        cur_song_ind = -1
        if self is self.ui.cur_pl and self.ui.player.cur_song['path'] in self:
            for i, d in enumerate(self.data):
                if d.data == self.ui.player.cur_song:
                    cur_song_ind = i - self.offset
                    break
        
        if self.data:
            self.chgat(self.cursor, 0, self.w - 1, ct.cursor)

        if 0 <= cur_song_ind < self.h:
            if cur_song_ind == self.cursor:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.cursor | ct.playing)
            else:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.playing)


        for i, d in enumerate(self.data[self.offset:self.offset+self.h]):
            colour = ct.highlight
            if d.highlighted:
                if i == cur_song_ind:
                    colour |= ct.playing
                if i == self.cursor:
                    colour |= ct.cursor
                self.chgat(i, 0, self.w - 1, colour)

        self.ui.leftwin.win.touchwin()
