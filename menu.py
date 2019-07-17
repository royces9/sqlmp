#!/usr/bin/python

import curses

class Menu:
    def __init__(self, x = 0, y = 0, w = 0, h = 0, data = []):
        self.x = x;
        self.y = y;
        self.w = w;
        self.h = h;
        self.win = curses.newwin(h, w, y, x);
        self.data = data;

        self.blank = " " * self.w;

        self.cursor = 0;
        self.offset = 0;
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);

    def highlighted(self):
        return self.cursor + self.offset;

    def up(self):
        at_top = self.cursor < 1;

        if self.cursor > 0:
            self.cursor -= 1;

        if self.offset > 0:
            self.offset -= 1;

        self.win.chgat(self.cursor + 1, 0, curses.A_NORMAL);
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);

        self.disp();
        
    def down(self):
        at_bot = self.cursor > self.h - 1;
        if at_bot:
            if self.offset < len(self.data):
                self.offset += 1;
        else:
            self.cursor += 1;


        self.win.chgat(self.cursor - 1, 0, curses.A_NORMAL);
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);

        self.disp();
                                        

    def exe(self):
        arg = self.highlighted();

    def disp(self):
        for ii in range(0, self.h):
            if (ii + self.offset) > len(self.data):
                break;
            self.print_line(0, ii, self.data[ii + self.offset]);

        self.win.refresh();

    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.w);
        self.win.addstr(y, x, line);

    def refresh(self):
        self.win.refresh();

        
def main(stdscr):
    curses.curs_set(False);

    stdscr.clear();


    shit = [str(i) for i in range(0, 40)];
        
    a = Menu(w = curses.COLS, h = curses.LINES, data=shit);
    a.data = shit;
    a.disp();
    
    while(True):
        a.refresh()
        key = a.win.getkey();
        if key == 'KEY_UP':
            a.up();
        elif key == 'KEY_DOWN':
            a.down();


if __name__ == "__main__":
    curses.wrapper(main);
    
