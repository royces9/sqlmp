import db_pl
import menu
import random

def get_songs_playlist(pl, curs):
    songs = db_pl.list_pl_songs(pl, curs)
    out = []

    tags = ['path', 'title', 'artist', 'album', 'length', 'bitrate', 'playcount']
    joined_tag = ", ".join(tags);

    for i, song in enumerate(songs):
        song = song.replace("'", r"''");
        for queries in curs.execute(f"SELECT {joined_tag} FROM library WHERE path='{song}';"):
            newd = dict()
            for tag, query in zip(tags, queries):
                newd[tag] = query

            out.append(newd);
            
    return out;
                                                                                    

class Playlist:
    def __init__(self, name, curs):
        self.name = name
        self.data = get_songs_playlist(name, curs)
        self.order = list(range(len(self.data)))
        self.new_order()
        
    def __len__(self):
        return len(self.data)

    def __getitem__(self, ind):
        return self.data[ind]
            
    def new_order(self):
        random.shuffle(self.order)
        self.ind = 0

    def _next(self):
        self.ind += 1

        if self.ind >= len(self.data):
            self.new_order()

        return self.data[self.order[self.ind]]
