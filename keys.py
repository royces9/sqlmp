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


DEFAULT_VOLUME=90
VOL_STEP=1

SONG_DISP=lambda ll: song_format(ll)


def song_format(ll):
    title = ll['title']
    album = ll['album']
    artist = ll['artist']

    names = [title, artist, album]
    max_name = [40, 20, 30]
    
    out = [None] * len(names)
    i = 0
    import string
    for name, _max in zip(names, max_name):
        out[i] = name.ljust(_max)
        i += 1
    
    return ''.join(out)
