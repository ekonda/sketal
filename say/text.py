"""
A text object that uses say to aggregate lines, say in a file or script.
"""

from say.core import fmt
from say.util import *
from say.util import _PY3
import inspect
import sys
import six
import os
import re
from simplere import Re


class Text(object):
    def __init__(self, data=None, interpolate=True, dedent=True):
        self._lines = []
        if data:
            lines = self._data_to_lines(data)
            callframe = inspect.currentframe().f_back
            self.extend(lines, callframe, interpolate, dedent)

    def _dedent_lines(self, lines):
        """
        Given a list of lines, remove a leading or trailing blank line (if any),
        as well as common leading blank prefixes.
        """
        if lines and lines[0].strip() == "":
            lines.pop(0)
        if lines and lines[-1].strip() == "":
            lines.pop()
        if lines:
            nonblanklines = [line for line in lines if line.strip() != ""]
            # piggyback os.path function to compute longest common prefix
            prefix = os.path.commonprefix(nonblanklines)
            # but then determine how much of that prefix is blank
            prelen, maxprelen = 0, len(prefix)
            while prelen < maxprelen and prefix[prelen] == ' ':
                prelen += 1
            if prelen:
                lines = [line[prelen:] for line in lines]
        return lines

    def __add__(self, data):
        """
        Add the contents of the self with the contents of the other item, returning
        a next text.
        """
        result = self.copy()
        lines = self._data_to_lines(data)
        callframe = inspect.currentframe().f_back
        result.extend(lines, callframe, interpolate=True, dedent=True)
        return result

    def __or__(self, data):
        """
        Add the contents of the self with the contents of the other item, returning
        a next text.
        """
        result = self.copy()
        lines = self._data_to_lines(data)
        callframe = inspect.currentframe().f_back
        result.extend(lines, callframe, interpolate=True, dedent=False)
        return result

    def __and__(self, data):
        """
        Add the contents of the self with the contents of the other item, returning
        a next text.
        """
        result = self.copy()
        lines = self._data_to_lines(data)
        result._lines.extend(lines)
        return result

    # TODO: Add the final 'yes dedent, no interpret' operation

    def __iadd__(self, data):
        """
        In-place add the text or lines contained in data, with auto-dedent.
        """
        lines = self._data_to_lines(data)
        callframe = inspect.currentframe().f_back
        self.extend(lines, callframe, interpolate=True, dedent=True)
        return self

    def __ior__(self, data):
        """
        In-place add the text or lines contained in data, with NO auto-dedent.
        """
        lines = self._data_to_lines(data)
        callframe = inspect.currentframe().f_back
        self.extend(lines, callframe, interpolate=True, dedent=False)
        return self

    def __iand__(self, data):
        """
        In-place add the text or lines contained in data, with NO auto-dedent
        and NO iterpolation.
        """
        lines = self._data_to_lines(data)
        self._lines.extend(lines)
        return self

    def __contains__(self, other):
        other = str(other)
        return other in self.text

    def append(self, line, callframe=None, interpolate=True):
        if interpolate:
            callframe = callframe or inspect.currentframe().f_back
            line = fmt(line, _callframe=callframe)
        self._lines.append(line)

    def extend(self, lines, callframe=None, interpolate=True, dedent=True):
        if dedent:
            lines = self._dedent_lines(lines)
        if interpolate:
            callframe = callframe or inspect.currentframe().f_back
        for line in lines:
            self.append(line, callframe, interpolate)

    # TODO: consider whether append and extend should be calls to insert

    def insert(self, i, data, callframe=None, interpolate=True, dedent=True):
        lines = self._data_to_lines(data)
        if dedent:
            lines = self._dedent_lines(lines)
        if interpolate:
            callframe = callframe or inspect.currentframe().f_back
            lines = [fmt(line, _callframe=callframe) for line in lines]
        for line in reversed(lines):
            self._lines.insert(i, line)

    def __getitem__(self, n):
        return self._lines[n]

    def __setitem__(self, n, value):
        self._lines[n] = value.rstrip('\n')

    def __len__(self):
        return len(self._lines)

    def __iter__(self):
        return iter(self._lines)

    def _data_to_lines(self, data):
        if isinstance(data, Text):
            return data.lines
        elif isinstance(data, list):
            return [line.rstrip('\n') for line in data]
        else:
            return data.splitlines()

    @property
    def text(self):
        return six.u('\n').join(self._lines)

    @text.setter
    def text(self, data):
        self._lines = self._data_to_lines(data)

    @property
    def lines(self):
        return self._lines[:]

    @lines.setter
    def lines(self, somelines):
        self._lines = [line.rstrip('\n') for line in somelines]

    def __str__(self):
        return self.text

    def render(self):
        """
        Equivalent to ``__str__``. For compatibility with ``Template``
        subclass.
        """
        return self.text

    def __repr__(self):
        return 'Text({0}, {1} lines)'.format(id(self), len(self._lines))

    def copy(self):
        """
        Make a copy.
        """
        newt = Text()
        newt._lines = self._lines[:]
        return newt

    def replace(self, target, replacement=None):
        """
        Replace all instances of the target string with the replacement string.
        Works in situ, contra str.replace().
        """
        if target and isinstance(target, dict) and replacement is None:
            replacement = ''
            for (targ, repl) in target.items():
                repl = str(repl)
                for i, line in enumerate(self._lines):
                    self._lines[i] = line.replace(targ, repl)
                    replacement += repl  # for newline check below
        else:
            replacement = str(replacement)
            for i, line in enumerate(self._lines):
                self._lines[i] = line.replace(target, replacement)

        # recalibrate lines, if new lines included in replacement
        if replacement and '\n' in replacement:
            self._lines = self._data_to_lines(self.text)

        return self

    # TODO: add doc note about caution re dict-based replacements; order is
    # base on dict iteration order, and subsequent can overwrite previous

    def re_replace(self, target, replacement):
        """
        Regular expression replacement. Target is either compiled re object or
        string that will be compiled into one. Replacement is either string or
        function that takes re match object as a parameter and returns replacement
        string.
        """
        target = Re(target) if not isinstance(target, Re) else target
        for i, line in enumerate(self._lines):
            self._lines[i] = target.sub(replacement, line)
        return self

    # TODO: for some reason, replacement not getting to be a simplere.ReMatch obj
    # TODO: extend dict-style invocation to re_replace

    def read_from(self, filepath, interpolate=True, dedent=True, encoding='utf-8'):
        """
        Reads lines from the designated file, appending them to the end of the
        given Text. By default, interpolates and dedents any {}
        expressions.
        """
        lines = open(filepath, encoding=encoding).read().splitlines()
        caller = inspect.currentframe().f_back
        self.extend(lines, caller, interpolate=interpolate, dedent=dedent)
        return self

    # TODO: make above a combo method

    def write_to(self, filepath, append=False, encoding='utf-8'):
        """
        Write the Text instance's contents to the given filepath.
        :param filepath: Filepath to write to.
        :param append: Whether to appened to the file (if it exists) or overwrite (default)
        :param encoding: How to encode the contents (default utf-8)
        """
        mode = "a" if append else "w"
        with open(filepath, mode, encoding=encoding) as f:
            f.write(self.text)

    def write(self, contents):
        """
        Make it possible for Text objects to operate like file objects, and be written to.
        """
        if contents.endswith('\n'):
            contents = contents[:-1]
        lines = contents.split('\n')
        self._lines.extend(lines)

        # THIS MIGHT CAUSE SOME UNICODE ERRORS, NO?

        # TODO: add a backup feature


class Template(Text):
    def __init__(self, data=None, interpolate=False, dedent=True):
        self._lines = []
        if data:
            lines = self._data_to_lines(data)
            callframe = inspect.currentframe().f_back
            self.extend(lines, callframe, interpolate, dedent)

    def render(self):
        """
        Render the Template to a (unicode) string based on the current
        values in the current context.
        """
        t = Text()
        callframe = inspect.currentframe().f_back
        t.extend(self._lines, callframe, interpolate=True, dedent=False)
        return unicode(t)

        # Would be convenient if there were a value override in `fmt` so
        # that Template().render() could pass some specific values, in
        # addition to grabbing the current values

        # TODO: Consider additional `list` and `str` methods
        # TODO: Possibly add in-place replacement, modification, etc.
        # TODO: Extend tests
