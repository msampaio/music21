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
