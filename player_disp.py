import curses
import curses.textpad as tp
import os
import shlex
import threading
import time

import display
import musicdb
import playlist

import keys

import debug

class Player_disp(display.Display):
    def __init__(self, wins, stdscr, db, player):
        super().__init__(wins, stdscr)
        self.ex_dict = {
            'sort': self.sort,
            'newpl': self.newpl,
            'delpl': self.delpl,
            'renamepl': self.renamepl,
            'playmode': self.playmode,
            'adddir': self.adddir,
            'addfile': self.addfile,
            'update': self.update,
        }

        self.player = player
        self.db = db
        self.conn = db.conn
        self.curs = db.curs

        #text window for information
        self.textwin = self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)
        self[2].win.leaveok(True)
        
        #init a blank song 
        self.cur_song = {'title': 'Nothing currently playing',
                         'artist': '',
                         'album': '',
                         'length': 0,
                         'bitrate': 0}

        self.cur_pl = None
        
        self.thread = threading.Thread(target=self.__info_print, daemon=True)
        self.thread.start()

        self[0].disp()
        self[1].disp()

        self.stdscr.refresh()

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
            self[1].highlight_list = []
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()

    def down(self, arg=None):
        """
        same as up, but down (?)
        """
        self.curwin().down()

        if self.cur == 0:
            self[1].data = self[0].highlighted().data
            self[1].highlight_list = []
            self[1].cursor = 0
            self[1].offset = 0
            self[1].disp()

        
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
        self[2].print_blank(2)
        
        self[2].win.move(2, 1)
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
            
        self.curwin().disp()

            
    def select(self, arg=None):
        """
        play a song in a playlist
        """
        next_song = self[1].highlighted()
        if not next_song:
            return
        
        with self.player.playq.mutex:
            self.player.playq.queue.clear()
            self.player.pauseq.put_nowait(())

        self.player.play(next_song);

        self.cur_pl = self[0].highlighted()

        self.cur_pl.cur = self[1].highlighted_ind()
        self.cur_pl.ind = self.cur_pl.cur
        self.cur_pl.set_order()

        self.__enqueue()


    def resize(self):
        """
        handle resize event
        """
        hh, ww, bottom_bar, ll, cc = keys.set_size(self.stdscr)

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

        self.stdscr.refresh()

        self.__print_cur_playing()
        

    """
    Functions called from exec_inp
    """
    def exec_inp(self, inp):
        """
        executes the actual command from grab_inp
        """
        spl = shlex.split(shlex.quote(inp))
        if not spl:
            return
        
        if spl[0] in self.ex_dict:
            self.err_print("")
            self.ex_dict[spl[0]](spl[1:])
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

            if ind < 0:
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

            if ind < 0:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

        self[0].data[ind].rename(newname)
        self[0].disp()
        
        
    def addfile(self, args):
        """
        add a file to a playlist, also adds the file to the playlist
        1 arg : add file to highlighted playlist
        2 args: add file to named playlist
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

        newfile = args[0]
        pl.insert(newfile)
        self[1].disp()


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
    def pl_exists(self, name):
        """
        check if pl exists and return its index in list
        """
        for i, d in enumerate(self[0].data):
            if d.name == name:
                return i

        return -1


    def __song_str_info(self, song):
        """
        return a string with formatted song info
        """
        info = [song[key] for key in ['artist', 'title', 'album'] if song[key] is not '']
        return ' - '.join(info)


    #stuff for bottom window
    def __info_print(self):
        """
        function that runs on separate thread
        prints information onto bottom window
        """
        while True:
            start = time.time()
            time_str = self.str_song_length(self.player.cur_time())
            total_time_str = self.str_song_length(self.cur_song['length'])

            self[2].print_line(' / '.join([time_str, total_time_str]),y=1)
            
            playmode = self[0].highlighted().playmode
            self[2].print_line(' ' + playmode + ' ', y=1, x=self[2].w - len(playmode) - 2)
            
            if not self.player.curq.empty():
                player_event = self.player.curplay()
                #check if the event is for playback starting or ending
                if player_event:
                    #playback started, print information to bottom window
                    self.cur_song = player_event
                    
                    self[2].refresh()
                else:
                    #playback ended, queue another song
                    self.__enqueue()

            self.__print_cur_playing()

            self[2].refresh()
            diff = time.time() - start
            if diff < 0.1:
                time.sleep(0.1 -diff)



    def __enqueue(self):
        """
        add a new song onto the player queue
        """
        self.player.append(self.cur_pl._next())

        
    def __print_cur_playing(self):
        """
        print currently playing song in bottom window with highlight
        """
        self[2].print_line(self.__song_str_info(self.cur_song))
        self[2].win.chgat(0, 0, self[2].w, keys.FOCUSED[0])


    def err_print(self, err):
        self[2].print_blank(3)
        self[2].print_line(err, y=3)


    def str_song_length(self, len_s):
        """
        return formatted string for time given a value in seconds
        """
        m = str(int(len_s // 60))
        s = int(round(len_s % 60))

        s = str(s) if s > 9 else '0' + str(s)

        return ':'.join([m, s])
        
