#!/usr/bin/python

import os
import socket

import keys

def main():
    if not os.path.exists(keys.SOCKET):
        print('', end='')
        return

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(keys.SOCKET)
            data = s.recv(1024)
            print(data.decode('utf-8'), end='')
        except:
            print('', end='')

if __name__ == '__main__':
    main()
