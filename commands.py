import os
import shlex
import threading

import menu
import player_ui
import playlist
import config

class Commands:
    def __init__(self, ui):
        self.ui = ui
        
        #typed commands
        self.commands = {
            'add': self.add,
            'delpl': self.delpl,
            'export': self.export,
            'export_all': self.export_all,
            'find': self.find, 
            'newpl': self.newpl,
            'playmode': self.playmode,
            'renamepl': self.renamepl,
            'sort': self.sort,
            'update': self.update,
        }

        self.find_list = None
        self.command_event = threading.Event()
        self.command_event.set()


    def __getitem__(self, ind):
        return self.ui[ind]


    def err_print(self, err):
        self[2].print_blank(3)
        self[2].print_line(err, y=3)


    def exe(self, inp):
        """
        executes the actual command from grab_inp
        """
        try:
            spl = shlex.split(inp)
        except:
            self.err_print('Mismatched quotations.')
            self.command.set()
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
            pl = self[0].highlighted().data
        else:
            ind = self.pl_exists(args[1])
            if ind < 0:
                return

            pl = self[0].data[ind].data

        newitem = args[0]
        if os.path.isfile(newitem):
            pl.insert(newitem)
        elif os.path.isdir(newitem):
            pl.insert_dir(newitem)

        self[1].disp()


    def delpl(self, args):
        """
        delete a playlist
        0 args: delete highlighted playlist
        1 arg : delete the named playlist
        """
        if not args:
            pl = self[0].highlighted()
            plname = pl.data.name
        else:
            plname = args[0]
            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(plname))
                return

            pl = self[0].data[ind]

        self[0].delete(pl)
        playlist.Playlist.del_pl(plname, self.ui.db)

        self.ui.draw()

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
            pl = self[0].highlighted().data
            plname = pl.name
            dest = args[0]
        else:
            plname = args[0]
            dest = args[1]

            ind = self.pl_exists(plname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(plname))
                return

            pl = self[0].data[ind].data

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
            for pl in self[0]:
                self.export((pl.name, dest))

    def find(self, args):
        """
        find a song with the matching arguments
        1 args: jump to the first song that matches the arg by the current sorting key
        2 args: jump to the first song that matches the arg by the given key
        """
        curpl = self[0].highlighted().data
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
                if key not in curpl.tags:
                    self.err_print('Invalid key: ' + key)
                    return

            self.find_list = (ii for ii, item in enumerate(curpl.data) if item[key] == term)

        try:
            ind = next(self.find_list)
        except StopIteration:
            self.err_print('Not found.')
            return

        self.ui.jump_to_ind(ind, len(curpl.data), 1)

        self.ui.switch_view_right()
        self.ui.draw()


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
            newpl = menu.Menu(win=self[1].win,
                              data=playlist.Playlist(name=plname, db=self.ui.db),
                              form=config.SONG_DISP,
                              cursor_colour=config.CURSOR[0],
                              highlight_colour=config.HIGHLIGHT_COLOUR[0],
                              normal_colour=config.NORMAL[0])
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
            newpl = menu.Menu(win=self[1].win,
                              data=playlist.Playlist(name=plname, db=self.ui.db),
                              form=config.SONG_DISP,
                              cursor_colour=config.CURSOR[0],
                              highlight_colour=config.HIGHLIGHT_COLOUR[0],
                              normal_colour=config.NORMAL[0])

            newpl.insert_from_file(plfile)

        self[0].insert(newpl)
        self[0].disp()


    def playmode(self, args):
        """
        change the playmode (shuffle, in order, single)
        """
        if not args:
            self.err_print('One argument required')
            return

        playmode = args[0]
        cur = self[0].highlighted().data
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
            ind = self[0].highlighted_ind()
            newname = args[0]
        else:
            curname = args[0]
            newname = args[1]
            ind = self.pl_exists(curname)

            if ind < 0:
                self.err_print('Playlist "{}" doesn\'t exist'.format(curname))
                return

        self[0].data[ind].data.rename(newname)
        self[0].disp()


    def sort(self, args):
        """
        sort the playlist according to some key
        changes are saved to the db
        """
        if not args:
            self.err_print('One argument required')
            return

        _key = args[0]
        cur = self[0].highlighted().data
        if _key in cur.tags:
            cur.change_sort(_key)
            self[1].disp()
        else:
            self.err_print('"{}" is not a valid key to sort by'.format(_key))


    def update(self, args):
        """
        update db
        """
        self.ui.db.update_db()


    def pl_exists(self, name):
        """                                                                                                            
        check if pl exists and return its index in list                                                                
        """
        for i, d in enumerate(self[0].data):
            if d.data.name == name:
                return i

        return -1