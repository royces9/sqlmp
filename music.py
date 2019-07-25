from pydub import AudioSegment

import atexit
import json
import subprocess as sp
import threading
import mpv
import os

import keys

global mpv_proc

class my_mpv:
    def __init__(self):
        self.mpv = mpv.MPV(__no_video=True);
        self.vol = keys.DEFAULT_VOLUME;
        @self.mpv.property_observer()
        self.set_prop(['"volume"', str(self.vol)]);

        self.thread = threading.Thread(target = self.checkq);

    def checkq(self):
        p=sp.Popen(['socat ' + self.pipe + ' -'], shell=True, stdout=sp.PIPE);
        ap = p.communicate();
        if not ap:
            event = json.loads(ap[0]);
            if event['event'] == 'end-file':
                sys.exit();
            

    def ex(self, args):
        joined = ','.join(args);
        cmd = '{"command":[' + joined + ']}';
        inp = 'echo \'' + cmd + '\' | socat - ' + self.pipe;

        p = sp.Popen(inp, shell=True, stdout = sp.PIPE);
        return p.communicate();

    def set_prop(self, args):
            return self.ex(['"set_property"'] + args);

    def get_prop(self, arg):
            return self.ex(['"get_property"'] + [arg]);

    def vol_up(self, *args):
            newvol = self.vol + keys.VOL_STEP;
            if newvol > 100:
                newvol = 100;
            self.vol = newvol;

            self.set_prop(['"volume"', str(newvol)]);
    
    def vol_down(self, *args):
            newvol = self.vol - keys.VOL_STEP;
            if newvol < 0:
                newvol = 0;
            self.vol = newvol;

            self.set_prop(['"volume"', str(newvol)]);

    def play(self, *args):
        self.ex(['"loadfile"', '"' + args[0][2] + '"']);
        self.set_prop(['"pause"', 'false']);
        self.thread.start();
        
    def play_pause(self, *args):
        a = self.get_prop('"pause"');
        out = json.loads(a[0]);
        flag = 'false' if out['data'] else 'true';
        self.set_prop(['"pause"', flag]);
        
    def pause(self, *args):
        self.set_prop(['"pause"', 'true']);

    def unpause(self, *args):
        self.set_prop(['"pause"', 'false']);

    def seek_forward(self, *args):
        pass;
    
    def __del__(self):
        self.p.kill()

def init_music():
    mpv_proc = my_mpv(__no_video=True);
    atexit.register(mpv_proc.__del__);
    return mpv_proc;
