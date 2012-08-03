from music21.stream import Stream
from collections import MutableSequence
import plot
import matrix
import auxiliary
import diagonal
import fuzzy
import utils
import itertools


def max_min(list_of_tuples, fn):
    """Returns a list with the position of maximum or minimum
    cpitches of a cseg. Maximum or minimum function is defined in
    fn argument.

    'n' stores the number of elements that is evaluated.
    'r' means result.
    """

    n = 3
    list_range = range(len(list_of_tuples) - n + 1)
    m_list = [list_of_tuples[0]]

    [m_list.append(fn(list_of_tuples[i:i + n])) for i in list_range]
    m_list.append(list_of_tuples[-1])

    return [x for x in m_list if x]


def maxima_pair(list_of_tuples):
    """Returns maxima (Morris, 1993) positions in a cseg.

    >>> maxima_pair([(0, 1), (1, 2), (2, 4), (4, 5), (3, 3)])
    [(0, 1), (4, 5), (3, 3)]
    """

    def maximum(dur_list):
        """Returns the maximum (Morris, 1993) position of a three
        c-pitches set. The input data is a list of three tuples. Each
        tuple has the c-pitch and its position.
        """

        (el1, p1), (el2, p2), (el3, p3) = dur_list
        return (el2, p2) if el2 >= el1 and el2 >= el3 else ''

    return max_min(list_of_tuples, maximum)


def minima_pair(list_of_tuples):
    """Returns minima (Morris, 1993) positions in a cseg.

    >>> minima_pair([(0, 1), (1, 2), (2, 4), (4, 5), (3, 3)])
    [(0, 1), (3, 3)]
    """

    def minimum(dur_list):
        """Returns the minimum (Morris, 1993) position of a three
        c-pitches set. The input data is a list of three tuples. Each
        tuple has the c-pitch and its position.
        """

        (el1, p1), (el2, p2), (el3, p3) = dur_list
        return (el2, p2) if el2 <= el1 and el2 <= el3 else ''

    return max_min(list_of_tuples, minimum)


def reduction_retention(els):
    """Returns medial cps value if it is maxima or minima of a given
    list with an even number of consecutive cps. (Bor, 2009)

    >>> reduction_retention([None, 0, 2, 1, 2])
    2
    """

    size = len(els)
    if size % 2 == 0:
        print "Error. 'els' must be a sequence with an even number of elements."
    else:
        els_max = max(els)
        els_min = min([x for x in els if x != None])

        medial_pos = size / 2
        medial = els[medial_pos]
        left_seq = els[:medial_pos]
        right_seq = els[medial_pos + 1:]

        ## retain if medial is the first or last el
        if list(set(left_seq)) == [None] or list(set(right_seq)) == [None]:
            return medial
        ## repeations. Do not retain if medial is the second consecutive
        ## repeated cps
        elif medial == els[medial_pos - 1]:
            return None
        ## retain if medial is max or min
        elif medial == els_max or medial == els_min:
            return medial
        else:
            return None


def possible_cseg(base_3):
    """Returns a cseg from a base 3 sequence, if the cseg is possible
    (Polansky and Bassein 1992).

    >>> possible_cseg([2, 2, 2])
    < 0 1 2 >
    """

    seq = utils.flatten(base_3)
    size = len(seq)
    for x in itertools.product(range(size), repeat=3):
        cseg = Contour(x)
        if utils.flatten(cseg.base_three_representation()) == seq:
            return Contour(x)
    return "Impossible cseg"


class Contour(MutableSequence):
    def __init__(self, args):
        """args can be either a music21.stream or a list of numbers

        >>> Contour(tinyNotation.TinyNotationStream('c4 d8 f g16 a g f#', '3/4'))
        < 0 2 5 7 9 7 6 >

        >>> Contour([0, 3, 2, 1])
        < 0 3 2 1 >
        """

        if isinstance(args, Stream):
            midi_args = [n.midi for n in args.flat.notes]
            midi_args_translation = [sorted(set(midi_args)).index(x) for x in midi_args]
            self.items = self.remove_adjacent(midi_args_translation)
            self.expanded = midi_args
        else:
            self.items = self.remove_adjacent(args)
            self.expanded = args

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
        if len(self.items) == len(other.items):
            return all(x == y for x, y in zip(self.items, other.items))
        else:
            return False

    def __add__(self, other):
        return Contour(self.items + other.items)

    def insert(self, i, value):
        self.items.insert(i, value)

    @staticmethod
    def remove_adjacent(list):
        """Removes duplicate adjacent elements from a list.

        >>> remove_adjacent([0, 1, 1, 2, 3, 1, 4, 2, 2, 5])
        [0, 1, 2, 3, 1, 4, 2, 5]
        """

        groups = itertools.izip(list, list[1:])
        return [a for a, b in groups if a != b] + [list[-1]]

    def rotation(self, factor=1):
        """Rotates a cseg around a factor.

        factor is optional. Default factor=1.

        'n' is the module of input factor. It's allowed to use factor
        numbers greater than cseg size.

        >>> Contour([0, 1, 2, 3]).rotation(2)
        < 2 3 0 1 >
        """

        n = factor % len(self.expanded)
        subset = self.expanded[n:]
        subset.extend(self.expanded[0:n])
        return Contour(subset)

    def retrogression(self):
        """Returns contour retrograde.

        >>> Contour([0, 1, 2, 3]).retrogression()
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

        return matrix.ComparisonMatrix([[cmp(b, a) for b in self] for a in self])

    def internal_diagonals(self, n=1):
        """Returns Morris (1987) int_n. The first internal diagonal
        (int_1) is the same of Friedmann (1985, 1987) contour
        adjacency series (CC).

        >>> Contour([0, 1, 3, 2]).internal_diagonals()
        < + + - >
        """

        matrix = self.comparison_matrix()
        int_d = [x for x in itertools.imap(cmp, matrix, itertools.islice(matrix, n, None)) if x != 0]
        return diagonal.InternalDiagonal(int_d)

    def interval_succession(self):
        """Return Friedmann (1985) CIS, a series which indicates the
        order of Contour Intervals in a given CC (normal form cseg
        here).

        >>> Contour([1, 2, 3, 5, 4, 0]).interval_succession()
        [1, 1, 2, -1, -4]
        """

        return [b - a for a, b in zip(self, self[1:])]

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
            cseg = cseg.retrogression()

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

    def class_representatives(self, prime_algorithm="prime_form_marvin_laprade"):
        """Returns the four csegclass representatives (Marvin and
        Laprade 1987, p. 237): prime, inversion, and retrograde
        inversion.

        >>> Contour([0, 1, 3, 2]).class_representatives()
        [< 0 1 3 2 >, < 3 2 0 1 >, < 2 3 1 0 >, < 1 0 2 3 >]
        """

        p = auxiliary.apply_fn(Contour(self), prime_algorithm)
        i = Contour(self).inversion()
        r = Contour(self).retrogression()
        ri = Contour(i).retrogression()

        return [p, i, r, ri]

    def class_four_forms(self):
        """Returns four csegclass representative forms. This method is
        similar to class_representatives, but the first cseg form is
        the normal, not prime form.

        >>> Contour([0, 1, 3, 2]).class_representatives()
        [< 0 1 3 2 >, < 3 2 0 1 >, < 2 3 1 0 >, < 1 0 2 3 >]
        """

        t = self.translation()
        i = t.inversion()
        r = t.retrogression()
        ri = i.retrogression()

        return [t, i, r, ri]

    def subsets(self, n):
        """Returns adjacent and non-adjacent subsets of a given
        contour.

        >>> Contour([0, 2, 1, 3, 4]).subsets(4)
        [< 0 1 3 4 >, < 0 2 1 3 >, < 0 2 1 4 >, < 0 2 3 4 >, < 2 1 3 4 >]
        """

        cseg = self
        r = [Contour(list(x)) for x in itertools.combinations(cseg, n)]
        return sorted(r)

    def subsets_normal(self, n):
        """Returns adjacent and non-adjacent subsets of a given
        contour grouped by their normal forms.

        Output is a dictionary where the key is the normal form, and
        the attribute is csubsets list.

        >>> Contour([0, 3, 1, 4, 2]).subsets_normal()
        {(0, 1, 3, 2): [[0, 1, 4, 2]],
        (0, 2, 1, 3): [[0, 3, 1, 4]],
        (0, 2, 3, 1): [[0, 3, 4, 2]],
        (0, 3, 1, 2): [[0, 3, 1, 2]],
        (2, 0, 3, 1): [[3, 1, 4, 2]]}
        """

        subsets = self.subsets(n)
        dic = {}

        for x in subsets:
            processed = tuple(x.translation())
            if processed in dic:
                z = dic[processed]
                z.append(x)
                dic[processed] = z
            else:
                dic[processed] = [x]

        return dic

    def cps_position(self):
        """Returns a tuple with c-pitch and its position for each
        c-pitch of a cseg done.

        >>> Contour([0, 1, 3, 2]).cps_position()
        [(0, 0), (1, 1), (3, 2), (2, 3)]
        """

        return [(self[p], p) for p in range(len(self))]

    def reduction_morris(self):
        """Returns Morris (1993) contour reduction from a cseg, and
        its depth.

        >>> Contour([0, 4, 3, 2, 5, 5, 1]).reduction_morris()
        [< 0 2 1 >, 2]
        """

        def cps_position_to_cseg(cps_position):
            """Converts a list of cps_position tuples to cseg object."""

            return Contour([x for (x, y) in cps_position])

        def init_flag(tuples_list):
            """Returns max_list, min_list, flagged and unflagged
            cpitch tuples.

            Accepts a tuples_list with the original contour.

            It runs steps 1 and 2."""

            max_list = maxima_pair(tuples_list)
            min_list = minima_pair(tuples_list)

            # flagged cpitches are all cpitches that are in max_list
            # or min_list
            flagged = list(set(utils.flatten([max_list, min_list])))

            not_flagged = []
            for el in tuples_list:
                if el not in flagged:
                    not_flagged.append(el)

            return max_list, min_list, flagged, not_flagged

        def flag(max_list, min_list):
            """Returns max_list, min_list and unflagged cpitch tuples.

            It runs steps 6, and 7."""

            init_list = list(set(utils.flatten([max_list, min_list])))
            new_max_list = utils.remove_duplicate_tuples(maxima_pair(max_list))
            new_min_list = utils.remove_duplicate_tuples(minima_pair(min_list))

            # flagged cpitches are all cpitches that are in max_list
            # or min_list
            flagged = list(set(utils.flatten([new_max_list, new_min_list])))
            flagged = sorted(flagged, key=lambda(x, y): y)
            not_flagged = []
            # fills not_flagged:
            for el in init_list:
                if el not in flagged:
                    not_flagged.append(el)

            return new_max_list, new_min_list, flagged, not_flagged

        # returns list of cpitch/position tuples
        cseg_pos_tuples = self.cps_position()

        # initial value (step 0)
        depth = 0

        # runs steps 1 and 2
        max_list, min_list, flagged, not_flagged = init_flag(cseg_pos_tuples)

        if not_flagged != []:

            # step 5 (first time)
            depth += 1

            # loop to run unflagged until finish unflagged cpitches
            # tests if there are unflagged cpitches (partial step 3)
            while flag(max_list, min_list)[3] != []:
                # back to steps 6 and 7
                r = flag(max_list, min_list)
                max_list, min_list, flagged, not_flagged = r

                # increases depth (step 5)
                depth += 1

        sorted_flagged = sorted(flagged, key=lambda x: x[1])
        reduced = Contour(cps_position_to_cseg(sorted_flagged).translation())

        return [reduced, depth]

    def reduction_window(self, window_size=3, translation=True):
        """Returns a reduction in a single turn of n-window reduction
        algorithm. (Bor, 2009).

        >>> Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5]).reduction_window(3, False)
        < 7 10 0 3 1 8 2 5>
        """

        def _red(cseg, pos, n):
            return reduction_retention(cseg[pos - n:pos + 1 + n])

        if window_size % 2 == 0:
            print "Window size must be an even number."
        else:
            cseg = self.expanded[:]
            size = len(cseg)
            n = window_size / 2

            for i in range(n):
                cseg.insert(0, None)
                cseg.append(None)

            prange = range(n, size + n)

            reduced = Contour([_red(cseg, pos, n) for pos in prange if _red(cseg, pos, n) != None])
            if translation == True:
                reduced = reduced.translation()
            return reduced

    def reduction_bor(self, windows=3, translation=True):
        """Returns reduction contour and its depth with given windows
        sequence (Bor, 2009).

        >>> Contour([0, 6, 1, 4, 3, 5, 2]).reduction_bor(53)
        [< 0 2 1 >, 2]
        """

        cseg = self
        win_vals = [int(x) for x in str(windows)]
        for window in win_vals:
            cseg = cseg.reduction_window(window, translation)
        return [cseg, len(win_vals)]

    def fuzzy_membership_matrix(self):
        """Returns a Fuzzy membership matrix. Quinn (1997).

        >>> Contour([0, 1, 3, 2]).fuzzy_membership_matrix()
        0 1 1 1
        0 0 1 1
        0 0 0 0
        0 0 1 0
        """

        return fuzzy.FuzzyMatrix([[fuzzy.membership([a, b]) for b in self] for a in self])

    def fuzzy_comparison_matrix(self):
        """Returns a Fuzzy comparison matrix. Quinn (1997).

        >>> Contour([0, 1, 3, 2]).fuzzy_comparison_matrix()
        0 1 1 1
        -1 0 1 1
        -1 -1 0 -1
        -1 -1 1 0
        """

        return fuzzy.FuzzyMatrix([[fuzzy.comparison([a, b]) for b in self] for a in self])

    def base_three_representation(self):
        """Returns Base three Contour Description, by Polansky and
        Bassein (1992). The comparison between c-points returns 0, 1,
        or 2 if the second c-point is lower, equal or higher than the
        first, respectively. This method returns a list with
        comparison of all combinations of c-points.

        >>> Contour([0, 1, 3, 2]).base_three_representation()
        [[2, 2, 2], [2, 2], [0]]
        """

        combinations = itertools.combinations(self, 2)

        def aux_list(base_3, self):
            size = len(self)
            r_size = range(size - 1, 0, -1)
            result = []
            n = 0
            for i in r_size:
                seq = base_3[n:n + i]
                result.append(seq)
                n += i
            return result

        ternary = [auxiliary.base_3_comparison(a, b) for a, b in combinations]

        return aux_list(ternary, self)

    def oscillation(self):
        """Returns number of direction changes of a given
        cseg. (Schmuckler, 1999).
        """

        int_1 = self.internal_diagonals()
        return sum([1 for i in range(len(int_1) - 1) if int_1[i] != int_1[i + 1]])

    def oscillation_index(self):
        """Returns index of direction changes of a given cseg."""

        return self.oscillation() / float(len(self) - 1)

    def __repr__(self):
        return "< {0} >".format(" ".join([str(x) for x in self[:]]))

    def show(self):
        print self

    def plot(self):
        g_title = 'MusiContour in Music21'
        obj = plot.GraphPlot(doneAction=None, title=g_title)
        obj.setData(self)
        obj.process()
        obj.show()
