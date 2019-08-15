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
PIPE='~/.config/sqlmppipe'

SONG_DISP=lambda ll: song_format(ll)


def song_format(ll):
    title = ll['title']
    album = ll['album']
    artist = ll['artist']

    title_len = len(title)
    album_len = len(album)
    artist_len = len(artist)

    names = [title, artist, album]
    max_name = [40, 20, 30]
    names_len = [len(name) for name in names]
    
    out = [None] * len(names)
    i = 0

    for name, _max, _len in zip(names, max_name, names_len):
        if _len > _max:
            out[i] = name[0:_max]
        else:
            out[i] = name + (_max - _len) * ' '

        i += 1
    
    return ''.join(out)
