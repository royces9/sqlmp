import mutagen
import os

import debug

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg', '.opus'}

tags = ['id', 'path', 'title', 'artist', 'album', 'length', 'samplerate', 'channels', 'bitrate', 'playcount']


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
        song = mutagen.File(path, easy=True)

        t_tags = [song['title'][0], song['artist'][0], song['album'][0]]
        attr = [song.info.length, song.info.sample_rate, song.info.channels]
        bitrate = song.info.bitrate

        return (0,) + (path,) + tuple(t_tags, ) + tuple(attr, ) + (int(bitrate), ) + (0,)



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


blank_song = Song({'id': 0,
                   'path': '',
                   'title': 'Nothing currently playing',
                   'artist': '',
                   'album': '',
                   'length': 0,
                   'samplerate': 0,
                   'channels': 0,
                   'bitrate': 0,
                   'playcount': 0
})
