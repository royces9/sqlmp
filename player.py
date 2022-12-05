import enum
import os
import sys

import song

import debug

import ctypes
backend=ctypes.CDLL(os.path.dirname(__file__) + '/backend.so')
backend.player_get_volume.restype = ctypes.c_float


class Event(enum.Enum):
    error=-1
    start=0
    end_normal=1
    end_early=2


class Player:
    def __init__(self, vol, step):
        self.backend_init(vol)
        self.vol_step = step/100

        self.seek_delta = 5

        self.path = None

        #currently playing song
        self.cur_song = song.blank_song


    def state(self):
        st = backend.player_get_status()
        play_state = ['playing',
                      'not playing',
                      'paused',
                      'quit',
                      'new',
                      'end',
                      ]
        return play_state[st]


    def is_paused(self, *args):
        return backend.player_is_paused()

    def is_playing(self, *args):
        return backend.player_is_playing()

    def is_not_playing(self, *args):
        return backend.player_is_not_playing()

    @property
    def vol(self):
        return int(backend.player_get_volume() * 100)

    
    def vol_up(self, *args):
        backend.player_increment_volume(ctypes.c_float(self.vol_step))


    def vol_down(self, *args):
        backend.player_increment_volume(ctypes.c_float(-self.vol_step))


    def append(self, arg):
        self.cur_song = arg
        self.path = self.cur_song['path'].encode()
        rate = self.cur_song['samplerate']
        channels = self.cur_song['channels']
        
        backend.player_put_playq(ctypes.c_char_p(self.path),
                                 ctypes.c_double(rate),
                                 ctypes.c_int(channels),
                                 )


    def play(self, arg):
        #reset playback before starting new song
        #backend.player_unpause()

        backend.player_set_status(4)
        self.append(arg)


    def play_pause(self, *args):
        backend.player_play_pause()

    def pause(self, *args):
        backend.player_pause()


    def unpause(self, *args):
        backend.player_unpause()


    def seek_forward(self, *args):
        backend.player_seek_forward(ctypes.c_int(self.seek_delta))


    def seek_backward(self, *args):
        backend.player_seek_backward(ctypes.c_int(self.seek_delta))


    @property
    def mute(self):
        return backend.player_is_muted()

    def toggle_mute(self, *args):
        backend.player_toggle_mute()


    def cur_time(self, *args):
        return backend.player_get_time()


    def curplay(self):
        return backend.player_get_curq()


    def curempty(self):
        return backend.player_is_curq_empty()


    def backend_init(self, *args):
        og_err = sys.stderr.fileno()
        cp_err = os.dup(og_err)

        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), og_err)

        backend.player_init(ctypes.c_float(args[0]/100))
