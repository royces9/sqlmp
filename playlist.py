import random
import keys

def init_pl(name, db):
    if name in {'library', 'playlists'}:
        print("Can't name playlist 'library' or 'playlists'.")
        return
                
    db.exe(f"CREATE TABLE '{name}' (path);");
    db.exe(f"INSERT INTO playlists VALUES ('{name}', 'artist', 'shuffle');");
    db.commit();


def del_pl(name, db):
    db.exe(f"DELETE FROM playlists WHERE plname='{name}';")
    db.exe(f"DELETE FROM pl_song WHERE plname='{name}';")
    db.exe(f"DROP TABLE {name};")

    db.commit();

class Playlist:
    def __init__(self, name, db):
        self.name = name
        self.db = db

        self.ind = 0
        self.cur = 0

        self.sort_key = self.get_val('sort')
        self.tags = ['path', 'title', 'artist', 'album', 'length', 'bitrate', 'playcount']
        self.joined_tag = ", ".join(self.tags)
        self.data = self.get_songs()

        self.sort()

        self.playback = self.get_val('playorder')
        self.play_order_list = {'shuffle': self.shuffle,
                                'inorder': self.inorder,
                                'single': self.single}
        self.set_order()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, ind):
        return self.data[ind]
            
    def get_songs(self):

        """
        out = []
        for song in curs.execute(f"SELECT {self.joined_tag} FROM library WHERE path IN (SELECT path FROM pl_song WHERE plname='{pl}');"):
            out.append({tag: data for tag, data in zip(tags, song)})
        same thing as the bit above lol
        """
        return [{tag: data for tag, data in zip(self.tags, song)}
               for song in self.db.exe(f"SELECT {self.joined_tag} FROM library WHERE path IN (SELECT path FROM pl_song WHERE plname='{self.name}');")]
    
    def get_val(self, val):
        self.db.exe(f"SELECT {val} FROM playlists WHERE plname='{self.name}';")
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
        self.data.sort(key=lambda x: x[self.sort_key])

    def set_order(self):
        self.play_order_list[self.playback]()

    def _next(self):
        self.ind += 1

        if self.ind >= len(self.data):
            self.set_order()
            self.ind = 0

        return self.data[self.order[self.ind]]

    def remove(self, path):
        self.db.exe(f"DELETE FROM {self.name} WHERE path='{path}';")
        self.db.exe(f"DELETE FROM pl_song WHERE path='{path}' AND plname='{self.name}';")
        self.db.commit()

    def insert(self, path):
        #add file to library table if it's not already
        self.db.add_to_lib(path)
        path = path.replace("'", "''")

        #add file into playlist table
        self.db.exe(f"INSERT INTO {self.name} VALUES ('{path}');")
        self.db.exe(f"INSERT INTO pl_song VALUES ('{path}','{self.name}');")

        self.db.commit()

        for song in self.db.exe(f"SELECT {self.joined_tag} FROM library WHERE path='{path}';"):
            self.data.append({tag: data for tag, data in zip(self.tags, song)})

            
    def insert_from_file(self, path):
        with open(path, "r") as fp:
            path_list = [p.rstrip().replace("'", "''") for p in fp]

        path_join = "'),('".join(path_list)

        combined = ",".join([f"('{path}','{self.name}')" for path in path_list])
            
        self.db.exe(f"INSERT INTO {self.name} VALUES ('{path_join}');")
        self.db.exe(f"INSERT INTO pl_song VALUES {combined};")

        self.data += self.get_songs()
        self.db.commit()


    def change_sort(self, sort):
        self.sort_key = sort
        self.sort()
        
        self.db.exe(f"UPDATE playlists SET sort='{sort}' WHERE plname='{self.name}';")
        self.db.commit()

    def change_playtype(self, play):
        self.playback = play
        self.set_order()
        
        self.db.exe(f"UPDATE playlists SET playorder='{play}' WHERE plname='{self.name}';")
        self.db.commit()

    def rename(self, newname):
        self.db.exe(f"UPDATE TABLE pl_song SET plname='{newname}' WHERE plname='{self.name}';")
        self.db.exe(f"ALTER TABLE {self.name} RENAME TO {newname}")
        self.db.exe(f"UPDATE TABLE playlists SET plname='{newname}' WHERE plname='{self.name}';")

        self.name = newname

        self.commit()
