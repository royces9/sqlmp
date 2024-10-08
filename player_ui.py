import curses
import enum
import itertools
import threading
import time

import commands
import inp
import menu
import player
import playlist
import random
import threadwin
import window
import wchar

import config
import debug

class Win(enum.IntEnum):
    left=0
    right=1

song_info_bar_height = 2
command_bar_height = 2
class Player_ui:
    def __init__(self, stdscr, palette, db):
        #currently highlighted window
        #left window is 0, right is 1
        self.cur = Win.left

        #pointer to the ncurses stdscr
        self.stdscr = stdscr
        #y, x = stdscr.getmaxyx()
        #self.stdscr = curses.newwin(y, x)
        self.stdscr.keypad(1)

        #music database
        self.db = db

        #all the colours and stuff
        self.palette = palette

        #flag to decide if we kill the ui
        self.die = False

        #currently playing playlist
        self.cur_pl = None

        #amount of time in between drawing in seconds
        #not really a frame time but w/e
        self.frame_time = 0.01667

        #actual music player
        self.player = player.Player(config.DEFAULT_VOLUME, config.VOL_STEP)
        
        #the windows of the player
        self.leftwin, self.botwin, self.textwin = self.__init_windows()

        #handles typed commands
        self.commands = commands.Commands(self)

        #input queue and thread
        self.inp = inp.Input(self)

        #thread for updating everything visually
        threading.Thread(target=self.__info_print_loop, daemon=True).start()


    @property
    def rightwin(self):
        return self.leftwin.highlighted().data


    def cur_win(self):
        return [self.leftwin, self.rightwin][self.cur]


    def set_die(self, *args):
        self.die = True


    def __init_windows(self):
        hh, ww, cc = config.set_size(self.stdscr)

        win = threadwin.Threadwin(hh, cc - ww, 0, ww)

        data = [playlist.Playlist(pl, self.db, win=win,
                                  form=config.SONG_DISP,
                                  palette=self.palette[0], ui=self,
                                  )
                for pl in self.db.list_pl()]

        leftwin = menu.Menu(0, 0, ww, hh, data=data,
                            palette=self.palette[1],
                            )

        botwin = window.Window(0, hh, cc, song_info_bar_height)

        textwin = window.Window(0, hh + song_info_bar_height, cc, command_bar_height)

        return leftwin, botwin, textwin


    """
    Functions called from key press/events
    """
    def delete(self, *args):
        """
        delete songs from playlists
        """
        if self.cur == Win.left:
            self.commands.delpl([])
        else:
            cur_song = self.rightwin.highlighted()

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
        cw = self.cur_win()
        cw.highlight()
        if self.cur == Win.right:
            cw.down()


    def jump_cur_play(self, *args):
        if self.player.is_not_playing():
            return

        #if cur_pl isn't the currently selected pl
        if self.cur_pl is not self.rightwin:
            for i, menu_pl in enumerate(self.leftwin.data):
                if menu_pl.data is self.cur_pl:
                    ind = i
                    self.jump_to_ind(ind, len(self.leftwin.data), self.leftwin)
                    self.switch_view_left()
                    break

        #check that the song is in cur_pl
        elif self.player.cur_song['path'] in self.cur_pl:
            for i, d in enumerate(self.rightwin.data):
                if d.data is self.player.cur_song:
                    ind = i
                    self.jump_to_ind(ind, len(self.cur_pl.data), self.rightwin)
                    self.switch_view_right()
                    break

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
        #TODO: this doesn't work exactly right idk why
        #it probably has something to do with the draw function
        #being in a separate thread
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
            win.win.clear()
            win.win.resize(h, w)
            win.win.mvwin(y, x)
            win.win.touchwin()

        for win in wins[0:2]:
            if win.cursor >= win.h:
                prev = win.cursor + win.offset
                win.cursor = win.h - 1
                win.offset = prev - win.cursor

        self.draw()

    def select(self, *args):
        """
        play a song in a playlist
        """
        self.cur_pl = self.rightwin
        if self.cur == Win.right:
            self.cur_pl.cur_song = self.rightwin.highlighted()
        else:
            self.cur_pl.cur_song = random.choice(self.cur_pl.data)

        self.cur_pl.set_order(self.cur_pl.playmode)
        self.player.play(self.cur_pl.cur_song.data)

        self.cur_pl.remake_gen()


    def switch_view(self, *args):
        """
        switch focus from left to right, and vice versa
        """
        if not self.rightwin.data:
            return

        if self.cur == Win.right:
            self.switch_view_left()
        else:
            self.switch_view_right()
        self.leftwin.win.touchwin()

        
    def switch_view_right(self):
        self.cur = Win.right
        self.rightwin.palette = self.palette[1]
        self.leftwin.palette = self.palette[0]


    def switch_view_left(self):
        self.cur = Win.left
        self.leftwin.palette = self.palette[1]
        self.rightwin.palette = self.palette[0]


    def transfer(self, *args):
        """
        move songs around playlists
        """
        if self.cur != Win.right:
            return
        
        cur_pl = self.rightwin.data
        cur_song = self.rightwin.highlighted()
        if not cur_song:
            return

        for pl in itertools.filterfalse(lambda a: not a.highlighted, self.leftwin):
            if pl.data is not cur_pl:
                pl.data.insert(cur_song.data['path'])
        
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

        curses.doupdate()            

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
        song = ' - '.join(str(self.player.cur_song[key])
                          for key in config.SONG_INFO
                          if self.player.cur_song[key])

        if self.player.is_paused():
            song += ' *PAUSED*'

        self.botwin.print_line(song)

        if self.cur_pl:
            self.botwin.print_right_justified(' ' + self.cur_pl.name + ' ')
        
        self.botwin.win.chgat(0, 0, self.botwin.w, self.palette[1][1])

        
    def mainloop(self):
        while not self.die:
            #check input queue for any new things to do
            self.inp.exe()


    def __info_print(self):
        time_str = config.song_length(self.player.cur_time())

        total_time_str = config.song_length(self.player.cur_song['length'])
        
        info_str = ' '.join([time_str, '/', total_time_str, '| Vol:', str(self.player.vol)])
        if self.player.mute:
            info_str += ' [M]'

        self.botwin.print_line(info_str, y=1)
        self.botwin.print_right_justified(' ' + self.rightwin.playmode_str + ' ', y=1)
        
        if not self.player.curempty():
            player_event = self.player.curplay()
            #playback ended normally, increment playcount
            if player_event == player.Event.end_normal.value:
                self.inp.put_nowait((self.db.increment_playcount, self.player.cur_song,))

                #queue another song
                self.inp.put_nowait((self.__enqueue,))
            elif player_event < 0:
                self.inp.put_nowait((self.__enqueue,))
                
        self.__print_cur_playing()
        

    def __info_print_loop(self):
        while not self.die:
            start = time.time()

            self.__info_print()
            self.draw()
            
            diff = time.time() - start

            if diff < self.frame_time:
                time.sleep(self.frame_time - diff)

            self.commands.err.check()

    def __refresh_all(self):
        self.stdscr.refresh()

        curses.doupdate()
