import unittest
import auxiliary


class TestUtils(unittest.TestCase):
    def test_interval(self):
        self.assertEqual(auxiliary.interval([4, 0]), -4)

    def test_position_comparison(self):
        self.assertEqual(auxiliary.position_comparison([0, 1, 2, 3], [0, 1, 3, 2]), 0.5)

    def test_base_3_comparison(self):
        self.assertEqual(auxiliary.base_3_comparison(1, 0), 0)
        self.assertEqual(auxiliary.base_3_comparison(1, 1), 1)
        self.assertEqual(auxiliary.base_3_comparison(0, 1), 2)

if __name__ == '__main__':
    unittest.main()
