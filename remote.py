import copy
import json
import socket
import threading

import remote_json as rj
import debug

class Remote:
    def __init__(self, ui, socket):
        super().__init__()
        self.ui = ui
        self.socket = socket
        threading.Thread(target=self.__socket, daemon=True).start()

    def __socket(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(self.socket)
            s.listen()

            while True:
                conn, _ = s.accept()
                with conn:
                    msg = rj.recv(conn)
                    cmd = msg['cmd']

                    if cmd == 'pl_add':
                        self.ui.inp.put_nowait((self.pl_add, msg['playlist'], msg['file']))
                    elif cmd == 'pause':
                        self.ui.inp.put_nowait((self.ui.player.pause,))
                    elif cmd == 'play-pause':
                        self.ui.inp.put_nowait((self.ui.player.play_pause,))
                    else:
                        js = copy.copy(self.ui.player.cur_song.dict())
                        js['status'] = format(self.ui.player.state)
                        rj.send(conn, js)


    def pl_add(self, pl, fn):
        for p in pl:
            for f in fn:
                out = self.ui.commands.add((f, p))
        

        
