import threading

import mainloop_event as me

from loadconf import config

import debug


def __inp(ui, inpq):
    while True:
        #if a command is running, this
        #blocks until it's done running
        ui.command_event.wait()

        #grab an event from player_ui
        key = ui.getevent()

        #ui.commands.inp is True if a command is being input
        #otherwise, check if it's a hotkey for something
        if ui.commands.inp:
            #command returns True when enter is pressed
            command = ui.handle_input(key)
            if command:
                inpq.put_nowait((me.from_command, command))

        elif key in ui.actions:
            inpq.put_nowait((me.from_ui, key))

            #clear command_event so the top of the loop blocks
            #to guarantee that ui.commands.inp is set to True
            if key in config.COMMAND:
                ui.command_event.clear()


def mainloop(ui, inpq):
    #start thread for grabbing input
    threading.Thread(target=__inp, args=(ui, inpq, ), daemon=True).start()

    while not ui.die:
        #check input queue for any new things to do
        item = inpq.get()

        #do something based off of type of item
        item[0](item, ui)
