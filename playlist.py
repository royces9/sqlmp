import random

import pldb

class Playlist:
    def __init__(self, name, curs):
        self.name = name
        self.data = pldb.get_songs_playlist(name, curs)
        self.order = list(range(len(self.data)))
        self.ind = 0
        self.cur = 0

        self.sort_key = pldb.get_val(self.name, 'sort', curs)
        self.sort()

        self.playback = pldb.get_val(self.name, 'playorder', curs)
        self.play_order_list = {'shuffle': self.shuffle,
                                'inorder': self.inorder,
                                'single': self.single}

        self.set_order()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, ind):
        return self.data[ind]
            
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
