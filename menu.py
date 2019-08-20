import curses

class Menu:
    def __init__(self, x = 0, y = 0, w = 0, h = 0, data = [], form = lambda ll: (str(ll), 0)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.win = curses.newwin(h, w, y, x)
        self.win.keypad(True)
        self.data = data
        self.form = form
        
        self.blank = " " * self.w

        self.cursor = 0
        self.offset = 0
        self.win.chgat(self.cursor, 0, curses.A_STANDOUT)


    def __getitem__(self, ind):
        return self.data[ind]


    def highlighted(self):
        return self.data[self.highlighted_ind()];


    def highlighted_ind(self):
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
            self.print_line(0, ii, self.blank)
            if not ((ii + self.offset) > (len(self.data) - 1)):
                formatted_list, flag = self.form(self.data[ii + self.offset])

                if flag:
                    self.print_col(ii, formatted_list)
                else:
                    self.print_line(0, ii, formatted_list)

        self.win.chgat(self.cursor, 0, curses.A_STANDOUT);

        
    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.w);
        self.win.addstr(y, x, line);

        
    def print_col(self, y, datas):
        previous = 0
        for string, fraction in datas:
            ind = previous
            previous += int(self.w * fraction)
            self.win.addstr(y, ind, string)

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

        disp.refresh()
        
    def print_line(self, x, y, line):
        self.win.addnstr(y, x, self.blank, self.w);
        self.win.addstr(y, x, line);

    def refresh(self):
        self.win.refresh();
