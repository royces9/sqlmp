#move to ~/.config/sqlmp/ to use

import curses
import os

#database path
DBPATH = os.path.expanduser('newlib.db')
LIBPATH = os.path.expanduser('~/Music/')

SOCKET = 'test_sqlmp.sock'

#key bindings
UP = {curses.KEY_UP, 'l'}
DOWN = {curses.KEY_DOWN, 'k'}
LEFT = {curses.KEY_LEFT, 'j'}
RIGHT = {curses.KEY_RIGHT, ';'}
JUMP_UP = {'\f'} #ctrl-L
JUMP_DOWN = {'\v'} #ctrl-K
VOLUP = {']'}
VOLDOWN = {'['}
MUTE = {'m'}
PLAYPAUSE = {'c'}
QUIT = {'q'}
SWITCH = {'\t'} #tab
COMMAND = {':'}
SELECT = {'\n'} #enter
HIGHLIGHT = {' '}
TRANSFER = {'y'}
DELETE = {'D'}
CUR_PLAY = {'i'}

#volume
DEFAULT_VOLUME = 0
VOL_STEP = 1


#display
def song_length(len_s):
    """
    return formatted string for time given a value in seconds
    """
    m, s = divmod(int(len_s), 60)
    s = str(s) if s > 9 else '0' + str(s)
    return ':'.join([str(m), s])


def song_format(ll):
    title = ll['title']
    album = ll['album']
    artist = ll['artist']
    bitrate = str(int(ll['bitrate']/1000))

    length = song_length(ll['length'])

    playcount = str(ll['playcount'])

    return (
        (artist, 1/4, False),
        (title, 5/16, False),
        (album, 1/4, False),
        (bitrate, 1/16, True),
        (length, 1/16, True),
        (playcount, 1/16, True),
    )


#how songs are formatted on the right window
SONG_DISP = song_format


#what info is displayed on the bottom window
#info like bitrate and length might need to be
#tinkered with
SONG_INFO = ['artist', 'title', 'album']


#colours
#list with two elements containing tuples with RGB values
#1: fg colour
#1: bg colour

MAIN_COLOUR=(255, 209, 220)
MAIN_TEXT=(255, 91, 130)

CURSOR = [MAIN_COLOUR, MAIN_TEXT]
FOCUSED = [MAIN_COLOUR, (248, 0, 59)]
HIGHLIGHT_COLOUR = [(0, 0, 0), (131, 131, 131)]
NORMAL = [MAIN_TEXT, MAIN_COLOUR]
PLAYING_HIGHLIGHT = [(232, 158, 255), MAIN_COLOUR]

def set_size(stdscr):
    #cur term size
    lines, cols = stdscr.getmaxyx()

    #height of the left and right windows
    #hardcoded value of the bottom bar height
    height = lines - 4

    #width of the left window
    width = cols // 6

    return height, width, cols
