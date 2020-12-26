import curses
import queue
import threading

import debug
import wchar

from loadconf import config

class Input(queue.Queue):
    def __init__(self, ui):
        super().__init__(0)
        self.ui = ui
        self.commands = self.ui.commands
        self.keys = self.commands.keys
        
        threading.Thread(target=self.__input_loop, daemon=True).start()

    def exe(self):
        #check input queue for stuff to do
        func, args = self.get()
        
        #execute item in queue
        func(*args)

    def get_key(self):
        key = self.ui.stdscr.get_wch()

        return key

    def handle_input(self, key):
        if key in self.keys:
            if self.keys[key]():
                return self.keys.get_string()
        else:
             self.keys.add(key)

        self.__print_typing()

    def __print_typing(self):
        tw = self.ui.textwin

        tmp = self.keys.get_string()
        tw.print_blank(x=1, y=0)
        tw.win.addnstr(0, 1, wchar.set_width(tmp, tw.w - 1), tw.w - 1)
        wid, _ = wchar.wcswidth(tmp[:self.keys.index])
        if wid + 1 < tw.w:
            tw.win.move(0, wid + 1)

    def __input_loop(self):
        while True:
            self.commands.command_event.wait()

            key = self.get_key()

            if key and self.commands.inp:
                command = self.handle_input(key)
                if command != None:
                    self.put_nowait((self.commands.from_command, (command,)))
            elif key in self.ui.actions:
                self.put_nowait((self.ui.actions[key], (None,)))

                if key in config.COMMAND:
                    self.commands.command_event.clear()
