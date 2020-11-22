import curses
import curses.textpad as tp
import threading
import time

import commands
import keys
import menu
import player
import playlist
import song
import threadwin
import wchar

from loadconf import config
import debug

song_info_bar_height = 2
command_bar_height = 2
class Player_ui:
    def __init__(self, stdscr, db):
        self.cur = 0
        self.stdscr = stdscr
        self.db = db

        #actual music player
        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)

        #the windows of the player
        self.leftwin, self.botwin, self.textwin = self.__init_windows()

        #hotkeys from config.py
        self.actions = self.__init_actions()

        #init a blank song
        self.cur_song = song.blank_song

        #currently playing playlist
        self.cur_pl = None

        #amount of time in between drawing
        #not really a frame time but w/e
        self.frame_time = 0.01

        #typed commands
        self.commands = commands.Commands(self)
        self.command_event = self.commands.command_event

        #handles input for typed commands
        self.keys = keys.Keys()
        #flag to decide if command is getting entered
        self.inp = False

        #thread for updating everything visually
        self.info = threading.Thread(target=self.__info_print_loop, daemon=True)
        self.info.start()

        #flag to decide if we kill the ui
        self.die = False

        
    @property
    def rightwin(self):
        return self.leftwin.highlighted()


    def getkey(self):
        out = self.stdscr.getch()
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
            [config.COMMAND, self.prepare_command],
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


    def down(self, arg=None):
        """
        same as up, but down (?)
        """
        self.curwin().down()


    def prepare_command(self, arg=None):
        """
        prepare input loop to handle command input
        when config.COMMAND key is pressed
        """
        #command_event.wait() is called from the input thread
        #in sqlmp, this prevents a race condition where getkey
        #gets called before the queue can execute prepare_command
        self.textwin.print_blank(0)
        self.textwin.win.addch(0, 0, ':')
        curses.curs_set(2)

        self.inp = True
        self.command_event.set()


    def handle_input(self, key):
        if key in self.keys:
            if self.keys[key]():
                return self.keys.get_string()
        else:
            self.keys.add(key)

        self.__print_typing()

    def __print_typing(self):
        tmp = self.keys.get_string()
        self.textwin.print_blank(x=1, y=0)
        self.textwin.win.addnstr(0, 1, wchar.set_width(tmp, self.textwin.w - 1), self.textwin.w - 1)
        wid, _ = wchar.wcswidth(tmp[:self.keys.index])
        if wid + 1 < self.textwin.w:
            self.textwin.win.move(0, wid + 1)


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
                self.jump_to_ind(ind, len(self.cur_pl.data), self.rightwin)
                self.switch_view_right()
        else:
            for i, menu_pl in enumerate(self.leftwin.data):
                if menu_pl.data is self.cur_pl:
                    ind = i
                    break

            self.jump_to_ind(ind, len(self.leftwin.data), self.leftwin)


    def jump_down(self, arg=None):
        self.curwin().jump_down(self.curwin().h // 2)


    def jump_up(self, arg=None):
        self.curwin().jump_up(self.curwin().h // 2)

    def mute(self, arg=None):
        self.player.toggle_mute()


    def resize(self, test=None):
        """
        handle resize event
        """
        hh, ww, cc = config.set_size(self.stdscr)

        xx = [0, ww, 0, 0]
        yy = [0, 0, hh, hh + song_info_bar_height]
        wl = [ww, cc - ww, cc, cc]
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
        self.botwin.refresh()
        self.textwin.refresh()
            

    def __enqueue(self):
        """
        add a new song onto the player queue
        """
        self.player.append(next(self.cur_pl))


    def jump_to_ind(self, ind, data_len, window):
        offset = ind - int(window.h / 2)
        if offset < 0:
            #for the case that the found index is near the top
            offset = 0
        elif offset >= data_len - window.h:
            #for the case that the found index is near the bottom
            offset = data_len - window.h

        window.cursor = ind - offset
        window.offset = offset


    def __print_cur_playing(self):
        """
        print currently playing song/playlist in bottom window with highlight
        """
        song = self.cur_song.info()

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

        #TODO
        #maybe make this into one line
        self.botwin.print_line(info_str, y=1)
        self.botwin.print_right_justified(' ' + self.rightwin.data.playmode + ' ', y=1)

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
            self.draw()
            
            curses.doupdate()
            diff = time.time() - start

            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)

            self.commands.err.check()
