import os
import random

import musicdb
import song

import debug


class Playlist:
    def __init__(self, name, db):
        self.name = name
        self.db = db
        self.commit = self.db.commit

        self.ind = 0

        self.sort_key = self.get_val('sort')
        self.tags = ['path', 'title', 'artist', 'album', 'length', 'samplerate', 'channels', 'bitrate', 'playcount']
        self.data = self.get_songs()

        self.sort()
        
        self.playmode = self.get_val('playmode')
        self.playmode_list = {'shuffle': self.shuffle,
                              'inorder': self.inorder,
                              'single': self.single}

        self.gen = self.playmode_list[self.playmode]()


    def __contains__(self, path):
        return any(filter(lambda x: x['path'] == path, self.data))


    def __getitem__(self, ind):
        return self.data[ind]


    def __len__(self):
        return len(self.data)


    def __next__(self):
        if not self.data:
            return None

        return next(self.gen)


    @staticmethod
    def init_pl(name, db):
        if name in {'library', 'playlists', 'pl_song'}:
            return
        try:
            db.exe("INSERT INTO playlists VALUES (?, 'artist', 'shuffle');", (name,))
            db.commit()

        except Exception as err:
            raise err

    @staticmethod
    def del_pl(name, db):
        try:
            db.exe("DELETE FROM playlists WHERE plname=?;", (name,))
            db.exe("DELETE FROM pl_song WHERE plname=?;", (name,))

            db.commit()
        except Exception as err:
            raise err


    def exe(self, query, args=()):
        try:
            return self.db.exe(query, args)
        except Exception as err:
            raise err


    def executemany(self, query, args=()):
        try:
            return self.db.executemany(query, args)
        except Exception as err:
            raise err

    def get_songs(self):
        #dict comprehension in a list comprehension (yikes)
        return [
            {
                tag: data
                for tag, data in zip(self.tags, song)
            }
            for song in self.exe("SELECT * FROM library WHERE path IN\
            (SELECT path FROM pl_song WHERE plname=?);", (self.name,))
        ]


    def get_val(self, val):
        self.exe("SELECT {} FROM playlists WHERE plname=?;".format(val), (self.name,))
        out = self.db.curs.fetchone()
        if out:
            return out[0]

        return None


    def remake_gen(self):
        self.gen = self.playmode_list[self.playmode]()

    def __set_order(self, playmode):
        order = list(range(len(self.data)))
        if playmode == 'shuffle':
            random.shuffle(order)
            
        return order


    def shuffle(self):
        order = self.__set_order('shuffle')
        old_len = len(self.data)

        while True:
            if old_len != len(self.data):
                old_len = len(self.data)
                order = self.__set_order('shuffle')
            
            if self.ind >= len(self.data):
                self.ind = 0
                
            yield self.data[order[self.ind]]
            self.ind += 1


    #TODO: my god this is horrid
    #this can be improved, but i think that
    #requires a change in design too, i have
    #to think about it more
    def inorder(self):
        order = self.__set_order('inorder')
        cur_song = self.data[order[self.ind]]

        while True:
            if cur_song in self.data:
                self.ind = self.data.index(cur_song) + 1
                
            if self.ind >= len(self.data):
                self.ind = 0

            cur_song = self.data[order[self.ind]]

            yield cur_song


    def single(self):
        same = self.data[self.ind]
        while True:
            yield same


    def sort(self):
        if self.sort_key in {'path', 'artist', 'album', 'title'}:
            key = lambda x: x[self.sort_key].lower()
        else:
            key = lambda x: x[self.sort_key]

        self.data.sort(key=key)


    def remove(self, song):
        if song in self.data:
            self.data.remove(song)

        self.exe("DELETE FROM pl_song WHERE plname=? AND path=?;", (self.name, song['path'],))
        self.commit()


    def insert(self, path):
        if path in self:
            return

        #add file to library table if it's not already
        self.db.insert_song(path)

        #add file into playlist table
        self.exe("INSERT INTO pl_song VALUES (?,?);", (path, self.name,))

        self.data += [
            {
                tag: data
                for tag, data
                in zip(self.tags, song)
            }
            for song
            in self.exe("SELECT * FROM library WHERE path=?;", (path,))
        ]
            
        self.commit()


    def insert_dir(self, di):
        new_db = []
        new_pl = []
        for root, _, files in os.walk(di):
            for ff in files:
                path = os.path.join(root, ff)
                out = song.Song.from_path(path)                
                if not out:
                    continue

                if path not in self.db:
                    new_db.append(out.tuple())
                if path not in self:
                    new_pl.append(path)

        if new_db:
            self.db.insert_multi(new_db)

        if new_pl:
            self.insert_path_list(new_pl)

        self.sort()


    def insert_from_file(self, path):
        with open(path, "r") as fp:
            path_list = [p.rstrip() for p in fp]

        self.db.insert_song_list(path_list)

        self.insert_path_list(path_list)
        self.sort()


    def insert_path_list(self, path_list):
        self.executemany("INSERT INTO pl_song VALUES (?,?)", ((path,self.name) for path in path_list))

        for path in path_list:
            self.data += [
                {
                    tag: data
                    for tag, data
                    in zip(self.tags, song)
                }
                for song
                in self.exe("SELECT * FROM library WHERE path=?;", (path,))
            ]
        
        self.commit()


    def change_sort(self, sort):
        self.sort_key = sort
        self.sort()

        self.exe("UPDATE playlists SET sort=? WHERE plname=?;", (sort, self.name,))
        self.commit()


    def change_playmode(self, play):
        self.playmode = play
        self.gen = self.playmode_list[self.playmode]()

        self.exe("UPDATE playlists SET playmode=? WHERE plname=?;", (play, self.name,))
        self.commit()


    def rename(self, newname):
        self.exe("UPDATE pl_song SET plname=? WHERE plname=?;", (newname, self.name,))
        self.exe("UPDATE playlists SET plname=? WHERE plname=?;", (newname, self.name,))

        self.name = newname
        self.commit()
