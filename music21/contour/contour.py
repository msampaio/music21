from music21.stream import Stream
from collections import MutableSequence


class Contour(MutableSequence):
    def __init__(self, args):
        """args can be either a music21.stream or a list of numbers"""
        
        if isinstance(args, Stream):
            self.items = [n.pitchClass for n in args.notes]
        else:
            self.items = args

    def __delitem__(self, i):
        del self.items[i]

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    def __setitem__(self, i, value):
        self.items[i] = value

    def __repr__(self):
        return "< {0} >".format(" ".join([str(x) for x in self.items]))

    def __eq__(self, other):
        return all(x == y for x, y in zip(self.items, other.items))

    def __add__(self, other):
        return Contour(self.items + other.items)

    def insert(self, i, value):
        self.items.insert(i, value)

    def rotation(self, factor=1):
        """Rotates a cseg around a factor.

        factor is optional. Default factor=1.

        'n' is the module of input factor. It's allowed to use factor
        numbers greater than cseg size.

        >>> Contour([0, 1, 2, 3]).rotation(2)
        < 2 3 0 1 >
        """

        n = factor % len(self)
        subset = self[n:]
        subset.extend(self[0:n])
        return Contour(subset)

    def show(self):
        print self

    def plot(self):
        print self
