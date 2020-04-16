#!/usr/bin/python

import os
import sqlite3

import musicdb
import playlist

#quick script to init lib and some playlists or something
#only run this once

#location of database file
dbpath = 'newlib.db'

#Folder to recursively search through
libpath = os.getenv('HOME') + '/Music/'

#textfile with list of playlists to add
plfile = 'pl_list'

with open(plfile, 'r') as fp:
    pl_list = [line.rstrip() for line in fp.readlines()]

conn = sqlite3.connect(dbpath)
curs = conn.cursor()
db = musicdb.Musicdb(dbpath, libpath)

"""
print('Creating database')
musicdb.Musicdb.init_db(db)

import time
print('Adding ' + libpath)
s = time.time()
db.add_dir(libpath)
print(time.time() - s)
"""
for pl in pl_list:
    plname = os.path.splitext(os.path.basename(pl))[0]

    print('Adding "' + plname + '"')
    playlist.Playlist.init_pl(plname, db)

    plclass = playlist.Playlist(plname, db)
    plclass.insert_from_file(pl)
