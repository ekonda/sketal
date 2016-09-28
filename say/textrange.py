"""
A range of say.text.Text lines that can be edited on their own,
effecting the underlying lines. If the underlying text object
changes (especially changing the number of lines somewhere
before or overlapping whether the text range lies), TextRange
will probably become confused. However, edits made through the
TextRange are completely fine.
"""

# TextRange shows the difficulty of 'sub object' references in
# Python. On the one hand, if t is a Text object, t[1:4] should
# return a list of strings for those lines. OTOH, maybe it should
# return an abstracted TextRange object. But then if the underlying
# Text object changes, how to have the TextRange then adjust? I.e.
# if a few lines are prepended to t, shouldn't the text range still
# refer to the new lines, albeit at a higher index range? Building
# this invovles dependencies, and Text knowing about TextRange, and
# vice versa. For the meanwhile, lacking a generalized dependency
# mechanism (not to mention a generalized lvalue mechanism),
# just going to make TextRange be static.

# Also note how TextRange is not really a subclass of Text, though
# logically it could, or should, or sorta wants to be. But even if
# it were, we'd still have to do lots of the copy-paste-modify
# style of programming here.

# For further investigation:
# http://pypi.python.org/pypi/Cellulose

from say import Text
import inspect
import sys
import re
from simplere import Re
from .util import *
from codecs import open


class TextRange(object):
    def __init__(self, text=None, start=None, stop=None):
        """
        Create a TextRange object on the given text, over the given range.
        Just as with Python list specifications, the stop value should be
        one more than the last index.
        """
        self._text = text
        if stop is None:
            stop = len(text)
        elif stop < 0:
            stop = len(text) + stop
        if start is None:
            start = 0
        elif start < 0:
            start = len(text) + start
        self._indices = slice(start, stop)

    def __iadd__(self, data):
        """
        In-place add the text or lines contained in data, with auto-dedent.
        """
        caller = inspect.currentframe().f_back
        self._insert(self._indices.stop, data,
                     caller, interpolate=True, dedent=True)
        return self

    def __ior__(self, data):
        """
        In-place add the text or lines contained in data, with NO auto-dedent.
        """
        caller = inspect.currentframe().f_back
        self._insert(self._indices.stop, data,
                     caller, interpolate=True, dedent=False)
        return self

    def __iand__(self, data):
        """
        In-place add the text or lines contained in data, with NO auto-dedent
        and NO iterpolation.
        """
        self._insert(self._indices.stop, data,
                     None, interpolate=False, dedent=False)
        return self

    def append(self, data, caller=None, interpolate=True):
        caller = caller or inspect.currentframe().f_back if interpolate else None
        self._insert(self._indices.stop, data, caller=caller, interpolate=interpolate)

    def extend(self, data, caller=None, interpolate=True, dedent=True):
        caller = caller or inspect.currentframe().f_back if interpolate else None
        self._insert(self._indices.stop, data, caller, interpolate, dedent)

    def _base_index(self, n):
        """
        Check to the given index n to ensure it's within the range of lines.
        """
        index = self._indices.start + n if n >= 0 else self._indices.stop + n
        if self._indices.start <= index < self._indices.stop:
            return index
        raise IndexError('index {0} ({1} in underlying Text) out of range'.format(n, index))

    def _insert(self, n, data, caller=None, interpolate=True, dedent=True):
        """
        Insert into the underlying Text at a point relative to the underlying text indices.
        """
        newlines = self._data_to_lines(data)
        caller = caller or inspect.currentframe().f_back if interpolate else None
        self._text.insert(n, newlines, caller, interpolate, dedent)
        self._adjust_indices(newlines, replacing=False)

    def insert(self, n, data, caller=None, interpolate=True, dedent=True):
        """
        Insert into the underlying Text at a point relative to the TextRange's
        indices.
        """
        caller = caller or inspect.currentframe().f_back if interpolate else None
        self._insert(self._indices.start + n, data, caller, interpolate, dedent)

    def __getitem__(self, n):
        index = self._base_index(n)
        return self._text._lines[index]

    def __setitem__(self, n, value):
        index = self._base_index(n)
        self._text._lines[index] = value.rstrip('\n')

    # FIXME: get and set item do no interpolation - is that ok?

    def __len__(self):
        return self._indices.stop - self._indices.start

    def __iter__(self):
        return iter(self._text._lines[self._indices])

    def _data_to_lines(self, data):
        if isinstance(data, list):
            return [line.rstrip('\n') for line in data]
        else:
            return data.splitlines()

    @property
    def text(self):
        return '\n'.join(self._text._lines[self._indices])

    @text.setter
    def text(self, data):
        newlines = self._data_to_lines(data)
        self._text._lines[self._indices] = newlines
        self._adjust_indices(newlines)

    def _adjust_indices(self, newlines, replacing=True):
        """
        If a TextRange is modified, we adjust ._indices to reflect the length
        of the new text. If replacing, assume the new lines replace the given
        text range; if not replacing, adding to the text range.
        """
        newlen = len(newlines)
        newstop = self._indices.start + newlen if replacing else self._indices.stop + newlen
        if self._indices.stop != newstop:
            self._indices = slice(self._indices.start, newstop)

    @property
    def lines(self):
        return self._text._lines[self._indices]

    @lines.setter
    def lines(self, newlines):
        newlines = [line.rstrip('\n') for line in newlines]
        self._text._lines[self._indices] = newlines
        self._adjust_indices(newlines)

    def __str__(self):
        return self.text

    def __repr__(self):
        return 'TextRange({0}, {1}:{2} of {3})'.format(id(self),
                                                       self._indices.start, self._indices.stop, id(self._text))

    def replace(self, target, replacement=None):
        """
        Replace all instances of the target string with the replacement string.
        Works in situ, contra str.replace().
        """
        if target and isinstance(target, dict) and replacement is None:
            for (targ, repl) in target.items():
                self.replace(targ, repl)
        else:
            for i, line in enumerate(self._text._lines[self._indices], start=self._indices.start):
                self._text._lines[i] = line.replace(target, replacement)

                # TODO: should lines be recalibrated, if there are any \n in
                # replacement?

    def re_replace(self, target, replacement):
        """
        Regular expression replacement. Target is either compiled re object or
        string that will be compiled into one. Replacement is either string or
        function that takes re match object as a parameter and returns replacement
        string. Intead of Python's stock ``_sre.SRE_Match`` objects, returns a
        ``ReMatch``, which adds the ability to directly access via indices
        """
        target = Re(target) if not isinstance(target, Re) else target
        for i, line in enumerate(self._text._lines[self._indices], start=self._indices.start):
            self._text._lines[i] = target.sub(replacement, line)

    def read_from(self, filepath, interpolate=True, dedent=True, encoding='utf-8'):
        """
        Reads lines from the designated file, appending them to the end of the
        given TextRange. By default, interpolates and dedents any {}
        expressions.
        """
        lines = open(filepath, encoding=encoding).read().splitlines()
        caller = inspect.currentframe().f_back
        self.extend(lines, caller, interpolate=interpolate, dedent=dedent)
        return self

    def write_to(self, filepath, append=True, encoding='utf-8'):
        mode = "a" if append else "w"
        with open(filepath, "w", encoding=encoding) as f:
            f.write(self.text)

            # FIXME: some errors on Python 3.2 and 3.3 (NOT 3.4 and later)
