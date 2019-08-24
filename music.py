import enum
import sys
import threading
import os
import queue

import ffmpeg
import pyaudio
from pydub import AudioSegment
from pydub.playback import make_chunks

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
        self.vol = keys.DEFAULT_VOLUME;

        #size of chunks in ms to playback
        self.step = 250

        self.state = Play_state.init
        self.playq = queue.Queue(0)
        self.curq = queue.Queue(0)
        self.cur = None

        self.thread = threading.Thread(target=self.__play_loop)
        self.thread.daemon = True;
        self.thread.start();        


    def curplay(self):
        return self.curq.get(block=True, timeout = None)


    def vol_up(self, *args):
            newvol = self.vol + keys.VOL_STEP;
            if newvol > 100:
                newvol = 100;
            self.vol = newvol;

    
    def vol_down(self, *args):
            newvol = self.vol - keys.VOL_STEP;
            if newvol < 0:
                newvol = 0;
            self.vol = newvol;


    def append(self, *args):
        self.playq.put_nowait(args[0])


    def play(self, *args):
        self.append(*args);
        self.state = Play_state.new;

        
    def __play_loop(self):
        #always loop unless we quit
        while self.state != Play_state.end:
            #this call blocks until something is pushed onto the queue
            fn = self.playq.get(block=True, timeout=None);

            #change state to playing
            self.state = Play_state.playing
            
            #push onto play queue
            self.curq.put_nowait(fn);

            #grab path
            fp = fn['path']
            
            #convert input file to wav and put it into wav variable
            wav, _ = (ffmpeg
                     .input(fp)
                     .output('-', format='wav', acodec='pcm_s16le')
                     .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
            )

            #convert wav to pydub AudioSegment
            #we do this to allow for easy volume changes
            md = AudioSegment(wav)

            #open a pyaudio stream
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(md.sample_width),
                channels=md.channels,
                rate=md.frame_rate,
                output=True,
            )

            #iterate through the AudioSegment
            for dd in make_chunks(md, self.step):
                if self.state == Play_state.paused:
                    while self.state == Play_state.paused:
                        pass
                elif self.state in {Play_state.new, Play_state.end}:
                    break;
                
                adjust = dd - (100 - self.vol);
                stream.write(adjust._data);

            #resource clean up
            stream.stop_stream()
            stream.close()

            #set stream to not playing after playback ends
            self.state = Play_state.not_playing
                
        
    def play_pause(self, *args):
        if self.state == Play_state.playing:
            self.state = Play_state.paused;
        elif self.state == Play_state.paused:
            self.state = Play_state.playing;

            
    def pause(self, *args):
        self.state = Play_state.paused


    def unpause(self, *args):
        self.state = Play_state.playing


    def seek_forward(self, *args):
        pass


    def seek_backward(self, *args):
        pass


    def pyaudio_init(self):
        og_err = sys.stderr.fileno()
        cp_err = os.dup(og_err)

        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), og_err)
        
        self.pyaudio = pyaudio.PyAudio();

        os.dup2(cp_err, og_err)


def init_music():
    return Player()
