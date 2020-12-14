import curses
import enum
import queue
import threading
import time

import commands
import inp
import menu
import player
import playlist
import threadwin
import wchar

from loadconf import config
import debug

song_info_bar_height = 2
command_bar_height = 2
class Player_ui:
    def __init__(self, stdscr, db):
        #currently highlighted window
        #left window is 0, right is 1
        self.cur = 0

        #pointer to the ncurses stdscr
        self.stdscr = stdscr

        #music database
        self.db = db

        #flag to decide if we kill the ui
        self.die = False

        #currently playing playlist
        self.cur_pl = None

        #amount of time in between drawing in seconds
        #not really a frame time but w/e
        self.frame_time = 0.01

        #actual music player
        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)

        #the windows of the player
        self.leftwin, self.botwin, self.textwin = self.__init_windows()

        #handles typed commands
        self.commands = commands.Commands(self)
        
        #hotkeys from config.py
        self.actions = self.__init_actions()

        #input queue and thread
        self.inp = inp.Input(self)

        #thread for updating everything visually
        threading.Thread(target=self.__info_print_loop, daemon=True).start()

        
    @property
    def rightwin(self):
        return self.leftwin.highlighted()


    def cur_win(self):
        return [self.leftwin, self.rightwin][self.cur]


    def set_die(self, *args):
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
            [config.COMMAND, self.commands.prepare_command],
            [config.SELECT, self.select],
            [config.HIGHLIGHT, self.highlight],
            [config.TRANSFER, self.transfer],
            [config.DELETE, self.delete],
            [config.CUR_PLAY, self.jump_cur_play],
            [config.JUMP_UP, self.jump_up],
            [config.JUMP_DOWN, self.jump_down],
            [{curses.KEY_RESIZE}, self.resize],
        ]

        for key, val in pairs:
            actions.update(dict.fromkeys(key, val))

        return actions

        
    def __init_windows(self):
        hh, ww, cc = config.set_size(self.stdscr)

        win = threadwin.Threadwin(hh, cc - ww, 0, ww)

        data = [menu.Menu(win=win, data=playlist.Playlist(name=pl, db=self.db),
                          form=config.SONG_DISP,
                          cursor_colour=config.CURSOR[0],
                          highlight_colour=config.HIGHLIGHT_COLOUR[0],
                          normal_colour=config.NORMAL[0])
                for pl in self.db.list_pl()]

        leftwin = menu.Menu(0, 0, ww, hh, data=data,
                            cursor_colour=config.FOCUSED[0],
                            highlight_colour=config.HIGHLIGHT_COLOUR[0],
                            normal_colour=config.NORMAL[0])

        botwin = menu.Window(0, hh, cc, song_info_bar_height)
        textwin = menu.Window(0, hh + song_info_bar_height, cc, command_bar_height)
        return leftwin, botwin, textwin


    """
    Functions called from key press/events
    """
    def delete(self, *args):
        """
        delete songs from playlists
        """
        if self.cur == 0:
            self.commands.delpl([])
        elif self.cur == 1:
            cur_song = self.rightwin.highlighted()

            self.rightwin.data.remove(cur_song)
            self.rightwin.delete(cur_song)

            if not self.rightwin.data:
                self.switch_view_left()


    def down(self, *args):
        """
        same as up, but down (?)
        """
        self.cur_win().down()


    def highlight(self, *args):
        """
        highlight an entry to do stuff with
        """
        self.cur_win().highlight()
        self.cur_win().down()


    def jump_cur_play(self, *args):
        if self.player.is_not_playing():
            return

        #check that cur_pl and the currently selected pl are the same
        if self.cur_pl is self.rightwin.data:
            #check that cur_song is in the cur_pl
            if self.player.cur_song in self.cur_pl.data:
                ind = self.rightwin.data.index(self.player.cur_song)
                self.jump_to_ind(ind, len(self.cur_pl.data), self.rightwin)
                self.switch_view_right()
        else:
            for i, menu_pl in enumerate(self.leftwin.data):
                if menu_pl.data is self.cur_pl:
                    ind = i
                    break

            self.jump_to_ind(ind, len(self.leftwin.data), self.leftwin)
        self.leftwin.win.touchwin()


    def jump_down(self, *args):
        cw = self.cur_win()
        cw.jump_down(cw.h // 2)


    def jump_up(self, *args):
        cw = self.cur_win()
        cw.jump_up(cw.h // 2)


    def mute(self, *args):
        self.player.toggle_mute()


    def resize(self, *args):
        """
        handle resize event
        """
        hh, ww, cc = config.set_size(self.stdscr)

        #x position
        xx = [0, ww, 0, 0]

        #y position
        yy = [0, 0, hh, hh + song_info_bar_height]

        #window widths
        wl = [ww, cc - ww, cc, cc]

        #window heights
        hl = [hh, hh, song_info_bar_height, command_bar_height]

        wins = [self.leftwin, self.rightwin, self.botwin, self.textwin]

        for win, x, y, w, h in zip(wins, xx, yy, wl, hl):
            win.win.resize(h, w)
            win.win.mvwin(y, x)

        for win in wins[0:2]:
            if win.cursor >= win.h:
                prev = win.cursor + win.offset
                win.cursor = win.h - 1
                win.offset = prev - win.cursor


    def select(self, *args):
        """
        play a song in a playlist
        """
        self.cur_pl = self.rightwin.data
        if self.cur == 1:
            next_song = self.rightwin.highlighted()
        elif self.cur == 0:
            next_song = next(self.cur_pl)
        else:
            next_song = None
            
        if next_song:
            self.player.play(next_song)
            self.cur_pl.remake_gen()
            self.cur_pl.ind = self.rightwin.highlighted_ind()


    def switch_view(self, *args):
        """
        switch focus from left to right, and vice versa
        """
        if not self.leftwin.data:
            return

        if self.cur == 1:
            self.switch_view_left()
        else:
            self.switch_view_right()
        self.leftwin.win.touchwin()

        
    def switch_view_right(self):
        self.cur = 1
        self.rightwin.cursor_colour = config.FOCUSED[0]
        self.leftwin.cursor_colour = config.CURSOR[0]


    def switch_view_left(self):
        self.cur = 0
        self.leftwin.cursor_colour = config.FOCUSED[0]
        self.rightwin.cursor_colour = config.CURSOR[0]


    def transfer(self, *args):
        """
        move songs around playlists
        """
        if self.cur != 1:
            return
        
        if not self.leftwin.highlight_list:
            return

        curpl = self.rightwin.data
        cur_song = self.rightwin.highlighted()
        if not cur_song:
            return

        for pl in self.leftwin.highlight_list:
            if pl is not curpl:
                pl.data.insert(cur_song['path'])

        self.rightwin.down()

    
    def up(self, *args):
        """
        scroll up on the menu
        also update the right window's data if the left window is scrolled up
        """
        self.cur_win().up()


    """
    Utility functions
    """
    def draw(self):
        if self.leftwin.win.is_wintouched() or self.rightwin.win.is_wintouched():
            self.leftwin.disp()
            self.rightwin.disp()

        if self.botwin.win.is_wintouched():
            self.botwin.refresh()

        if self.textwin.win.is_wintouched():
            self.textwin.refresh()


    def __enqueue(self, args=None):
        """
        add a new song onto the player queue
        """
        self.player.append(next(self.cur_pl))


    def jump_to_ind(self, ind, data_len, window):
        offset = ind - int(window.h / 2)
        if offset >= data_len - window.h:
            #for the case that the found index is near the bottom
            offset = data_len - window.h
        if offset < 0:
            #offset must be greater than 0
            offset = 0

        window.cursor = ind - offset
        window.offset = offset


    def __print_cur_playing(self):
        """
        print currently playing song/playlist in bottom window with highlight
        """
        song = self.player.cur_song.info()

        if self.player.is_paused():
            song += ' *PAUSED*'

        self.botwin.print_line(song)

        if self.cur_pl:
            self.botwin.print_right_justified(' ' + self.cur_pl.name + ' ')
        
        self.botwin.win.chgat(0, 0, self.botwin.w, config.FOCUSED[0])

        
    def mainloop(self):
        while not self.die:
            #check input queue for any new things to do
            func, args = self.inp.get()

            #do something based off of type of item
            func(*args)


    def __info_print(self):
        time_str = config.song_length(self.player.cur_time())
        total_time_str = config.song_length(self.player.cur_song['length'])

        info_str = ' '.join([time_str, '/', total_time_str, '| Vol:', str(self.player.vol)])
        if self.player.mute:
            info_str += ' [M]'

        self.botwin.print_line(info_str, y=1)
        self.botwin.print_right_justified(' ' + self.rightwin.data.playmode + ' ', y=1)

        if not self.player.curempty():
            player_event = self.player.curplay()
            
            #playback ended normally, increment playcount
            if player_event == player.Event.end_normal:
                self.inp.put_nowait((self.db.increment_playcount, (self.player.cur_song,)))

                #queue another song
                self.inp.put_nowait((self.__enqueue, (None,)))

        self.__print_cur_playing()


    def __info_print_loop(self):
        while not self.die:
            start = time.time()
            self.__info_print()

            self.draw()
            self.colour_cur_playing()
            
            curses.doupdate()
            diff = time.time() - start

            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)

            self.commands.err.check()

    def colour_cur_playing(self):
        if self.player.is_not_playing():
            return

        if self.cur_pl != self.rightwin.data:
            return

        if self.player.cur_song not in self.cur_pl.data:
            return

        newind = self.rightwin.data.index(self.player.cur_song) - self.rightwin.offset
        self.rightwin.paint(config.PLAYING_HIGHLIGHT[0], newind)
        self.rightwin.refresh()
