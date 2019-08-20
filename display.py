import curses

class Disp:
    def __init__(self, *argv):
        self.cur = 0
        self.wins = []
        for arg in argv:
            self.wins.append(arg)
        
            
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
                                                                                    

class Player_disp(Disp):
    def up(self, *args):
         curwin = self.curwin();
         curwin.up();

         sel_song = self[1].highlighted();
         disp_song = sel_song['title'] + ' - ' + sel_song['artist']
         self[2].print_line(0, 1, disp_song)

         if self.cur == 0:
             self[1].data = self[0].highlighted().data
             self[1].cursor = 0
             self[1].offset = 0
             self[1].disp()

    def down(self, *args):
        curwin = self.curwin();
        curwin.down();

        sel_song = self[1].highlighted();
        disp_song = sel_song['title'] + ' - ' + sel_song['artist']
        self[2].print_line(0, 1, disp_song)

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()
                                                            
    def switch_view(self, *args):
        if self.cur == 1:
            self.cur = 0
        else:
            self.cur = 1

            
    def grab_input(self, *args):
        self[2].win.addstr(3, 0, self[2].blank);
        self[2].win.addstr(3, 0, ":");
        self[2].refresh();

        curses.echo();
        inp = self[2].win.getstr(3, 1, curses.COLS - 2);
        curses.noecho()
        self[2].win.addnstr(3, 0, " " * curses.COLS, curses.COLS);
        self[2].win.refresh();
        
        
        self.exec_inp(inp.decode('utf-8'))

        """
        a = self[2].win.subwin(1, self[2].w, 3, 1)
        import curses.textpad as tp
        tb = tp.Textbox(a, insert_mode=True)
        def valid(c):
            if c == 10:
                return 1
        inp = tb.edit(valid)

        self.exec_inp(inp, *args);
        """        


    def exec_inp(self, inp):
        spl = inp.split()
        if len(spl) < 1:
            return
        
        if spl[0] == 'sort':
            self.sort_pl(spl[1])
    
    
    def select(self, *args):
        player = args[2]

        with player.playq.mutex:
            player.playq.queue.clear()

        player.play(self[1].highlighted());
        
        for i in range(len(self[1].data)):
            newsong = self[0].highlighted()._next()
            player.append(newsong)


    def sort_pl(self, _key):
        if _key in self[1].data[0]:
            self[1].data.sort(key=lambda x: x[_key])
            self[1].disp()
                                                    
