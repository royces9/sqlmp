import os

import ffmpeg

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}

class Song:
    def __init__(self, path):
        self.path = path.replace("'", "''")
        
        if os.path.splitext(self.path)[1] not in ext_list:
            return None
    
        if not os.path.exists(self.path):
            return None

        prob = ffmpeg.probe(self.path)
    
        tags_out = ['title', 'artist', 'album']
        if 'tags' in prob['format']:
            tmp = prob['format']['tags']
            tmp = {k.lower(): i for k, i in tmp.items()}
            tags = [tmp[t].replace("'", "''") if t in tmp else '' for t in tags_out]
        elif 'tags' in prob['streams'][0]:
            tmp = prob['streams'][0]['tags']
            tmp = {k.lower(): i for k, i in tmp.items()}
            tags = [tmp[t].replace("'", "''") if t in tmp else '' for t in tags_out]
        else:
            tags = [''] * len(tags_out)
        
        attr = [a[1](prob['streams'][0][a[0]])
                for a in [('duration', float), ('sample_rate', int), ('channels', int)]]
        
        self.title = tags[0]
        self.artist = tags[1]
        self.album = tags[2]

        self.length = attr[0]
        self.samplerate = attr[1]
        self.channels = attr[2]

        self.bitrate = int(prob['format']['bit_rate'])

    def tuple(self):
        return (self.path, self.title, self.artist, self.length, self.samplerate, self.channels, self.bitrate,)

    def db_str(self):
        return f"('{self.path}', '{self.title}', '{self.artist}', '{self.album}', {self.length}, {self.samplerate}, {self.channels}, {self.bitrate}, 0)")
