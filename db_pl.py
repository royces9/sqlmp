#!/usr/bin/python

import libdb
import os
import sqlite3
import sys

def get_songs_playlist(pl, curs):
    songs = list_pl_songs(pl, curs)
    out = []

    tags = ['path', 'title', 'artist', 'album', 'length', 'bitrate', 'playcount']
    joined_tag = ", ".join(tags);

    for song in songs:
        song = song.replace("'", r"''");
        for queries in curs.execute(f"SELECT {joined_tag} FROM library WHERE path='{song}';"):
            newd = dict()
            for tag, query in zip(tags, queries):
                newd[tag] = query
                
            out.append(newd);
                
    return out;


def add_to_pl(path, pl_table, conn, curs):
    #add file to library table if it's not already
    libdb.add_to_lib(path, conn, curs);
    path = path.replace("'", "''");

    #add file into playlist table
    sqlstr = f"INSERT INTO {pl_table} VALUES ('{path}');";
    curs.execute(sqlstr);

    sqlstr = f"INSERT INTO pl_song VALUES ('{path}', '{pl_table}');";
    curs.execute(sqlstr);

    conn.commit();


def remove_from_pl(path, pl_table, curs, conn):
    sqlstr = f"DELETE FROM {pl_table} WHERE path='{path}';";
    curs.execute(sqlstr);

    sqlstr = f"DELETE FROM pl_song WHERE path='{path}' AND plname='{pl_table}';";
    curs.execute(sqlstr);
    
    conn.commit();

    
def add_to_pl_from_file(pl_table, file_path, conn, curs):
    with open(file_path, "r") as fp:
        for path in fp:
            path = path.rstrip();
            add_to_pl(path, pl_table, conn, curs);


def init_pl(pl_table, conn, curs):
    if pl_table == "library" or pl_table == "playlists":
        print("Can't name playlist 'library' or 'playlists'.");
        return;

    curs.execute(f"CREATE TABLE '{pl_table}' (path);");
    curs.execute(f"INSERT INTO playlists VALUES ('{pl_table}');");
    conn.commit();


def del_pl(pl, conn, curs):
    sqlstr = f"DELETE FROM playlists WHERE plname='{pl}';";
    curs.execute(sqlstr);

    sqlstr = f"DELETE FROM pl_song WHERE plname='{pl}';";
    curs.execute(sqlstr);

    sqlstr = f"DROP TABLE {pl};";
    curs.execute(sqlstr);
    
    conn.commit();


def rename_pl(pl, newname, conn, curs):
    sqlstr = f"UPDATE TABLE pl_song SET plname='{newname}' WHERE plname='{pl}';"
    curs.execute(sqlstr);
    
    sqlstr = f"ALTER TABLE {pl} RENAME TO {newname}";
    curs.execute(sqlstr);

    sqlstr = f"ALTER TABLE playlists SET plname='{newname}' WHERE plname='{pl}';"
    curs.execute(sqlstr);
    
        
def list_pl_songs(pl, curs):
    songs =[];
    for song in curs.execute(f"SELECT path FROM '{pl}';"):
        songs.append(song[0]);

    return songs;

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Incorrect args.");

    file_path = sys.argv[1];
    music_db_dir = sys.argv[2];

    pl_table = os.path.splitext(os.path.basename(file_path))[0];
    conn = sqlite3.connect(music_db_dir);
    curs = conn.cursor();
    
    sqlstr = f"SELECT plname FROM playlists WHERE plname='{pl_table}' LIMIT 1;";
    curs.execute(sqlstr);
    if not curs.fetchone():
        init_pl(pl_table, conn, curs);

    add_to_pl_from_file(pl_table, file_path, conn, curs);
    conn.close();
