import curses
import os
import shlex
import threading

import keys
import menu
import playlist
import song
from loadconf import config

import debug

class Error_msg:
    def __init__(self, ui, timer, frame_time, exe, args):
        self.exe = exe
        self.args = args
        self.timer = timer
        self.count = int(self.timer / frame_time)
        self.total = 0
        
    def check(self):
        if self.total:
            self.total += 1
            if self.total >= self.count:
                self.total = 0
                self.exe(*self.args)

    def set(self):
        self.total = 1

class Commands:
    def __init__(self, ui):
        self.ui = ui
        self.textwin = self.ui.textwin

        #typed commands
        self.commands = {
            'add': self.add,
            'delpl': self.delpl,
            'export': self.export,
            'export-all': self.export_all,
            'find': self.find,
            'newpl': self.newpl,
            'playmode': self.playmode,
            'renamepl': self.renamepl,
            'sort': self.sort,
            'update': self.update,
            'update-single': self.update_single
        }

        self.err = Error_msg(self.ui, 2, self.ui.frame_time, self.textwin.print_blank, (1,))
        self.find_list = None


        #handles input for typed commands
        self.keys = keys.Keys()
        #flag to decide if command is getting entered
        self.inp = False

        self.command_event = threading.Event()
        self.command_event.set()


    def __getitem__(self, ind):
        return self.ui[ind]


    def err_print(self, err):
        self.textwin.print_blank(1)
        self.textwin.print_line(err, y=1)
        self.err.set()


    def from_command(self, command):
        curses.curs_set(0)
        self.textwin.print_blank(0)
        self.inp = False
        self.exe(command)
        self.keys.reset()
        

    def prepare_command(self, arg=None):
        """
        prepare input loop to handle command input
        when config.COMMAND key is pressed
        """

        self.textwin.print_blank(0)
        self.textwin.win.addch(0, 0, ':')
        curses.curs_set(2)

        self.inp = True
        self.command_event.set()

    def exe(self, inp):
        """
        executes the actual command from handle_input
        """
        try:
            spl = shlex.split(inp)
        except:
            self.err_print('Mismatched quotations.')
            self.command_event.set()
            return

        if not spl:
            self.err_print("")
        elif spl[0] in self.commands:
            self.err_print("")
            self.commands[spl[0]](spl[1:])
        else:
            self.err_print('Invalid command: ' + spl[0])

        self.command_event.set()


    def add(self, args):
        """
        add a directory or file to a playlist
        1 arg : add arg to highlighted playlist
        2 args: add arg to named playlist
        """

        if not args:
            self.err_print('One argument required')
            return

        if len(args) == 1:
            pl = self.ui.leftwin.highlighted().data
        else:
            ind = self.pl_exists(args[1])
            if ind < 0:
                return

            pl = self.ui.leftwin.data[ind].data

        newitem = args[0]
        if os.path.isfile(newitem):
            pl.insert(newitem)
        elif os.path.isdir(newitem):
            pl.insert_dir(newitem)

        self.ui.rightwin.disp()


    def delpl(self, args):
        """
        delete a playlist
        0 args: delete highlighted playlist
        1 arg : delete the named playlist
        """
        if not args:
            pl = self.ui.leftwin.highlighted()
            plname = pl.data.name
        else:
            plname = args[0]
            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(plname))
                return

            pl = self.ui.leftwin.data[ind]

        self.ui.leftwin.delete(pl)
        playlist.Playlist.del_pl(plname, self.ui.db)


    def export(self, args):
        """
        export a playlist
        1 args: export highlighted playlist to directory
        2 args: export the named playlist to directory
        """
        if not args:
            self.err_print('One argument required')
            return
        elif len(args) == 1:
            pl = self.ui.leftwin.highlighted().data
            plname = pl.name
            dest = args[0]
        else:
            plname = args[0]
            dest = args[1]

            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(plname))
                return

            pl = self.ui.leftwin.data[ind].data

        if not os.path.exists(dest):
            self.err_print('Directory "{}" doesn\'t exist'.format(dest))
            return

        with open('/'.join([dest, plname]), 'w+') as fp:
            for d in pl.data:
                print(d['path'], file=fp)


    def export_all(self, args):
        if not args:
            self.err_print('One argument required')
            return
        elif len(args) == 1:
            dest = args[0]
            for pl in self.ui.leftwin:
                self.export((pl.data.name, dest))

    def find(self, args):
        """
        find a song with the matching arguments
        1 args: jump to the first song that matches the arg by the current sorting key
        2 args: jump to the first song that matches the arg by the given key
        """
        curpl = self.ui.leftwin.highlighted().data
        if not args:
            if not self.find_list:
                self.err_print('At least one argument required')
                return
        else:
            term = args[0]
            if len(args) == 1:
                key = curpl.sort_key
            elif len(args) > 1:
                key = args[1]
                if key not in song.tags:
                    self.err_print('Invalid key: ' + key)
                    return

            self.find_list = (ii for ii, item in enumerate(curpl.data) if item[key] == term)

        try:
            ind = next(self.find_list)
        except StopIteration:
            self.err_print('Not found.')
            return

        self.ui.jump_to_ind(ind, len(curpl.data), self.ui.rightwin)

        self.ui.switch_view_right()


    def newpl(self, args):
        """
        makes a new playlist
        1 arg : blank playlist with given name
        2 args: playlist with given name and contents given by file argument
        """
        if not args:
            self.err_print('One argument required')
            return
        elif len(args) == 1:
            plname = args[0]

            if self.pl_exists(plname) >= 0:
                self.err_print('Playlist "{}" already exists'.format(plname))
                return

            playlist.Playlist.init_pl(plname, self.ui.db)
            newpl = menu.Music_menu(win=self.ui.rightwin.win,
                                    data=playlist.Playlist(name=plname, db=self.ui.db),
                                    form=config.SONG_DISP,
                                    palette=self.ui.palette[0], ui=self)
        else:
            plname = args[0]
            plfile = args[1]
            if not os.path.isfile(plfile):
                self.err_print('File does not exist: {}.'.format(plfile))
                return

            if self.pl_exists(plname) >= 0:
                self.err_print('Playlist "{}" already exists'.format(plname))
                return

            playlist.init_pl(plname, self.ui.db)
            newpl = menu.Menu(win=self.ui.rightwin.win,
                              data=playlist.Playlist(name=plname, db=self.ui.db),
                              form=config.SONG_DISP,
                              cursor_colour=config.CURSOR[0],
                              highlight_colour=config.HIGHLIGHT_COLOUR[0],
                              normal_colour=config.NORMAL[0])

            newpl.insert_from_file(plfile)

        self.ui.leftwin.insert(newpl)
        self.ui.leftwin.disp()


    def playmode(self, args):
        """
        change the playmode (shuffle, in order, single)
        """
        if not args:
            self.err_print('One argument required')
            return

        playmode = args[0]
        cur = self.ui.leftwin.highlighted().data
        if playmode in cur.playmode_list:
            cur.change_playmode(playmode)
        else:
            self.err_print('"{}" is not a valid playback mode'.format(playmode))


    def renamepl(self, args):
        """
        rename a playlist
        1 arg : rename highlighted playlist
        2 args: rename the named playlist
        """
        if not args:
            self.err_print('One argument required')
            return
        elif len(args) == 1:
            ind = self.ui.leftwin.highlighted_ind()
            newname = args[0]
        else:
            curname = args[0]
            newname = args[1]
            ind = self.pl_exists(curname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(curname))
                return

        self.ui.leftwin.data[ind].data.rename(newname)
        self.ui.leftwin.disp()


    def sort(self, args):
        """
        sort the playlist according to some key
        changes are saved to the db
        """
        if not args:
            self.err_print('One argument required')
            return

        _key = args[0]
        cur = self.ui.leftwin.highlighted().data
        if _key in song.tags:
            cur.change_sort(_key)
            self.ui.rightwin.disp()
        else:
            self.err_print('"{}" is not a valid key to sort by'.format(_key))


    def update(self, args):
        """
        update db
        """
        self.ui.db.update_db()


    def update_single(self, args):
        """
        update selected entry
        args[0]: the tag to change
        args[1]: the new value for the tag
        """
        if len(args) < 2:
            self.err_print('Two arguments required')
            return
            
        tag = args[0]
        value = args[1]
        if tag not in song.tags:
            self.err_print('Invalid key: ' + key)
            return

        cursong = self.ui.rightwin.highlighted()
        cursong[tag] = value
        self.ui.db.update_song(cursong)


    def pl_exists(self, name):
        """
        check if pl exists and return its index in list
        """
        for i, d in enumerate(self.ui.leftwin.data):
            if d.data.name == name:
                return i

        return -1
 
