import debug

#anything from an external process
#there's only one possible action right now
#so this function is simple
def from_remote(item, ui):
    pl, fn = item[1:]
    for p in pl:
        for f in fn:
            ui.commands.add((f, p))
