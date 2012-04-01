import unittest
import contour
import comparison


class TestUtils(unittest.TestCase):
    def test_cseg_similarity(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([3, 1, 0, 2])
        cseg3 = contour.Contour([1, 0, 4, 3, 2])
        cseg4 = contour.Contour([3, 0, 4, 2, 1])
        cseg5 = contour.Contour([0, 1, 2, 3, 4, 5, 6])
        cseg6 = contour.Contour([2, 6, 5, 4, 1, 0, 3])
        self.assertEqual(comparison.cseg_similarity(cseg1, cseg2), 0)
        self.assertEqual(comparison.cseg_similarity(cseg3, cseg4), 0.8)
        self.assertEqual(comparison.cseg_similarity(cseg5, cseg6), 0.2857142857142857)

    def test_csegclass_similarity(self):
        cseg1 = contour.Contour([0, 2, 3, 1])
        cseg2 = contour.Contour([3, 1, 0, 2])
        self.assertEqual(comparison.csegclass_similarity(cseg1, cseg2), 1)

    def test_subsets_embed_total_number(self):
        cseg1 = contour.Contour([0, 1, 2, 3])
        cseg2 = contour.Contour([1, 0, 2])
        cseg3 = contour.Contour([0, 1, 3, 2])
        cseg4 = contour.Contour([1, 0, 2])
        self.assertEqual(comparison.subsets_embed_total_number(cseg1, cseg2), 4)
        self.assertEqual(comparison.subsets_embed_total_number(cseg3, cseg4), 4)

    def test_subsets_embed_number(self):
        cseg1 = contour.Contour([0, 2, 1, 3])
        cseg2 = contour.Contour([0, 1, 2])
        self.assertEqual(comparison.subsets_embed_number(cseg1, cseg2), 2)

    def test_contour_embed(self):
        cseg1 = contour.Contour([0, 2, 1, 3])
        cseg2 = contour.Contour([0, 1, 2])
        cseg3 = contour.Contour([0, 2, 1, 3, 4])
        cseg4 = contour.Contour([0, 1, 2])
        self.assertEqual(comparison.contour_embed(cseg1, cseg2), 0.5)
        self.assertEqual(comparison.contour_embed(cseg3, cseg4), 0.7)

    def test_csubseg_mutually_embed(self):
        cseg1 = contour.Contour([1, 0, 4, 3, 2])
        cseg2 = contour.Contour([2, 0, 1, 4, 3])
        self.assertEqual(comparison.csubseg_mutually_embed(3, cseg1, cseg2), 0.8)
        self.assertEqual(comparison.csubseg_mutually_embed(5, cseg1, cseg2), 0.5)

    def test_all_contour_mutually_embed(self):
        cseg1 = contour.Contour([0, 1, 2, 3])
        cseg2 = contour.Contour([0, 2, 1, 3])
        cseg3 = contour.Contour([0, 2, 1, 3, 4])
        self.assertEqual(comparison.all_contour_mutually_embed(cseg1, cseg2), 17.0 / 22)
        self.assertEqual(comparison.all_contour_mutually_embed(cseg1, cseg3), 29.0 / 37)
        self.assertEqual(comparison.all_contour_mutually_embed(cseg2, cseg3), 33.0 / 37)


if __name__ == '__main__':
    unittest.main()
