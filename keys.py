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
HIGHLIGHT={' '}
TRANSFER={'y'}
DELETE={'D'}

#database path
LIBPATH='lib.db'

#volume
DEFAULT_VOLUME=50
VOL_STEP=1

#display
SONG_DISP=lambda ll: song_format(ll)

#colours
#list with three elements
#0: curses colour, use None if you want a different colour scheme
#1: fg colour
#1: bg colour
FOCUSED=[None, 219, 9]
CURSOR=[curses.A_STANDOUT, 0, 0]
HIGHLIGHT_COLOUR=[curses.A_REVERSE, 0, 0]
NORMAL=[curses.A_NORMAL, 0, 0]


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
        (artist, 1/4),
        (title, 3/8),
        (album, 1/4),
        (bitrate, 1/16),
        (length, 1/16),
    ), 1


def set_size(stdscr):
    #heigh of bottom window
    bottom = 4

    #cur term size
    lines, cols  = stdscr.getmaxyx()

    #height of the left and right windows
    height = lines - bottom

    #width of the left window
    width = cols // 6

    return height, width, bottom, lines, cols

    

def debug_file(err):
    with open('test.txt', 'a+') as fp:
        for e in err:
            print(str(e), file=fp)
                    
