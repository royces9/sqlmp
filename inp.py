import curses
import queue
import threading

import wchar

import config
import debug

class Input(queue.Queue):
    def __init__(self, ui):
        super().__init__(0)
        self.ui = ui
        self.commands = self.ui.commands
        self.keys = self.commands.keys
        
        self.actions = self.__init_actions()
        threading.Thread(target=self.__input_loop, daemon=True).start()

        
    def __init_actions(self):
        ui = self.ui
        actions = {}
        pairs = [
            [config.UP, ui.up],
            [config.DOWN, ui.down],
            [config.LEFT, ui.player.seek_backward],
            [config.RIGHT, ui.player.seek_forward],
            [config.VOLUP, ui.player.vol_up],
            [config.VOLDOWN, ui.player.vol_down],
            [config.MUTE, ui.mute],
            [config.PLAYPAUSE, ui.player.play_pause],
            [config.QUIT, ui.set_die],
            [config.SWITCH, ui.switch_view],
            [config.COMMAND, ui.commands.prepare_command],
            [config.SELECT, ui.select],
            [config.HIGHLIGHT, ui.highlight],
            [config.TRANSFER, ui.transfer],
            [config.DELETE, ui.delete],
            [config.CUR_PLAY, ui.jump_cur_play],
            [config.JUMP_UP, ui.jump_up],
            [config.JUMP_DOWN, ui.jump_down],
            [{curses.KEY_RESIZE}, ui.resize],
        ]

        for key, val in pairs:
            actions.update(dict.fromkeys(key, val))

        return actions
        

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
        elif isinstance(key, str):
            self.keys.add(key)

        self.__print_typing()

    def __print_typing(self):
        tw = self.ui.textwin

        tmp = self.keys.get_string()
        tw.print_blank(x=1, y=0) 
        tw.win.addnstr(0, 1, wchar.set_width(tmp, tw.w - 1), tw.w - 1)
        wid, _ = wchar.wcswidth(tmp[:self.keys.index])
        wid += 1
        tw.win.chgat(0, wid, 1, curses.A_STANDOUT)

        if wid < tw.w:
            tw.win.move(0, wid)

    def __input_loop(self):
        while True:
            self.commands.command_event.wait()

            key = self.get_key()
            if key and self.commands.inp:
                command = self.handle_input(key)
                if command != None:
                    self.put_nowait((self.commands.from_command, (command,)))
            elif key in self.actions:
                self.put_nowait((self.actions[key], (None,)))
                
                if key in config.COMMAND:
                    self.commands.command_event.clear()
