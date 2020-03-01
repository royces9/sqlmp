# sqlmp
Pet project using sqlite database backend and curses frontend for a music player.
Similar to cmus since I like how cmus works

### Dependencies:
ffmpeg-python

PyAudio

### Use:
##### initlib.py:
Use this when starting, initializes the database with your music library and playlists

##### remote.py:
Allows one to add songs to a playlist through the shell

##### sqlmp.py:
The actual player

#### List of commands:

Many commands also have optional arguments, marked by `Opt`

##### `adddir <directory> Opt<playlist>`
Adds `directory` to the currently highlighted playlist
or a playlist given as a second argument.

##### `addfile <filename> Opt<playlist>`
Add `filename` to the currently highlighted playlist
or a playlist given as a second argument.

##### `delpl Opt<playlist>`
Delete the currently highlighted playlist, or a playlist
given as a second argument.

##### `export <directory> Opt<playlist>`
Copy the files in the currently highlighted playlist, or to a playlist given
as a second argument to `directory`.

##### `find <term> Opt<key>`
Find the first occurring exact instance of `term` in the currently highlighted playlist's sort key and
go to it, other keys can be used by supplying a second argument

##### `newpl <name> Opt<file>`
Make a new blank playlist named `name`, contents can be added from file on creation by supplying
a name of a file with paths to music files

##### `playmode <mode>`
Change the playmode of the currently highlighted playlist to one of the following modes:
shuffle, inorder, single

##### `renamepl <name> Opt<playlist>`
Rename the currently highlighted playlist to `name`,
or rename a playlist given as a second argument

##### `sort <key>`
Sort the currently highlighted playlist by `key`