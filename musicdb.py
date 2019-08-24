import os

import sqlite3
import mutagen


ext_list = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}
key_list = ['title',
            'artist',
            'album',
]
attr_list = ['length',
             'bitrate',
]


class Musicdb:
    def __init__(self, path):
        #assume that the db exists
        self.path = path

        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()


    #only check library, not anything else like playlists
    def __contains__(self, path):
        path = path.replace("'", "''")
        self.exe(f"SELECT path FROM library WHERE path='{path}' LIMIT 1;")
        return True if self.curs.fetchone() else False

    def __def__(self):
        self.conn.close()

    def exe(self, query):
        return self.curs.execute(query)


    def commit(self):
        self.conn.commit()
    
    def in_table(path, table):
        path = path.replace("'", "''")
        self.exe(f"SELECT path FROM {table} WHERE path='{path}' LIMIT 1;")
        return True if self.curs.fetchone() else False


    def extract_metadata(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in ext_list:
            return None

        try:
            out = mutagen.File(path, easy=True)
        except:
            return None

        if not out:
            return None

        song_dict = {}
        for key in key_list:
            if key in out.keys():
                song_dict[key] = out[key][0].replace("'", "''")
            else:
                song_dict[key] = ""

        attr_out = {}
        if hasattr(out, 'info'):
            for attr in attr_list:
                attr_out[attr] = getattr(out.info, attr) if hasattr(out.info, attr) else 0
        else:
            for attr in attr_list:
                attr_out[attr] = 0;
                    
        return (song_dict.values(), attr_out.values());


    def add_to_lib(self, path):
        if path in self:
            return

        out = self.extract_metadata(path)
        if not out:
            return
        ((title, artist, album), (length, bitrate)) = out
        
        path = path.replace("'", "''")

        self.exe(f"INSERT INTO library VALUES ('{path}','{title}','{artist}','{album}',{length},{bitrate},0);")
        self.commit();

        
    def remove_from_lib(path):
        if path not in self:
            return

        self.exe(f"DELETE FROM library WHERE path='{path}';")
        pl_all = "','".join([qq[0] for qq in self.exe(f"SELECT plname FROM pl_song WHERE path='{path}';")])

        self.exe(f"DELETE FROM {pl_all} WHERE path='{path}';")
        self.exe(f"DELETE FROM pl_song WHERE path='{path}';")
        self.commit()
        

    def add_dir(self, di):
        list_all = []
        for root, subdirs, files in os.walk(di):
            for ff in files:
                path = os.path.join(root, ff);
                path = path.replace("'", "''")
                if path not in self:
                    out = self.extract_metadata(path)
                    if out:
                        ((title, artist, album), (length, bitrate)) = out
                        list_all.append(f"('{path}', '{title}', '{artist}', '{album}', {length}, {bitrate}, 0)")
                

        joined = ",".join(list_all)
        self.exe(f"INSERT INTO library VALUES {joined}")
        self.commit()

                                
    def list_pl(self):
        return [pl[0] for pl in self.exe("SELECT plname FROM playlists;")]
