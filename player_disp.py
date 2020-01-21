import curses
import curses.textpad as tp
import os
import shlex
import sys
import threading
import time

import display
import player
import playlist

import config

import debug

def song_info(song):
    """
    return a string with formatted song info
    """
    info = [str(song[key]) for key in config.SONG_INFO
            if song[key]]
    return ' - '.join(info)


class Player_disp(display.Display):
    def __init__(self, wins, stdscr, db):
        super().__init__(wins, stdscr)

        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)
        self.db = db
        self.conn = db.conn
        self.curs = db.curs

        #typed commands
        self.commands = {
            'adddir': self.adddir,
            'addfile': self.addfile,
            'delpl': self.delpl,
            'export': self.export,
            'newpl': self.newpl,
            'playmode': self.playmode,
            'renamepl': self.renamepl,
            'sort': self.sort,
            'update': self.update,
        }

        #hotkeys, from keys.py
        self.actions = {}
        self.__init_actions()

        #text window for information
        self.textwin = self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)
        self[2].win.leaveok(True)

        #init a blank song
        self.cur_song = {'title': 'Nothing currently playing',
                         'artist': '',
                         'album': '',
                         'length': 0,
                         'samplerate': 0,
                         'channels': 0,
                         'bitrate': 0,
                         'playcount': 0
        }

        #currently playing playlist
        self.cur_pl = None

        #amount of time in between drawing
        #not really a frame time but w/e
        self.frame_time = 0.1

        self.info = threading.Thread(target=self.__info_print, daemon=True)
        self.info.start()

        self[0].disp()
        self[1].disp()

        self.die = False
        self.stdscr.refresh()


    def set_die(self):
        self.die = True

    def __init_actions(self):
        import signal
        pairs = [
            [config.UP, self.up],
            [config.DOWN, self.down],
            [config.LEFT, self.player.seek_backward],
            [config.RIGHT, self.player.seek_forward],
            [config.VOLUP, self.player.vol_up],
            [config.VOLDOWN, self.player.vol_down],
            [config.MUTE, self.mute],
            [config.PLAYPAUSE, self.player.play_pause],
            [config.QUIT, self.set_die],
            [config.SWITCH, self.switch_view],
            [config.COMMAND, self.grab_input],
            [config.SELECT, self.select],
            [config.HIGHLIGHT, self.highlight],
            [config.TRANSFER, self.transfer],
            [config.DELETE, self.delete],
            [config.CUR_PLAY, self.jump_cur_play],
            [['KEY_RESIZE'], self.resize],
        ]

        for key, val in pairs:
            self.actions.update(dict.fromkeys(key, val))


    """
    Functions called from key press/events
    """
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

            if not self[1].data:
                self.cur = 0
                self.wins[0].cursor_colour = config.FOCUSED[0]
                self.wins[1].cursor_colour = config.CURSOR[0]

        self.curwin().disp()


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


    def jump_cur_play(self, arg=None):
        if self.cur == 0 or self.player.is_not_playing():
            return

        #O(n) :grimacing:
        for i, song in enumerate(self[1].data):
            if song is self.cur_song:
                self[1].cursor = 0
                self[1].offset = i
                self[1].disp()
                break


    def mute(self, arg=None):
        self.player.toggle_mute()

    def resize(self):
        """
        handle resize event
        """
        hh, ww, bottom_bar, cc = config.set_size(self.stdscr)

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


    def select(self, arg=None):
        """
        play a song in a playlist
        """
        self.cur_pl = self[0].highlighted()
        if self.cur == 1:
            next_song = self[1].highlighted()
        elif self.cur == 0:
            next_song = next(self.cur_pl)

        if next_song:
            self.player.status = player.Play_state.new
            self.player.play(next_song)
            self.cur_pl.ind = self[1].highlighted_ind()


    def switch_view(self, arg=None):
        """
        switch focus from left to right, and vice versa
        """
        if not self[1].data:
            return

        if self.cur == 1:
            self.cur = 0
            self.wins[0].cursor_colour = config.FOCUSED[0]
            self.wins[1].cursor_colour = config.CURSOR[0]
        else:
            self.cur = 1
            self.wins[1].cursor_colour = config.FOCUSED[0]
            self.wins[0].cursor_colour = config.CURSOR[0]

        self[0].disp()
        self[1].disp()


    def transfer(self, arg=None):
        """
        move songs around playlists
        """
        if not self.wins[0].highlight_list:
            return

        curpl = self[0].highlighted()
        cursong = self[1].highlighted()
        if not cursong:
            return

        for pl in self[0].highlight_list:
            if pl is not curpl:
                pl.insert(cursong['path'])

        self[1].down()


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


    """
    Functions called from exec_inp
    """
    def exec_inp(self, inp):
        """
        executes the actual command from grab_inp
        """
        spl = shlex.split(inp)
        if not spl:
            self.err_print("")
            return

        if spl[0] in self.commands:
            self.err_print("")
            self.commands[spl[0]](spl[1:])
        else:
            self.err_print('Invalid command: ' + spl[0])


    def adddir(self, args):
        """
        add a directory to a playlist, this also adds new directories to the db
        1 arg : add directory to highlighted playlist
        2 args: add directory to named playlist
        """
        if not args:
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


    def addfile(self, args):
        """
        add a file to a playlist, also adds the file to the playlist
        1 arg : add file to highlighted playlist
        2 args: add file to named playlist
        """
        if not args:
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


    def delpl(self, args):
        """
        delete a playlist
        0 args: delete highlighted playlist
        1 arg : delete the named playlist
        """
        if not args:
            pl = self[0].highlighted()
            plname = pl.name
        else:
            plname = args[0]
            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

            pl = self[0].data[ind]

        self[0].delete(pl)
        playlist.del_pl(plname, self.db)

        self[0].disp()
        self[1].disp()


    def export(self, args):
        """
        export a playlist
        1 args: export highlighted playlist to directory
        2 args: export the named playlist to directory
        """
        if not args:
            self.err_print('One argument required')
            return
        elif len(args) == 1:
            pl = self[0].highlighted()
            plname = pl.name
            dest = args[0]
        else:
            plname = args[0]
            dest = args[1]

            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print(f'Playlist "{plname}" doesn\'t exist')
                return

            pl = self[0].data[ind]

        if not os.path.exists(dest):
            self.err_print(f'Directory "{dest}" doesn\'t exists')
            return

        with open('/'.join([dest, plname]), 'w+') as fp:
            for d in pl.data:
                print(d['path'], file=fp)


    def newpl(self, args):
        """
        makes a new playlist
        1 arg : blank playlist with given name
        2 args: playlist with given name and contents given by file argument
        """
        if not args:
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


    def playmode(self, args):
        """
        change the playmode (shuffle, in order, single)
        """
        if not args:
            self.err_print('One argument required')
            return

        playmode = args[0]
        cur = self[0].highlighted()
        if playmode in cur.playmode_list:
            cur.change_playmode(playmode)
        else:
            self.err_print(f'"{playmode}" is not a valid playback mode')


    def renamepl(self, args):
        """
        rename a playlist
        0 args: rename highlighted playlist
        1 arg : rename the named playlist
        """
        if not args:
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
                self.err_print(f'Playlist "{curname}" doesn\'t exist')
                return

        self[0].data[ind].rename(newname)
        self[0].disp()


    def sort(self, args):
        """
        sort the playlist according to some key
        changes are saved to the db
        """
        if not args:
            self.err_print('One argument required')
            return

        _key = args[0]
        cur = self[0].highlighted()
        if _key in cur.tags:
            cur.change_sort(_key)
            self[1].disp()
        else:
            self.err_print(f'"{_key}" is not a valid key to sort by')


    def update(self, args):
        """
        update db
        """
        self.db.update()


    """
    Utility functions
    """
    def __enqueue(self):
        """
        add a new song onto the player queue
        """
        self.player.append(next(self.cur_pl))


    def err_print(self, err):
        self[2].print_blank(3)
        self[2].print_line(err, y=3)


    def pl_exists(self, name):
        """
        check if pl exists and return its index in list
        """
        for i, d in enumerate(self[0].data):
            if d.name == name:
                return i

        return -1


    def __print_cur_playing(self):
        """
        print currently playing song/playlist in bottom window with highlight
        """
        song = song_info(self.cur_song)

        if self.player.is_paused():
            song += ' *PAUSED*'

        self[2].print_line(song)

        if self.cur_pl:
            self[2].print_right_justified(' ' + self.cur_pl.name + ' ')

        self[2].win.chgat(0, 0, self[2].w, config.FOCUSED[0])


    #stuff for bottom window
    def __info_print(self):
        """
        function that runs on separate thread
        prints information onto bottom window
        also checks if a new songs needs to be
        queued
        """
        while True:
            start = time.time()
            time_str = config.song_length(self.player.cur_time())
            total_time_str = config.song_length(self.cur_song['length'])

            info_str = ' '.join([time_str, '/', total_time_str, '| Vol:', str(self.player.vol)])
            if self.player.mute:
                info_str += ' [M]'
            playmode = self[0].highlighted().playmode

            self[2].print_line(info_str, y=1)
            self[2].print_right_justified(' ' + playmode + ' ', y=1)

            if not self.player.curempty():
                player_event = self.player.curplay()
                #check if the event is for playback starting or ending
                if player_event:
                    #playback started, print information to bottom window
                    self.cur_song = player_event
                else:
                    #playback ended, queue another song
                    self.__enqueue()

            self.__print_cur_playing()

            self[2].refresh()

            diff = time.time() - start
            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)
