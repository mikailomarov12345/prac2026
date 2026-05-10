"""Тесты преобразования команд клиента из пользовательского формата в протокол.
 
Сервер в этих тестах не запускается. Цепочка
    user input -> parse_command -> writer.write
тестируется через мокеры:
    * builtins.input         — последовательность пользовательских команд
    * MudClient.writer       — AsyncMock/MagicMock со счётчиком вызовов
 
Выбраны две команды, у которых пользовательский формат отличается от
протокольного:
 
    1) "move <direction>"             ->  "<direction>"
       (например "move up"            ->  "up")
    2) "attack <monster> [<weapon>]"  ->  "attack <monster> with <weapon>"
       (например "attack dragon axe"  ->  "attack dragon with axe")
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
 
from mood.client.main import MudClient, InvalidCommand
 
 
def make_client():
    """Клиент без сетевого ввода-вывода — для парсера этого достаточно."""
    return MudClient(host="localhost", port=1337, username="tester")
 
 
# --------------------------------------------------------------------------
# 1) Команда "move <direction>"  ->  "<direction>"
# --------------------------------------------------------------------------
class TestParseMove(unittest.TestCase):
    """Преобразование команды движения."""
 
    def setUp(self):
        self.client = make_client()
 
    def test_move_up(self):
        self.assertEqual(self.client.parse_command("move up"), "up")
 
    def test_move_left(self):
        # второе направление, отличающееся от первого
        self.assertEqual(self.client.parse_command("move left"), "left")
 
    def test_move_unknown_direction(self):
        # неправильный параметр — должен быть отвергнут
        with self.assertRaises(InvalidCommand):
            self.client.parse_command("move forwards")
 
    def test_move_no_argument(self):
        # тоже неправильный ввод — нет направления вовсе
        with self.assertRaises(InvalidCommand):
            self.client.parse_command("move")
 
 
# --------------------------------------------------------------------------
# 2) Команда "attack <monster> [<weapon>]"  ->  "attack <monster> with <weapon>"
# --------------------------------------------------------------------------
class TestParseAttack(unittest.TestCase):
    """Преобразование команды атаки."""
 
    def setUp(self):
        self.client = make_client()
 
    def test_attack_with_sword(self):
        self.assertEqual(
            self.client.parse_command("attack dragon sword"),
            "attack dragon with sword",
        )
 
    def test_attack_with_axe(self):
        # другие значения параметров (другой монстр, другое оружие)
        self.assertEqual(
            self.client.parse_command("attack goblin axe"),
            "attack goblin with axe",
        )
 
    def test_attack_unknown_weapon(self):
        # неправильный параметр оружия
        with self.assertRaises(InvalidCommand):
            self.client.parse_command("attack dragon stick")
 
 
# --------------------------------------------------------------------------
# 3) Полная цепочка: input() -> parse_command -> writer.write
#    Через мокер input возвращаем последовательность пользовательских
#    команд; writer мокаем, чтобы посмотреть что в него ушло.
# --------------------------------------------------------------------------
class TestFullChainWithMocks(unittest.TestCase):
    """Проверка всей цепочки от пользовательского ввода до отправки."""
 
    def test_chain_two_commands(self):
        client = make_client()
 
        # Мокер writer — фиксирует все вызовы .write(...)
        client.writer = MagicMock()
        client.writer.drain = AsyncMock()
 
        # Мокер input — возвращает последовательность команд
        user_inputs = ["move down", "attack dragon spear"]
 
        async def run_chain():
            with patch("builtins.input", side_effect=user_inputs):
                for _ in range(len(user_inputs)):
                    user_cmd = input("> ")
                    await client.send_command(user_cmd)
 
        asyncio.run(run_chain())
 
        # В сокет должны были уйти преобразованные команды
        sent_payloads = [
            call.args[0] for call in client.writer.write.call_args_list
        ]
        self.assertEqual(
            sent_payloads,
            [b"down\n", b"attack dragon with spear\n"],
        )
 
    def test_chain_skips_invalid_command(self):
        """Неправильная команда не должна доходить до writer.write."""
        client = make_client()
        client.writer = MagicMock()
        client.writer.drain = AsyncMock()
 
        user_inputs = ["move sideways", "move right"]
 
        async def run_chain():
            with patch("builtins.input", side_effect=user_inputs):
                for _ in range(len(user_inputs)):
                    user_cmd = input("> ")
                    await client.send_command(user_cmd)
 
        asyncio.run(run_chain())
 
        # Только корректная команда дошла до отправки.
        sent_payloads = [
            call.args[0] for call in client.writer.write.call_args_list
        ]
        self.assertEqual(sent_payloads, [b"right\n"])
 
 
if __name__ == "__main__":
    unittest.main()
