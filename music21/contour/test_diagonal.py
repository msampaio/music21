import unittest
from diagonal import InternalDiagonal
from contour import Contour

class TestUtils(unittest.TestCase):
    def test_csegs(self):
        i1 = InternalDiagonal([-1, 1])
        i2 = InternalDiagonal([-1, 1, 1])
        self.assertEqual(i1.csegs(), [Contour([1, 0, 2]), Contour([2, 0, 1])])
        self.assertEqual(i2.csegs(), [Contour([1, 0, 2, 3]), Contour([2, 0, 1, 3]),
                                      Contour([3, 0, 1, 2])])

    def test_inversion_Int(self):
        i1 = InternalDiagonal([-1, 1])
        i2 = InternalDiagonal([-1, 1, 1])
        self.assertEqual(i1.inversion(), InternalDiagonal([1, -1]))
        self.assertEqual(i2.inversion(), InternalDiagonal([1, -1, -1]))

    def test_rotation_Int(self):
        i1 = InternalDiagonal([1, 1, 0, -1, -1, 1])
        i2 = InternalDiagonal([1, 1, 0, -1, -1, 1])
        i3 = InternalDiagonal([1, 1, 0, -1, -1, 1])
        i4 = InternalDiagonal([1, 1, 0, -1, -1, 1])
        self.assertEqual(i1.rotation(), InternalDiagonal([1, 0, -1, -1, 1, 1]))
        self.assertEqual(i2.rotation(1), InternalDiagonal([1, 0, -1, -1, 1, 1]))
        self.assertEqual(i3.rotation(2), InternalDiagonal([0, -1, -1, 1, 1, 1]))
        self.assertEqual(i4.rotation(20), InternalDiagonal([0, -1, -1, 1, 1, 1]))


if __name__ == '__main__':
    unittest.main()
