import copy
import json
import socket
import threading

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
                    data = conn.recv(1024)
                    if data != b' \n\n ':
                        flag, *args = data.decode('utf-8').split('\n\n')
                        if flag == 'pl_add':
                            self.ui.inp.put_nowait((self.pl_add, (args[0].split('\n'), args[1].split('\n'),)))
                        elif flag == 'pause':
                            self.ui.inp.put_nowait((self.ui.player.pause, (None,)))
                        elif flag == 'play-pause':
                            self.ui.inp.put_nowait((self.ui.player.play_pause, (None,)))


                    else:
                        js = copy.copy(self.ui.player.cur_song.dict())
                        js['status'] = format(self.ui.player.state)
                        conn.send(json.dumps(js).encode())

    def pl_add(self, pl, fn):
        for p in pl:
            for f in fn:
                out = self.ui.commands.add((f, p))
        

        
