import curses

import debug

class Keys:
    def __init__(self):
        #keep the string as a list so multibyte characters can be handled by index
        #lists are faster than unicode arrays for small sizes
        self.string = []

        #index of the cursor
        self.index = 0

        #dict of the special keymaps
        #everything else is printed
        self.funcs = {'\n': self.enter,
                      curses.KEY_BACKSPACE: self.backspace,
                      chr(1): self.ctrl_a,
                      chr(2): self.ctrl_b,
                      chr(4): self.ctrl_d,
                      chr(5): self.ctrl_e,
                      chr(6): self.ctrl_f,
                      chr(11): self.ctrl_k,
                      }

    def __contains__(self, key):
        return key in self.funcs

    def __getitem__(self, ind):
        return self.funcs[ind]

    def get_string(self):
        return ''.join(self.string)

    def reset(self):
        self.string = []
        self.index = 0

    def ctrl_a(self):
        """
        go to beginning
        """
        self.index = 0

    def ctrl_b(self):
        """
        move cursor back one
        """
        if self.index > 0:
            self.index -= 1
        
    def ctrl_d(self):
        """
        delete character at cursor
        """
        if self.index < len(self.string):
            self.string.pop(self.index)

    def ctrl_e(self):
        """
        go to end
        """
        self.index = len(self.string)

    def ctrl_f(self):
        """
        move cursor forward one
        """
        if self.index < len(self.string):
            self.index += 1

    def ctrl_k(self):
        """
        kill everything on and past the cursor
        """
        self.string = self.string[0:self.index]
        
    def add(self, key):
        self.string.insert(self.index, key)
        self.index += 1

    def backspace(self):
        if self.index != 0:
            self.string.pop(self.index - 1)
            self.index -= 1
        else:
            return True

    def enter(self):
        return True
