import os
import queue
import random

import song
import menu
from colours import Colour_types as ct

import debug


playmodes = ['shuffle', 'inorder', 'single']

class Playlist_item(menu.Menu_item):
    def __init__(self, data):
        super().__init__(data)
        self.play_next = None
        self.play_prev = None


class Playlist(menu.Menu):
    def __init__(self, name, db, x=0, y=0, w=0, h=0, win=None,
                 form=lambda w, h, addnstr, x, y, ll: self.win.addnstr(y, x, ll['title'], w),
                 palette=None, ui=None
                 ):
        self.name = name
        self.db = db
        self.commit = self.db.commit


        self.exe("SELECT id FROM playlists WHERE plname=?;", (self.name,))
        self.id = self.db.curs.fetchone()[0]

        self.sort_key = self.get_val('sort')

        super().__init__(x, y, w, h, win, data=None,
                         palette=palette)
         
        self.form = form
        self.ui = ui

        self.data = self.get_songs()
        self.cur_song = None

        self.playmode = self.get_val('playmode')
        self.playmode_list = [self.shuffle,
                              self.inorder,
                              self.single]

        #self.gen = self.playmode_list[self.playmode]()
        #sort makes self.gen
        self.order = queue.Queue()
        self.sort()


    def __contains__(self, path):
        return any(filter(lambda x: x.data['path'] == path, self.data))


    def __getitem__(self, ind):
        return self.data[ind]


    def __len__(self):
        return len(self.data)


    def __next__(self):
        if not self.data:
            return None

        return next(self.gen)

    def __str__(self):
        return self.name

    @property
    def playmode_str(self):
        return playmodes[self.playmode]

    def index(self, obj):
        for i, d.data in enumerate(self.data):
            if obj == d.data:
                return i

        return -1

    @staticmethod
    def init_pl(name, db):
        if name in {'library', 'playlists', 'pl_song'}:
            return
        try:
            db.exe("INSERT INTO playlists (plname, sort, playmode) VALUES (?, 0, 0);", (name,))
            db.commit()

        except Exception as err:
            raise err

    @staticmethod
    def del_pl(name, db):
        try:
            db.exe("DELETE FROM playlists WHERE plname=?;", (name,))

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
        return [
            Playlist_item(song.Song.from_iter(song_i))
            for song_i in self.exe("SELECT * FROM library WHERE id IN (SELECT song_id FROM pl_song WHERE pl_id=?);", (self.id,))
        ]


    def get_val(self, val):
        self.exe("SELECT {} FROM playlists WHERE plname=?;".format(val), (self.name,))
        out = self.db.curs.fetchone()
        if out:
            return out[0]

        return None


    def remake_gen(self):
        self.gen = self.playmode_list[self.playmode]()


    def set_order(self, playmode):
        with self.order.mutex:
            self.order.queue.clear()
            
        l = len(self.data)
        iter_values = list(range(l))
        
        i = 0
        if playmode == 0:
            #shuffle
            random.shuffle(iter_values)
            cur = self.data[iter_values[0]]

            for i in iter_values[1:]:
                cur.play_next = self.data[i]
                self.data[i].play_prev = cur
                cur = self.data[i]

            self.data[iter_values[-1]].play_next = self.data[iter_values[0]]
            self.data[iter_values[0]].play_prev = self.data[iter_values[i]]


        elif playmode == 1:
            #inorder
            cur = self.data[0]

            for i in iter_values[1:]:
                cur.play_next = self.data[i]
                self.data[i].play_prev = cur
                cur = self.data[i]


            self.data[-1].play_next = self.data[0]
            self.data[0].play_prev = self.data[i]

    def shuffle(self):
        self.set_order(0)

        while True:
            next_song = self.cur_song.play_next
            self.cur_song = next_song
            yield self.cur_song.data

            
    def inorder(self):
        self.set_order(1)

        while True:
            next_song = self.cur_song.play_next
            self.cur_song = next_song

            yield self.cur_song.data


    def single(self):
        while True:
            yield self.cur_song.data


    def sort(self):
        sort_key = song.tags[self.sort_key]
        if sort_key in {'path', 'artist', 'album', 'title'}:
            key = lambda x: x.data[sort_key].lower()
        else:
            key = lambda x: x.data[sort_key]

        self.data.sort(key=key)
        self.remake_gen()


    def delete(self, song):
        if song in self.data:
            #link up the linked list
            if song.play_prev and song.play_next:
                play_prev = song.play_prev
                play_next = song.play_next
                play_prev.play_next = play_next
                play_next.play_prev = play_prev

            self.data.remove(song)

            self.exe("DELETE FROM pl_song WHERE pl_id=? AND song_id=?;", (self.id, song.data['id'],))
            self.commit()

            if self.highlighted_ind() >= len(self.data):
                self.up()


    def insert(self, path):
        if path in self:
            return

        #add file to library table if it's not already
        self.db.insert_song(path)
        song_id = self.db.get_song_id(path)
        #add file into playlist table
        self.exe("INSERT INTO pl_song (song_id, pl_id) VALUES (?,?);", (song_id, self.id,))

        self.data += [
            Playlist_item(song.Song.from_iter(song_i))
            for song_i
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
                    new_db.append(tuple(out)[1:])
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
        for path in path_list:
            song_id = self.db.get_song_id(path)
            self.exe("INSERT INTO pl_song VALUES (?, ?)", (song_id, self.id,))

        for path in path_list:
            self.data += [
                Playlist_item(song.Song.from_iter(song_i))
                for song_i
                in self.exe("SELECT * FROM library WHERE path=?;", (path,))
            ]
        
        self.commit()


    def change_sort(self, sort):
        self.sort_key = sort
        self.sort()

        self.exe("UPDATE playlists SET sort=? WHERE id=?;", (sort, self.id,))
        self.commit()


    def change_playmode(self, play):
        self.playmode = play
        self.gen = self.playmode_list[self.playmode]()

        self.exe("UPDATE playlists SET playmode=? WHERE id=?;", (play, self.id,))
        self.commit()


    def rename(self, newname):
        self.exe("UPDATE playlists SET plname=? WHERE id=?;", (newname, self.id,))

        self.name = newname
        self.commit()

    def disp(self):
        self.win.erase()
        diff = len(self.data) - self.offset
        smaller = self.h if diff > self.h else diff

        for ii in range(smaller):
            self.form(self.w, self.h, self.win.addnstr, 0, ii, self.data[ii + self.offset].data)

        self.paint()
        self.refresh()


    def update(self):
        self.data = self.get_songs()
        self.sort()

    def paint(self):
        #check that playlist to be displayed has both be true:
        #the currently playing playlist is the currently displayed playlist
        #the currently playing song is in the playlist
        cur_song_ind = -1
        if self is self.ui.cur_pl and self.ui.player.cur_song['path'] in self:
            for i, d in enumerate(self.data):
                if d.data == self.ui.player.cur_song:
                    cur_song_ind = i - self.offset
                    break
        if self.data:
            self.chgat(self.cursor, 0, self.w - 1, ct.cursor)

        if 0 <= cur_song_ind < self.h:
            if cur_song_ind == self.cursor:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.cursor | ct.playing)
            else:
                self.chgat(cur_song_ind, 0, self.w - 1, ct.playing)

        for i, d in enumerate(self.data[self.offset:self.offset+self.h]):
            colour = ct.highlight
            if d.highlighted:
                if i == cur_song_ind:
                    colour |= ct.playing
                if i == self.cursor:
                    colour |= ct.cursor
                self.chgat(i, 0, self.w - 1, colour)

        self.ui.leftwin.win.touchwin() 
