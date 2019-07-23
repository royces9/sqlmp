from pydub import AudioSegment

import keys
import subprocess as sp
import json
global mpv_proc

import atexit
tmppipe = '/home/royce/Documents/program/test/sql_lib/test_pipe';

def init_music():
    global mpv_proc
    mpv_proc = sp.Popen(['mpv', '--idle', '--no-input-default-bindings', '--no-terminal', '--no-video', '--input-ipc-server='+tmppipe], stdin=sp.PIPE, stdout=sp.DEVNULL, stderr = sp.DEVNULL);

    atexit.register(cleanmpv)();

    return;

def play(data):
    exec_mpv(['loadfile', data[2]]);
    return;

def play_pause(disp, curs):
    a=exec_mpv(['get_property', 'pause']);
    out = json.loads(a[0]);

    if out['data']:
        flag = 'false';
    else:
        flag = 'true';

    exec_mpv(["set_property", 'pause', flag]);
    return;

def vol_up(disp, curs):
    global mpv_proc
    return;
        
def vol_down(disp, curs):
    global mpv_proc
    return;

def exec_mpv(args):
    joined = '","'.join(args);
    cmd = '{ "command": ["' + joined + '"] }';

    inp = 'echo "' + cmd + '" | socat - ' + tmppipe;

    p = sp.Popen(inp, shell=True, stdout = sp.PIPE);
    return p.communicate();
    

def cleanmpv():
    global mpv_proc;
    mpv_proc.kill();
