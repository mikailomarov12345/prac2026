"""The main logic of the MUD game client."""

import time
import asyncio
import threading
import queue
from io import StringIO

import cowsay

from mood.common import JGSBAT_ASCII_ART

DIRECTIONS = ("up", "down", "left", "right")
WEAPONS_NAMES = ("sword", "spear", "axe")

class InvalidCommand(Exception):
    """Команда не распознана / параметры неправильные."""

class MudClient:
    """Асинхронный клиент для подключения к MUD серверу."""

    def __init__(self, host, port, username, script_file=None):
        """Инициализация клиента.

        Args:
            host: Адрес сервера
            port: Порт сервера
            username: Имя пользователя
        """
        self.host = host
        self.port = port
        self.username = username
        self.script_file = script_file
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
    def parse_command(self, user_input):
        """Преобразовать пользовательский ввод в строку протокольной команды."""
        if user_input is None or not user_input.strip():
            raise InvalidCommand("empty input")
        parts = user_input.strip().split()
        cmd, args = parts[0], parts[1:]

        # "move <direction>"  ->  "<direction>"
        if cmd == "move":
            if len(args) != 1:
                raise InvalidCommand("move requires direction")
            if args[0] not in DIRECTIONS:
                raise InvalidCommand(f"unknown direction '{args[0]}'")
            return args[0]

        # "attack <monster> [<weapon>]"  ->  "attack <monster> with <weapon>"
        if cmd == "attack":
            if len(args) == 1:
                return f"attack {args[0]} with sword"
            if len(args) == 2:
                if args[1] not in WEAPONS_NAMES:
                    raise InvalidCommand(f"unknown weapon '{args[1]}'")
                return f"attack {args[0]} with {args[1]}"
            raise InvalidCommand("attack requires monster and optional weapon")

        # остальные команды — как есть
        return user_input.strip()

    async def send_command(self, user_input):
        """Распарсить ввод и отправить серверу. False — если ввод невалиден."""
        try:
            protocol_cmd = self.parse_command(user_input)
        except InvalidCommand as e:
            print(f"Ошибка команды: {e}")
            return False
        self.writer.write((protocol_cmd + "\n").encode())
        await self.writer.drain()
        return True

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
        if self.script_file:
            try:
                with open(self.script_file, 'r') as f:
                    commands = [line.strip() for line in f if line.strip()]
                for cmd in commands:
                    if not self.running:
                        break
                    self.input_queue.put(cmd)
                    time.sleep(1)  # Интервал 1 секунда
            except FileNotFoundError:
                print(f"Файл {self.script_file} не найден")
                self.running = False
            except Exception as e:
                print(f"Ошибка чтения файла: {e}")
                self.running = False
            self.running = False
        else:
            print("Команды: up, down, left, right, addmon, attack, sayall, movemonsters, locale, quit")
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
