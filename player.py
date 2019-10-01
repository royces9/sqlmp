import enum
import os
import queue
import sys
import threading

import ffmpeg
import pyaudio
import audioop

import keys

class Play_state(enum.Enum):
    init = 0
    not_playing = 1
    playing = 2
    paused = 3
    new = 4
    end = 5

    
class Player:
    def __init__(self):
        self.pyaudio_init()
        self.vol = keys.DEFAULT_VOLUME

        #the length of time (s) each chunk of playback is
        #the play call blocks during this time, so the
        #thread will completely stop
        self.play_len = 0.1

        #size of chunks in bytes to playback
        self.step = 0

        #seconds to skip when seeking
        self.vol_inc = 5
        #number of chunks to skip when seeking
        self.vol_inc_c = 0

        #music info
        self.rate = 0
        self.channels = 0
        self.width = 2

        self.iterator = 0
        self.time = 0

        self.state = Play_state.init
        self.playq = queue.Queue(0)
        self.curq = queue.Queue(0)
        self.pauseq = queue.Queue(0)

        self.thread = threading.Thread(target=self.__play_loop, daemon=True)
        self.thread.start()


    def curplay(self, arg=None):
        return self.curq.get_nowait()
        #return self.curq.get(block=True, timeout = None)


    def vol_up(self, arg=None):
            newvol = self.vol + keys.VOL_STEP
            if newvol > 100:
                newvol = 100
            self.vol = newvol

    
    def vol_down(self, arg=None):
            newvol = self.vol - keys.VOL_STEP
            if newvol < 0:
                newvol = 0
            self.vol = newvol


    def append(self, arg):
        self.playq.put_nowait(arg)


    def play(self, arg):
        self.append(arg)
        self.state = Play_state.new

        
    def __play_loop(self):
        #always loop unless we quit
        while self.state != Play_state.end:
            #this call blocks until something is pushed onto the queue
            fn = self.playq.get(block=True, timeout=None)

            #change state to playing
            self.state = Play_state.playing
            
            #push song onto play queue to signal that playback is starting
            self.curq.put_nowait(fn)

            #grab path
            fp = fn['path']
            
            #convert input file to pcm data
            wav, _ = (ffmpeg
                     .input(fp)
                     .output('-', format='s16le', acodec='pcm_s16le')
                     .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
            )
            
            #grab stream data for the pyaudio stream
            prob = ffmpeg.probe(fp)
            self.rate = int(prob['streams'][0]['sample_rate'])
            self.channels = int(prob['streams'][0]['channels'])
            self.width = 2

            self.set_time()
            #open a pyaudio stream
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(self.width),
                channels=self.channels,
                rate=self.rate,
                output=True,
            )
            #bytes = len * rate * width * channels
            self.step = int(self.play_len * self.rate * self.width * self.channels)
            self.vol_inc_c = self.vol_inc * self.rate * self.width * self.channels // self.step

            wav_chunks = [wav[i:i+self.step] for i in range(0, len(wav), self.step)]
            self.iterator = 0
            while self.iterator < len(wav_chunks):
                if self.state == Play_state.paused:
                    while self.state == Play_state.paused:
                        self.pauseq.get(block=True, timeout=None)
                        
                elif self.state in {Play_state.new, Play_state.end}:
                    break
                
                adjust = audioop.mul(wav_chunks[self.iterator], self.width, self.vol/100)
                stream.write(adjust)
                self.iterator += 1
                self.set_time()

            #resource clean up
            stream.stop_stream()
            stream.close()

            #push None to queue to signal that playback of a song has ended
            self.curq.put_nowait(None)

            #set stream to not playing after playback ends
            self.state = Play_state.not_playing

        
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
        self.iterator += self.vol_inc_c


    def seek_backward(self, *args):
        self.iterator -= self.vol_inc_c
        if self.iterator < 0:
            self.iterator = 0


    def set_time(self):
        self.time = self.step * self.iterator / (self.width * self.channels * self.rate)


    def cur_time(self, *args):
        return self.time

    def pyaudio_init(self):
        og_err = sys.stderr.fileno()
        cp_err = os.dup(og_err)

        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), og_err)
        
        self.pyaudio = pyaudio.PyAudio()

        os.dup2(cp_err, og_err)
