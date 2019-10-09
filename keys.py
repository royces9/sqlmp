import curses
import os

#database path
DBPATH='lib.db'
LIBPATH= os.getenv('HOME') + '/Music/'


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


#volume
DEFAULT_VOLUME=10
VOL_STEP=1


#display
def song_format(ll):
    title = ll['title']
    album = ll['album']
    artist = ll['artist']
    bitrate = str(int(ll['bitrate']/1000))

    minutes = str(int(ll['length'] // 60))
    seconds = int(round(ll['length'] % 60))
    seconds = str(seconds) if seconds > 9 else '0' + str(seconds)
    
    length = ':'.join([minutes, seconds])
    
    return (
        (artist, 1/4),
        (title, 3/8),
        (album, 1/4),
        (bitrate, 1/16),
        (length, 1/16),
    )

SONG_DISP=song_format


#colours
#list with three elements
#0: curses colour, use None if you want a different colour scheme
#1: fg colour
#1: bg colour
FOCUSED=[None, 219, 9]
CURSOR=[curses.A_STANDOUT, 0, 0]
HIGHLIGHT_COLOUR=[curses.A_REVERSE, 0, 0]
NORMAL=[curses.A_NORMAL, 0, 0]


def set_size(stdscr):
    #height of bottom window
    bottom = 4

    #cur term size
    lines, cols  = stdscr.getmaxyx()

    #height of the left and right windows
    height = lines - bottom

    #width of the left window
    width = cols // 6

    return height, width, bottom, lines, cols
