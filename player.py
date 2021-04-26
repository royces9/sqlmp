import audioop
import enum
import os
import queue
import sys
import threading

import ffmpeg
import pyaudio

import song

import debug

class Play_state(enum.Enum):
    not_playing = enum.auto()
    playing = enum.auto()
    paused = enum.auto()
    new = enum.auto()
    end = enum.auto()

    def __format__(self, form):
        return self.name
    
class Event(enum.Enum):
    start = enum.auto()
    end_normal = enum.auto()
    end_early = enum.auto()


class Player:
    def __init__(self, vol, step):
        self.pyaudio_init()
        self.vol = vol
        self.vol_step = step
        self.mute = False

        #the length of time (s) each chunk of playback is
        #the play call blocks during this time, so the
        #thread will completely stop
        self.play_len = 0.2

        #size of chunks in bytes to playback
        self.step = 0

        #seconds to skip when seeking
        self.seek_delta = 5
        #number of chunks to skip when seeking
        #calculated and set for each song
        self.seek_delta_c = 0

        #music info
        self.rate = 0
        self.channels = 0
        self.width = 2

        #currently playing song
        self.cur_song = song.blank_song
        
        #current count of the
        #chunk that is currently
        #playing
        self.iterator = 0

        self.playq = queue.Queue(0)
        self.curq = queue.Queue(0)
        self.pauseq = queue.Queue(0)

        self.state = Play_state.not_playing
        self.thread = threading.Thread(target=self.__play_loop, daemon=True)
        self.thread.start()


    def __play_loop(self):
        #always loop unless we quit
        while self.state != Play_state.end:
            #this call blocks until something is pushed onto the queue
            self.cur_song = self.playq.get(block=True, timeout=None)

            #change state to playing
            self.state = Play_state.playing

            #start onto play queue to signal that playback is starting
            self.curq.put_nowait(Event.start)

            #grab path
            fp = self.cur_song['path']

            #convert input file to pcm data
            wav, _ = (ffmpeg
                      .input(fp)
                      .output('-', format='s16le', acodec='pcm_s16le')
                      .overwrite_output()
                      .run(capture_stdout=True, capture_stderr=True))

            #grab stream data for the pyaudio stream
            self.rate = self.cur_song['samplerate']
            self.channels = self.cur_song['channels']
            self.width = 2

            #open a pyaudio stream
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(self.width),
                channels=self.channels,
                rate=self.rate,
                output=True,
            )

            #bytes = len * rate * width * channels
            self.step = int(self.play_len * self.rate * self.width * self.channels)
            self.seek_delta_c = self.seek_delta * self.rate *\
                self.width * self.channels // self.step
            self.iterator = 0

            wav_chunks = [wav[i:i+self.step] for i in range(0, len(wav), self.step)]

            end_code = Event.end_early
            while self.iterator < len(wav_chunks):
                if self.state in {Play_state.new, Play_state.end}:
                    break

                vol = self.vol / 500 if not self.mute else 0
                adjust = audioop.mul(wav_chunks[self.iterator], self.width, vol)

                stream.write(adjust)
                self.iterator += 1

                while self.is_paused():
                    self.pauseq.get(block=True, timeout=None)
            else:
                end_code = Event.end_normal

            #resource clean up
            stream.stop_stream()
            stream.close()

            #push to queue to signal that playback of a song has ended
            self.curq.put_nowait(end_code)

            #set stream to not playing after playback ends
            self.state = Play_state.not_playing


    def is_paused(self, *args):
        return self.state == Play_state.paused


    def is_playing(self, *args):
        return self.state == Play_state.playing


    def is_not_playing(self, *args):
        return self.state == Play_state.not_playing


    def vol_up(self, *args):
        self.vol += self.vol_step
        if self.vol > 100:
            self.vol = 100


    def vol_down(self, *args):
        self.vol -= self.vol_step
        if self.vol < 0:
            self.vol = 0


    def append(self, arg):
        self.playq.put_nowait(arg)


    def play(self, arg):
        #reset playback before starting new song
        with self.playq.mutex:
            self.playq.queue.clear()
            self.pauseq.put_nowait(())

        self.append(arg)

        #set state to new so the loop
        #in __play_loop will break
        self.state = Play_state.new


    def play_pause(self, *args):
        if self.state == Play_state.playing:
            self.pause()
        elif self.state == Play_state.paused:
            self.unpause()


    def pause(self, *args):
        self.state = Play_state.paused


    def unpause(self, *args):
        self.state = Play_state.playing
        self.pauseq.put_nowait(())


    def seek_forward(self, *args):
        self.iterator += self.seek_delta_c


    def seek_backward(self, *args):
        self.iterator -= self.seek_delta_c
        if self.iterator < 0:
            self.iterator = 0


    def toggle_mute(self, *args):
        self.mute = not self.mute


    def cur_time(self, *args):
        d = self.width * self.channels * self.rate
        n = self.step * self.iterator
        return n / d if d != 0 else 0


    def curplay(self):
        return self.curq.get_nowait()


    def curempty(self):
        return self.curq.empty()


    def pyaudio_init(self):
        og_err = sys.stderr.fileno()
        cp_err = os.dup(og_err)

        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), og_err)

        self.pyaudio = pyaudio.PyAudio()

        os.dup2(cp_err, og_err)
