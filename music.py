from pydub import AudioSegment as AS
import pydub.playback as pb

import keys


def init_music():
    
    pgm.music.set_volume(keys.DEFAULT_VOLUME / 100);

def play(data):
    if pgm.music.get_busy():
        pgm.music.stop();
    pgm.music.load(data[2]);
    pgm.music.play();

def play_pause(disp, curs):
    if pgm.music.get_busy():
        pgm.music.pause();
    else:
        pgm.music.unpause();

def vol_up(disp, curs):
    cur = pgm.music.get_volume();
    new = cur + keys.VOL_STEP / 100;
    if new > 1:
        new = 1;
    pgm.music.set_volume(new);
        
def vol_down(disp, curs):
    cur = pgm.music.get_volume();
    new = cur - keys.VOL_STEP / 100;
    if new < 0:
        new = 0;
    pgm.music.set_volume(new);

                                                                                                                    
    

