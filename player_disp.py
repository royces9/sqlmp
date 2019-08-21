import curses

import display
import db_pl
import libdb
import playlist

import keys

class Player_disp(display.Disp):
    def __init__(self, wins, conn, curs):
        display.Disp.__init__(self, wins)
        self.ex_dict = {
            'sort': self.sort_pl,
            'newpl': self.new_pl,
            'delpl': self.del_pl,
        }
        
        for win in self.wins:
            win.win.syncok(True)

        self.conn = conn
        self.curs = curs

        #get list of playlists for left window
        for pl in libdb.list_playlists(curs):
            self[0].data.append(playlist.Playlist(name=pl, curs=curs))

        #set data for the first playlist
        self[1].data = self[0].data[0].data

        self[0].disp()
        self[1].disp()

    def up(self, *args):
         curwin = self.curwin();
         curwin.up();

         if self.cur == 0:
             self[1].data = self[0].highlighted().data
             self[1].cursor = 0
             self[1].offset = 0
             self[1].disp()

         sel_song = self[1].highlighted();
         disp_song = sel_song['title'] + ' - ' + sel_song['artist']
         self[2].print_line(0, 1, disp_song)


    def down(self, *args):
        curwin = self.curwin();
        curwin.down();

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()
                                                            
        sel_song = self[1].highlighted();
        disp_song = sel_song['title'] + ' - ' + sel_song['artist']
        self[2].print_line(0, 1, disp_song)


    def switch_view(self, *args):
        if self.cur == 1:
            self.cur = 0
            self.wins[0].highlight_colour = keys.FOCUSED
            self.wins[1].highlight_colour = keys.HIGHLIGHTED
        else:
            self.cur = 1
            self.wins[1].highlight_colour = keys.FOCUSED
            self.wins[0].highlight_colour = keys.HIGHLIGHTED
            
        self.wins[0].disp()
        self.wins[1].disp()
        

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

        if not spl:
            return
        
        if spl[0] in self.ex_dict:
            self.ex_dict[spl[0]](spl[1:])
    
    
    def select(self, *args):
        player = args[2]

        with player.playq.mutex:
            player.playq.queue.clear()

        player.play(self[1].highlighted());

        curpl = self[0].highlighted()

        curpl.cur = self[1].highlighted_ind()
        curpl.ind = curpl.cur
        curpl.set_order()

        for i in range(len(self[1].data)):
            newsong = curpl._next()
            player.append(newsong)


    def sort_pl(self, args):
        if len(args) < 1:
            return

        _key = args[0]
        if _key in self[1].data[0]:
            self[1].data.sort(key=lambda x: x[_key])
            self[1].disp()

            
    def new_pl(self, args):
        if len(args) < 1:
            return

        plfile = args[0]
        plname = args[1]

        sqlstr = f"SELECT plname FROM playlists WHERE plname='{plname}' LIMIT 1;";
        self.curs.execute(sqlstr);
        if not self.curs.fetchone():
            db_pl.init_pl(plname, self.conn, self.curs);
                            
        db_pl.add_to_pl_from_file(plname, plfile, self.conn, self.curs)

        self[0].data.append(playlist.Playlist(name=plname, curs=self.curs))
        self[0].disp()

        
    def del_pl(self, args):
        if len(args) > 0:
            plname = args[0]
            ind = -1
            for i in range(len(self[0].data)):
                if self[0].data[i].name == plname:
                    ind = i
                    break

            if ind == -1:
                return
        else:
            ind = self[0].highlighted_ind()
            plname = self[0].data[ind].name

        db_pl.del_pl(plname, self.conn, self.curs)

        self[0].data.pop(ind)

        self[0].disp()
                
