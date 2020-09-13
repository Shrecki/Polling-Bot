import unittest
from core import *
from unittest import mock
from bdd_handler_mock import query_bdd_for_player_mock

class MyTestCase(unittest.TestCase):
    @mock.patch('bdd_handler.query_bdd_for_player', side_effect=query_bdd_for_player_mock)
    def test_something(self, query_bdd_function):
        array_p_1 = np.asarray([[0, 100000], [200000, 500000], [700000, 1100000]])
        array_p_2 = np.asarray([[3, 90000], [150000, 310000]])
        array_p_3 = np.asarray([[2, 80000], [170000, 700000]])

        interval = find_intersections([array_p_1, array_p_2, array_p_3], minimum_length=4)
        print(interval)

        print(find_intersections([array_p_1], minimum_length=4))

        player_0_data = convert_player_json(188626510901542912, 0, 0, 90000)
        player_1_data = convert_player_json(265523588918935552, 0, 0, 90000)
        player_2_data = convert_player_json(298673420181438465, 0, 0, 90000)

        assert (np.all(player_0_data == array_p_1))
        assert (np.all(player_1_data == array_p_2))
        assert (np.all(player_2_data == array_p_3))


if __name__ == '__main__':
    unittest.main()
