def flatten(seq):
    """Flatten Sequences.

    >>> flatten([[0, 1], [2, 3]])
    [0, 1, 2, 3]
    """

    return [item for sublist in seq for item in sublist]


def double_replace(string):
    """Replaces -1 by -, and 1 by +. Accepts string as input.

    >>> double_replace('-1 1 -1 1')
    '- + - +'
    """

    return string.replace("-1", "-").replace("1", "+")


def replace_list_to_plus_minus(list):
    """Convert a list in a string and replace -1 by -, and 1 by +

    >>> replace_list_to_plus_minus([1, 1, -1, -1])
    '+ + - -'
    """

    return " ".join([double_replace(str(x)) for x in list])


def with_index(seq):
    """Returns a generator from a sequence."""

    for i in xrange(len(seq)):
        yield i, seq[i]


def replace_all(seq, replacement):
    """Replace all zeros in a sequence by a given replacement element.

    >>> replace_all([0, 3, 2, 0], -1)
    [-1, 3, 2, -1]
    """

    new_seq = seq[:]

    for i, elem in with_index(new_seq):
        if elem == 0:
            new_seq[i] = replacement
    return new_seq


def greatest_first(list1, list2):
    """Returns greatest list first.

    >>> greatest_first([0, 1], [3, 2, 1])
    [[3, 2, 1], [0, 1]]
    """

    if len(list1) > len(list2):
        return [list1, list2]
    else:
        return [list2, list1]
