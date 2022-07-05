import ffmpeg
import os

import debug

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg', '.opus'}

tags = ['path', 'title', 'artist', 'album', 'length', 'samplerate', 'channels', 'bitrate', 'playcount']


class Song:
    def __init__(self, di):
        self.__dict = di


    def __getitem__(self, key):
        return self.__dict[key]


    def __setitem__(self, key, item):
        self.__dict[key] = item

    def __iter__(self):
        for item in tags:
            yield self.__dict[item]


    def __str__(self):
        return self.__dict['title']


    def dict(self):
        return self.__dict


    @staticmethod
    def grab_tags(path):
        prob = ffmpeg.probe(path)

        tags_out = ['title', 'artist', 'album']
        if 'tags' in prob['format']:
            tmp = {k.lower(): i for k, i in prob['format']['tags'].items()}
            tags = [tmp[t] if t in tmp else '' for t in tags_out]
        elif 'tags' in prob['streams'][0]:
            tmp = {k.lower(): i for k, i in prob['streams'][0]['tags'].items()}
            tags = [tmp[t] if t in tmp else '' for t in tags_out]
        else:
            tags = [''] * len(tags_out)

        attr = (a[1](prob['streams'][0][a[0]])
                for a in [('duration', float), ('sample_rate', int), ('channels', int)])

        return (path,) + tuple(tags, ) + tuple(attr, ) + (int(prob['format']['bit_rate']), ) + (0,)


    @classmethod
    def from_path(cls, path):
        if os.path.splitext(path)[1] not in ext_list:
            return None
    
        if not os.path.exists(path):
            return None

        return cls(Song.new_dict(Song.grab_tags(path)))


    @classmethod
    def from_iter(cls, it):
        return cls(Song.new_dict((it)))


    @staticmethod
    def new_dict(datas):
        return {
            tag: data
            for tag, data
            in zip(tags, datas)
        }


blank_song = Song({'path': '',
                   'title': 'Nothing currently playing',
                   'artist': '',
                   'album': '',
                   'length': 0,
                   'samplerate': 0,
                   'channels': 0,
                   'bitrate': 0,
                   'playcount': 0
})
