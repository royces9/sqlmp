class Display:
    def __init__(self, wins):
        self.cur = 0
        self.wins = wins
            
    def __len__(self):
        return len(self.wins)


    def __getitem__(self, ind):
        return self.wins[ind]
    
    def append(self, arg):
        self.wins.append(arg);

        
    def refresh(self):
        for win in self.wins:
            win.refresh();
            
    def getkey(self):
        return self.wins[0].win.getkey()

    def curwin(self):
        return self.wins[self.cur];
