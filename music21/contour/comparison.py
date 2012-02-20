import utils
import auxiliary


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
