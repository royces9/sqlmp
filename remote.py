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
        self.thread = threading.Thread(target=self.__socket, daemon=True)
        self.thread.start()


    def __socket(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(self.socket)
            s.listen()

            while True:
                conn, _ = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data != b' \n\n ':
                        pl, fn = data.decode('utf-8').split('\n\n')
                        self.ui.inpq.put_nowait((self.from_remote, (pl.split('\n'), fn.split('\n'),)))

                    js = copy.copy(self.ui.cur_song.dict())
                    js['status'] = format(self.ui.player.state)
                    conn.send(json.dumps(js).encode())

    def from_remote(self, pl, fn):
        for p in pl:
            for f in fn:
                self.ui.commands.add((f, p))
