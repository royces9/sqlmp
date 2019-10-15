#!/usr/bin/python

import os
import socket
import sys

import keys

def parse_args(argv):
    if not argv[0].startswith('-'):
        return '', ''

    args = []
    for arg in argv:
        if arg.startswith('-'):
            args.append([arg])
        else:
            args[-1].append(arg)

    pl = ''
    fn = ''

    for arg in args:
        if arg[0] == '-p':
            #playlist
            pl = [p for p in arg[1:]]
        elif arg[0] == '-f':
            #files or dir
            fn = [f for f in arg[1:]]
        else:
            break

    return pl, fn

def main():
    if not os.path.exists(keys.SOCKET):
        print('', end='')
        return

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(keys.SOCKET)
        if len(sys.argv) > 1:
            pl, fn = parse_args(sys.argv[1:])
            s.send('\n'.join(pl).encode())
            s.send(b'\n\n')
            s.send('\n'.join(fn).encode())
            s.send(b'\n')
            s.recv(1024)

        else:
            s.send(b' \n\n ')
            data = s.recv(1024)
            print(data.decode('utf-8'), end='')

if __name__ == '__main__':
    main()
