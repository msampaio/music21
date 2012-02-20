from music21.stream import Stream
from collections import MutableSequence
import plot
import matrix
import auxiliary
import diagonal
import itertools


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

    def internal_diagonals(self, n=1):
        """Returns Morris (1987) int_n. The first internal diagonal
        (int_1) is the same of Friedmann (1985, 1987) contour
        adjacency series (CC).

        >>> Contour([0, 1, 3, 2]).internal_diagonals()
        < + + - >
        """

        matrix = self.comparison_matrix()
        int_d = [row[i + n] for i, row in enumerate(matrix[:-n])]
        return diagonal.InternalDiagonal([x for x in int_d if x != 0])

    def interval_succession(self):
        """Return Friedmann (1985) CIS, a series which indicates the
        order of Contour Intervals in a given CC (normal form cseg
        here).

        >>> Contour([1, 2, 3, 5, 4, 0]).interval_succession()
        [1, 1, 2, -1, -4]
        """

        return [(self[pos + 1] - self[pos]) for pos in range(len(self) - 1)]

    def adjacency_series_vector(self):
        """Returns Friedmann (1985) CASV, a two digit summation of ups
        and downs of a CAS (internal diagonal n=1 here). For example,
        [2, 1] means 2 ups and 1 down.

        'internal_diagonal' stores cseg internal diagonal, n = 1.

        'ups' stores the total number of ups

        'downs' stores the total number of downs

        >>> Contour([0, 1, 3, 2]).adjacency_series_vector()
        [2, 1]
        """

        internal_diagonal = self.internal_diagonals(1)
        ups = sum([(x if x > 0 else 0) for x in internal_diagonal])
        downs = sum([(x if x < 0 else 0) for x in internal_diagonal])
        return [ups, abs(downs)]

    def interval_array(self):
        """Return Friedmann (1985) CIA, an ordered series of numbers
        that indicates the multiplicity of each Contour Interval type
        in a given CC (normal form cseg here). For cseg < 0 1 3 2 >,
        there are 2 instances of type +1 CI, 2 type +2 CI, 1. CIA =
        ([2, 2, 1], [1, 0, 0])

        'up_intervals' and 'down_intervals' store the contour intervals
        that the method counts.

        The loop appends positive elements in ups_list and negative in
        downs_list.

        'ups' and 'downs' stores contour intervals counting for all
        types of positive and negative intervals in the cseg.

        >>> Contour([0, 1, 3, 2]).interval_array()
        ([2, 2, 1], [1, 0, 0])
        """

        up_intervals = range(1, len(self))
        down_intervals = [-x for x in up_intervals]
        ups_list = []
        downs_list = []

        for x in itertools.combinations(self, 2):
            y = auxiliary.interval(x)
            if y > 0:
                ups_list.append(y)
            elif y < 0:
                downs_list.append(y)

        ups = [ups_list.count(x) for x in up_intervals]
        downs = [downs_list.count(x) for x in down_intervals]

        return ups, downs

    def class_vector_i(self):
        """Return Friedmann (1985) CCVI, a two-digit summation of
        degrees of ascent and descent expressed in contour interval
        array. The first digit is the total of products of frequency
        and contour interval types of up contour intervals, and the
        second, of down contour intervals. For example, in CIA([2, 2,
        1], [1, 0, 0], CCVI = [(2 * 1) + (2 * 2) + (1 * 3)], [(1 * 1),
        (2 * 0), (3 * 0)]. So, CCVI = [5, 1].

        'items' stores the contour intervals to be sum.

        'up_list' and 'down_list' stores the up and down contour
        interval frequency lists.

        'up_sum' and 'down_sum' stores the sum of the product of each
        contour interval frequency and contour interval value.

        >>> Contour([0, 1, 3, 2]).class_vector_i()
        [9, 1]
        """

        items = range(1, len(self))
        up_list, down_list = self.interval_array()
        up_sum = sum([a * b for a, b in itertools.izip(up_list, items)])
        down_sum = sum([a * b for a, b in itertools.izip(down_list, items)])
        return [up_sum, down_sum]

    def class_vector_ii(self):
        """Return Friedmann (1985) CCVII, a two-digit summation of
        degrees of ascent and descent expressed in contour interval
        array. The first digit is the total of frequency of up contour
        intervals, and the second, of down contour intervals. For
        example, in CIA([2, 2, 1], [1, 0, 0], CCVII = [5, 1].

        >>> Contour([0, 1, 3, 2]).class_vector_ii()
        [5, 1]
        """

        return [sum(x) for x in self.interval_array()]

    def __unequal_edges(self):
        """Returns the first cps position with different value from
        its symmetric. For instance, given a cseg C [0, 3, 1, 4, 2, 3,
        0], the first cps with different value for its symmetric is
        C_2 = 1.
        C_0 == C_-1
        c_1 == C_-2
        c_2 != C_-3
        So, the function returns cpitch position: 2.
        """

        for position in range(len(self) / 2):
            if self[position] != self[(position * -1) - 1]:
                return position

    def __prime_form_marvin_laprade_step_2(self, position):
        """Runs Marvin and Laprade (1987) second step of prime form
        algorithm.

        If (n - 1) - last pitch < first pitch, invert.

        position: the first cps position that its value is different
        for its symmetric (cf. unequal_edges).
        """

        cseg = self
        n = len(cseg)

        # if first and last cps are equal, the second must be compared
        # to penultimate cps and so on to break the "tie".
        false_first = cseg[position]
        false_last = cseg[(position * -1) - 1]

        if ((n - 1) - false_last) < false_first:
            cseg = cseg.inversion()

        return cseg

    def __prime_form_marvin_laprade_step_3(self, position):
        """Runs Marvin and Laprade (1987) third step of prime form
        algorithm.

        If last cpitch < first cpitch, retrograde.

        position: the first cps position that its value is different
        for its symmetric (cf. unequal_edges).
        """

        cseg = self

        if cseg[(position * -1) - 1] < cseg[position]:
            cseg = cseg.retrograde()

        return cseg

    def __non_repeated_prime_form_marvin_laprade(self):
        """Returns the prime form of a given contour (Marvin and
        Laprade, 1987)."""

        # the first cps position that its value is different for its
        # symmetric (cf. unequal_edges).
        position = self.__unequal_edges()

        # step 1: translate if necessary
        step1 = Contour(self).translation()
        step2 = step1.__prime_form_marvin_laprade_step_2(position)
        step3 = step2.__prime_form_marvin_laprade_step_3(position)

        return step3

    def __repeated_prime_generic(self, prime_algorithm):
        """Returns prime forms of a repeated cpitch cseg calculated
        with a given prime_algorithm.
        """

        triangle = self.comparison_matrix().superior_triangle()
        csegs = matrix.triangle_zero_replace_to_cseg(triangle)

        return sorted([auxiliary.apply_fn(t, prime_algorithm) for t in csegs])

    def __repeated_prime_form_marvin_laprade(self):
        """Returns prime forms of a repeated cpitch cseg."""

        return self.__repeated_prime_generic("prime_form_marvin_laprade")

    def prime_form_marvin_laprade(self):
        """Returns the prime form of a given contour (Marvin and
        Laprade, 1987).

        >>> Contour([4, 2, 6, 1]).prime_form_marvin_laprade()
        < 0 3 1 2 >
        """

        # tests if cseg has repeated elements
        if len(self) == len(set([x for x in self])):
            return self.__non_repeated_prime_form_marvin_laprade()
        else:
            return self.__repeated_prime_form_marvin_laprade()

    def show(self):
        print self

    def plot(self):
        g_title = 'MusiContour in Music21'
        obj = plot.GraphPlot(doneAction=None, title=g_title)
        obj.setData(self)
        obj.process()
        obj.show()
