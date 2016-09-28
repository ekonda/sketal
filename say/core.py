"""Interpolating string formatter. """

import string
import inspect
import sys
import os
from codecs import open
import codecs
import re
from options import Options, OptionsContext, Transient, Prohibited
from options.chainstuf import chainstuf
import six
import textwrap
from .util import *
from .util import _PY3
from .styling import *
from .vertical import Vertical, vertical
from .version import __version__

### Workhorse functions

sformatter = string.Formatter()  # piggyback Python's format() template parser

QUOTES = ("'", '"')


def populate_style(style_name, styles):
    if style_name.startswith(QUOTES):
        style_name = style_name.strip(style_name[0])
    if style_name not in styles:
        styles[style_name] = autostyle(style_name)


def _sprintf(arg, caller, styles=None, override=None):
    """
    Format the template string (arg) with the values seen in the context of the
    caller. If override is defined, it is a Mapping providing additional values
    atop those of the local context.
    """

    def seval(s):
        """
        Evaluate the string s in the caller's context. Return its value.
        """
        try:
            localvars = caller.f_locals if override is None \
                else chainstuf(override, caller.f_locals)
            return eval(s, caller.f_globals, localvars)
        except SyntaxError:
            raise SyntaxError("syntax error when formatting '{0}'".format(s))

    def parse_style(fs, styles):
        """
        Get the style component out of the format string, if any.
        """
        if "style" in fs:
            fs_parts = fs.split(',')
            raw_fs_parts = []
            for fsp in fs_parts:
                if fsp.startswith('style='):
                    style_name = fsp[6:].strip(QUOTE_DELIM_STR)
                else:
                    raw_fs_parts.append(fsp)
            populate_style(style_name, styles)
            return style_name, raw_fs_parts
        else:
            return None, fs

            # TODO: Replace this parser with something more professional
            # TODO: join=

    if is_string(arg):
        arg = unicode(arg) if not _PY3 and isinstance(arg, str) else arg
        parts = []
        for (literal_text, field_name, format_spec, conversion) in sformatter.parse(arg):
            parts.append(literal_text)
            if field_name is not None:

                style_name, raw_format_spec = parse_style(format_spec, styles)
                format_str = six.u("{0") + \
                             ("!" + conversion if conversion else "") + \
                             (":" + raw_format_spec if raw_format_spec else "") + "}"
                field_value = seval(field_name)
                formatted = format_str.format(field_value)
                if style_name and style_name in styles:
                    formatted = styles[style_name](formatted)

                parts.append(formatted)
        return ''.join(parts)
    else:
        return str(seval(str(arg)))


def get_stdout():
    """
    It used to be that Say objects had their own encoding
    mechanism. We simplified by pushing that responsibility
    onto an underlying file object (or analog). That causes
    problems on some terminals (e.g. Komodo IDE) that for
    some reason initialize the sys.stdout encoding to US-ASCII.
    In those cases, instead of returning sys.stdout per se,
    return a writer object that does the encoding we want.
    """
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # line buffering
    if sys.stdout.encoding == 'UTF-8':
        return sys.stdout
    else:
        if sys.version_info[0] >= 3:
            out = sys.stdout.buffer
        else:
            out = sys.stdout
        return codecs.getwriter('UTF-8')(out)


### Helpers for method style setting

def methset(cls, mname, **kwargs):
    """
    Called to update a method's default args
    """
    # print "methset: cls:", cls, "mname:", mname
    methdefs = cls.meth_defaults.setdefault(mname, {})
    methdefs.update(kwargs)


def install_method_setter(cls, mname):
    meth = getattr(cls, mname)
    target = meth if _PY3 else meth.__func__
    cls.meth_defaults.setdefault(mname, {})
    setattr(target, 'set', lambda **kwargs: methset(cls, mname, **kwargs))


def install_method_setters(cls, methnames):
    """
    Called once class is defined to update those methods
    that need to have per-method set() routines
    """
    if isinstance(methnames, basestring):
        methnames = methnames.strip().split()
    for mname in methnames:
        meth = getattr(cls, mname)
        # print "mname:", mname, "meth:", meth

        target = meth if _PY3 else meth.__func__
        setattr(target, 'set', lambda **kwargs: methset(cls, mname, **kwargs))

        # TODO: clean this up by integrating with @methargs decorator
        # Does not seem to work to do them all in one process -- which is
        # perplexing, but probably due to some subtle closure / context locking


### Core Say class

class Say(object):
    """
    Say encapsulates printing functions. Instances are configurable, and callable.
    """

    options = Options(
        indent=0,  # indent level (if set to None, indentation is turned off)
        indent_str='    ',  # indent string for each level
        prefix='',  # prefix each line with this (string or string generator)
        suffix='',  # suffix each line with this (string or string generator)
        files=[get_stdout()],  # where is output headed? a list of write() able objects
        wrap=None,  # column to wrap lines to, if any
        sep=' ',  # separate args with this (Python print function compatible)
        vsep=None,  # vertical separation
        end='\n',  # end output with this (Python print function compatible)
        silent=False,  # be quiet
        style=None,  # name of style in which to wrap entire output line
        styles={},  # style dict
        _callframe=Transient,  # frome from which the caller was calling
    )

    options.magic(
        indent=lambda v, cur: cur.indent + int(v) if isinstance(v, (str, unicode, Relative)) else v,
        files=lambda v, cur: opened(v)
    )

    meth_defaults = {}

    def __init__(self, **kwargs):
        """
        Make a say object with the given options.
        """
        self.options = Say.options.push(kwargs)
        self.__version__ = __version__

    def _method_push(self, base_options, method_name, kwargs):
        """
        Transitional helper function to simplify the grabbing of
        method-specific arguments. Will be phased out as the learnings
        about method arguments are piped back into Options and a more
        long-term API is completed.
        """
        mkwargs = self.meth_defaults.get(method_name, {}).copy()
        mkwargs.update(kwargs)
        if base_options:
            return base_options.add(**mkwargs)
            # different formulation than in Show
            # to enable adding new items for methods
        else:
            return mkwargs

    @staticmethod
    def escape(s):
        """
        Double { and } characters in a string to 'escape' them so ``str.format``
        doesn't treat them as template characters. NB This is NOT idempotent!
        Escaping more than once (when { or } are present ) = ERROR.
        """
        return s.replace('{', '{{').replace('}', '}}')

    def hr(self, **kwargs):
        """
        Print a horizontal line. Like the HTML hr tag. Optionally
        specify the width, character repeated to make the line, and vertical separation.

        Good options for the separator may be '-', '=', or parts of the Unicode
        box drawing character set. http://en.wikipedia.org/wiki/Box-drawing_character
        """
        # opts = self.options.push(kwargs)
        self.meth_defaults['hr'].setdefault('width', 40)
        self.meth_defaults['hr'].setdefault('sep', six.u('\u2500'))
        opts = self._method_push(self.options, 'hr', kwargs)

        # no interpolation required, so no caller frame introspection
        line = opts.sep * opts.width
        return self._output(line, opts)

    def title(self, name, **kwargs):
        """
        Print a horizontal line with an embedded title.
        """
        # opts = self.options.push(kwargs)
        self.meth_defaults['title'].setdefault('width', 15)
        self.meth_defaults['title'].setdefault('sep', six.u('\u2500'))
        # TODO: move these into method-setup decorator
        opts = self._method_push(self.options, 'title', kwargs)

        opts.setdefault('_callframe', inspect.currentframe().f_back)

        formatted = _sprintf(name, opts._callframe, opts.styles) if is_string(name) else str(name)
        bars = opts.sep * opts.width
        line = ' '.join([bars, formatted, bars])
        return self._output(line, opts)

    def sep(self, text='', **kwargs):
        """
        Print a short horizontal line, possibly with some text following,
        of the desired width. Useful as a separator for different parts
        of output.
        """
        self.meth_defaults['sep'].setdefault('sep', '-')
        self.meth_defaults['sep'].setdefault('width', 2)

        # opts = self.options.push(kwargs)
        opts = self._method_push(self.options, 'sep', kwargs)
        opts.setdefault('_callframe', inspect.currentframe().f_back)

        formatted = _sprintf(text, opts._callframe, opts.styles) if is_string(text) else stringify(text)
        bars = opts.sep * opts.width
        line = ' '.join([bars, formatted]) if formatted else bars
        return self._output(line, opts)

    def blank_lines(self, n, **kwargs):
        """
        Output N blank lines ("vertical separation"). Unlike other methods, this
        does not obey normal vertical separation rules, because it is about
        explicit vertical separation. If it obeyed vsep, it would usually gild
        the lily (double space).
        """
        if not n:
            return
        # opts = self.options.push(kwargs)
        opts = self._method_push(self.options, 'blank_lines', kwargs)

        # no interpolation required, so no caller frame introspection
        opts.vsep = None
        return self._output([''] * n, opts)

        # TODO: make it so blank_lines can take a default n as a method arg

    def set(self, **kwargs):
        """
        Permanently change the reciver's settings to those defined in the kwargs.
        An update-like function.
        """
        self.options.set(**kwargs)

    def setfiles(self, files):
        """
        Set the list of output files. ``files`` is a list. For each item, if
        it's a real file like ``sys.stdout``, use it. If it's a string, assume
        it's a filename and open it for writing.
        """

        def opened(f):
            """
            If f is a string, consider it a file name and return it, ready for writing.
            Else, assume it's an open file. Just return it.
            """
            return open(f, "w", encoding='utf-8') if is_string(f) else f
            # NB use codecs.open to get encoding to UTF-8 in Python 2

        self.options.files = [opened(f) for f in files]
        return self

        # TBD: Turn this into 'magical' attribute set

    def settings(self, **kwargs):
        """
        Open a context manager for a `with` statement. Temporarily change settings
        for the duration of the with.
        """
        return SayContext(self, kwargs)

    def clone(self, **kwargs):
        """
        Create a new instance whose options are chained to this instance's
        options (and thence to self.__class__.options). kwargs become the
        cloned instance's overlay options.
        """
        cloned = self.__class__()
        cloned.options = self.options.push(kwargs)
        return cloned

    but = clone

    def fork(self, **kwargs):
        """
        Create a new instance whose options are chained to this instance's
        class's options, then this instance's current values, then any
        difference values stated in kwwargs.
        """
        forked = self.__class__()
        forked.options = forked.options.push({})
        for k, v in self.options.items():
            if v != forked.options[k]:
                forked.options[k] = v
        forked.options = forked.options.push(kwargs)  # not previously processed
        return forked

    # should determine variations of cloning
    # How much dynamic linkage should clone have to its predecessor?
    # Full dynamic linkage along the clone/but model? Or all of the
    # parent's options as they now are, frozen in time, then building
    # on those? Propose "fork()" as a "fork in the road" kind of diversion
    # in which the Class options + instance options as they now stand +
    # kwargs are in place. Thus common heritage and common values to start,
    # but no ongoing linkage.

    def style(self, *args, **kwargs):
        """
        Define a style.
        """
        for k, v in kwargs.items():
            if isinstance(v, six.string_types):
                self.options.styles[k] = autostyle(v)
            else:
                self.options.styles[k] = v

    def __call__(self, *args, **kwargs):
        """
        Primary interface. say(something)
        """
        opts = self.options.push(kwargs)
        opts.setdefault('_callframe', inspect.currentframe().f_back)

        formatted = [_sprintf(arg, opts._callframe, opts.styles) if is_string(arg) else str(arg)
                     for arg in args]
        return self._output(opts.sep.join(formatted), opts)

    def __gt__(self, arg):
        """
        Simple, non-functional call. Experimental.
        """
        opts = self.options.push({})
        opts.setdefault('_callframe', inspect.currentframe().f_back)

        formatted = [_sprintf(arg, opts._callframe, opts.styles) if is_string(arg) else str(arg)]
        return self._output(opts.sep.join(formatted), opts)

    def _return_value(self, outstr, opts):
        """
        Prepare a quality return value. Manages encoding of string and
        stripping of final newline, if desired, based on opts.return_encoded
        and opts.return_strip_newline.
        """
        ret_encoding = opts.encoding if opts.return_encoded is True else opts.encoded
        ret_encoded = encoded(outstr, ret_encoding)
        if opts.return_strip_newline:
            ret_encoded = ret_encoded[:-1] if ret_encoded.endswith('\n') else ret_encoded
        return ret_encoded

    def _outstr(self, data, opts):
        """
        Given result text, format it. ``data`` may be either a
        list of lines, or a composed string. NB: Don't feed it a list of strings,
        some of which contain newlines; that will break its assumptions.
        """
        datalines = data if isinstance(data, list) else data.splitlines()

        if opts.indent or opts.wrap or opts.prefix or opts.suffix or opts.vsep or opts.style:
            indent_str = opts.indent_str * opts.indent
            if opts.wrap:
                datastr = '\n'.join(datalines)
                wrap_width = opts.wrap - len(indent_str) - len(opts.prefix) - len(opts.suffix)
                wrappedlines = textwrap.wrap(datastr,
                                             width=wrap_width,
                                             replace_whitespace=False,
                                             initial_indent='',
                                             subsequent_indent='')
                datalines = []
                for line in wrappedlines:
                    datalines.extend(line.splitlines())
            if opts.style:
                styler = opts.styles.get(opts.style, None)
                if not styler:
                    styler = opts.styles.setdefault(opts.style, autostyle(opts.style))
                datalines = [styler(line) for line in datalines]
            if opts.indent:
                datalines = [indent_str + line for line in datalines]
            vbefore, vafter = vertical(opts.vsep).render()
            datalines = vbefore + datalines + vafter
            if opts.prefix or opts.suffix:
                datalines = [''.join([next_str(opts.prefix), line, next_str(opts.suffix)])
                             for line in datalines]
            outstr = '\n'.join(datalines)
        else:
            outstr = '\n'.join(data) if isinstance(data, list) else data
        # by end of indenting, dealing with string only

        # prepare and emit output
        if opts.end is not None:
            outstr += opts.end
        return outstr

    def _output(self, data, opts):
        """
        Construct the output string and write it to files.
        """
        if opts.silent:
            return
        else:
            outstr = self._outstr(data, opts)
            for f in opts.files:
                f.write(outstr)


class SayContext(OptionsContext):
    """
    Context helper to support Python's with statement.  Generally called
    from ``with say.settings(...):``
    """
    pass


class SayReturn(Say):
    """
    Combo of Say and Fmt that both says and returns data. Not a typical
    use case, but consistent with original design of ``Say``, and needed
    for ``show`` module
    """

    options = Say.options.add(
        retvalue=True,  # return formatted value if this is so
        trimrv=True,  # remove end (usually "\n") from retval if so
    )

    def __init__(self, **kwargs):
        self.options = SayReturn.options.push(kwargs)
        self.options.styles = say.options.styles  # styles are idiosyncratially shared

    def _output(self, data, opts):
        """
        Construct the output string, write it to files, and return it.
        """
        outstr = self._outstr(data, opts)
        if opts.trimrv and opts.end and outstr.endswith(opts.end):
            retstr = outstr[:-len(opts.end)]
        else:
            retstr = outstr

        if not opts.silent:
            outstr = self._outstr(data, opts)
            for f in opts.files:
                f.write(outstr)

        return retstr


class Fmt(Say):
    """
    A type of Say that returns its result, rather than writes it
    to files.
    """

    options = Say.options.copy().add(
        files=Prohibited,  # no files needed
        end=None,  # no extra newline
        silent=Prohibited,  # Fmt is never silent
    )

    def __init__(self, **kwargs):
        self.options = Fmt.options.push(kwargs)
        self.options.styles = say.options.styles  # styles are idiosyncratially shared

    def _output(self, data, opts):
        """
        Construct the output string and return it.
        """
        return self._outstr(data, opts)


# Create method style setters
# Individual settings are needed. For some reason, the group
# setting is just setting the last item. Closure issues?
install_method_setter(Say, 'blank_lines')
install_method_setter(Say, 'hr')
install_method_setter(Say, 'title')
install_method_setter(Say, 'sep')

### Define default callables
say = Say()
fmt = Fmt()

# institute nice defaults
say.sep.set(vsep=(1, 0))
say.title.set(vsep=1)


### Helpers

def caller_fmt(*args, **kwargs):
    """
    Like ``fmt()``, but iterpolating strings not from the caller's context, but
    the caller's caller's context. It sounds uber meta, but it helps easily make
    other routines be able to do what ``fmt()`` can do.
    """
    kwargs.setdefault('_callframe', inspect.currentframe().f_back.f_back)
    return fmt(*args, **kwargs)


class FmtException(Exception):
    """
    An exception class that formats its arguments in the calling context.
    Also, an example of how ``caller_fmt`` can be used.
    """

    def __init__(self, message):
        formatted = caller_fmt(message)
        super(FmtException, self).__init__(formatted)


class numberer(object):
    """
    A class-based factory for numbering generators. Rather like Python 2's
    ``xrange`` (or Python 3's ``range``), but intended to number lines in a file
    so it uses natural numbers starting at 1, not the typical Python 'start at
    0'. Also, returns formatted strings, not integers. Improves on what's
    possible as a functional generator on numberer because it can compute and
    return its own length.
    """

    def __init__(self, start=1, template="{n:>3}: ", length=None):
        """
        Make a numberer.
        """
        self.n = start
        self.template = template
        self.length = None
        self._formatted = None

    def __next__(self):
        """
        Return the next numbered template.
        """
        t = self.template
        result = t.format(n=self.n) if self._formatted is None else self._formatted
        self._formatted = None
        self.n += 1
        return result

    next = __next__  # for Python 2

    def __len__(self):
        """
        What is the string length of the instantiated template now? NB This can change
        over time, as n does. Fixed-width format strings limit how often it can change
        (to when n crosses a power-of-10 boundary > the fixed template length
        can accomodate). This implementation saves the templated string its has created
        for reuse. If self.length is set, however, this computation is not done, and
        self.length is assumed to be the right answer.
        """
        if self.length is not None:
            return self.length
        else:
            t = self.template
            result = t.format(n=self.n)
            self._formatted = result
            return len(result)

            # TODO: provide an ANSI-control-character independent version of string length that
            # can provide a "logical string length"
