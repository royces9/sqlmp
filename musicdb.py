import os
import sqlite3

import ffmpeg

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}

def init_db(db):
    db.exe("CREATE TABLE library (path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, samplerate INT, channels INT, bitrate INT, playcount INT);")
    db.exe("CREATE TABLE playlists (plname TEXT, sort TEXT, playmode TEXT);")
    db.exe("CREATE TABLE pl_song (path TEXT, plname TEXT);")
    db.commit()


def extract_metadata(path):
    ext = os.path.splitext(path)[1]
    if ext not in ext_list:
        return None

    #ffmpeg
    prob = ffmpeg.probe(path)
    
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
        
    bitrate = int(prob['format']['bit_rate'])

    return tuple(tags) + tuple(attr) + tuple([bitrate])


class Musicdb:
    def __init__(self, path, lib):
        #assume that the db exists
        self.path = path
        self.lib = lib

        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()

        self.commit = self.conn.commit


    #only check library, not anything else like playlists
    def __contains__(self, path):
        path = path.replace("'", "''")
        self.exe("SELECT path FROM library WHERE path=? LIMIT 1;", (path,))
        return bool(self.curs.fetchone())


    def __del__(self):
        self.conn.close()


    def exe(self, query, args=()):
        try:
            return self.curs.execute(query, args)
        except Exception as err:
            raise err


    def in_table(self, path, table):
        path = path.replace("'", "''")
        self.exe("SELECT path FROM ? WHERE path=? LIMIT 1;", (table, path,))
        return bool(self.curs.fetchone())


    def add_to_lib(self, path):
        if path in self:
            return

        out = extract_metadata(path)
        if not out:
            return
        (title, artist, album, length, samplerate, channels, bitrate) = out

        path = path.replace("'", "''")

        self.exe("INSERT INTO library VALUES (?,?,?,?,?,?,?,?,0);", (path, title, artist, album, length, samplerate, channels, bitrate,))
        self.commit()


    def remove_from_lib(self, path):
        if path not in self:
            return
        self.exe(f"DELETE FROM library WHERE path=?;", (path,))
        pl_all = "','".join([qq[0] for qq in self.exe("SELECT plname FROM pl_song WHERE path=?;", (path,))])

        if pl_all:
            self.exe(f"DELETE FROM {pl_all} WHERE path=?;", (path,))
            self.exe("DELETE FROM pl_song WHERE path=?;", (path,))

        self.commit()


    def add_dir(self, di):
        list_all = self.dir_files(di)
        if list_all:
            self.add_multi(list_all)


    def dir_files(self, di):
        list_all = []

        for root, _, files in os.walk(di):
            for ff in files:
                path = os.path.join(root, ff)

                if path not in self:
                    out = extract_metadata(path)
                    if out:
                        path = path.replace("'", "''")
                        (title, artist, album, length, samplerate, channels, bitrate) = out
                        list_all.append(f"('{path}', '{title}', '{artist}', '{album}', {length}, {samplerate}, {channels}, {bitrate}, 0)")
        return list_all


    def add_multi(self, li):
        joined = ",".join(li)
        self.exe(f"INSERT INTO library VALUES {joined}")
        self.commit()


    def update(self):
        #this gets every file
        all_files = [
            os.path.join(root, ff)
            for root, _, files in os.walk(self.lib)
            for ff in files if os.path.splitext(ff)[1] in ext_list
        ]

        new_files = []
        for path in all_files:
            if path not in self:
                out = extract_metadata(path)
                if not out:
                    continue
                
                path = path.replace("'", "''")
                (title, artist, album, length, samplerate, channels, bitrate) = out
                new_files.append(f"('{path}','{title}','{artist}','{album}',{length},{samplerate},{channels},{bitrate},0)")

        self.add_multi(new_files)
        return


    def list_pl(self):
        return [pl[0] for pl in self.exe("SELECT plname FROM playlists;")]
