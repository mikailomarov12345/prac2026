"""The main logic of the MUD game server."""

import asyncio
import random
import gettext
from pathlib import Path
from shlex import split

from mood.common import SIZE, WEAPONS


def _(s):
    """Marker for pybabel extract."""
    return s


class GameState:
    """Game state."""

    def __init__(self):
        """Initialize game state."""
        self.HEIGHT, self.WIDTH = SIZE
        # Player positions: {username: (x, y)}
        self.players = {}
        # Monsters: [[(name, hello, hp) or None, ...], ...]
        self.monsters = [
            [None for _i in range(self.HEIGHT)] for _i in range(self.WIDTH)
        ]
        self.weapons = WEAPONS


class MudServer:
    """MUD server for handling client connections."""

    def __init__(self):
        """Initialize the server."""
        self.game = GameState()
        self.writers = {}
        self.positions = {}
        self.wandering_task = None
        self.monsters_move_enabled = True
        self.client_locales = {}  # username -> locale
        # Setup translations
        locale_dir = Path(__file__).parent / "locales"
        self.translations = {
            'ru_RU': gettext.translation('messages', localedir=locale_dir, languages=['ru_RU'], fallback=True)
        }

    def get_translated_message(self, username, message_id, **kwargs):
        """Get translated message for user."""
        locale = self.client_locales.get(username, 'en')
        if locale in self.translations:
            trans = self.translations[locale]
            msg = trans.gettext(message_id)
            # Substitute parameters with plural forms
            if 'hp' in kwargs:
                hp = kwargs['hp']
                hp_msg = trans.ngettext("point", "points", hp)
                kwargs['hp'] = f"{hp} {hp_msg}"
            return msg.format(**kwargs) if kwargs else msg
        return message_id.format(**kwargs) if kwargs else message_id

    async def handle_locale(self, username, locale_name):
        """Handle locale command."""
        if locale_name in self.translations or locale_name == 'en':
            self.client_locales[username] = locale_name
            msg = self.get_translated_message(username, _("Set up locale: {locale}"), locale=locale_name)
            await self.send_to_user(username, msg)
        else:
            await self.send_to_user(username, f"ERROR Unknown locale: {locale_name}")

    async def broadcast(self, message_id, exclude=None, *args, **kwargs):
        """Send localized message to all clients."""
        if exclude is None and 'username' in kwargs:
            exclude = kwargs.pop('username')
        for recipient, writer in self.writers.items():
            if recipient == exclude:
                continue
            try:
                try:
                    if args:
                        msg = message_id.format(*args)
                    else:
                        msg = self.get_translated_message(recipient, message_id, **kwargs)
                except (IndexError, KeyError, TypeError):
                    msg = message_id
                writer.write((msg + "\n").encode())
                await writer.drain()
            except (ConnectionError, BrokenPipeError):
                pass

    async def send_to_user(self, username, message_id, *args, **kwargs):
        """Send message to specific user."""
        if username in self.writers:
            try:
                if args:
                    msg = message_id.format(*args)
                else:
                    msg = self.get_translated_message(username, message_id, **kwargs)
                self.writers[username].write((msg + "\n").encode())
                await self.writers[username].drain()
            except (ConnectionError, BrokenPipeError):
                pass

    async def handle_move(self, username, dx, dy):
        """Handle player movement."""
        x, y = self.positions[username]
        new_x = (x + dx + self.game.WIDTH) % self.game.WIDTH
        new_y = (y + dy + self.game.HEIGHT) % self.game.HEIGHT

        self.positions[username] = (new_x, new_y)
        self.game.players[username] = (new_x, new_y)

        monster = self.game.monsters[new_x][new_y]
        if monster:
            name, hello, hp = monster
            await self.send_to_user(username, "ENCOUNTER {} {}", name, hello)
        else:
            await self.send_to_user(username, "MOVED {} {}", new_x, new_y)

    async def handle_addmon(self, username, x, y, name, hello, hp):
        """Handle adding a monster."""
        old_monster = self.game.monsters[x][y] is not None
        old_name = self.game.monsters[x][y][0] if old_monster else None

        self.game.monsters[x][y] = (name, hello, hp)

        await self.send_to_user(username, "ADDMON {} {} {} {} {}", x, y, name, hello, hp)

        if old_monster:
            await self.broadcast(
                _("replaced {old_name} with {name} at ({x},{y}) (HP:{hp})"),
                username=username, old_name=old_name, name=name, x=x, y=y, hp=hp
            )
        else:
            await self.broadcast(
                _("placed {name} at ({x},{y}) (HP:{hp})"),
                username=username, name=name, x=x, y=y, hp=hp
            )

    async def handle_attack(self, username, monster_name, weapon):
        """Handle attack on a monster."""
        x, y = self.positions[username]
        monster = self.game.monsters[x][y]

        if not monster or monster[0] != monster_name:
            await self.send_to_user(username, "ATTACK MISS")
            return

        name, hello, hp = monster
        damage = min(hp, self.game.weapons[weapon])
        new_hp = hp - damage

        if new_hp == 0:
            self.game.monsters[x][y] = None
            await self.send_to_user(username, "ATTACK KILL {} {}", name, damage)
            await self.broadcast(_("killed {name} with {weapon}"), username=username, name=name, weapon=weapon)
        else:
            self.game.monsters[x][y] = (name, hello, new_hp)
            await self.send_to_user(username, "ATTACK HIT {} {} {}", name, damage, new_hp)
            await self.broadcast(
                _("attacked {name} with {weapon}, {hp} HP left"),
                username=username, name=name, weapon=weapon, hp=new_hp
            )

    async def handle_sayall(self, username, message):
        """Handle sayall command - send message to all."""
        await self.broadcast(f"CHAT {username}: {message}")

    async def handle_client(self, reader, writer):
        """Handle client connection."""
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=10.0)
            username = data.decode().strip()
        except asyncio.TimeoutError:
            writer.close()
            return

        if not username or ' ' in username:
            writer.write("ERROR Invalid username\n".encode())
            await writer.drain()
            writer.close()
            return

        if username in self.writers:
            writer.write("ERROR Name already taken\n".encode())
            await writer.drain()
            writer.close()
            return

        self.writers[username] = writer
        self.positions[username] = (0, 0)
        self.game.players[username] = (0, 0)

        writer.write("WELCOME\n".encode())
        await writer.drain()

        await self.send_to_user(username, "POSITION 0 0")

        await self.broadcast(_("entered the MUD"), username=username)

        if self.wandering_task is None or self.wandering_task.done():
            self.wandering_task = asyncio.create_task(self.wander_monsters())

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                line = data.decode().strip()
                if not line:
                    continue

                parts = split(line)
                if not parts:
                    continue

                command = parts[0]
                args = parts[1:]

                if command == "move" and len(args) == 2:
                    dx, dy = int(args[0]), int(args[1])
                    await self.handle_move(username, dx, dy)

                elif command == "up":
                    await self.handle_move(username, 0, 1)
                elif command == "down":
                    await self.handle_move(username, 0, -1)
                elif command == "left":
                    await self.handle_move(username, -1, 0)
                elif command == "right":
                    await self.handle_move(username, 1, 0)

                elif command == "movemonsters" and len(args) == 1:
                    await self.handle_movemonsters(username, args[0])

                elif command == "locale" and len(args) == 1:
                    await self.handle_locale(username, args[0])

                elif command == "addmon" and len(args) == 5:
                    x, y = int(args[0]), int(args[1])
                    name, hello, hp = args[2], args[3], int(args[4])
                    if 0 <= x < self.game.WIDTH and 0 <= y < self.game.HEIGHT:
                        await self.handle_addmon(username, x, y, name, hello, hp)
                    else:
                        await self.send_to_user(username, "ERROR Invalid coordinates")

                elif command == "attack":
                    if len(args) == 1:
                        monster_name = args[0]
                        weapon = "sword"
                        if weapon in self.game.weapons:
                            await self.handle_attack(username, monster_name, weapon)
                        else:
                            await self.send_to_user(username, "ERROR Unknown weapon")
                    elif len(args) == 3 and args[1] == "with":
                        monster_name, _kw, weapon = args
                        if weapon in self.game.weapons:
                            await self.handle_attack(username, monster_name, weapon)
                        else:
                            await self.send_to_user(username, "ERROR Unknown weapon")
                    else:
                        await self.send_to_user(username, "ERROR Invalid attack command")

                elif command == "sayall" and len(args) >= 1:
                    message = ' '.join(args).strip('"\'')
                    await self.handle_sayall(username, message)

                else:
                    await self.send_to_user(username, "ERROR Unknown command: {}", command)

        except Exception as e:
            print(f"Error handling {username}: {e}")

        finally:
            if username in self.writers:
                del self.writers[username]
            if username in self.positions:
                del self.positions[username]
            if username in self.game.players:
                del self.game.players[username]

            await self.broadcast(_("left the MUD"), username=username)
            writer.close()
            await writer.wait_closed()

    async def wander_monsters(self):
        """Move random monsters periodically (every 30 seconds)."""
        await asyncio.sleep(30)
        while True:
            await asyncio.sleep(30)

            if not self.monsters_move_enabled:
                continue

            monsters_list = []
            for x in range(self.game.WIDTH):
                for y in range(self.game.HEIGHT):
                    monster = self.game.monsters[x][y]
                    if monster:
                        monsters_list.append((x, y, monster[0], monster[1], monster[2]))

            if not monsters_list:
                continue

            for _i in range(10):
                idx = random.randrange(len(monsters_list))
                x, y, name, hello, hp = monsters_list[idx]

                dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
                dir_map = {(0, -1): "up", (0, 1): "down", (-1, 0): "left", (1, 0): "right"}
                direction = dir_map[(dx, dy)]

                new_x = (x + dx + self.game.WIDTH) % self.game.WIDTH
                new_y = (y + dy + self.game.HEIGHT) % self.game.HEIGHT

                if self.game.monsters[new_x][new_y] is None:
                    self.game.monsters[new_x][new_y] = self.game.monsters[x][y]
                    self.game.monsters[x][y] = None

                    await self.broadcast(_("moved one cell {direction}"), direction=direction)

                    for player, (px, py) in self.positions.items():
                        if px == new_x and py == new_y:
                            await self.send_to_user(player, "ENCOUNTER {} {}", name, hello)
                    break

    async def handle_movemonsters(self, username, state):
        """Handle movemonsters command to enable/disable wandering monsters."""
        if state == "on":
            self.monsters_move_enabled = True
            await self.send_to_user(username, _("Moving monsters: on"))
            if self.wandering_task is None or self.wandering_task.done():
                self.wandering_task = asyncio.create_task(self.wander_monsters())
        elif state == "off":
            self.monsters_move_enabled = False
            await self.send_to_user(username, _("Moving monsters: off"))
        else:
            await self.send_to_user(username, "ERROR Invalid state. Use 'on' or 'off'")


async def _serve(host, port):
    server = MudServer()
    srv = await asyncio.start_server(server.handle_client, host, port)
    async with srv:
        await srv.serve_forever()


def run_server(host="localhost", port=1337):
    """Entry point for multiprocessing.Process(target=run_server, args=(host, port))."""
    try:
        asyncio.run(_serve(host, port))
    except KeyboardInterrupt:
        pass
