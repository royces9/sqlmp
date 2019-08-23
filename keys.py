import curses

#key bindings
UP={'KEY_UP', 'l'}
DOWN={'KEY_DOWN', 'k'}
LEFT={'KEY_LEFT', 'j'}
RIGHT={'KEY_RIGHT', ';'}
VOLUP={']'}
VOLDOWN={'['}
PLAYPAUSE={'c'}
QUIT={'q'}
SWITCH={'\t'}
COMMAND={':'}
SELECT={'\n'}
LIBPATH='lib.db'

#volume
DEFAULT_VOLUME=90
VOL_STEP=1

#display
SONG_DISP=lambda ll: song_format(ll)

FOCUSED_BG=9
FOCUSED_FG=219

HIGHLIGHTED_BG=0
HIGHLIGHTED_FG=0

NORMAL_BG=0
NORMAL_FG=0

FOCUSED=None
HIGHLIGHTED=curses.A_STANDOUT
NORMAL=curses.A_NORMAL


def song_format(ll):
    title = ll['title']
    album = ll['album']
    artist = ll['artist']
    bitrate = str(int(ll['bitrate']/1000))
    
    return (
        (title, 3/8),
        (artist, 1/4),
        (album, 1/4),
        (bitrate, 1/8)
    ), 1
