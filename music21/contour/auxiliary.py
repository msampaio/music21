import contour

def apply_fn(cseg, fn):
    """Apply a method to a contour.

    >>> apply_fn(Contour([0, 1, 2]), 'retrogression')
    < 2 1 0 >
    """

    return apply(getattr(contour.Contour(cseg), fn))


def interval(els):
    """Returns Friedmann (1985) CI, the distance between one
    element in a CC (normal_form cseg here), and a later element
    as signified by +, - and a number (without + here). For
    example, in cseg = [0, 2, 1], CI(0, 2) = 2, e CI(2, 1) = -1.

    >>> interval([4, 0])
    -4
    """

    return els[1] - els[0]


def position_comparison(list_1, list_2):
    """Returns a similarity index based on the number of equal
    elements in same positions in two lists.

    >>> position_comparison([0, 1, 2, 3], [0, 1, 3, 2])
    0.5
    """

    value = 0
    size = len(list_1)
    for pos in range(size):
        if list_1[pos] == list_2[pos]:
            value += 1
    return value / float(size)
