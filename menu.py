import curses

class Menu:
    def __init__(self, x = 0, y = 0, w = 0, h = 0, data = [], form = lambda ll: str(ll)):
        self.x = x;
        self.y = y;
        self.w = w;
        self.h = h;
        self.win = curses.newwin(h, w, y, x);
        self.win.keypad(True);
        self.data = data;
        self.form = form;
        
        self.blank = " " * self.w;

        self.cursor = 0;
        self.offset = 0;
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);


    def selected(self):
        return self.data[self.selected_ind()];

    def selected_ind(self):
        return self.cursor + self.offset;

    def up(self):
        self.win.chgat(self.cursor, 0, curses.A_NORMAL);

        at_top = self.cursor < 1;

        if not at_top:
            self.cursor -= 1;
        else:
            if self.offset > 0:
                self.offset -= 1;

        self.disp();
        
    def down(self):
        self.win.chgat(self.cursor, 0, curses.A_NORMAL);
        
        at_bot = self.cursor > (self.h - 3);

        if at_bot:
            if (self.offset + self.cursor) < (len(self.data) - 1):
                self.offset += 1;
        else:
            if (self.offset + self.cursor) < (len(self.data) - 1):
                self.cursor += 1;

        self.disp();
                                        

    def exe(self):
        arg = self.highlighted();

    def disp(self):
        for ii in range(0, self.h - 1):
            if (ii + self.offset) > (len(self.data) - 1):
                self.print_line(0, ii, self.blank);
            else:
                self.print_line(0, ii, self.form(self.data[ii + self.offset]));

        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);
        self.win.refresh();

    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.w);
        self.win.addstr(y, x, line);

    def refresh(self):
        self.win.refresh();



class Window:
    def __init__(self, x = 0, y = 0, w = 0, h = 0):
        self.x = x;
        self.y = y;
        self.w = w;
        self.h = h;
        self.win = curses.newwin(h, w, y, x);
        self.win.keypad(True);

        self.blank = " " * self.w;

        self.cursor = 0;
        self.offset = 0;

    def disp(self):
        for ii in range(0, self.h - 1):
            if (ii + self.offset) > (len(self.data) - 1):
                self.print_line(0, ii, self.blank);
            else:
                self.print_line(0, ii, self.data[ii + self.offset]);

        self.win.refresh();

    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.w);
        self.win.addstr(y, x, line);

    def refresh(self):
        self.win.refresh();
