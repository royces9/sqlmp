import json
import os
import socket
import threading

import keys

def start_socket(disp):
    thread = threading.Thread(target=__socket, args=(disp,), daemon=True)
    thread.start()

def __socket(disp):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.bind(keys.SOCKET)
        s.listen()
                
        while True:
            conn, addr = s.accept()
            with conn:
                js = json.loads(json.dumps(disp.cur_song))
                js['status'] = format(disp.player.state)                
                js = json.dumps(js)
                conn.send(js.encode())

