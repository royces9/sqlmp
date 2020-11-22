import curses
import threading

import socket_thread

from loadconf import config

import debug


def __inp(ui, qq):
    while True:
        ui.command_event.wait()

        key = ui.stdscr.get_wch()
        debug.debug(key)
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

    event_dict = {1: from_remote,
                   2: from_key_press,
                   3: from_command,
                   }
    
    while not ui.die:
        #this call blocks
        item = remote.get()

        #do something based off of type of item
        event_dict[item[0]](item, ui, remote)


def from_remote(item, _, remote):
    remote.add_item(item[1:])

def from_key_press(item, ui, _):
    ui.actions[item[1]]()

def from_command(item, ui, _):
    curses.curs_set(0)
    ui.textwin.print_blank(0)
    ui.inp = False

    ui.commands.exe(item[1])
    ui.keys.reset()


