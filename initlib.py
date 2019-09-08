#!/usr/bin/python

import os
import sqlite3

import musicdb
import playlist

#quick script to init lib and some playlists or something
#only run this once

#location of database file
dbpath = 'lib.db'

#Folder to recursively search through
libpath = os.getenv('HOME') + '/Music/'

#list of playlists to add
prefix = os.getenv('HOME') + '/.config/cmus/playlists/'
pl_list = [
    prefix + 'damnsumman',
    prefix + 'anisongbanger',
    prefix + 'sumluv',
    prefix + 'THE_playlist',
    prefix + 'coolassshit',
    prefix + 'actuallykms',
    prefix + 'animusumluv',
]

conn = sqlite3.connect(dbpath);
curs = conn.cursor();
db = musicdb.Musicdb(dbpath)

print('Creating database')
db.exe("CREATE TABLE library (path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, bitrate INT, playcount INT);")
db.exe("CREATE TABLE playlists (plname TEXT, sort TEXT, playmode TEXT);")
db.exe("CREATE TABLE pl_song (path TEXT, plname TEXT);")
db.commit()

print('Adding ' + libpath)
db.add_dir(libpath)

for pl in pl_list:
    plname = os.path.splitext(os.path.basename(pl))[0];
    print('Adding "' + plname + '"')
    playlist.init_pl(plname, db)
    plclass = playlist.Playlist(plname, db)
    plclass.insert_from_file(pl)
                                        
