# sqlmp
Pet project using sqlite database backend and curses frontend for a music player.
Similar to cmus since I like how cmus works

### Dependencies:
ffmpeg-python

PortAudio

libsndfile

### Use:
##### initlib.py:
Use this when starting, initializes the database with your music library and playlists

##### remote.py:
Allows one to add songs to a playlist through the shell

##### sqlmp:
The actual player

======
#### List of commands:

Many commands also have optional arguments, marked by `Opt`

------
##### `add <arg> Opt<playlist>`
Adds `arg` to the currently highlighted playlist
or a playlist given as a second argument.
Can be either a file or directory.

------
##### `delpl Opt<playlist>`
Delete the currently highlighted playlist, or a playlist
given as a second argument.

------
##### `export <directory> Opt<playlist>`
List the files of the currently highlighted playlist, or a playlist given
as a second argument, to a textfile in `directory`.

------
##### `export-all <directory>`
Same as export, except for all playlists.

------
##### `find <term> Opt<key>`
Find the first occurring exact instance of `term` in the currently highlighted playlist's sort key and
go to it, other keys can be used by supplying a second argument.
Running `find` again without arguments will go to the next instance.

------
##### `newpl <name> Opt<file>`
Make a new blank playlist named `name`, contents can be added from file on creation by supplying
a name of a file with paths to music files.

------
##### `playmode <mode>`
Change the playmode of the currently highlighted playlist to one of the following modes:
shuffle, inorder, single

------
##### `renamepl <name> Opt<playlist>`
Rename the currently highlighted playlist to `name`,
or rename a playlist given as a second argument

------
##### `sort <key>`
Sort the currently highlighted playlist by `key`

------
##### `update-single Opt<<tag> <value>>`
No arguments: Update the currently selected song's metadata with its corresponding file
(for when the file is updated externally after it has been updated to the database).
This does not change the actual file's metadata.

Two arguments: Update the currently selected song's `tag` to `value` in the database.
This does not change the actual file's metadata.