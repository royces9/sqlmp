import curses
import curses.textpad as tp
import threading
import time

import commands
import menu
import player
import playlist
import song
import threadwin

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
    def __init__(self, stdscr, db):
        self.cur = 0
        self.stdscr = stdscr
        self.db = db

        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)

        self.leftwin, _, self.botwin = self.__init_windows()

        #typed commands
        self.commands = commands.Commands(self)
        self.command_event = self.commands.command_event

        #hotkeys, from keys.py
        self.actions = self.__init_actions()

        #text window for information
        self.textwin = self.botwin.win.subwin(1, self.botwin.w - 1, self.botwin.y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)
        self.botwin.win.leaveok(True)

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


    @property
    def rightwin(self):
        return self.leftwin.highlighted()


    def getkey(self):
        out = self.stdscr.getkey()
        curses.flushinp()

        return out

    def curwin(self):
        return [self.leftwin, self.rightwin][self.cur]


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
            #[['KEY_RESIZE'], self.resize],
        ]

        for key, val in pairs:
            actions.update(dict.fromkeys(key, val))

        return actions


    def __init_windows(self):
        hh, ww, bottom_bar, cc = config.set_size(self.stdscr)

        win = threadwin.Threadwin(hh, cc - ww, 0, ww)

        data = [menu.Menu(win=win, data=playlist.Playlist(name=pl, db=self.db),
                          form=config.SONG_DISP,
                          cursor_colour=config.CURSOR[0],
                          highlight_colour=config.HIGHLIGHT_COLOUR[0],
                          normal_colour=config.NORMAL[0])
                for pl in self.db.list_pl()]

        leftwin = menu.Menu(0, 0, ww, hh, data=data,
                            form=lambda x: ((x.data.name, 1),),
                            cursor_colour=config.FOCUSED[0],
                            highlight_colour=config.HIGHLIGHT_COLOUR[0],
                            normal_colour=config.NORMAL[0])

        rightwin = leftwin[0]
        botwin = menu.Window(0, hh, cc, bottom_bar)
        
        return leftwin, rightwin, botwin


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
            cursong = self.rightwin.highlighted()

            self.rightwin.data.remove(cursong)
            self.rightwin.delete(cursong)

            if not self.rightwin.data:
                self.switch_view_left()

        self.draw()


    def down(self, arg=None):
        """
        same as up, but down (?)
        """
        self.curwin().down()


    def grab_input(self, arg=None):
        """
        grab a command input when ':' is pressed
        """
        #command_event.clear() is called from the input thread
        #in sqlmp, this prevents a race condition where getkey
        #gets called before the queue can execute grab_input

        self.botwin.print_blank(2)
        self.botwin.win.addch(2, 0, ":")
        self.botwin.win.move(2, 1)
        self.botwin.refresh()

        self.tb.win.move(0, 0)

        curses.curs_set(2)
        inp = self.tb.edit()
        curses.curs_set(0)

        self.commands.exe(inp)
        self.botwin.print_blank(2)


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
        if self.cur_pl is self.rightwin.data:
            #check that cur_song is in the cur_pl
            if self.cur_song in self.cur_pl.data:
                ind = self.rightwin.data.index(self.cur_song)
                self.jump_to_ind(ind, len(self.cur_pl.data), 1)
                self.switch_view_right()
        else:
            for i, menu_pl in enumerate(self.leftwin.data):
                if menu_pl.data is self.cur_pl:
                    ind = i
                    break

            self.jump_to_ind(ind, len(self.leftwin.data), 0)


        self.draw()


    def mute(self, arg=None):
        self.player.toggle_mute()


    def resize(self, test=None):
        """
        handle resize event
        """
        hh, ww, bottom_bar, cc = config.set_size(self.stdscr)

        xx = [0, ww, 0]
        yy = [0, 0, hh]
        wl = [ww, cc - ww, cc]
        hl = [hh, hh, bottom_bar]
        wins = [self.leftwin, self.rightwin, self.botwin]

        for win, x, y, w, h in zip(wins, xx, yy, wl, hl):
            win.win.resize(h, w)
            win.win.mvwin(y, x)

        for win in wins[0:2]:
            if win.cursor >= win.h:
                prev = win.cursor + win.offset
                win.cursor = win.h - 1
                win.offset = prev - win.cursor

        
        self.textwin = self.botwin.win.subwin(1, self.botwin.w - 1, self.botwin.y + 2, 1)
        self.tb = tp.Textbox(self.textwin, insert_mode=True)

        self.draw()

    def select(self, arg=None):
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


    def switch_view(self, arg=None):
        """
        switch focus from left to right, and vice versa
        """
        if not self.leftwin.data:
            return

        if self.cur == 1:
            self.switch_view_left()
        else:
            self.switch_view_right()

        self.draw()

        
    def switch_view_right(self):
        self.cur = 1
        self.rightwin.cursor_colour = config.FOCUSED[0]
        self.leftwin.cursor_colour = config.CURSOR[0]


    def switch_view_left(self):
        self.cur = 0
        self.leftwin.cursor_colour = config.FOCUSED[0]
        self.rightwin.cursor_colour = config.CURSOR[0]

        

    def transfer(self, arg=None):
        """
        move songs around playlists
        """
        if self.cur != 1:
            return
        
        if not self.leftwin.highlight_list:
            return

        curpl = self.rightwin.data
        cursong = self.rightwin.highlighted()
        if not cursong:
            return

        for pl in self.leftwin.highlight_list:
            if pl is not curpl:
                pl.data.insert(cursong['path'])

        self.rightwin.down()

    
    def up(self, arg=None):
        """
        scroll up on the menu
        also update the right window's data if the left window is scrolled up
        """
        self.curwin().up()


    """
    Utility functions
    """
    def draw(self):
        self.leftwin.disp()
        self.rightwin.disp()

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

        self.botwin.print_line(song)

        if self.cur_pl:
            self.botwin.print_right_justified(' ' + self.cur_pl.name + ' ')
        
        self.botwin.win.chgat(0, 0, self.botwin.w, config.FOCUSED[0])


    def __info_print(self):
        time_str = config.song_length(self.player.cur_time())
        total_time_str = config.song_length(self.cur_song['length'])

        info_str = ' '.join([time_str, '/', total_time_str, '| Vol:', str(self.player.vol)])
        if self.player.mute:
            info_str += ' [M]'
        playmode = self.rightwin.data.playmode

        self.botwin.print_line(info_str, y=1)
        self.botwin.print_right_justified(' ' + playmode + ' ', y=1)

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

            self.botwin.refresh()

            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)
