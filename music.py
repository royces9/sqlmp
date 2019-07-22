from pydub import AudioSegment

import keys
import subprocess as sp

global mpv_proc

def init_music():
    return;

def play(data):
    global mpv_proc
    mpv_proc = sp.Popen(['mpv', '--idle', '--no-input-default-bindings', '--no-terminal', '--no-video', data[2]], stdin=sp.PIPE, stdout=sp.DEVNULL, stderr = sp.DEVNULL);
    return;

def play_pause(disp, curs):
    mpv_proc.stdin.write(bytes([112]));
    return;

def vol_up(disp, curs):
    global mpv_proc
    return;
        
def vol_down(disp, curs):
    global mpv_proc
    return;
                                                                                                                    
    

