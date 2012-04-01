import unittest
import contour


class TestUtils(unittest.TestCase):
    def test_maxima_pair(self):
        n = [(0, 0), (1, 1), (3, 2), (2, 3), (4, 4)]
        self.assertEqual(contour.maxima_pair(n), [(0, 0), (3, 2), (4, 4)])

    def test_minima_pair(self):
        n = [(0, 0), (1, 1), (3, 2), (2, 3), (4, 4)]
        self.assertEqual(contour.minima_pair(n), [(0, 0), (2, 3), (4, 4)])

    def test_reduction_retention_3(self):
        self.assertEqual(contour.reduction_retention_3([0, 0, 0]), None)
        self.assertEqual(contour.reduction_retention_3([0, 0, 1]), None)
        self.assertEqual(contour.reduction_retention_3([1, 1, 0]), None)
        self.assertEqual(contour.reduction_retention_3([0, 1, 0]), 1)
        self.assertEqual(contour.reduction_retention_3([1, 0, 1]), 0)
        self.assertEqual(contour.reduction_retention_3([1, 0, 0]), 0)
        self.assertEqual(contour.reduction_retention_3([0, 1, 1]), 1)
        self.assertEqual(contour.reduction_retention_3([None, 0, 0]), 0)
        self.assertEqual(contour.reduction_retention_3([None, 0, 1]), 0)
        self.assertEqual(contour.reduction_retention_3([None, 1, 0]), 1)
        self.assertEqual(contour.reduction_retention_3([None, 1, 2]), 1)
        self.assertEqual(contour.reduction_retention_3([0, 0, None]), 0)
        self.assertEqual(contour.reduction_retention_3([0, 1, None]), 1)
        self.assertEqual(contour.reduction_retention_3([1, 0, None]), 0)

    def test_reduction_retention_5(self):
        self.assertEqual(contour.reduction_retention_5([None, None, 0, 1, 2]), 0)
        self.assertEqual(contour.reduction_retention_5([0, 2, 1, None, None]), 1)
        self.assertEqual(contour.reduction_retention_5([None, 7, 10, 9, 0]), 10)
        self.assertEqual(contour.reduction_retention_5([7, 10, 9, 0, 2]), None)
        self.assertEqual(contour.reduction_retention_5([0, 2, 1, 4, 1]), None)
        self.assertEqual(contour.reduction_retention_5([1, 4, 1, 5, 3]), 1)
        self.assertEqual(contour.reduction_retention_5([3, 0, 4, 1, 4]), 4)
        self.assertEqual(contour.reduction_retention_5([4, 1, 4, 3, 5]), None)
        self.assertEqual(contour.reduction_retention_5([1, 0, 5, 2, 5]), 5)
        self.assertEqual(contour.reduction_retention_5([5, 2, 5, 3, 4]), 5)
        self.assertEqual(contour.reduction_retention_5([0, 3, 2, 4, 2]), None)
        self.assertEqual(contour.reduction_retention_5([2, 4, 2, 5, 1]), None)

    def test_rotation(self):
        cseg = contour.Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.rotation(), [4, 9, 9, 2, 1, 1])
        self.assertEqual(cseg.rotation(1), [4, 9, 9, 2, 1, 1])
        self.assertEqual(cseg.rotation(2), [9, 9, 2, 1, 1, 4])
        self.assertEqual(cseg.rotation(20), [9, 9, 2, 1, 1, 4])

    def test_retrograde(self):
        cseg = contour.Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.retrograde(), [1, 2, 9, 9, 4, 1])

    def test_inversion(self):
        cseg = contour.Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.inversion(), [8, 5, 0, 0, 7, 8])

    def test_translation(self):
        cseg = contour.Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.translation(), [0, 2, 3, 3, 1, 0])

    def test_prime_form_marvin_laprade_1(self):
        cseg1 = contour.Contour([1, 4, 9, 2])
        cseg2 = contour.Contour([5, 7, 9, 1])
        cseg3 = contour.Contour([5, 7, 9, 1])
        cseg4 = contour.Contour([0, 2, 1, 3, 4])
        cseg5 = contour.Contour([0, 1, 2, 3, 2])
        cseg6 = contour.Contour([1, 2, 3, 0, 3, 1])
        cseg7 = contour.Contour([0, 1, 2, 1, 2])
        self.assertEqual(cseg2.prime_form_marvin_laprade(), [0, 2, 3, 1])
        self.assertEqual(cseg2.prime_form_marvin_laprade(), [0, 3, 2, 1])
        self.assertEqual(cseg3.prime_form_marvin_laprade(), [0, 3, 2, 1])
        self.assertEqual(cseg4.prime_form_marvin_laprade(), [0, 2, 1, 3, 4])
        self.assertEqual(cseg5.prime_form_marvin_laprade(), [[0, 1, 2, 4, 3], [0, 1, 3, 4, 2]])
        self.assertEqual(cseg6.prime_form_marvin_laprade(), [[1, 3, 4, 0, 5, 2], [1, 4, 0, 5, 3, 2]])
        self.assertEqual(cseg7.prime_form_marvin_laprade(), [[0, 1, 3, 2, 4], [0, 2, 4, 1, 3]])

    def test_comparison_matrix(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([1, 2, 3, 0, 3, 1])
        result1 = [[0, 1, 1, 1], [-1, 0, 1, -1], [-1, -1, 0, -1], [-1, 1, 1, 0]]
        result2 = [[0, 1, 1, -1, 1, 0], [-1, 0, 1, -1, 1, -1], [-1, -1, 0, -1, 0, -1],
                [1, 1, 1, 0, 1, 1], [-1, -1, 0, -1, 0, -1], [0, 1, 1, -1, 1, 0]]
        self.assertEqual(cseg1.comparison_matrix(), result1)
        self.assertEqual(cseg2.comparison_matrix(), result2)

    def test_internal_diagonals(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([1, 0, 4, 3, 2])
        self.assertEqual(cseg1.internal_diagonals(1), [1, 1, -1])
        self.assertEqual(cseg1.internal_diagonals(2), [1, -1])
        self.assertEqual(cseg2.internal_diagonals(1), [-1, 1, -1, -1])
        self.assertEqual(cseg2.internal_diagonals(2), [1, 1, -1])

    def test_interval_succession(self):
        cseg = contour.Contour([0, 1, 3, 2])
        self.assertEqual(cseg.interval_succession(), [1, 2, -1])

    def test_adjacency_series_vector(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([1, 2, 3, 0, 3, 1])
        self.assertEqual(cseg1.adjacency_series_vector(), [2, 1])
        self.assertEqual(cseg2.adjacency_series_vector(), [3, 2])

    def test_interval_array(self):
        cseg = contour.Contour([0, 1, 3, 2])
        self.assertEqual(cseg.interval_array(), ([2, 2, 1], [1, 0, 0]))

    def test_class_vector_i():
        cseg = contour.Contour([0, 1, 3, 2])
        self.assertEqual(cseg.class_vector_i(), [9, 1])

    def test_class_vector_ii():
        cseg = contour.Contour([0, 1, 3, 2])
        self.assertEqual(cseg.class_vector_ii(), [5, 1])

    def test_class_representatives():
        cseg = Contour([0, 1, 3, 2])
        result = [[0, 1, 3, 2], [3, 2, 0, 1], [2, 3, 1, 0], [1, 0, 2, 3]]
        self.assertEqual(cseg.class_representatives(), result)

    def test_subsets(self):
        cseg = contour.Contour([2, 8, 12, 9])
        result1 = [[2, 8], [2, 9], [2, 12], [8, 9], [8, 12], [12, 9]]
        result2 = [[2, 8, 9], [2, 8, 12], [2, 12, 9], [8, 12, 9]]
        self.assertEqual(cseg.subsets(2), result1)
        self.assertEqual(cseg.subsets(3), result2)

    def test_subsets_normal(self):
        cseg = contour.Contour([0, 3, 1, 4, 2])
        result = {(0, 1, 3, 2): [[0, 1, 4, 2]],
                  (0, 2, 1, 3): [[0, 3, 1, 4]],
                  (0, 2, 3, 1): [[0, 3, 4, 2]],
                  (0, 3, 1, 2): [[0, 3, 1, 2]],
                  (2, 0, 3, 1): [[3, 1, 4, 2]]}
        self.assertEqual(cseg.subsets_normal(4), result)

    def test_cps_position(self):
        cseg = contour.Contour([2, 8, 12, 9, 5, 7, 3, 12, 3, 7])
        result = [(2, 0), (8, 1), (12, 2), (9, 3), (5, 4),
                  (7, 5), (3, 6), (12, 7), (3, 8), (7, 9)]
        self.assertEqual(cseg.cps_position(), result)

    def test_reduction_morris(self):
        cseg1 = contour.Contour([0, 4, 3, 2, 5, 5, 1])
        cseg2 = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg1.reduction_morris(), [[0, 2, 1], 2])
        self.assertEqual(cseg2.reduction_morris(), [[2, 3, 0, 1], 3])

    def test_reduction_window_3(self):
        cseg = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_window_3(), [7, 10, 0, 3, 1, 8, 2, 5])

    def test_reduction_window_5(self):
        cseg1 = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        cseg2 = contour.Contour([7, 10, 0, 1, 8, 2, 5])
        cseg3 = contour.Contour([7, 10, 0, 8, 5])
        cseg4 = contour.Contour([0, 3, 3, 1, 2, 4])
        cseg5 = contour.Contour([0, 3, 3, 1, 2])
        cseg6 = contour.Contour([12, 10, 13, 11, 7, 9, 8, 6, 3, 5, 4, 1, 0, 2])
        self.assertEqual(cseg1.reduction_window_5(), [7, 10, 0, 1, 8, 2, 5])
        self.assertEqual(cseg2.reduction_window_5(), [7, 10, 0, 8, 5])
        self.assertEqual(cseg3.reduction_window_5(), [7, 10, 0, 5])
        self.assertEqual(cseg4.reduction_window_5(), [0, 3, 1, 4])
        self.assertEqual(cseg5.reduction_window_5(), [0, 3, 1, 2])
        self.assertEqual(cseg6.reduction_window_5(), [12, 10, 13, 7, 3, 0, 2])

    def test_reduction_bor_35(self):
        cseg = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_35(), [[7, 10, 0, 8, 5], 2])

    def test_reduction_bor_53(self):
        cseg = contour.Contour([12, 10, 13, 11, 7, 9, 8, 6, 3, 5, 4, 1, 0, 2])
        self.assertEqual(cseg.reduction_bor_53(), [[12, 10, 13, 0, 2], 2])

    def test_reduction_bor_355(self):
        cseg = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_355(), [[7, 10, 0, 5], 3])

    def test_reduction_bor_555(self):
        cseg = contour.Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_555(), [[7, 10, 0, 5], 3])

    def test_fuzzy_membership_matrix(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([1, 2, 3, 0, 3, 1])
        result1 = [[0, 1, 1, 1],
                   [0, 0, 1, 0],
                   [0, 0, 0, 0],
                   [0, 1, 1, 0]]
        result2 = [[0, 1, 1, 0, 1, 0],
                   [0, 0, 1, 0, 1, 0],
                   [0, 0, 0, 0, 0, 0],
                   [1, 1, 1, 0, 1, 1],
                   [0, 0, 0, 0, 0, 0],
                   [0, 1, 1, 0, 1, 0]]
        self.assertEqual(cseg1.fuzzy_membership_matrix(), result1)
        self.assertEqual(cseg2.fuzzy_membership_matrix(), result2)

    def test_fuzzy_comparison_matrix(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([1, 2, 3, 0, 3, 1])
        result1 = [[0, 1, 1, 1], [-1, 0, 1, -1], [-1, -1, 0, -1], [-1, 1, 1, 0]]
        result2 =  [[0, 1, 1, -1, 1, 0],
                    [-1, 0, 1, -1, 1, -1],
                    [-1, -1, 0, -1, 0, -1],
                    [1, 1, 1, 0, 1, 1],
                    [-1, -1, 0, -1, 0, -1],
                    [0, 1, 1, -1, 1, 0]]
        self.assertEqual(cseg1.fuzzy_comparison_matrix(), result1)
        self.assertEqual(cseg2.fuzzy_comparison_matrix(), result2)


if __name__ == '__main__':
    unittest.main()
