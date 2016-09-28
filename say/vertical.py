"""
Define veritcal separation.
"""

from mementos import MementoMetaclass, with_metaclass
import sys

_PY3 = sys.version_info[0] == 3
if _PY3:
    unicode = str


class Vertical(with_metaclass(MementoMetaclass, object)):
    """
    Specification for vertical spacing. Object creation is
    memoized for efficiency.
    """

    def __init__(self, before=0, after=0, bstr='', astr=''):
        """
        Make one.
        """
        self.before = before
        self.after = after
        self.bstr = bstr
        self.astr = astr

    def render(self):
        """
        Return a list-of-lines representation of the receiver.
        """
        before = [self.bstr] * self.before
        after = [self.astr] * self.after
        return (before, after)

    def __eq__(self, other):
        return (isinstance(other, Vertical) and self.before == other.before
                and self.after == other.after and self.astr == other.astr
                and self.bstr == other.bstr)

    # TODO: memoize ``render`` output. Or does that crush the mementos caching strategy?
    # if changed, would have to invalidate the mementos cache?

    def __repr__(self):
        """
        Pretty representation, yo.
        """
        keys = ['before', 'after', 'bstr', 'astr']
        guts = ', '.join(['{0}={1!r}'.format(k, self.__dict__[k]) for k in keys])
        return "{0}({1})".format(self.__class__.__name__, guts)


def vertical(first=0, second=None):
    """
    Permissive factory function for vertical separation.
    """
    if not first and second is None:
        return Vertical(0, 0, '', '')
    elif isinstance(first, tuple) and second is None:
        return Vertical(*first)
    if isinstance(first, Vertical):
        return first
    before = first
    after = second if second is not None else first
    return Vertical(before, after)
