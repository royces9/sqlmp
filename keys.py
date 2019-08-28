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

#database path
LIBPATH='lib.db'

#volume
DEFAULT_VOLUME=80
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

    minutes = str(int(ll['length'] // 60))
    seconds = str(int(round(ll['length'] % 60)))
    if len(seconds) < 2:
        seconds = '0' + seconds
    
    length = ':'.join([minutes, seconds])
    
    return (
        (title, 3/8),
        (artist, 1/4),
        (album, 1/4),
        (bitrate, 1/16),
        (length, 1/16),
    ), 1


def set_size(stdscr):
    #heigh of bottom window
    bottom = 5

    #cur term size
    lines, cols  = stdscr.getmaxyx()

    #height of the left and right windows
    height = lines - bottom + 1

    #width of the left window
    width = cols // 6

    return height, width, bottom, lines, cols

    

def debug_file(err):
    with open('test.txt', 'a+') as fp:
        for e in err:
            print(str(e), file=fp)
                    
