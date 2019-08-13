from pydub import AudioSegment

import atexit
import ffmpeg
import json
import subprocess as sp
import threading
import os
import pyaudio
import queue

import keys

def debug_file(line):
    with open("test.txt", "w+") as fp:
        fp.write(line);

class Player:
    def __init__(self):
        self.pyaudio = pyaudio.PyAudio();
        self.vol = keys.DEFAULT_VOLUME;
        self.eventq = queue.Queue(0);
        self.stream = self.pyaudio.open(
            format=self.pyaudio.get_format_from_width(2, unsigned=False),
            channels=2,
            rate=44100,
            output=True)

        self.state = 0;
        self.playq = queue.Queue(0);
        self.thread = threading.Thread(target=self.__play_loop)
        self.thread.start();        

    def checkq(self):
        pass

    def ex(self, args):
        pass
    def set_prop(self, args):
        pass

    def get_prop(self, arg):
        pass

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


    def play(self, *args):
        fp = str(args[0][2])
        self.state = 1;
        self.eventq.put_nowait('q');
        self.playq.put_nowait(fp);


    def __play_loop(self):
        self.eventq.get(block=True, timeout=None);
        while True:
            fn = self.playq.get(block=True, timeout=None);
            md, _ = (ffmpeg
                     .input(fn)
                     .output('-', format='s16le', acodec='pcm_s16le')
                     .overwrite_output()
                     .run(capture_stdout=True, capture_stderr=True)
            )

            frame = 4096;
            chunk = len(md) // frame + 1;
            data = [None] * chunk;
            i = 0;
            j = 0;
            
            while j < chunk:
                data[j] = md[i:i + frame];
                i += frame;
                j += 1;
            ev = 'a';
            for dd in data:
                if not self.eventq.empty():
                    while True:
                        ev = self.eventq.get(block=True, timeout=None);
                        self.eventq.task_done();
                        if ev == 'pp':
                            if self.state == 0:
                                break;
                        elif ev == 'q':
                            break;
                elif ev == 'q':
                    break;
                self.stream.write(dd);
        
        
    def play_pause(self, *args):
        self.eventq.put_nowait('pp');
        if self.state == 0:
            self.state = 1;
        else:
            self.state = 0;
        
    def pause(self, *args):
        self.eventq.put_nowait('p');

    def unpause(self, *args):
        pass

    def seek_forward(self, *args):
        pass
    
    def __del__(self):
        self.eventq.put_nowait('q');
        self.pyaudio.terminate();

def init_music():
    player = Player();
    atexit.register(player.__del__);
    return player;
