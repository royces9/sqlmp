import ffmpeg
import os
import sqlite3

import debug
import song


class Musicdb:
    def __init__(self, path, lib):
        if os.path.exists(path):
            self.path = path
        else:
            raise FileNotFoundError(f"{path} does not exist")
        
        self.lib = lib

        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()

        self.commit = self.conn.commit


    #only check library, not anything else like playlists
    def __contains__(self, path):
        self.exe("SELECT path FROM library WHERE path=? LIMIT 1;", (path,))
        return bool(self.curs.fetchone())


    def __del__(self):
        self.conn.close()


    @staticmethod
    def init_db(db):
        db.exe("CREATE TABLE library (path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, samplerate INT, channels INT, bitrate INT, playcount INT);")
        db.exe("CREATE TABLE playlists (plname TEXT, sort TEXT, playmode TEXT);")
        db.exe("CREATE TABLE pl_song (path TEXT, plname TEXT);")
        db.commit()


    def exe(self, query, args=()):
        try:
            return self.curs.execute(query, args)
        except Exception as err:
            raise err

    def executemany(self, query, args=()):
        try:
            return self.curs.executemany(query, args)
        except Exception as err:
            raise err


    def in_table(self, path, table):
        self.exe("SELECT path FROM ? WHERE path=? LIMIT 1;", (table, path,))
        return bool(self.curs.fetchone())


    def add_song(self, path):
        if path in self:
            return

        out = song.Song.from_path(path)
        if not out:
            return

        self.exe("INSERT INTO library VALUES (?,?,?,?,?,?,?,?,0);", out.tuple())
        self.commit()


    def remove_song(self, path):
        if path not in self:
            return
        self.exe("DELETE FROM library WHERE path=?;", (path,))

        if pl_all:
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
                    out = song.Song.from_path(path)
                    if out:
                        list_all.append(out.tuple())

        return list_all


    def add_multi(self, li):
        self.executemany("INSERT INTO library VALUES (?,?,?,?,?,?,?,?,0);", li)
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
                out = song.Song.from_path(path)
                if not out:
                    continue
                new_files.append(out.db_str())

        self.add_multi(new_files)
        return


    def list_pl(self):
        return [pl[0] for pl in self.exe("SELECT plname FROM playlists;")]
