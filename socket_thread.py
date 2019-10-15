import json
import os
import queue
import socket
import threading

import keys

import debug

class Remote:
    def __init__(self, disp):
        self.disp = disp
        self.queue = queue.Queue(0)
        self.thread = threading.Thread(target=self.__socket, daemon=True)
        self.thread.start()

    def __socket(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(keys.SOCKET)
            s.listen()
            
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data != b' \n\n ':
                        pl, fn = data.decode('utf-8').split('\n\n')
                        self.queue.put_nowait((pl.split('\n'), fn.split('\n')))
                        
                    js = json.loads(json.dumps(self.disp.cur_song))
                    js['status'] = format(self.disp.player.state)                
                    js = json.dumps(js)
                    conn.send(js.encode())

    def get(self):
        return self.queue.get_nowait()

    def empty(self):
        return self.queue.empty()
