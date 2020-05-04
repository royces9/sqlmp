import os

import ffmpeg

import debug

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}

blank_song = {'title': 'Nothing currently playing',
              'artist': '',
              'album': '',
              'length': 0,
              'samplerate': 0,
              'channels': 0,
              'bitrate': 0,
              'playcount': 0
}


class Song:
    def __init__(self, path):
        self.path = path
        
        (self.title, self.artist, self.album,
         self.length, self.samplerate, self.channels,
         self.bitrate) =  self.grab_tags(path)


    def grab_tags(self, path):
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

        return tuple(tags, ) + tuple(attr, ) + (int(prob['format']['bit_rate']), )

    @classmethod
    def from_path(cls, path):
        if os.path.splitext(path)[1] not in ext_list:
            return None
    
        if not os.path.exists(path):
            return None

        return cls(path)


    def tuple(self):
        return (self.path, self.title, self.artist, self.album, self.length, self.samplerate, self.channels, self.bitrate,)
