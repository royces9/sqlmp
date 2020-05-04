import curses
import curses.textpad as tp
import threading
import time

import commands
import player
import song

from loadconf import config
import debug


def song_info(song):
    """
    return a string with formatted song info
    """
    info = [str(song[key]) for key in config.SONG_INFO
            if song[key]]

    return ' - '.join(info)


class Player_ui:
    def __init__(self, wins, stdscr, db):
        self.cur = 0
        self.wins = wins
        self.stdscr = stdscr

        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)
        self.db = db

        #typed commands
        self.commands = commands.Commands(self)
        self.command_event = self.commands.command_event

        #hotkeys, from keys.py
        self.actions = self.__init_actions()

        #text window for information
        self.textwin = self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)
        self[2].win.leaveok(True)

        #init a blank song
        self.cur_song = song.blank_song

        #currently playing playlist
        self.cur_pl = None

        #amount of time in between drawing
        #not really a frame time but w/e
        self.frame_time = 0.1

        self.info = threading.Thread(target=self.__info_print_loop, daemon=True)
        self.info.start()

        self.die = False


    def __len__(self):
        return len(self.wins)


    def __setitem__(self, ind, item):
        self.wins[ind] = item


    def __getitem__(self, ind):
        return self.wins[ind]


    def getkey(self):
        out = self.stdscr.getkey()
        curses.flushinp()

        return out


    def curwin(self):
        return self.wins[self.cur]


    def set_die(self):
        self.die = True


    def __init_actions(self):
        actions = {}
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
            actions.update(dict.fromkeys(key, val))

        return actions

    """
    Functions called from key press/events
    """
    def delete(self, arg=None):
        """
        delete songs from playlists
        """
        if self.cur == 0:
            self.commands.delpl([])
        elif self.cur == 1:
            cursong = self[1].highlighted()

            self[0].highlighted().data.remove(cursong)
            self[1].delete(cursong)

            if not self[1].data:
                self.switch_view_left()

        self.draw()


    def down(self, arg=None):
        """
        same as up, but down (?)
        """
        self.curwin().down()

        if self.cur == 0:
            self[1] = self[0].highlighted()


    def grab_input(self, arg=None):
        """
        grab a command input when ':' is pressed
        """
        #command_event.clear() is called from the input thread
        #in sqlmp, this prevents a race condition where getkey
        #gets called before the queue can execute grab_input

        self[2].print_blank(2)
        self[2].win.addch(2, 0, ":")
        self[2].win.move(2, 1)
        self[2].refresh()

        self.tb.win.move(0, 0)

        curses.curs_set(2)
        inp = self.tb.edit()
        curses.curs_set(0)

        self.commands.exe(inp)
        self[2].print_blank(2)


    def highlight(self, arg=None):
        """
        highlight an entry to do stuff with
        """
        self.curwin().highlight()
        self.curwin().down()


    def jump_cur_play(self, arg=None):
        if self.player.is_not_playing():
            return

        #check that cur_pl and the currently selected pl
        #are the same
        if self.cur_pl is self[1].data:
            #check that cur_song is in the cur_pl
            if self.cur_song in self.cur_pl.data:
                ind = self[1].data.index(self.cur_song)
                self.jump_to_ind(ind, len(self.cur_pl.data), 1)
                self.switch_view_right()
        else:
            for i, menu_pl in enumerate(self[0].data):
                if menu_pl.data is self.cur_pl:
                    ind = i
                    break

            self.jump_to_ind(ind, len(self[0].data), 0)

            self[1].data = self[0].highlighted().data
            self[1].highlight_list = []

        self.draw()


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
            win.win.resize(h, w)
            win.win.mvwin(y, x)

        for win in self[0:2]:
            if win.cursor >= win.h:
                prev = win.cursor + win.offset
                win.cursor = win.h - 1
                win.offset = prev - win.cursor
        
        self.textwin = self[2].win.subwin(1, self[2].w - 1, self[2].y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)

        self.draw()

    def select(self, arg=None):
        """
        play a song in a playlist
        """
        self.cur_pl = self[0].highlighted().data
        if self.cur == 1:
            next_song = self[1].highlighted()
        elif self.cur == 0:
            next_song = next(self.cur_pl)
        else:
            next_song = None
            
        if next_song:
            self.player.play(next_song)
            self.cur_pl.remake_gen()
            self.cur_pl.ind = self[1].highlighted_ind()


    def switch_view(self, arg=None):
        """
        switch focus from left to right, and vice versa
        """
        if not self[1].data:
            return

        if self.cur == 1:
            self.switch_view_left()
        else:
            self.switch_view_right()

        self.draw()

        
    def switch_view_right(self):
        self.cur = 1
        self[1].cursor_colour = config.FOCUSED[0]
        self[0].cursor_colour = config.CURSOR[0]


    def switch_view_left(self):
        self.cur = 0
        self[0].cursor_colour = config.FOCUSED[0]
        self[1].cursor_colour = config.CURSOR[0]

        

    def transfer(self, arg=None):
        """
        move songs around playlists
        """
        if self.cur != 1:
            return
        
        if not self[0].highlight_list:
            return

        curpl = self[0].highlighted().data
        cursong = self[1].highlighted()
        if not cursong:
            return

        for pl in self[0].highlight_list:
            if pl is not curpl:
                pl.data.insert(cursong['path'])

        self[1].down()

    
    def up(self, arg=None):
        """
        scroll up on the menu
        also update the right window's data if the left window is scrolled up
        """
        self.curwin().up()

        if self.cur == 0:
            self[1] = self[0].highlighted()


    """
    Utility functions
    """
    def draw(self):
        self[0].disp()
        self[1].disp()

        curses.doupdate()

    def __enqueue(self):
        """
        add a new song onto the player queue
        """
        self.player.append(next(self.cur_pl))


    def jump_to_ind(self, ind, data_len, window):
        offset = ind - int(self[window].h / 2)
        if offset < 0:
            #for the case that the found index is near the top
            offset = 0
        elif offset >= data_len - self[window].h:
            #for the case that the found index is near the bottom
            offset = data_len - self[window].h

        self[window].cursor = ind - offset
        self[window].offset = offset


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


    def __info_print(self):
        time_str = config.song_length(self.player.cur_time())
        total_time_str = config.song_length(self.cur_song['length'])

        info_str = ' '.join([time_str, '/', total_time_str, '| Vol:', str(self.player.vol)])
        if self.player.mute:
            info_str += ' [M]'
        playmode = self[0].highlighted().data.playmode

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


    def __info_print_loop(self):
        while True:
            start = time.time()
            self.__info_print()
            diff = time.time() - start

            self[2].refresh()

            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)
