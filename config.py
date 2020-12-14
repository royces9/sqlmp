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
#list with three elements
#0: curses colour, use None if you want a different colour scheme
#1: fg colour
#1: bg colour
FOCUSED = [None, 219, 9]
CURSOR = [curses.A_STANDOUT, 0, 0]
HIGHLIGHT_COLOUR = [curses.A_REVERSE, 0, 0]
NORMAL = [curses.A_NORMAL, 0, 0]
PLAYING_HIGHLIGHT = [None, 161, -1]


def set_size(stdscr):
    #cur term size
    lines, cols = stdscr.getmaxyx()

    #height of the left and right windows
    #hardcoded value of the bottom bar height
    height = lines - 4

    #width of the left window
    width = cols // 6

    return height, width, cols
