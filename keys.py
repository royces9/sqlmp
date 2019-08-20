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

DEFAULT_VOLUME=90
VOL_STEP=1

SONG_DISP=lambda ll: song_format(ll)

def song_format(ll):
    title_max = 50
    artist_max = 50
    album_max = 50

    
    title = ll['title']
    album = ll['album']
    artist = ll['artist']
    bitrate = str(int(ll['bitrate']/1000))
    
    return (
        (title, 1/4),
        (artist, 1/4),
        (album, 1/4),
        (bitrate, 1/4)
    ), 1
