import unittest
import matrix


class TestUtils(unittest.TestCase):
    def test_Com_matrix_cseg(self):
        cm = matrix.ComparisonMatrix([[0, 1, 1, 1], [-1, 0, -1, 1], [-1, 1, 0, 1], [-1, -1, -1, 0]])
        self.assertEqual(cm.cseg(), [0, 2, 1, 3])

    def test_Com_matrix_superior_triangle(self):
        cm = matrix.ComparisonMatrix([[0, 1, 1, 1], [-1, 0, -1, 1], [-1, 1, 0, 1], [-1, -1, -1, 0]])
        self.assertEqual(cm.superior_triangle(), [[1, 1, 1], [-1, 1], [1]])
        self.assertEqual(cm.superior_triangle(2), [[1, 1], [1]])

    def test_matrix_from_triangle(self):
        tri = [[1, 1, 1, 1], [1, 1, 1], [-1, -1], [1]]
        result = [[0, 1, 1, 1, 1],
                  [-1, 0, 1, 1, 1],
                  [-1, -1, 0, -1, -1],
                  [-1, -1, 1, 0, 1],
                  [-1, -1, 1, -1, 0]]
        self.assertEqual(matrix.matrix_from_triangle(tri), result)

    def test_triangle_zero_replace(self):
        triangle = [[1, 0, 1, 1], [1, 0, 1], [1, 0], [1]]
        result = [[1, -1, 1, 1], [1, -1, 1], [1, -1], [1]]
        self.assertEqual(matrix.triangle_zero_replace(triangle, -1), result)

    def test_triangle_zero_replace_to_cseg(self):
        triangle = [[1, 1, 1, 1], [1, 0, 1], [-1, 0], [1]]
        self.assertEqual(matrix.triangle_zero_replace_to_cseg(triangle), [[0, 1, 3, 2, 4], [0, 2, 4, 1, 3]])


if __name__ == '__main__':
    unittest.main()


