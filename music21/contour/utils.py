import itertools

def flatten(seq):
    """Flatten Sequences.

    >>> flatten([[0, 1], [2, 3]])
    [0, 1, 2, 3]
    """

    return list(itertools.chain.from_iterable(seq))


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


def replace_all(seq, replacement):
    """Replace all zeros in a sequence by a given replacement element.

    >>> replace_all([0, 3, 2, 0], -1)
    [-1, 3, 2, -1]
    """

    return [replacement if x == 0 else x for x in seq]


def greatest_first(list1, list2):
    """Returns greatest list first.

    >>> greatest_first([0, 1], [3, 2, 1])
    [[3, 2, 1], [0, 1]]
    """

    if len(list1) > len(list2):
        return [list1, list2]
    else:
        return [list2, list1]

    
def remove_duplicate_tuples(list_of_tuples):
    """Removes tuples that the first item is repeated in adjacent
    tuples. The removed tuple is the second.

    >>> remove_duplicate_tuples([(0, 1), (0, 2), (1, 3), (2, 4), (1, 5)])
    [(0, 1), (1, 3), (2, 4), (1, 5)]
    """

    prev = None
    tmp = []
    for a, b in list_of_tuples:
        if a != prev:
            tmp.append((a, b))
            prev = a
    return tmp
