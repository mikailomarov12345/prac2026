"""Юнит-тесты клиента с использованием мокеров (без запуска сервера)."""

import unittest
from unittest.mock import MagicMock
import queue

from mood.client.main import MudCmd


class TestClientCommands(unittest.TestCase):
    """Тестирование преобразования пользовательских команд в протокол."""

    def setUp(self):
        self.q = queue.Queue()
        self.client = MagicMock()
        self.mud_cmd = MudCmd(self.q, self.client)

    # ---- движение ----

    def test_up_sends_correct_protocol(self):
        self.mud_cmd.do_up("")
        self.assertEqual(self.q.get_nowait(), "up")

    def test_down_sends_correct_protocol(self):
        self.mud_cmd.do_down("")
        self.assertEqual(self.q.get_nowait(), "down")

    def test_left_sends_correct_protocol(self):
        self.mud_cmd.do_left("")
        self.assertEqual(self.q.get_nowait(), "left")

    def test_right_sends_correct_protocol(self):
        self.mud_cmd.do_right("")
        self.assertEqual(self.q.get_nowait(), "right")

    # ---- attack (два разных параметра) ----

    def test_attack_with_sword(self):
        self.mud_cmd.do_attack("dragon with sword")
        self.assertEqual(self.q.get_nowait(), "attack dragon with sword")

    def test_attack_with_axe(self):
        self.mud_cmd.do_attack("dragon with axe")
        self.assertEqual(self.q.get_nowait(), "attack dragon with axe")

    # ---- attack: неверный ввод -> ничего не отправляется ----

    def test_attack_empty_sends_nothing(self):
        self.mud_cmd.do_attack("")
        self.assertTrue(self.q.empty())

    # ---- addmon (два разных набора параметров) ----

    def test_addmon_basic(self):
        self.mud_cmd.do_addmon("dragon 1 2 Hello 50")
        self.assertEqual(self.q.get_nowait(), "addmon dragon 1 2 Hello 50")

    def test_addmon_different_coords(self):
        self.mud_cmd.do_addmon("cow 5 7 Moo 30")
        self.assertEqual(self.q.get_nowait(), "addmon cow 5 7 Moo 30")


if __name__ == "__main__":
    unittest.main()
