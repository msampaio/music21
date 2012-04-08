#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contour
import utils
import auxiliary
import itertools

try:
    import numpy
except ImportError:
    pass


def membership(els):
    """Returns Fuzzy membership value in ascent set: 1 if (cps1, cps2)
    is element of ascent contours, 0, if not. Quinn 1997, equations
    4.1, 4.2, and 4.3, and table 3.

    >>> membership([1, 3])
    1
    """

    if els[1] - els[0] > 0:
        return 1
    else:
        return 0


def comparison(els):
    """Returns fuzzy comparison. Quinn 1997, equation 4.4 and table 3.

    >>> comparison([3, 1])
    -1
    """

    retrograde_els = els[:]
    retrograde_els.reverse()
    return membership(els) - membership(retrograde_els)


class FuzzyMatrix(list):
    """Returns an object fuzzy matrix.
    Input is a list of lists, each of them representing a line in
    matrix:

    >>> FuzzyMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]])
    """

    def diagonal(self, n=1):
        """Returns the matrix n diagonal.

        >>> FuzzyMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]]).diagonal()
        [1, -1]
        """

        if n < len(self):
            diagonal_size = len(self) - n
            return [self[x][x + n] for x in range(diagonal_size)]

    def superior_triangle(self, n=1):
        """Returns the matrix superior triangle from a given n
        diagonal.

        >>> FuzzyMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]]).superior_triangle()
        [[1, 1], [-1]]
        """

        if n < len(self):
            return [line[i + n:] for i, line in enumerate(self) if line][:-n]

    def except_zero_diagonal(self):
        """Returns the matrix without main zero diagonal.

        >>> FuzzyMatrix([[0, 1, 1, 1],
                         [0, 0, 1, 1],
                         [0, 0, 0, 0],
                         [0, 0, 1, 0]]).except_zero_diagonal()
        [[1, 1, 1], [0, 1, 1], [0, 0, 0], [0, 0, 1]]
        """

        return [[el for r, el in enumerate(line) if l != r] for l, line in enumerate(self)]

    def comparison(self):
        """Returns a comparison matrix from an average matrix.

        >>> FuzzyMatrix([[0.0, 0.0, 0.0, 0.0, 0.0],
                         [1.0, 0.0, 1.0, 1.0, 0.66666666666666663],
                         [1.0, 0.0, 0.0, 1.0, 0.33333333333333331],
                         [1.0, 0.0, 0.0, 0.0, 0.0],
                         [1.0, 0.33333333333333331, 0.33333333333333331, 1.0, 0.0]]).comparison()
        [[0.0, -1.0, -1.0, -1.0, -1.0],
        [1.0, 0.0, 1.0, 1.0, 0.3333333333333333],
        [1.0, -1.0, 0.0, 1.0, 0.0],
        [1.0, -1.0, -1.0, 0.0, -1.0],
        [1.0, -0.3333333333333333, 0.0, 1.0, 0.0]]
        """

        def __comparison(matrix, a, b):
            return matrix.item((x, y)) - matrix.item((y, x))

        def __product(rsize, n):
            return itertools.product(range(n, n + 1), rsize)

        size = len(self)
        rsize = range(size)
        matrix = numpy.matrix(self)

        fm = [[__comparison(matrix, x, y)  for x, y in __product(rsize, n)] for n in rsize]
        return FuzzyMatrix(fm)

    def __repr__(self):

        return "\n".join([" ".join([str(row) for row in line]) for line in self])


def membership_similarity(cseg1, cseg2):
    """Returns similarity from a fuzzy membership matrix. Quinn 1997.

    >>> fuzzy.membership_similarity(Contour([4, 0, 1, 3, 2]), Contour([4, 1, 2, 3, 0]))
    0.8
    """

    def aux(cseg):
        f_matrix = cseg.fuzzy_membership_matrix()
        f_comparison_matrix = f_matrix.comparison()
        return utils.flatten(f_comparison_matrix.except_zero_diagonal())

    return auxiliary.position_comparison(*[aux(cseg) for cseg in [cseg1, cseg2]])


def average_matrix(*csegs):
    """Returns the matrix of an average contour from a list of
    contours. Quinn 1997.

    >>> average_matrix(Contour([3, 0, 1, 2, 1]), Contour([4, 0, 1, 3, 2]), Contour([4, 1, 2, 3, 0]))
    [[0.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 0.66666666666666663],
    [1.0, 0.0, 0.0, 1.0, 0.33333333333333331],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 0.33333333333333331, 0.33333333333333331, 1.0, 0.0]]
    """

    matrices = [numpy.array(cseg.fuzzy_membership_matrix()) for cseg in csegs]
    return [list(sum(a) / float(len(matrices))) for a in zip(*matrices)]


def comparison_matrix_from_csegs(*csegs):
    """Returns a comparison matrix from a list of contours.

    >>> comparison_matrix_from_csegs(Contour([3, 0, 1, 2, 1]),
                                     Contour([4, 0, 1, 3, 2]),
                                     Contour([4, 1, 2, 3, 0]))
    [[0.0, -1.0, -1.0, -1.0, -1.0],
    [1.0, 0.0, 1.0, 1.0, 0.3333333333333333],
    [1.0, -1.0, 0.0, 1.0, 0.0],
    [1.0, -1.0, -1.0, 0.0, -1.0],
    [1.0, -0.3333333333333333, 0.0, 1.0, 0.0]]
    """

    return FuzzyMatrix(average_matrix(*csegs)).comparison()


def entry_numbers(size):
    """Returns the entries to be compared in a fuzzy comparison
    matrix. Quinn 1997, equation 6.2.

    >>> entry_numbers(5)
    20
    """

    return (size ** 2) - size


def entry_numbers_cseg(cseg):
    """Returns the entries to be compared in a fuzzy comparison
    matrix. Quinn 1997, equation 6.2.

    >>> entry_numbers_cseg(Contour([2, 0, 3, 1, 4]))
    20
    """

    return entry_numbers(len(cseg))


def similarity_increment(el_1, el_2, entries_number):
    """Returns increment for fuzzy retrofitting similarity comparison
    function. Quinn 1997, equation 6.4.

    el_1 = fuzzy comparison matrix entry for cseg 1
    el_2 = fuzzy comparison matrix entry for cseg 2

    >>> similarity_increment(0.8, 0.9, 2)
    0.45
    """

    return (1 - abs(el_2 - el_1)) / float(entries_number)


def matrix_similarity_crisp(matrix1, matrix2):
    """Returns crisp ascent membership similarity between two ascend
    matrices. Quinn 1997, based on figure 11.

    >>> m1 = fuzzy.FuzzyMatrix([[0, 0, 0, 0, 0],
                                [1, 0, 1, 1, 0],
                                [1, 0, 0, 1, 0],
                                [1, 0, 0, 0, 0],
                                [1, 1, 1, 1, 0]])
        m2 = fuzzy.FuzzyMatrix([[0, 0, 0, 0, 0],
                                [1, 0, 1, 1, 1],
                                [1, 0, 0, 1, 1],
                                [1, 0, 0, 0, 0],
                                [1, 0, 0, 1, 0]])
        matrix_similarity_crisp(m1, m2)
    0.8
    """

    n = entry_numbers(len(matrix1[0]))

    ## fuzzy comparison matrix without zero main diagonal
    m1 = matrix1.except_zero_diagonal()
    m2 = matrix2.except_zero_diagonal()

    ## matrix entries pairs for each position
    pairs = utils.flatten([zip(x, y) for x, y in zip(m1, m2)])

    return sum([(1 / float(n)) for pair in pairs if pair[0] == pair[1]])


def matrix_similarity_fuzzy(matrix1, matrix2):
    """Returns fuzzy ascent membership similarity between two ascend
    matrices. Quinn 1997, based on figure 11.

    >>> matrix_similarity_fuzzy([[0, 0.8], [0, 0]], [[0, 0.9], [0, 0]])
    0.95
    """

    size = len(matrix1[0])
    rsize = range(size)

    # number of compared entries
    j = entry_numbers(size)

    ## fuzzy comparison matrix without zero main diagonal
    m1 = numpy.matrix(matrix1)
    m2 = numpy.matrix(matrix2)

    def __increment(m1, m2, j, x, y):
        return (1 - abs(m1.item(x, y) - m2.item(x, y))) / float(j)

    matrix_model = [(x, y) for x, y in itertools.product(rsize, rsize) if x != y]

    return sum([__increment(m1, m2, j, x, y) for x, y in matrix_model])


def similarity_crisp(cseg1, cseg2):
    """Returns crisp ascent membership similarity between two csegs.
    Quinn 1997, figure 11.

    >>> similarity_crisp(Contour([4, 1, 2, 3, 0]), Contour([4, 0, 1, 3, 2]))
    0.8
    """

    m1 = cseg1.fuzzy_membership_matrix()
    m2 = cseg2.fuzzy_membership_matrix()
    return matrix_similarity_crisp(m1, m2)


def similarity_fuzzy(cseg1, cseg2):
    """Returns fuzzy ascent membership similarity between two csegs.
    Quinn 1997, figure 11.

    >>> similarity_fuzzy(Contour([4, 1, 2, 3, 0]), Contour([4, 0, 1, 3, 2]))
    0.8
    """

    m1 = cseg1.fuzzy_membership_matrix()
    m2 = cseg2.fuzzy_membership_matrix()
    return matrix_similarity_fuzzy(m1, m2)
