import math
import utils
import auxiliary
import contour


def cseg_similarity(cseg1, cseg2):
    """Returns Marvin and Laprade (1987) CSIM(A, B) for a single
    cseg. It's a contour similarity function that measures similarity
    between two csegs of the same cardinality. The maximum similarity
    is 1, and minimum is 0.

    >>> cseg_similarity(Contour([0, 2, 3, 1]), Contour([3, 1, 0, 2]))
    0
    """

    cseg1_triangle = utils.flatten(cseg1.comparison_matrix().superior_triangle())
    cseg2_triangle = utils.flatten(cseg2.comparison_matrix().superior_triangle())

    return auxiliary.position_comparison(cseg1_triangle, cseg2_triangle)


def csegclass_similarity(cseg1, cseg2, prime_algorithm="prime_form_marvin_laprade"):
    """Returns Marvin and Laprade (1987) CSIM(_A, _B) with csegclasses
    representatives comparison.

    >>> csegclass_similarity(Contour([0, 2, 3, 1]), Contour([3, 1, 0, 2]))
    1
    """

    cseg1_p = auxiliary.apply_fn(cseg1, prime_algorithm)
    representatives = cseg2.class_representatives()
    csims = [cseg_similarity(cseg1_p, c) for c in representatives]
    return sorted(csims, reverse=True)[0]


def subsets_embed_total_number(cseg1, cseg2):
    """Returns the number of subsets with csubseg_size in a set with
    cseg_size. Marvin and Laprade (1987, p. 237).

    >>> c1, c2 = Contour([0, 1, 2, 3]), Contour([1, 0, 2])
    >>> subsets_embed_total_number(c1, c2)
    4
    """

    cseg, csubseg = utils.greatest_first(cseg1, cseg2)
    cseg_size = len(cseg)
    csubseg_size = len(csubseg)

    a = math.factorial(cseg_size)
    b = math.factorial(csubseg_size)
    c = math.factorial(cseg_size - csubseg_size)
    return a / (b * c)


def subsets_embed_number(cseg1, cseg2):
    """Returns the number of time the normal form of a csubseg appears
    in cseg subsets. Marvin and Laprade (1987).

    >>> c1, c2 = Contour([0, 1, 2, 3]), Contour([1, 0, 2])
    >>> subsets_embed_number(c1, c2)
    0
    """

    cseg, csubseg = utils.greatest_first(cseg1, cseg2)

    dic = contour.Contour(cseg).subsets_normal(len(csubseg))
    if tuple(csubseg) in dic:
        return len(dic[tuple(csubseg)])
    else:
        return 0


def contour_embed(cseg1, cseg2):
    """Returns similarity between contours with different
    cardinalities. 1 for greater similarity. Marvin and Laprade
    (1987).

    >>> contour_embed(Contour([0, 1, 2, 3]), Contour([0, 1, 2]))
    1.0
    """

    cseg, csubseg = utils.greatest_first(cseg1, cseg2)

    n_csubseg = contour.Contour(csubseg).translation()
    cseg_size = len(cseg)
    csubseg_size = len(csubseg)

    embed_times = subsets_embed_number(cseg, n_csubseg)
    total_subsets = subsets_embed_total_number(cseg, csubseg)
    return 1.0 * embed_times / total_subsets


def __csubseg_mutually_embed(cardinality, cseg1, cseg2):
    """Returns CMEMBn(X, A, B) (Marvin and Laprade, 1987) auxiliary
    values.

    Outputs a list with [incidence_number, total_numbers]

    All subsets of a given cardinality (n) are counted if they are
    embed in both csegs A and B. This number is divided by the sum of
    total contour subsets number of that cardinality in each segment,
    A, and B.

    'cseg1_s' and 'cseg2_s' store dictionaries with all their subsegs
    and related normal forms.

    'cseg1_t' and 'cseg2_t' store the number of csubsegs related to
    each normal form.

    'total_number' store the sum of all possible subsets of same
    cardinality for each contour cseg1, and cseg2.

    'intersection' store a list with normal forms common to cseg1 and
    cseg2.

    'incidence_number' stores the sum of subsets related by the same
    normal form embed in cseg1 and cseg2.

    >>> __csubseg_mutually_embed(3, Contour([0, 1, 2, 3]), Contour([0, 1, 2]))
    [5, 5]
    """

    try:
        cseg1_s = contour.Contour(cseg1).subsets_normal(cardinality)
        cseg2_s = contour.Contour(cseg2).subsets_normal(cardinality)
        cseg1_t = 0
        cseg2_t = 0

        for key in cseg1_s.keys():
            cseg1_t += len(cseg1_s[key])

        for key in cseg2_s.keys():
            cseg2_t += len(cseg2_s[key])

        total_number = cseg1_t + cseg2_t

        intersection = list(set(cseg2_s.keys()) & set(cseg1_s.keys()))
        incidence_number = 0

        for key in intersection:
            incidence_number += len(cseg1_s[key])
            incidence_number += len(cseg2_s[key])

        return [incidence_number, total_number]

    except ValueError:
        print("Csegs length must be greater than cardinality.")


def csubseg_mutually_embed(cardinality, cseg1, cseg2):
    """Returns CMEMBn(X, A, B) (Marvin and Laprade, 1987).

    >>> csubseg_mutually_embed(3, Contour([0, 1, 2, 3]), Contour([0, 1, 2]))
    1.0
    """

    [a, b] = __csubseg_mutually_embed(cardinality, cseg1, cseg2)
    return 1.0 * a / b


def __all_contour_mutually_embed(cseg1, cseg2):
    """Returns ACMEMB(A,B) (Marvin and Laprade, 1987).

    It's total number of significant mutually embeded csegs of
    cardinality 2 through the cardinality of the smaller cseg divided
    by the total possible csegs embed in both cseg1 and cseg2.

    >>> __all_contour_mutually_embed(Contour([0, 1, 2, 3]), Contour([0, 1, 2]))
    0.93333333333333335
    """

    incidence, total = (0, 0)
    for i in range(2, max(len(cseg1), len(cseg2)) + 1):
        incidence += __csubseg_mutually_embed(i, cseg1, cseg2)[0]
        total += __csubseg_mutually_embed(i, cseg1, cseg2)[1]
    return 1.0 * incidence / total


def all_contour_mutually_embed(cseg1, cseg2):
    """Returns ACMEMB(A,B) (Marvin and Laprade, 1987).

    It's total number of significant mutually embeded csegs of
    cardinality 2 through the cardinality of the smaller cseg divided
    by the total possible csegs embed in both cseg1 and cseg2 and its
    csegclasses representatives.

    >>> all_contour_mutually_embed(Contour([0, 1, 2, 3]), Contour([0, 1, 2]))
    0.93333333333333335
    """

    representatives = cseg2.class_representatives()
    acmembs = [__all_contour_mutually_embed(cseg1, c) for c in representatives]
    return sorted(acmembs, reverse=True)[0]
