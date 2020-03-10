import curses

class Display:
    def __init__(self, wins, stdscr):
        self.cur = 0
        self.wins = wins
        self.stdscr = stdscr


    def __len__(self):
        return len(self.wins)


    def __getitem__(self, ind):
        return self.wins[ind]


    def append(self, arg):
        self.wins.append(arg)


    def refresh(self):
        for win in self.wins:
            win.refresh()

        self.stdscr.refresh()


    def getkey(self):
        out = self.stdscr.getkey()
        curses.flushinp()
        return out
    

    def curwin(self):
        return self.wins[self.cur]
