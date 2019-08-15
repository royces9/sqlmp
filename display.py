class Disp:
    def __init__(self, *argv):
        self.cur = 0;
        self.wins = [];
        for arg in argv:
            self.wins.append(arg);
        

    def __len__(self):
        return len(self.wins);

    
    def append(self, arg):
        self.wins.append(arg);

        
    def refresh(self):
        for win in self.wins:
            win.refresh();
            

    def curwin(self):
        return self.wins[self.cur];
                                                                                    
