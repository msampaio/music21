import unittest
import utils


class TestUtils(unittest.TestCase):
    def test_replace_all(self):
        list1 = [0, 3, 2, 0]
        self.assertEqual(utils.replace_all(list1, -1), [-1, 3, 2, -1])
        self.assertEqual(utils.replace_all(list1, "a"), ["a", 3, 2, "a"])

    def test_greatest_first(self):
        result = utils.greatest_first([0, 1], [3, 2, 1])
        self.assertEqual(result, [[3, 2, 1], [0, 1]])

    def test_flatten(self):
        result = utils.flatten([[0, 1], [2, 3]])
        self.assertEqual(result, [0, 1, 2, 3])


if __name__ == '__main__':
    unittest.main()
