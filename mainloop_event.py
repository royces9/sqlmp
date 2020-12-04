#anything from an external process
#there's only one possible action right now
#so this function is simple
def from_remote(item, ui):
    pl, fn = item[1:]
    for p in pl:
        for f in fn:
            ui.commands.add((f, p))


#event from player_ui
#includes key presses and playback changes
def from_ui(item, ui):
    ui.actions[item[1]]()

#any typed commands that are not single key presses
def from_command(item, ui):
    curses.curs_set(0)
    ui.textwin.print_blank(0)
    ui.commands.inp = False

    ui.commands.exe(item[1])
    ui.keys.reset()
