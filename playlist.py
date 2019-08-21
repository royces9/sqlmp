import enum
import random

import db_pl
import menu

class Playlist:
    def __init__(self, name, curs):
        self.name = name
        self.data = db_pl.get_songs_playlist(name, curs)
        self.order = list(range(len(self.data)))
        self.ind = 0
        self.cur = 0

        """
        playback type:
        0 - shuffle
        1 - inorder
        2 - single
        """
        self.playback = 1
        self.play_order_list = [self.shuffle,
                                self.inorder,
                                self.single]
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


    def set_order(self):
        self.play_order_list[self.playback]()

    def _next(self):
        self.ind += 1

        if self.ind >= len(self.data):
            self.set_order()
            self.ind = 0

        return self.data[self.order[self.ind]]
