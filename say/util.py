"""
Home for separable utility functions used in say
"""

import itertools
import sys
import six
import types
import csv
from codecs import open

_PY3 = sys.version_info[0] == 3
if _PY3:
    from codecs import getencoder

    basestring = unicode = str
    from io import StringIO

    stringify = lambda v: str(v)
else:
    from StringIO import StringIO

    stringify = lambda v: v if isinstance(v, basestring) else unicode(v)


def is_string(v):
    """
    Is the value v a string? Useful especially in making a test that works on
    both Python 2.x and Python 3.x
    """
    return isinstance(v, basestring)


def opened(f):
    """
    If f is a string, consider it a file name and return it, ready for writing.
    Else, assume it's an open file. Just return it.
    """
    if isinstance(f, list):
        return [opened(ff) for ff in f]
    else:
        return open(f, "w", encoding="utf-8") if is_string(f) else f
        # NB use codecs.open for encoding to UTF-8 in Python 2


def encoded(u, encoding):
    """
    Encode string u (denoting it is expected to be in Unicode) if there's
    encoding to be done. Tries to mask the difference between Python 2 and 3,
    which have different models of string processing, and different codec APIs
    and quirks. Some Python 3 encoders further require ``bytes`` in, not
    ``str``. These are first encoded into utf-8, encoded, then decoded.
    """
    if not encoding:
        return u
    elif _PY3:
        try:
            return getencoder(encoding)(u)[0]
        except LookupError:
            name = encoding.replace('-', '')  # base-64 becomes base64 e.g.
            bytesout = getencoder(name + '_codec')(u.encode('utf-8'))[0]
            if name in set(['base64', 'hex', 'quopri', 'uu']):
                return bytesout.decode('utf-8')
            else:
                return bytesout

                # NB PY3 requires lower-level interface for many codecs. s.encode('utf-8')
                # works fine, but others do not. Some codecs convert bytes to bytes,
                # and are not properly looked up by nickname (e.g. 'base64'). These are
                # managed by first encoding into utf-8, then if it makes sense decoding
                # back into a string. The others are things like bz2 and zlib--binary
                # encodings that have little use to us here.

                # There are also be some slight variations in results that will make
                # testing more fun. Possibly related to adding or not adding a terminal
                # newline.
    else:
        # Python 2 may not have the best handling of Unicode, but by
        # by God its encode operations are straightforward!
        return u.encode(encoding)


def flatten(*args):
    """
    Like itertools.chain(), but will pretend that single scalar values are
    singleton lists. Convenient for iterating over values whether they're lists
    or singletons.
    """
    flattened = [x if isinstance(x, (list, tuple)) else [x] for x in args]
    return itertools.chain(*flattened)

    # would use ``hasattr(x, '__iter__')`` rather than ``isinstance(x, (list, tuple))``,
    # but other objects like file have ``__iter__``, which screws things up


def next_str(g):
    """
    Given a generator g, return its next result as a unicode string. If not a
    generator, just return the value as a unicode string.
    """
    try:
        value = next(g)
    except TypeError:
        value = g if g is not None else ''
    return unicode(value)
