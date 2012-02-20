from music21.stream import Stream
from collections import MutableSequence
import plot
import matrix
import auxiliary


class Contour(MutableSequence):
    def __init__(self, args):
        """args can be either a music21.stream or a list of numbers

        >>> Contour(tinyNotation.TinyNotationStream('c4 d8 f g16 a g f#', '3/4'))
        < 0 2 5 7 9 7 6 >

        >>> Contour([0, 3, 2, 1])
        < 0 3 2 1 >
        """

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

    def retrograde(self):
        """Returns contour retrograde.

        >>> Contour([0, 1, 2, 3]).retrograde()
        < 3 2 1 0 >
        """

        tmp = self[:]
        tmp.reverse()
        return Contour(tmp)

    def inversion(self):
        """Returns contour inversion.

        >>> Contour([0, 3, 1, 2]).inversion()
        < 3 0 2 1 >
        """

        maxim = max(self)
        return Contour([(maxim - cps) for cps in self])

    def translation(self):
        """Returns the normal form (Marvin 1987) of a given contour.
        It's the same of Friedmann (1985, 1987) contour class (CC).

        >>> Contour([4, 2, 6, 1]).translation()
        < 2 1 3 0 >
        """

        return Contour([sorted(list(set(self))).index(x) for x in self])

    def comparison_matrix(self):
        """Returns Morris (1987) a cseg COM-Matrix.

        >>> Contour([0, 1, 3, 2]).comparison_matrix()
        0 + + +
        - 0 + +
        - - 0 -
        - - + 0
        """

        return matrix.ComparisonMatrix([[auxiliary.comparison([a, b]) for b in self] for a in self])

    def show(self):
        print self

    def plot(self):
        g_title = 'MusiContour in Music21'
        obj = plot.GraphPlot(doneAction=None, title=g_title)
        obj.setData(self)
        obj.process()
        obj.show()
