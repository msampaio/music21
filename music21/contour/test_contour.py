import unittest
import contour
from contour import Contour
from matrix import ComparisonMatrix
from diagonal import InternalDiagonal
from fuzzy import FuzzyMatrix


class TestUtils(unittest.TestCase):
    def test_logical(self):
        self.assertNotEqual(Contour([0, 1, 2]), Contour([0, 1]))

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
        cseg = Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.rotation(), Contour([4, 9, 9, 2, 1, 1]))
        self.assertEqual(cseg.rotation(1), Contour([4, 9, 9, 2, 1, 1]))
        self.assertEqual(cseg.rotation(2), Contour([9, 9, 2, 1, 1, 4]))
        self.assertEqual(cseg.rotation(20), Contour([9, 9, 2, 1, 1, 4]))

    def test_retrogression(self):
        cseg = Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.retrogression(), Contour([1, 2, 9, 9, 4, 1]))

    def test_inversion(self):
        cseg = Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.inversion(), Contour([8, 5, 0, 0, 7, 8]))

    def test_translation(self):
        cseg = Contour([1, 4, 9, 9, 2, 1])
        self.assertEqual(cseg.translation(), Contour([0, 2, 3, 3, 1, 0]))

    def test_prime_form_marvin_laprade(self):
        cseg1 = Contour([1, 4, 9, 2])
        cseg2 = Contour([5, 7, 9, 1])
        cseg3 = Contour([5, 7, 9, 1])
        cseg4 = Contour([0, 2, 1, 3, 4])
        cseg5 = Contour([0, 1, 2, 3, 2])
        cseg6 = Contour([1, 2, 3, 0, 3, 1])
        cseg7 = Contour([0, 1, 2, 1, 2])
        self.assertEqual(cseg1.prime_form_marvin_laprade(), Contour([0, 2, 3, 1]))
        self.assertEqual(cseg2.prime_form_marvin_laprade(), Contour([0, 3, 2, 1]))
        self.assertEqual(cseg3.prime_form_marvin_laprade(), Contour([0, 3, 2, 1]))
        self.assertEqual(cseg4.prime_form_marvin_laprade(), Contour([0, 2, 1, 3, 4]))
        self.assertEqual(cseg5.prime_form_marvin_laprade(), [Contour([0, 1, 2, 4, 3]), Contour([0, 1, 3, 4, 2])])
        ## FIXME: wrong test
        # self.assertEqual(cseg6.prime_form_marvin_laprade(), [Contour([1, 3, 4, 0, 5, 2]), Contour([1, 4, 0, 5, 3, 2])])
        self.assertEqual(cseg7.prime_form_marvin_laprade(), [Contour([0, 1, 3, 2, 4]), Contour([0, 2, 4, 1, 3])])

    def test_comparison_matrix(self):
        cseg1 = Contour([0, 2, 3, 1])
        cseg2 = Contour([1, 2, 3, 0, 3, 1])
        result1 = ComparisonMatrix([[0, 1, 1, 1], [-1, 0, 1, -1], [-1, -1, 0, -1], [-1, 1, 1, 0]])
        result2 = ComparisonMatrix([[0, 1, 1, -1, 1, 0], [-1, 0, 1, -1, 1, -1], [-1, -1, 0, -1, 0, -1],
                                    [1, 1, 1, 0, 1, 1], [-1, -1, 0, -1, 0, -1], [0, 1, 1, -1, 1, 0]])
        self.assertEqual(cseg1.comparison_matrix(), result1)
        self.assertEqual(cseg2.comparison_matrix(), result2)

    def test_internal_diagonals(self):
        cseg1 = Contour([0, 2, 3, 1])
        cseg2 = Contour([1, 0, 4, 3, 2])
        self.assertEqual(cseg1.internal_diagonals(1), InternalDiagonal([1, 1, -1]))
        self.assertEqual(cseg1.internal_diagonals(2), InternalDiagonal([1, -1]))
        self.assertEqual(cseg2.internal_diagonals(1), InternalDiagonal([-1, 1, -1, -1]))
        self.assertEqual(cseg2.internal_diagonals(2), InternalDiagonal([1, 1, -1]))

    def test_interval_succession(self):
        cseg = Contour([0, 1, 3, 2])
        self.assertEqual(cseg.interval_succession(), [1, 2, -1])

    def test_adjacency_series_vector(self):
        cseg1 = Contour([0, 2, 3, 1])
        cseg2 = Contour([1, 2, 3, 0, 3, 1])
        self.assertEqual(cseg1.adjacency_series_vector(), [2, 1])
        self.assertEqual(cseg2.adjacency_series_vector(), [3, 2])

    def test_interval_array(self):
        cseg = Contour([0, 1, 3, 2])
        self.assertEqual(cseg.interval_array(), ([2, 2, 1], [1, 0, 0]))

    def test_class_vector_i(self):
        cseg = Contour([0, 1, 3, 2])
        self.assertEqual(cseg.class_vector_i(), [9, 1])

    def test_class_vector_ii(self):
        cseg = Contour([0, 1, 3, 2])
        self.assertEqual(cseg.class_vector_ii(), [5, 1])

    def test_class_representatives(self):
        cseg = Contour([0, 1, 3, 2])
        result = [Contour([0, 1, 3, 2]), Contour([3, 2, 0, 1]), Contour([2, 3, 1, 0]), Contour([1, 0, 2, 3])]
        self.assertEqual(cseg.class_representatives(), result)

    ## FIXME: wrong test
    # def test_subsets(self):
    #     cseg = Contour([2, 8, 12, 9])
    #     result1 = [Contour([2, 8]), Contour([2, 9]), Contour([2, 12]), Contour([8, 9]), Contour([8, 12]), Contour([12, 9])]
    #     result2 = [Contour([2, 8, 9]), Contour([2, 8, 12]), Contour([2, 12, 9]), Contour([8, 12, 9])]
    #     self.assertEqual(cseg.subsets(2), result1)
    #     self.assertEqual(cseg.subsets(3), result2)

    def test_subsets_normal(self):
        cseg = Contour([0, 3, 1, 4, 2])
        result = {(0, 1, 3, 2): [Contour([0, 1, 4, 2])],
                  (0, 2, 1, 3): [Contour([0, 3, 1, 4])],
                  (0, 2, 3, 1): [Contour([0, 3, 4, 2])],
                  (0, 3, 1, 2): [Contour([0, 3, 1, 2])],
                  (2, 0, 3, 1): [Contour([3, 1, 4, 2])]}
        self.assertEqual(cseg.subsets_normal(4), result)

    def test_cps_position(self):
        cseg = Contour([2, 8, 12, 9, 5, 7, 3, 12, 3, 7])
        result = [(2, 0), (8, 1), (12, 2), (9, 3), (5, 4),
                  (7, 5), (3, 6), (12, 7), (3, 8), (7, 9)]
        self.assertEqual(cseg.cps_position(), result)

    def test_reduction_morris(self):
        cseg1 = Contour([0, 4, 3, 2, 5, 5, 1])
        cseg2 = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg1.reduction_morris(), [Contour([0, 2, 1]), 2])
        self.assertEqual(cseg2.reduction_morris(), [Contour([2, 3, 0, 1]), 3])

    def test_reduction_window_3(self):
        cseg = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_window_3(False), Contour([7, 10, 0, 3, 1, 8, 2, 5]))
        self.assertEqual(cseg.reduction_window_3(True), Contour([5, 7, 0, 3, 1, 6, 2, 4]))

    def test_reduction_window_5(self):
        cseg1 = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        cseg2 = Contour([7, 10, 0, 1, 8, 2, 5])
        cseg3 = Contour([7, 10, 0, 8, 5])
        cseg4 = Contour([0, 3, 3, 1, 2, 4])
        cseg5 = Contour([0, 3, 3, 1, 2])
        cseg6 = Contour([12, 10, 13, 11, 7, 9, 8, 6, 3, 5, 4, 1, 0, 2])
        self.assertEqual(cseg1.reduction_window_5(False), Contour([7, 10, 0, 1, 8, 2, 5]))
        self.assertEqual(cseg2.reduction_window_5(False), Contour([7, 10, 0, 8, 5]))
        self.assertEqual(cseg3.reduction_window_5(False), Contour([7, 10, 0, 5]))
        self.assertEqual(cseg4.reduction_window_5(False), Contour([0, 3, 1, 4]))
        self.assertEqual(cseg5.reduction_window_5(False), Contour([0, 3, 1, 2]))
        self.assertEqual(cseg6.reduction_window_5(False), Contour([12, 10, 13, 7, 3, 0, 2]))

    def test_reduction_bor_35(self):
        cseg = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_35(False), [Contour([7, 10, 0, 8, 5]), 2])

    def test_reduction_bor_53(self):
        cseg = Contour([12, 10, 13, 11, 7, 9, 8, 6, 3, 5, 4, 1, 0, 2])
        self.assertEqual(cseg.reduction_bor_53(False), [Contour([12, 10, 13, 0, 2]), 2])

    def test_reduction_bor_355(self):
        cseg = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_355(False), [Contour([7, 10, 0, 5]), 3])

    def test_reduction_bor_555(self):
        cseg = Contour([7, 10, 9, 0, 2, 3, 1, 8, 6, 2, 4, 5])
        self.assertEqual(cseg.reduction_bor_555(False), [Contour([7, 10, 0, 5]), 3])

    def test_fuzzy_membership_matrix(self):
        cseg1 = Contour([0, 2, 3, 1])
        cseg2 = Contour([1, 2, 3, 0, 3, 1])
        result1 = FuzzyMatrix([[0, 1, 1, 1],
                               [0, 0, 1, 0],
                               [0, 0, 0, 0],
                               [0, 1, 1, 0]])
        result2 = FuzzyMatrix([[0, 1, 1, 0, 1, 0],
                               [0, 0, 1, 0, 1, 0],
                               [0, 0, 0, 0, 0, 0],
                               [1, 1, 1, 0, 1, 1],
                               [0, 0, 0, 0, 0, 0],
                               [0, 1, 1, 0, 1, 0]])
        self.assertEqual(cseg1.fuzzy_membership_matrix(), result1)
        self.assertEqual(cseg2.fuzzy_membership_matrix(), result2)

    def test_fuzzy_comparison_matrix(self):
        cseg1 = Contour([0, 2, 3, 1])
        cseg2 = Contour([1, 2, 3, 0, 3, 1])
        result1 = FuzzyMatrix([[0, 1, 1, 1], [-1, 0, 1, -1], [-1, -1, 0, -1], [-1, 1, 1, 0]])
        result2 =  FuzzyMatrix([[0, 1, 1, -1, 1, 0],
                                [-1, 0, 1, -1, 1, -1],
                                [-1, -1, 0, -1, 0, -1],
                                [1, 1, 1, 0, 1, 1],
                                [-1, -1, 0, -1, 0, -1],
                                [0, 1, 1, -1, 1, 0]])
        self.assertEqual(cseg1.fuzzy_comparison_matrix(), result1)
        self.assertEqual(cseg2.fuzzy_comparison_matrix(), result2)

    def test_base_three_representation(self):
        self.assertEqual(Contour([0, 1]).base_three_representation(), [[2]])
        self.assertEqual(Contour([1, 0]).base_three_representation(), [[0]])
        self.assertEqual(Contour([0, 1, 0]).base_three_representation(), [[2, 1], [0]])
        self.assertEqual(Contour([0, 1, 2]).base_three_representation(), [[2, 2], [2]])
        self.assertEqual(Contour([0, 2, 1]).base_three_representation(), [[2, 2], [0]])

    def test_possible_cseg(self):
        self.assertEqual(contour.possible_cseg([[2, 2], [2]]), Contour([0, 1, 2]))
        self.assertEqual(contour.possible_cseg([[0, 2], [1]]), "Impossible cseg")


if __name__ == '__main__':
    unittest.main()
