import os
import random

import musicdb
import debug

def init_pl(name, db):
    if name in {'library', 'playlists'}:
        return

    try:
        db.exe(f"CREATE TABLE {name} (path);")
        db.exe(f"INSERT INTO playlists VALUES ('{name}', 'artist', 'shuffle');")
        db.commit()

    except Exception as err:
        raise err



def del_pl(name, db):
    try:
        db.exe("DELETE FROM playlists WHERE plname=?;", (name,))
        db.exe("DELETE FROM pl_song WHERE plname=?;", (name,))
        db.exe(f"DROP TABLE '{name}';")

        db.commit()
    except Exception as err:
        raise err


class Playlist:
    def __init__(self, name, db):
        self.name = name
        self.db = db
        self.commit = self.db.commit

        self.ind = 0
        self.cur = 0

        self.sort_key = self.get_val('sort')
        self.tags = ['path', 'title', 'artist', 'album', 'length', 'bitrate', 'playcount']
        self.joined_tag = ','.join(self.tags)
        self.data = self.get_songs()

        self.sort()

        self.playmode = self.get_val('playmode')
        self.playmode_list = {'shuffle': self.shuffle,
                              'inorder': self.inorder,
                              'single': self.single}
        self.order = []
        self.set_order()


    def __contains__(self, path):
        return any(filter(lambda x: x['path'] == path, self.data))


    def __len__(self):
        return len(self.data)


    def __getitem__(self, ind):
        """
        I don't think I need this but I'll keep it here just cause
        if isinstance(ind, str):
            s = list(filter(lambda x: x['path'] == ind, self.data))[:1]
            if not s:
                return None
            return s[0]
        """
        return self.data[ind]


    def exe(self, query, args=()):
        try:
            return self.db.exe(query, args)
        except Exception as err:
            raise err


    def get_songs(self):
        #dict comprehension in a list comprehension (yikes)
        return [
            {
                tag: data if not isinstance(data, str)
                     else data.replace("''", "'")
                for tag, data in zip(self.tags, song)
            }
            for song in self.exe(f"SELECT {self.joined_tag} FROM library WHERE path IN\
            (SELECT path FROM pl_song WHERE plname=?);", (self.name,))
        ]


    def get_val(self, val):
        self.exe(f"SELECT {val} FROM playlists WHERE plname=?;", (self.name,))
        out = self.db.curs.fetchone()
        if out:
            return out[0]

        return None


    def shuffle(self):
        self.order = list(range(len(self.data)))
        random.shuffle(self.order)


    def inorder(self):
        self.order = list(range(len(self.data)))


    def single(self):
        self.order = [self.cur] * len(self.data)


    def sort(self):
        if self.sort_key in {'path', 'artist', 'album', 'title'}:
            key = lambda x: x[self.sort_key].lower()
        else:
            key = lambda x: x[self.sort_key]

        self.data.sort(key=key)


    def set_order(self):
        self.playmode_list[self.playmode]()


    def next_(self):
        if not self.data:
            return None

        self.ind += 1

        if self.ind >= len(self.data):
            self.set_order()
            self.ind = 0

        return self.data[self.order[self.ind]]


    def remove(self, path):
        delsong = list(filter(lambda x: x['path'] == path, self.data))[:1]
        if not delsong:
            return

        self.data.remove(delsong[0])
        self.exe(f"DELETE FROM {self.name} WHERE path=?;", (path,))
        self.exe(f"DELETE FROM pl_song WHERE plname=? AND path=?;", (self.name, path,))
        self.commit()


    def insert(self, path):
        if path in self:
            return

        self.data += [
            {
                tag: data
                for tag, data in zip(self.tags, song)
            }
            for song in self.exe(f"SELECT {self.joined_tag} FROM library WHERE path=?;", (path,))
        ]

        #add file to library table if it's not already
        self.db.add_to_lib(path)
        path = path.replace("'", "''")

        #add file into playlist table
        self.exe(f"INSERT INTO {self.name} VALUES (?);", (path,))
        self.exe("INSERT INTO pl_song VALUES (?,?);", (path, self.name,))

        self.commit()


    def insert_dir(self, di):
        list_all = []
        path_list = []
        for root, _, files in os.walk(di):
            for ff in files:
                path = os.path.join(root, ff).replace("'", "''")
                if path not in self.db:
                    out = musicdb.extract_metadata(path)
                    if out:
                        (title, artist, album, length, bitrate) = out
                        list_all.append(
                            f"('{path}', '{title}', '{artist}', '{album}', {length}, {bitrate}, 0)"
                        )
                if path not in self:
                    path_list.append(path)

        self.db.add_multi(list_all)
        self.insert_path_list(path_list)
        self.sort()


    def insert_from_file(self, path):
        with open(path, "r") as fp:
            path_list = [p.rstrip().replace("'", "''") for p in fp]

        self.insert_path_list(path_list)
        self.sort()


    def insert_path_list(self, path_list):
        path_join = "'),('".join(path_list)

        combined = ",".join([f"('{path}','{self.name}')" for path in path_list])
        if not combined:
            combined = '(0, 0)'

        self.exe(f"INSERT INTO {self.name} VALUES (?);", (path_join,))
        self.exe(f"INSERT INTO pl_song VALUES {combined};")

        self.data += self.get_songs()
        self.commit()


    def change_sort(self, sort):
        self.sort_key = sort
        self.sort()

        self.exe("UPDATE playlists SET sort=? WHERE plname=?;", (sort, self.name,))
        self.commit()


    def change_playmode(self, play):
        self.playmode = play
        self.set_order()

        self.exe("UPDATE playlists SET playmode=? WHERE plname=?;", (play, self.name,))
        self.commit()


    def rename(self, newname):
        self.exe("UPDATE TABLE pl_song SET plname=? WHERE plname=?;", (newname, self.name,))
        self.exe(f"ALTER TABLE {self.name} RENAME TO {newname}")
        self.exe("UPDATE TABLE playlists SET plname=? WHERE plname=?;", (newname, self.name,))

        self.name = newname

        self.commit()
