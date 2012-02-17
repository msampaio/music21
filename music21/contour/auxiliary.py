def interval(els):
    """Returns Friedmann (1985) CI, the distance between one
    element in a CC (normal_form cseg here), and a later element
    as signified by +, - and a number (without + here). For
    example, in cseg = [0, 2, 1], CI(0, 2) = 2, e CI(2, 1) = -1.

    >>> interval([4, 0])
    -4
    """

    el1, el2 = els
    return el2 - el1


def comparison(els):
    """Returns Morris (1987) comparison [COM(a, b)] for two
    c-pitches.

    This function calls interval(), but in contour theory there is no
    relation between them. This calling reason is only to reduce code.

    >>> comparison([4, 0])
    -1
    """

    delta = interval(els)
    return 0 if abs(delta) == 0 else (delta) / abs(delta)
