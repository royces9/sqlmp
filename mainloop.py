import curses
import threading

import socket_thread

from loadconf import config

def __inp(ui, qq):
    while True:
        ui.command_event.wait()

        key = ui.stdscr.get_wch()
        if ui.inp:
            command = ui.handle_input(key)
            if command:
                qq.put_nowait((3, command))
        elif key in ui.actions:
            qq.put_nowait((2, key))

            if key in config.COMMAND:
                ui.command_event.clear()


def mainloop(ui):
    remote = socket_thread.Remote(ui, config.SOCKET)

    threading.Thread(target=__inp, args=(ui, remote, ), daemon=True).start()

    while not ui.die:
        #this call blocks
        item = remote.get()

        if item[0] == 1:
            #from remote
            remote.add_item(item[1:])
        elif item[0] == 2:
            #from key press
            ui.actions[item[1]]()
        elif item[0] == 3:
            #from command
            ui.commands.exe(item[1])
            ui.keys.reset()
            ui.inp = False
            curses.curs_set(0)
            ui.textwin.print_blank(0)


            
