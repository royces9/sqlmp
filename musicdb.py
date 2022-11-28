import os
import sqlite3

import song

import debug


class Musicdb:
    def __init__(self, path, lib):
        if os.path.exists(path):
            self.path = path
        else:
            raise FileNotFoundError("{} does not exist".format(path))
        
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
        db.exe("CREATE TABLE library (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, samplerate INT, channels INT, bitrate INT, playcount INT);")
        db.exe("CREATE TABLE playlists (id INTEGER PRIMARY KEY, plname TEXT, sort INTEGER, playmode INTEGER);")
        db.exe("CREATE TABLE pl_song (song_id INTEGER, pl_id INTEGER, FOREIGN KEY(song_id) REFERENCES library(id) ON DELETE CASCADE, FOREIGN KEY(pl_id) REFERENCES playlists(id));")

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
        self.exe("SELECT id FROM ? WHERE path=? LIMIT 1;", (table, path,))
        return bool(self.curs.fetchone())


    def insert_song(self, path):
        if path in self:
            return

        out = song.Song.from_path(path)
        if not out:
            return

        self.exe("INSERT INTO library (path, title, artist, album, length, samplerate, channels, bitrate, playcount) VALUES (?,?,?,?,?,?,?,?,?);", tuple(out))
        self.commit()


    def remove_song(self, path):
        if path not in self:
            return

        self.exe("DELETE FROM library WHERE path=?;", (path,))

        self.commit()


    def insert_song_list(self, paths):
        self.insert_multi(
            [
                tuple(s)
                for p in (pp for pp in paths if pp not in self)
                if (s := song.Song.from_path(p) is not None)
            ]
        )


    def insert_dir(self, di):
        list_all = self.dir_files(di)
        if list_all:
            self.insert_multi(list_all)


    def dir_files(self, di):
        return [
            tuple(out)
            for root, _, files in os.walk(di)
            for ff in files
            if (out := song.Song.from_path(os.path.join(root, ff))) is not None and out['path'] not in self
        ]


    def insert_multi(self, li):
        self.executemany("INSERT INTO library (path, title, artist, album, length, samplerate, channels, bitrate, playcount) VALUES (?,?,?,?,?,?,?,?,?);", li)
        self.commit()


    def update_db(self):
        #this gets every file
        all_files = (
            os.path.join(root, ff)
            for root, _, files in os.walk(self.lib)
            for ff in files if os.path.splitext(ff)[1] in song.ext_list
        )

        new_files = []
        for path in all_files:
            out = song.Song.from_path(path)
        
            if not out:
                continue
            if path not in self:
                new_files.append(tuple(out))
            else:
                self.update_song(out)


        self.insert_multi(new_files)


    def increment_playcount(self, song):
        """
        increment playcount for a song by one
        """
        self.exe("UPDATE library SET playcount=playcount+1 WHERE path=?", (song['path'],))
        song['playcount'] += 1
        self.commit()

    def update_song(self, song):
        """
        update a song in the db with metadata from input song
        the song must be updated before the call to update_song
        """
        self.exe("UPDATE library SET title=?, artist=?, album=?, length=?, samplerate=?, channels=?, bitrate=? WHERE path=?", (song['title'], song['artist'], song['album'], song['length'], song['samplerate'], song['channels'], song['bitrate'], song['path']))
        self.commit()
        
    def list_pl(self):
        return [pl[0] for pl in self.exe("SELECT plname FROM playlists;")]


    def get_song_id(self, path):
        self.exe("SELECT id FROM library WHERE path=?", (path,))
        return self.curs.fetchone()[0]
