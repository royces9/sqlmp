import curses
import threadwin

import song
import window
import wchar

import debug


class Menu(window.Window):
    def __init__(self, x=0, y=0, w=0, h=0, win=None, data=None,
                 form=lambda ll: ((str(ll), 1, 0),),
                 palette=None
                 ):
        super().__init__(x, y, w, h, win)

        #the coordinate of the cursor on the screen
        self.cursor = 0

        #the number of items the top item
        #of the list is offset from the top
        self.offset = 0

        self.data = data
        self.form = form
        self.palette = palette

        self.highlight_list = []

        self.paint_cursor()

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

        self.paint_highlight()


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


    def disp(self):
        self.win.erase()
        diff = len(self.data) - self.offset
        smaller = self.h if diff > self.h else diff

        for ii in range(smaller):
            formatted_list = self.form(self.data[ii + self.offset])
            self.print_col(0, ii, formatted_list)

        self.paint()
        self.refresh()


    def paint_highlight(self):
        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            if 0 <= newind < self.h:
                self.chgat(newind, 0, self.w - 1, 2)


    def paint_all(self):
        cursor_painted = False
        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            if 0 <= newind < self.h:
                if newind == self.cursor:
                    self.chgat(newind, 0, self.w - 1, 3)
                    cursor_painted = True
                else:
                    self.chgat(newind, 0, self.w - 1, 2)
                
        if self.data and not cursor_painted:
            self.chgat(self.cursor, 0, self.w - 1, 1)

                
    def chgat(self, y, x, width, colour):
        self.win.chgat(y, x, self.w - x, self.palette[colour])


    def paint(self):
        self.paint_cursor()
        self.paint_highlight()

    def paint_cursor(self):
        if self.data:
            self.chgat(self.cursor, 0, self.w - 1, 1)


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

            
class Music_menu(Menu):
    def __init__(self, x=0, y=0, w=0, h=0, win=None, data=None,
                 form=lambda ll: ((str(ll), 1, 0),),
                 palette=None, ui=None
                 ):
        super().__init__(x, y, w, h, win, data,
                         form=form,
                         palette=palette)
        self.ui = ui
        

    def paint(self):
        #check that playlist to be displayed has both be true:
        #the currently playing playlist is the currently displayed playlist
        #the currently playing song is in the playlist
        if self.data == self.ui.cur_pl and self.ui.player.cur_song['path'] in self.data:
            cur_song_ind = self.data.index(self.ui.player.cur_song) - self.offset
        else:
            cur_song_ind = -1
        if cur_song_ind == self.cursor:
            self.chgat(self.cursor, 0, self.w - 1, 5)
        else:
            if 0 <= cur_song_ind < self.h:
                self.chgat(cur_song_ind, 0, self.w - 1, 4)
            if self.data:
                self.chgat(self.cursor, 0, self.w - 1, 1)

        for hl in self.highlight_list:
            newind = self.data.index(hl) - self.offset
            colour = 2
            if 0 <= newind < self.h:
                if newind == cur_song_ind:
                    colour |= 4
                if newind == self.cursor:
                    colour |= 1
                self.chgat(newind, 0, self.w - 1, colour)

        self.ui.leftwin.win.touchwin()
