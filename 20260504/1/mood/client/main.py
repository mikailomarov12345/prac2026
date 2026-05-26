"""The main logic of the MUD game client."""

import cmd
import time
import asyncio
import threading
import queue
from io import StringIO

import cowsay

from mood.common import JGSBAT_ASCII_ART


class MudCmd(cmd.Cmd):
    """MUD game client with command line support."""

    prompt = "> "

    def __init__(self, input_queue, client):
        super().__init__()
        self.input_queue = input_queue
        self.client = client

    def do_up(self, _): self.input_queue.put("up")
    def do_down(self, _): self.input_queue.put("down")
    def do_left(self, _): self.input_queue.put("left")
    def do_right(self, _): self.input_queue.put("right")

    def do_addmon(self, arg):
        self.input_queue.put(f"addmon {arg}")

    def do_attack(self, arg):
        if not arg.strip():
            print("Invalid arguments. Usage: attack <name> [with <weapon>]")
            return
        self.input_queue.put(f"attack {arg}")

    def complete_attack(self, text, line, begidx, endidx):
        parts = line.split()
        if "with" in parts:
            return [w for w in ["sword", "spear", "axe"] if w.startswith(text)]
        if len(parts) >= 2:
            return ["with"] if "with".startswith(text) else []
        return [n for n in cowsay.list_cows() + ["jgsbat"] if n.startswith(text)]

    def do_sayall(self, arg): self.input_queue.put(f"sayall {arg}")
    def do_movemonsters(self, arg): self.input_queue.put(f"movemonsters {arg}")
    def do_locale(self, arg): self.input_queue.put(f"locale {arg}")

    def do_quit(self, _):
        self.client.running = False
        return True

    def do_EOF(self, _):
        self.client.running = False
        return True

    def default(self, line):
        print("Invalid command")


class MudClient:
    """Async client for connecting to MUD server."""

    def __init__(self, host, port, username, script_file=None):
        """Initialize the client.

        Args:
            host: Server address
            port: Server port
            username: Player username
            script_file: Path to .mood script file, or None

        """
        self.host = host
        self.port = port
        self.username = username
        self.script_file = script_file
        self.reader = None
        self.writer = None
        self.running = True
        self.input_queue = queue.Queue()

        try:
            self.jgsbat = cowsay.read_dot_cow(StringIO(JGSBAT_ASCII_ART))
        except Exception:
            self.jgsbat = None

    def render_encounter(self, name, hello):
        """Render monster encounter using cowsay.

        Args:
            name: Monster name
            hello: Monster greeting

        """
        try:
            if name == "jgsbat" and self.jgsbat:
                print(cowsay.cowsay(hello, cowfile=self.jgsbat))
            else:
                print(cowsay.cowsay(hello, cow=name))
        except Exception as e:
            print(f"Encounter with {name}: {hello}")
            print(f"Render error: {e}")

    async def connect(self):
        """Connect to server and register username."""
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port
        )
        self.writer.write((self.username + "\n").encode())
        await self.writer.drain()

        response = await self.reader.readline()
        if response.decode().strip() == "ERROR":
            print("Username already taken")
            return False
        print("Connected!")
        return True

    async def receive_messages(self):
        """Async receive messages from server."""
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = data.decode().strip()

                if msg.startswith("ENCOUNTER"):
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
                print(f"Receive error: {e}")
                break

    def input_loop(self):
        """Read user input in a separate thread."""
        if self.script_file:
            try:
                with open(self.script_file, 'r') as f:
                    commands = [line.strip() for line in f if line.strip()]
                for line in commands:
                    if not self.running:
                        break
                    self.input_queue.put(line)
                    time.sleep(1)
            except FileNotFoundError:
                print(f"File {self.script_file} not found")
                self.running = False
            except Exception as e:
                print(f"File read error: {e}")
                self.running = False
            self.running = False
        else:
            MudCmd(self.input_queue, self).cmdloop()

    async def run(self):
        """Run the main client loop."""
        if not await self.connect():
            return

        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()

        receive_task = asyncio.create_task(self.receive_messages())

        while self.running:
            try:
                line = self.input_queue.get_nowait()
                self.writer.write((line + "\n").encode())
                await self.writer.drain()
            except queue.Empty:
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Send error: {e}")
                break

        receive_task.cancel()
        self.writer.close()
        await self.writer.wait_closed()
