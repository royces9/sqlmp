import curses
import curses.textpad as tp
import shlex

import display
import musicdb
import playlist

import keys

class Player_disp(display.Display):
    def __init__(self, wins, db):
        super().__init__(wins)
        self.ex_dict = {
            'sort': self.sort_pl,
            'newpl': self.new_pl,
            'delpl': self.del_pl,
            'renamepl': self.rename_pl,
            'playmode': self.playmode_pl,
        }

        for win in self.wins:
            win.win.syncok(True)

        self.db = db
        self.conn = db.conn
        self.curs = db.curs

        #get list of playlists for left window
        self[0].data = [playlist.Playlist(name=pl, db=self.db) for pl in self.db.list_pl()]

        #set data for the first playlist
        self[1].data = self[0].data[0].data

        #text window for information
        self.textwin =  self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)

        self[0].disp()
        self[1].disp()
        self.disp_selected_song()

        
    """
    Functions called from key press/events
    """
    def up(self, *args):
        self.curwin().up()

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()

        self.disp_selected_song()


    def down(self, *args):
        self.curwin().down()

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()
                                                            
        self.disp_selected_song()

        
    def switch_view(self, *args):
        if self.cur == 1:
            self.cur = 0
            self.wins[0].highlight_colour = keys.FOCUSED
            self.wins[1].highlight_colour = keys.HIGHLIGHTED
        else:
            self.cur = 1
            self.wins[1].highlight_colour = keys.FOCUSED
            self.wins[0].highlight_colour = keys.HIGHLIGHTED
            
        self[0].disp()
        self[1].disp()
        

    def grab_input(self, *args):
        self[2].win.addstr(2, 0, ":")
        self[2].refresh()

        self.tb.win.move(0, 0)

        curses.curs_set(2)
        inp = self.tb.edit()
        curses.curs_set(0)

        self.exec_inp(inp)
        self[2].win.addstr(2, 0, self[2].blank)


    
    def select(self, *args):
        player = args[2]

        with player.playq.mutex:
            player.playq.queue.clear()

        player.play(self[1].highlighted());

        curpl = self[0].highlighted()

        curpl.cur = self[1].highlighted_ind()
        curpl.ind = curpl.cur
        curpl.set_order()

        for _ in range(len(self[1].data)):
            newsong = curpl._next()
            player.append(newsong)


    def resize(self, stdscr):
        y, x = stdscr.getmaxyx()
        curses.resizeterm(y, x)
        bottom_bar = 5
        hh = curses.LINES - bottom_bar + 1
        ww = curses.COLS // 6

        wl = [ww, curses.COLS - ww, curses.COLS]
        hl = [hh, hh, bottom_bar]
        """
        self[0].w = ww
        self[0].h = hh
        self[0].blank = " " * self[0].w

        self[1].w = curses.COLS - ww
        self[1].h = hh
        self[1].blank = " " * self[1].w

        
        self[2].w = curses.COLS
        self[2].h = bottom_bar
        self[2].blank = " " * self[2].w

        self[0].win.clear()
        self[1].win.clear()
        self[2].win.clear()
        """
        for win, w, h in zip(self.wins, wl, hl):
            win.w = w
            win.h = h
            win.blank = ' ' * w
            #win.win.resize(h, w)
            #win.win.clear()
            #win.win.refresh()
        #stdscr.clear()


    """
    Functions called from exec_inp
    """
    def exec_inp(self, inp):
        spl = shlex.split(inp)

        if not spl:
            return
        
        if spl[0] in self.ex_dict:
            self.err_print("")
            self.ex_dict[spl[0]](spl[1:])
            self.disp_selected_song()
        else:
            self.err_print('Invalid command: ' + spl[0])
            
    def playmode_pl(self, args):
        if len(args) < 1:
            self.err_print('One argument required')
            return

        playback = args[0]
        cur = self[0].highlighted()
        if playback in cur.play_order_list:
            cur.change_playtype(playback)
        else:
            self.err_print(f'"{playback}" is not a valid playback mode')


    def sort_pl(self, args):
        if len(args) < 1:
            self.err_print('One argument required')
            return

        _key = args[0]
        cur = self[0].highlighted()
        if _key in cur.tags:
            cur.change_sort(_key)
            self[1].disp()
        else:
            self.err_print(f'"{_key}" is not a valid key to sort by')
            
    def new_pl(self, args):
        if len(args) < 2:
            self.err_print('Two arguments required')
            return

        plfile = args[0]
        plname = args[1]

        sqlstr = f"SELECT plname FROM playlists WHERE plname='{plname}' LIMIT 1;";
        self.curs.execute(sqlstr);
        if self.curs.fetchone():
            self.err_print(f'Playlist "{plname}" already exists')
            return

        playlist.init_pl(plname, self.db);        
        newpl = playlist.Playlist(name=plname, db=self.db)
        newpl.insert_from_file(plfile)

        self[0].data.append(newpl)
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
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return
        else:
            ind = self[0].highlighted_ind()
            plname = self[0].data[ind].name

        playlist.del_pl(plname, self.db)
        self[0].data.pop(ind)
        if ind >= len(self[0].data):
            self.up(None)
            
        self[0].disp()
                
    def rename_pl(self, args):
        if len(args) > 1:
            curname = args[0]
            newname = args[1]
            ind = -1
            for i in range(len(self[0].data)):
                if self[0].data[i].name == curname:
                    ind = i
                    break

            if ind == -1:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

        elif len(args) > 0:
            ind = self[0].highlighted_ind()
            newname = args[0]

        else:
            self.err_print('One argument required')
            return

        self[0].data[ind].rename(newname)
        self[0].disp()
        
        
    """
    Utility functions
    """
    def err_print(self, err):
        self[2].win.addstr(3, 0, self[2].blank)
        self[2].win.addstr(3, 0, err)        
        

    def disp_selected_song(self):
        sel_song = self[1].highlighted()
        disp_song = ' - '.join([sel_song['title'], sel_song['artist'], sel_song['album']])
        self[2].print_line(0, 1, disp_song)

        playback = self[0].highlighted().playback
        self[2].win.addstr(1, self[2].w - len(playback) - 2, ' '+ playback + ' ')
        self[2].refresh()
