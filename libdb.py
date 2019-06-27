#!/usr/bin/python

import mutagen
import mutagen.mp3
import os
import sqlite3
import sys

def err_file(err, message):
    with open(err, "a") as fp:
        print(message, file=fp);

def extract_metadata(path, key_list, attr_list):
    ext = os.path.splitext(path)[1];
    ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'};
    if ext not in ext_list:
        return None;

    try:
        out = mutagen.File(path, easy=True);
    except Exception as e:
        err_file('broken.txt', path + ": " + str(e));
        return None;
            
    if not out:
        err_file('no_meta.txt', path);
        return None;

    song_dict = {};
    for key in key_list:
        song_dict[key] = "";
        if key in out.keys():
            song_dict[key] = out[key][0].replace("'", r"''");


    attr_out = {};
    if hasattr(out, 'info'):
        for attr in attr_list:
            attr_out[attr] = getattr(out.info, attr) if hasattr(out.info, attr) else 0
    else:
        for attr in attr_list:
            attr_out[attr] = 0;
        
    return (song_dict.values(), attr_out.values());


def in_table(path, curs, table):
    path = path.replace("'", r"''");
    sqlstr = f"SELECT path FROM {table} WHERE path='{path}' LIMIT 1;"
    curs.execute(sqlstr);
    return True if curs.fetchone() else False;


def add_to_lib(path, conn, curs):
    if in_table(path, curs, 'library'):
        return;

    key_list = ['title',
                'artist',
                'album',
    ];

    attr_list = ['length',
                 'bitrate',
    ];
    
    out = extract_metadata(path, key_list, attr_list);
    if not out:
        return;

    path = path.replace("'", r"''");            
    ((title, artist, album), (length, bitrate)) = out;

    sqlstr = f"INSERT INTO library VALUES ('{path}', '{title}', '{artist}', '{album}', {length}, {bitrate}, 0);";

    try:
        curs.execute(sqlstr);
        conn.commit();

    except Exception as e:
        print("Exception:");
        print(e);
            

def remove_from_lib(path, conn, curs):
    if not in_table(path, curs, 'library'):
        return;
    sqlstr = f"DELETE FROM library WHERE path='{path}';";
    curs.execute(sqlstr);
    
    pl_list = [];
    sqlstr = f"SELECT plname FROM pl_song WHERE path = '{path}';";
    for qq in curs.execute(sqlstr):
        pl_list.append(qq[0]);

    pl_all = "','".join(pl_list);
    sqlstr = f"DELETE FROM {pl_all} WHERE path='{path}';";
    curs.execute(sqlstr);

    sqlstr = f"DELETE FROM pl_song WHERE path = '{path}';";
    curs.execute(sqlstr);

    curs.commit();

    
def add_dir_to_lib(di, conn, curs):
    for root, subdirs, files in os.walk(di):
        for ff in files:
            path = os.path.join(root, ff);
            add_to_lib(path, conn, curs);


def init_lib(lib_dir, db_dir):
    if not os.path.isdir(lib_dir):
        sys.exit(f"{lib_dir} is not directory.");

    if not os.path.exists(db_dir):
        conn = sqlite3.connect(db_dir);
        curs = conn.cursor();
        curs.execute(f'''CREATE TABLE library
        (key INT PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, length REAL, bitrate INT, playcount INT);''');
        curs.execute(f"CREATE TABLE playlists (plname);");
        curs.execute(f"CREATE TABLE pl_song (path, plname);");
        conn.commit();
    else:
        conn = sqlite3.connect(db_dir);
        curs = conn.cursor();

    add_dir_to_lib(lib_dir, conn, curs);
    conn.close();
    

def list_playlists(curs):
    plout = [];
    for pl in curs.execute("SELECT plname FROM playlists;"):
        plout.append(pl[0]);

    return plout;

    
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Incorrect args.");

    lib_dir = sys.argv[1];
    db_dir = sys.argv[2];

    init_lib(lib_dir, db_dir);
