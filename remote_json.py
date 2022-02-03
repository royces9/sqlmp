import json
import debug

__packet_size = 4096

def send(conn, data):
    conn.send(json.dumps(data, ensure_ascii=False).encode())

def recv(conn):
    return json.loads(conn.recv(__packet_size))

def recv_raw(conn):
    return conn.recv(__packet_size)
