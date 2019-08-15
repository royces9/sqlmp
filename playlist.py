import menu
import random

class Playlist:
    def __init__(self, name, data):
        self.name = name
        self.data = data
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
