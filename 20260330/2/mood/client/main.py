"""The main logic of the MUD game client."""

import asyncio
import threading
import queue
from io import StringIO

import cowsay

from mood.common import JGSBAT_ASCII_ART


class MudClient:
    """Асинхронный клиент для подключения к MUD серверу."""

    def __init__(self, host, port, username):
        """Инициализация клиента.

        Args:
            host: Адрес сервера
            port: Порт сервера
            username: Имя пользователя
        """
        self.host = host
        self.port = port
        self.username = username
        self.reader = None
        self.writer = None
        self.running = True
        self.input_queue = queue.Queue()

        # Загружаем кастомного монстра (для новой версии cowsay)
        try:
            # Пробуем новый API
            self.jgsbat = cowsay.read_dot_cow(StringIO(JGSBAT_ASCII_ART))
        except AttributeError:
            # Старый API
            self.jgsbat = cowsay.read_dot_cow(StringIO(JGSBAT_ASCII_ART))
        except Exception:
            # Если ничего не работает, создаём простой cow
            self.jgsbat = None

    def render_encounter(self, name, hello):
        """Отрисовка встречи с монстром с помощью cowsay.

        Args:
            name: Имя монстра
            hello: Приветствие
        """
        try:
            if name == "jgsbat" and self.jgsbat:
                print(cowsay.cowsay(hello, cowfile=self.jgsbat))
            else:
                print(cowsay.cowsay(hello, cow=name))
        except Exception as e:
            # Fallback - просто печатаем текст
            print(f"Встреча с {name}: {hello}")
            print(f"Ошибка отрисовки: {e}")

    async def connect(self):
        """Подключение к серверу и регистрация имени."""
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port
        )
        self.writer.write((self.username + "\n").encode())
        await self.writer.drain()

        response = await self.reader.readline()
        if response.decode().strip() == "ERROR":
            print("Имя уже используется")
            return False
        print("Подключено!")
        return True

    async def receive_messages(self):
        """Асинхронный приём сообщений от сервера."""
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = data.decode().strip()

                # Обработка встречи с монстром
                if msg.startswith("ENCOUNTER"):
                    # Формат: ENCOUNTER имя приветствие
                    parts = msg.split(maxsplit=2)
                    if len(parts) == 3:
                        _, name, hello = parts
                        self.render_encounter(name, hello)
                else:
                    print(f"\n{msg}")

                print("> ", end="", flush=True)
            except (asyncio.CancelledError, ConnectionError):
                break
            except Exception as e:
                print(f"Ошибка приёма: {e}")
                break

    def input_loop(self):
        """Цикл чтения ввода пользователя в отдельном потоке."""
        print("Команды: up, down, left, right, addmon, attack, sayall, quit")
        while self.running:
            try:
                line = input("> ")
                if line == "quit":
                    self.running = False
                    break
                if line:
                    self.input_queue.put(line)
            except EOFError:
                break

    async def run(self):
        """Основной цикл работы клиента."""
        if not await self.connect():
            return

        # Запускаем поток ввода
        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()

        # Запускаем приём сообщений
        receive_task = asyncio.create_task(self.receive_messages())

        # Отправка команд
        while self.running:
            try:
                cmd = self.input_queue.get_nowait()
                self.writer.write((cmd + "\n").encode())
                await self.writer.drain()
            except queue.Empty:
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Ошибка: {e}")
                break

        receive_task.cancel()
        self.writer.close()
        await self.writer.wait_closed()
