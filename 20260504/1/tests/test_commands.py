"""Юнит-тесты на отработку сервером команд от клиента.
 
setup    -> запуск сервера (multiprocessing.Process(target=run_server, ...))
            и подключение к нему сокетом
teardown -> закрытие соединения и proc.terminate()
тесты    -> отправка команды в формате протокола и проверка ответа сервера
"""
import multiprocessing
import socket
import time
import unittest
 
from mood.server.main import run_server
 
 
HOST = "127.0.0.1"
PORT = 12345
 
 
def _readline(f, timeout=2.0):
    """Прочитать одну строку с тайм-аутом."""
    deadline = time.monotonic() + timeout
    while True:
        line = f.readline()
        if line:
            return line.rstrip(b"\r\n").decode()
        if time.monotonic() > deadline:
            raise TimeoutError("no data from server")
        time.sleep(0.01)
 
 
class ServerCommandsTests(unittest.TestCase):
    """Связка клиент+сервер: проверяем ответы сервера на команды."""
 
    @classmethod
    def setUpClass(cls):
        ctx = multiprocessing.get_context("spawn")
        cls.proc = ctx.Process(
            target=run_server, args=(HOST, PORT), daemon=True
        )
        cls.proc.start()
 
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((HOST, PORT), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            cls.proc.terminate()
            raise RuntimeError("Server did not start in time")
 
    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.join(timeout=3)
 
    def setUp(self):
        self.sock = socket.create_connection((HOST, PORT))
        self.sock.settimeout(2.0)
        self.f = self.sock.makefile("rb")
        self.username = (
            f"player_{self._testMethodName}_{int(time.time() * 1000)}"
        )
        self.sock.sendall((self.username + "\n").encode())
        self.assertEqual(_readline(self.f), "WELCOME")
        self.assertTrue(_readline(self.f).startswith("POSITION"))
 
    def tearDown(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
 
    # ---- сами тесты команд ----
 
    def test_addmon(self):
        """Установка монстра недалеко от начального положения игрока."""
        self.sock.sendall(b"addmon 1 0 dragon Hello 50\n")
        self.assertEqual(_readline(self.f), "ADDMON 1 0 dragon Hello 50")
 
    def test_encounter_on_move(self):
        """Подход к монстру -> сервер присылает ENCOUNTER + приветствие."""
        self.sock.sendall(b"addmon 1 0 dragon Hello 50\n")
        self.assertEqual(_readline(self.f), "ADDMON 1 0 dragon Hello 50")
        self.sock.sendall(b"right\n")
        self.assertEqual(_readline(self.f), "ENCOUNTER dragon Hello")
 
    def test_attack(self):
        """Атака на монстра -> ATTACK HIT с уроном и оставшимися HP."""
        self.sock.sendall(b"addmon 1 0 dragon Hello 50\n")
        self.assertEqual(_readline(self.f), "ADDMON 1 0 dragon Hello 50")
        self.sock.sendall(b"right\n")
        self.assertEqual(_readline(self.f), "ENCOUNTER dragon Hello")
        self.sock.sendall(b"attack dragon with sword\n")
        # sword = 10 урона, у дракона 50 HP -> остаётся 40
        self.assertEqual(_readline(self.f), "ATTACK HIT dragon 10 40")

    def test_locale_ru_response(self):
        """После locale ru_RU сервер отвечает по-русски."""
        self.sock.sendall(b"locale ru_RU\n")
        line = _readline(self.f)
        # сервер шлёт переведённое "Set up locale: ru_RU"
        self.assertIn("ru_RU", line)
        self.assertNotEqual(line, "Set up locale: ru_RU")
 
if __name__ == "__main__":
    unittest.main()
