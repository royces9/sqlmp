import threadwin
import wchar

class Window:
    def __init__(self, x=0, y=0, w=0, h=0, win=None):
        self.win = win if win else threadwin.Threadwin(h, w, y, x)
        self.win.keypad(1)

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
        self.win.addnstr(y, self.w - length, line, length - 1)
                

    def refresh(self):
        self.win.noutrefresh()
                    
