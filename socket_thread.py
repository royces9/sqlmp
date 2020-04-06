import json
import queue
import os
import socket
import threading

import debug

class Remote(queue.Queue):
    def __init__(self, disp, socket):
        super().__init__()
        self.disp = disp
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
                        self.put_nowait((pl.split('\n'), fn.split('\n')))

                    js = json.loads(json.dumps(self.disp.cur_song))
                    js['status'] = format(self.disp.player.state)
                    js = json.dumps(js)
                    conn.send(js.encode())

    def add_item(self, item):
        pl, fn = item
        for p in pl:
            for f in fn:
                self.disp.add((f, p))
                """
                if os.path.isdir(f):
                    self.disp.adddir((f, p))
                else:
                    self.disp.addfile((f, p))
                """
