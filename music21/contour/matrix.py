import contour
import utils


class ComparisonMatrix(list):
    """Returns an objcect comparison matrix.
    Input is a list of lists, each of them representing a line in
    matrix:

    >>> ComparisonMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]])
    0 + +
    - 0 -
    - + 0
    """

    def cseg(self):
        """Returns a cseg from Matrix.

        >>> ComparisonMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]]).cseg()
        < 0 2 1 >
        """

        return contour.Contour([(len(self) - 1 - sum(row)) // 2 for row in self]).translation()

    def superior_triangle(self, n=1):
        """Returns the right superior triangle from a matrix. The main
        diagonal is excluded.

        >>> ComparisonMatrix([[0, 1, 1], [-1, 0, -1], [-1, 1, 0]]).superior_triangle()
        [[1, 1], [-1]]
        """

        if n < len(self):
            return [line[i + n:] for i, line in enumerate(self) if line][:-n]

    def show(self):
        """Returns matrix with a matrix with cseg in a visual way.

        >>> ComparisonMatrix([[0, 1, 1, 1], [-1, 0, -1, 1], [-1, 1, 0, 1], [-1, -1, -1, 0]]).display()
        '  | 0 2 1 3\n-----------\n0 | 0 + + +\n2 | - 0 - +\n1 | - + 0 +\n3 | - - - 0'
        """

        def __lines(el, line, cseg):
            return str(cseg[el]) + " | " + str(utils.replace_list_to_plus_minus(line))

        cseg = self.cseg()
        first_line = "  | {0}\n".format(" ".join([str(x) for x in cseg]))
        second_line = "---" + ("-" * len(self) * 2) + "\n"
        other_lines = "\n".join([__lines(el, line, cseg) for el, line in enumerate(self)])
        return first_line + second_line + other_lines

    def __repr__(self):

        return "\n".join([str(utils.replace_list_to_plus_minus(line)) for line in self])


def matrix_from_triangle(triangle):
    """Returns a complete comparison matrix from a given superior
    triangle.

    >>> matrix_from_triangle([[1, 1, 1, 1], [1, 1, 1], [-1, -1], [1]])
    0 + + + +
    - 0 + + +
    - - 0 - -
    - - + 0 +
    - - + - 0
    """

    matrix = []
    for n in range(0, len(triangle) + 1):
        line = []
        for x in range(n):
            line.append(triangle[x][n - x - 1] * -1)
        line.append(0)
        if n < len(triangle):
            line.extend(triangle[n])
        matrix.append(line)
    return ComparisonMatrix(matrix)


def triangle_zero_replace(triangle, replacement):
    """Returns a triangle with zeros replaced by the given replacement factor.

    >>> triangle_zero_replace([[1, 0, 1, 1], [1, 0, 1], [1, 0], [1]], -1)
    [[1, -1, 1, 1], [1, -1, 1], [1, -1], [1]]
    """

    return [utils.replace_all(row, replacement) for row in triangle]


def triangle_zero_replace_to_cseg(triangle):
    """Returns two csegs obtained by zero to 1/-1 replacement.

    >>> triangle_zero_replace_to_cseg([[1, 1, 1, 1], [1, 0, 1], [-1, 0], [1])
    [< 0 1 3 2 4 >, < 0 2 4 1 3 >]
    """

    pair = []
    for r in [1, -1]:
        new_triangle = triangle_zero_replace(triangle, r)
        new_matrix = matrix_from_triangle(new_triangle)
        pair.append(new_matrix.cseg())
    return pair
