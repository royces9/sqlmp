import curses
import curses.textpad as tp
import os
import shlex
import threading

import display
import musicdb
import playlist

import keys

class Player_disp(display.Display):
    def __init__(self, wins, db, player):
        super().__init__(wins)
        self.ex_dict = {
            'sort': self.sort,
            'newpl': self.newpl,
            'delpl': self.delpl,
            'renamepl': self.renamepl,
            'playmode': self.playmode,
            'adddir': self.adddir,
            'update': self.update,
        }

        for win in self.wins:
            win.win.syncok(True)

        self.player = player
        self.db = db
        self.conn = db.conn
        self.curs = db.curs

        #text window for information
        self.textwin =  self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)

        self[0].disp()
        self[1].disp()

        self.cur_song = None
        
        self.thread = threading.Thread(target=self.__info_print, daemon=True)
        self.thread.start()

        self.disp_selected_song()

        
    """
    Functions called from key press/events
    """
    def up(self, arg=None):
        """
        scroll up on the menu
        also update the right window's data if the left window is scrolled up
        """
        self.curwin().up()

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()

        self.disp_selected_song()


    def down(self, arg=None):
        """
        same as up, but down (?)
        """
        self.curwin().down()

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()
                                                            
        self.disp_selected_song()

        
    def switch_view(self, arg=None):
        """
        switch focus from left to right, and vice versa
        """
        if len(self[1].data) == 0:
            return

        if self.cur == 1:
            self.cur = 0
            self.wins[0].cursor_colour = keys.FOCUSED[0]
            self.wins[1].cursor_colour = keys.CURSOR[0]

        else:
            self.cur = 1
            self.wins[1].cursor_colour = keys.FOCUSED[0]
            self.wins[0].cursor_colour = keys.CURSOR[0]
            
        self[0].disp()
        self[1].disp()
        

    def grab_input(self, arg=None):
        """
        grab a command input when ':' is pressed
        """
        self[2].win.win.move(2, 1)
        self[2].win.addstr(2, 0, ":")
        self[2].refresh()

        self.tb.win.move(0, 0)

        curses.curs_set(2)
        inp = self.tb.edit()
        curses.curs_set(0)

        self.exec_inp(inp)
        self[2].print_blank(2)

    
    def highlight(self, arg=None):
        """
        highlight an entry to do stuff with
        """
        if self.cur == 1:
            self[1].highlight()
            self[1].down()
        elif self.cur == 0:
            self[0].highlight()


    def transfer(self, arg=None):
        """
        move songs around playlists
        """
        if len(self.wins[0].highlight_list) <= 0:
            return

        curpl = self[0].highlighted()
        cursong = self[1].highlighted()
        if not cursong:
            return
        
        for pl in self[0].highlight_list:
            if pl is not curpl:
                pl.insert(cursong['path'])

        self[1].down()


    def delete(self, arg=None):
        """
        delete songs from playlists
        """
        if self.cur == 0:
            self.delpl([])
        elif self.cur == 1:
            curpl = self[0].highlighted()
            cursong = self[1].highlighted()

            curpl.remove(cursong['path'])
            self[1].delete(cursong)

            if not len(self[1].data):
                self.cur = 0
                self.wins[0].cursor_colour = keys.FOCUSED[0]
                self.wins[1].cursor_colour = keys.CURSOR[0]
            
        self[self.cur].disp()

            
    def select(self, arg=None):
        """
        play a song in a playlist
        """
        with self.player.playq.mutex:
            self.player.playq.queue.clear()
            self.player.pauseq.put_nowait(())

        self.player.play(self[1].highlighted());

        curpl = self[0].highlighted()

        curpl.cur = self[1].highlighted_ind()
        curpl.ind = curpl.cur
        curpl.set_order()

        for _ in range(len(self[1].data)):
            newsong = curpl._next()
            self.player.append(newsong)


    def resize(self, stdscr):
        """
        handle resize event (wip, still doesn't work)
        """
        hh, ww, bottom_bar, ll, cc = keys.set_size(stdscr)

        xx = [0, ww, 0]
        yy = [0, 0, hh]
        wl = [ww, cc - ww, cc]
        hl = [hh, hh, bottom_bar]

        for win, x, y, w, h in zip(self.wins, xx, yy, wl, hl):
            win.x = x
            win.y = y
            win.w = w
            win.h = h
            win.blank = ' ' * (w - 1)

            win.win.resize(h, w)
            win.win.mvwin(y, x)
            win.win.clear()

        for win in self.wins[0:2]:
            if win.cursor >= win.h:
                prev = win.cursor + win.offset
                win.cursor = win.h - 1
                win.offset = prev - win.cursor
            win.disp()

        self.disp_selected_song()
        self.__print_cur_playing()
        

    """
    Functions called from exec_inp
    """
    def exec_inp(self, inp):
        """
        executes the actual command from grab_inp
        """
        spl = shlex.split(inp)
        if not spl:
            return
        
        if spl[0] in self.ex_dict:
            self.err_print("")
            self.ex_dict[spl[0]](spl[1:])
            self.disp_selected_song()
        else:
            self.err_print('Invalid command: ' + spl[0])

            
    def playmode(self, args):
        """
        change the playmode (shuffle, in order, single)
        """
        if len(args) < 1:
            self.err_print('One argument required')
            return

        playmode = args[0]
        cur = self[0].highlighted()
        if playmode in cur.playmode_list:
            cur.change_playmode(playmode)
        else:
            self.err_print(f'"{playmode}" is not a valid playback mode')


    def sort(self, args):
        """
        sort the playlist according to some key
        changes are saved to the db
        """
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
            

    def newpl(self, args):
        """
        makes a new playlist
        1 arg : blank playlist with given name
        2 args: playlist with given name and contents given by file argument
        """
        if len(args) == 0:
            self.err_print('One argument required')
            return
            
        elif len(args) == 1:
            plname = args[0]

            if self.pl_exists(plname) >= 0:
                self.err_print(f'Playlist "{plname}" already exists')
                return

            playlist.init_pl(plname, self.db)
            newpl = playlist.Playlist(name=plname, db=self.db)

        else:
            plfile = args[0]
            plname = args[1]
            if not os.path.isfile(plfile):
                self.err_print(f'File does not exist: {plfile}.')
                return
            
            if self.pl_exists(plname) >= 0:
                self.err_print(f'Playlist "{plname}" already exists')
                return

            playlist.init_pl(plname, self.db)
            newpl = playlist.Playlist(name=plname, db=self.db)
            newpl.insert_from_file(plfile)
            
        self[0].insert(newpl)
        self[0].disp()

        
    def delpl(self, args):
        """
        delete a playlist
        0 args: delete highlighted playlist
        1 arg : delete the named playlist
        """
        if len(args) == 0:
            item = self[0].highlighted()
            plname = item.name
        else:
            plname = args[0]
            ind = self.pl_exists(plname)

            if ind == -1:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

            item = self[0].data[ind]

        self[0].delete(item)
        playlist.del_pl(plname, self.db)
            
        self[0].disp()

        self[1].data = self[0].highlighted().data
        self[1].disp()

                
    def renamepl(self, args):
        """
        rename a playlist
        0 args: rename highlighted playlist
        1 arg : rename the named playlist
        """
        if len(args) == 0:
            self.err_print('One argument required')
            return

        elif len(args) == 1:
            ind = self[0].highlighted_ind()
            newname = args[0]

        else:
            curname = args[0]
            newname = args[1]
            ind = self.pl_exists(curname)

            if ind == -1:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

        self[0].data[ind].rename(newname)
        self[0].disp()
        
        
    def adddir(self, args):
        """
        add a directory to a playlist, this also adds new directories to the db
        1 arg : add directory to highlighted playlist
        2 args: add directory to named playlist
        """
        if len(args) == 0:
            self.err_print('One argument required')
            return

        if len(args) == 1:
            pl = self[0].highlighted()
        else:
            ind = self.pl_exists(args[1])
            if ind < 0:
                return

            pl = self[0].data[ind]
        
        newdir = args[0]
        pl.insert_dir(newdir)
        self[1].disp()

        
    def update(self, args):
        """
        update db
        """
        self.db.update()
    
    """
    Utility functions
    """
    def disp_selected_song(self):
        if len(self[1].data) < 1:
            self[2].print_blank(1)

        else:
            sel_song = self[1].highlighted()
            disp_song = self.__print_song(sel_song)
            self[2].print_line(disp_song,y=1)


        playmode = self[0].highlighted().playmode

        self[2].win.addnstr(1, self[2].w - len(playmode) - 2, ' '+ playmode + ' ', len(playmode) + 1)
        self[2].refresh()


    def pl_exists(self, name):
        for i, d in enumerate(self[0].data):
            if d.name == name:
                return i

        return -1


    def __print_song(self, song):
        return ' - '.join([song['artist'], song['title'], song['album']])


    #stuff for bottom window
    def __info_print(self):
        self.__print_cur_playing()
        while True:
            self.cur_song = self.player.curplay()
            self[2].print_blank(0)
            self.__print_cur_playing()

            self[2].refresh()


    def __print_cur_playing(self):
        line = self.__print_song(self.cur_song)\
            if self.cur_song\
               else "Nothing currently playing"
        self[2].print_line(line)


    def err_print(self, err):
        self[2].print_blank(3)
        self[2].print_line(err, y=3)

        
