import utils
import itertools
import contour

class InternalDiagonal(list):
    """Returns an objcect Internal diagonal.
    Input is a list of 1 and -1, representing + and - in an internal
    diagonal:

    >>> InternalDiagonal([-1, 1, 1])
    < - + + >
    """

    def __repr__(self):
        data = [utils.double_replace(str(x)) for x in self[:]]
        return "< {0} >".format(" ".join(data))

    def retrogression(self):
        """Returns internal diagonal retrograde.

        >>> InternalDiagonal([1, 1, -1]).retrogression()
        < - + + >
        """

        diagonal = self[:]
        diagonal.reverse()
        return InternalDiagonal(diagonal)

    def inversion(self):
        """Returns Internal diagonal inversion.

        >>> InternalDiagonal([-1, 1, 1]).inversion()
        < + - - >
        """

        return InternalDiagonal([(x * -1) for x in self])

    def rotation(self, factor=1):
        """Rotates an internal diagonal around a factor.

        factor is optional. Default factor=1.

        'n' is the module of input factor. It's allowed to use factor
        numbers greater than internal diagonal size.

        >>> InternalDiagonal([-1, 1, 1, -1]).rotation(2)
        < + - - + >
        """

        n = factor % len(self)
        subset = self[n:]
        subset.extend(self[0:n])
        return InternalDiagonal(subset)

    def csegs(self, d=1):
        """Returns all csegs in normal form that have the given
        internal diagonal. Default diagonal is 1.

        >>> InternalDiagonal([-1, 1, 1]).csegs
        [[1, 0, 2, 3], [2, 0, 1, 3], [3, 0, 1, 2]]
        """

        size = len(self) + d
        all_lists = itertools.permutations(range(size), size)

        result = []
        for el in all_lists:
            cseg = contour.Contour(el)
            if cseg.internal_diagonals(d) == self:
                result.append(cseg)
        return result
