import os
import sqlite3

import mutagen

ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}
key_list = ['title',
            'artist',
            'album',
]
attr_list = ['length',
             'bitrate',
]

def init_db(db):
    db.exe("CREATE TABLE library (path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, bitrate INT, playcount INT);")
    db.exe("CREATE TABLE playlists (plname TEXT, sort TEXT, playmode TEXT);")
    db.exe("CREATE TABLE pl_song (path TEXT, plname TEXT);")
    db.commit()


class Musicdb:
    def __init__(self, path):
        #assume that the db exists
        self.path = path

        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()

        self.commit = self.conn.commit

        
    #only check library, not anything else like playlists
    def __contains__(self, path):
        path = path.replace("'", "''")
        self.exe("SELECT path FROM library WHERE path=? LIMIT 1;", (path,))
        return True if self.curs.fetchone() else False


    def __del__(self):
        self.conn.close()

    def exe(self, query, args=()):
        try:
            return self.curs.execute(query, args)
        except Exception as err:
            raise err


    def in_table(path, table):
        path = path.replace("'", "''")
        self.exe("SELECT path FROM ? WHERE path=? LIMIT 1;", (table, path,))
        return True if self.curs.fetchone() else False


    def extract_metadata(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in ext_list:
            return None

        try:
            out = mutagen.File(path, easy=True)
        except:
            return None

        if not out:
            return None

        song_dict = {key: out[key][0].replace("'", "''") if key in out.keys() else "" for key in key_list}

        attr_out = {attr: getattr(out.info, attr) if hasattr(out.info, attr) else 0 for attr in attr_list} if hasattr(out, 'info') else {attr: 0 for attr in attr_list}
                    
        return tuple(song_dict.values(),) + tuple(attr_out.values(),)


    def add_to_lib(self, path):
        if path in self:
            return

        out = self.extract_metadata(path)
        if not out:
            return
        (title, artist, album, length, bitrate) = out
        
        path = path.replace("'", "''")

        self.exe("INSERT INTO library VALUES (?,?,?,?,?,?,0);", (path, title, artist, album, length, bitrate,))
        self.commit()

        
    def remove_from_lib(self, path):
        if path not in self:
            return
        self.exe(f"DELETE FROM library WHERE path=?;", (path,))
        pl_all = "','".join([qq[0] for qq in self.exe("SELECT plname FROM pl_song WHERE path=?;", (path,))])

        if len(pl_all) > 0:
            self.exe(f"DELETE FROM {pl_all} WHERE path=?;", (path,))
            self.exe("DELETE FROM pl_song WHERE path=?;", (path,))

        self.commit()


    def add_dir(self, di):
        list_all = self.dir_files(di)
        self.add_multi(list_all)


    def dir_files(self, di):
        list_all = []

        for root, subdirs, files in os.walk(di):
            for ff in files:
                path = os.path.join(root, ff).replace("'", "''")

                if path not in self:
                    out = self.extract_metadata(path)
                    if out:
                        (title, artist, album,length, bitrate) = out
                        list_all.append(f"('{path}', '{title}', '{artist}', '{album}', {length}, {bitrate}, 0)")
        return list_all

    
    def add_multi(self, li):
        joined = ",".join(li)
        self.exe(f"INSERT INTO library VALUES {joined}")
        self.commit()


    def update(self):
        new = set(self.dir_files(self.path))
        new_paths = [path for path in new if path not in self]
        if len(new_paths) > 0:
            self.add_multi(new_paths)

        old_paths = new - set(new_paths)
        for path in old_paths:
            if not os.path.exists(path):
                self.remove_from_lib(path)

    def list_pl(self):
        return [pl[0] for pl in self.exe("SELECT plname FROM playlists;")]

    
