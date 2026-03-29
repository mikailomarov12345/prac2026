import argparse
import asyncio
import cmd
import os
import socket
import sys
from cowsay import cowsay, list_cows, read_dot_cow
from io import StringIO
from shlex import split

SIZE = (10, 10)

class serverMUD:
    prompt = "(mud) "
    pos_x, pos_y = 0, 0
    HEIGHT, WIDTH = SIZE

    weapons = { "sword": 10, "spear": 15, "axe": 20 }

    def __init__(self, writer):
        self.writer = writer
        self.monsters = [[None for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]

    def do_up(self):
        self.pos_y = (self.pos_y - 1 + self.HEIGHT) % self.HEIGHT
        self.writer.write((f"{self.pos_x} {self.pos_y} " + self._encounter()).encode())

    def do_down(self):
        self.pos_y = (self.pos_y + 1) % self.HEIGHT
        self.writer.write((f"{self.pos_x} {self.pos_y} " + self._encounter()).encode())

    def do_left(self):
        self.pos_x = (self.pos_x - 1 + self.WIDTH) % self.WIDTH
        self.writer.write((f"{self.pos_x} {self.pos_y} " + self._encounter()).encode())

    def do_right(self):
        self.pos_x = (self.pos_x + 1) % self.WIDTH
        self.writer.write((f"{self.pos_x} {self.pos_y} " + self._encounter()).encode())

    def _encounter(self) -> str:
        if self.monsters[self.pos_x][self.pos_y]:
            name, hello, hp = self.monsters[self.pos_x][self.pos_y]
            return f"{name} '{hello}'"

        return ""

    def addmon(self, x: int, y: int, name: str,  hello: str, hp: int) -> None:
        if self.monsters[x][y]:
            res_str = "1"
        else:
            res_str = "0"
        self.writer.write(res_str.encode())
        self.monsters[x][y] = (name, hello, hp)

    def attack(self, attack_name, weapon):
        if self.monsters[self.pos_x][self.pos_y] is None or attack_name != self.monsters[self.pos_x][self.pos_y][0]:
            self.writer.write("0".encode())
            return
        name, hello, hp = self.monsters[self.pos_x][self.pos_y]

        damage = min(hp, self.weapons[weapon])

        hp -= damage
        res = f"{name} {damage} {hp}"
        if hp == 0:
            self.monsters[self.pos_x][self.pos_y] = None
        else:
            self.monsters[self.pos_x][self.pos_y] = (name, hello, hp)
        self.writer.write(res.encode())


class clientMUD(cmd.Cmd):
    HEIGHT, WIDTH = SIZE
    weapons = ["sword", "spear", "axe"]
    jgsbat_ascii_art = r"""
        ,_                    _,
        ) '-._  ,_    _,  _.-' (
        )  _.-'.|\\\\--//|.'-._  (
         )'   .'\/o\/o\/'.   `(
          ) .' . \====/ . '. (
           )  / <<    >> \  (
            '-._/``  ``\_.-'
      jgs     __\\\\'--'//__
             (((""`  `"")))
    """
    jgsbat = read_dot_cow(StringIO(jgsbat_ascii_art))


    def __init__(self, sock, host = None, port = None):
        super().__init__()
        self.s = sock
        host = "localhost" if host is None else host
        port = 1337 if port is None else port
        self.s.connect((host, port))


    def _encounter_redner(self, name, hello):
        if name != "jgsbat":
            print(cowsay(hello, cow=name))
        else:
            print(cowsay(hello, cowfile=self.jgsbat))

    def do_up(self, args):
        """Use to move up"""
        if args:
            print("Invalid arguments")
            return
        self.s.sendall("up".encode() + b'\n')
        data = split(self.s.recv(1024).rstrip().decode())
        print(f"Moved to ({int(data[0])}, {int(data[1])})")
        if len(data) == 4:
            self._encounter_redner(data[2], data[3])
    def do_down(self, args):
        """Use to move down"""
        if args:
            print("Invalid arguments")
            return
        self.s.sendall("down".encode() + b'\n')
        data = split(self.s.recv(1024).rstrip().decode())
        print(f"Moved to ({int(data[0])}, {int(data[1])})")
        if len(data) == 4:
            self._encounter_redner(data[2], data[3])

    def do_left(self, args):
        """Use to move left"""
        if args:
            print("Invalid arguments")
            return
        self.s.sendall("left".encode() + b'\n')
        data = split(self.s.recv(1024).rstrip().decode())
        print(f"Moved to ({int(data[0])}, {int(data[1])})")
        if len(data) == 4:
            self._encounter_redner(data[2], data[3])

    def do_right(self, args):
        """Use to move right"""
        if args:
            print("Invalid arguments")
            return
        self.s.sendall("right".encode() + b'\n')
        data = split(self.s.recv(1024).rstrip().decode())
        print(f"Moved to ({int(data[0])}, {int(data[1])})")
        if len(data) == 4:
            self._encounter_redner(data[2], data[3])

    def _parse_addmon(self, args: list[str]) -> tuple[str ,str, int, int, int]:
        name = args[0]
        hello, hp, x, y = None, None, None, None
        args = args[1:]
        while args:
            if args[0] == "hello":
                if hello is None:
                    hello = args[1]
                else:
                    raise ValueError
                args = args[2:]
                continue

            if args[0] == "hp":
                if hp is None:
                    hp = int(args[1])
                    if hp <= 0:
                        raise ValueError
                else:
                    raise ValueError
                args = args[2:]
                continue

            if args[0] == "coords":
                if x is None and y is None:
                    x, y = int(args[1]), int(args[2])
                    if not(0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
                        raise ValueError
                else:
                    raise ValueError
                args = args[3:]
                continue

            raise ValueError

        return name, hello, hp, x, y

    def do_addmon(self, args):
        """Adds monster saying hello to coords with hp.
        Coords, hello message and hp are given after words coords, hello and hp"""
        args = split(args)
        if len(args) != 8:
            print("Invalid arguments")
            return
        try:
            name, hello, hp, x, y = self._parse_addmon(args)
        except ValueError:
            print("Invalid arguments")
            return

        if name not in list_cows() and name != "jgsbat":
            print("Cannot add unknown monster")
            return
        self.s.sendall(("addmon "+ f"{x} {y} {name} '{hello}' {hp}\n").encode())
        data = self.s.recv(1024).rstrip().decode()
        print(f"Added monster {name} to ({x}, {y}) saying {hello}")
        if data == '1':
            print("Replaced the old monster")

    def do_EOF(self, args):
        print()
        return 1

    def do_attack(self, args):
        """Damages named monster in room for some hp:
        10 - sword
        15 - spear
        20 - axe
        Chose weapon after with"""
        args = split(args)
        if len(args) != 1 and len(args) != 3:
            print("Invalid arguments")
            return
        elif len(args) == 1:
            attack_name, = args
            weapon = "sword"
        else:
            attack_name, command, weapon = args
            if command != "with":
                print("Invalid arguments")
                return

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        self.s.sendall(("attack "+ f"{attack_name} {weapon}\n").encode())
        data = self.s.recv(1024).rstrip().decode()

        if data == "0":
            print(f"No {attack_name} here")
            return

        name, damage, hp = split(data)
        print(f"Attacked {name}, damage {damage} hp")
        if hp == "0":
            print(f"{name} died")
        else:
            print(f"{name} now has {hp}")


    def complete_attack(self, text, line, begidx, endidx):
        line_words = split(line[:begidx])
        if len(line_words) <= 1:
            return [cow for cow in list_cows() + ["jgsbat"] if cow.startswith(text)]
        elif len(line_words) == 2:
            return ["with"] if "with".startswith(text) else []
        else:
            return [weapon for weapon in self.weapons if weapon.startswith(text)]

async def echo(reader, writer):
    MUD = serverMUD(writer)

    while data := await reader.readline():
        command, *args = split(data.decode())

        if command == "left":
            MUD.do_left()
        elif command == "right":
            MUD.do_right()
        elif command == "down":
            MUD.do_down()
        elif command == "up":
            MUD.do_up()
        elif command == "addmon":
            MUD.addmon(int(args[0]), int(args[1]), args[2], args[3], int(args[4]))
        elif command == "attack":
            MUD.attack(args[0], args[1])

    writer.close()
    await writer.wait_closed()

async def server_main(port):
    server = await asyncio.start_server(echo, '0.0.0.0', port)
    async with server:
        await server.serve_forever()

def server(port):
    asyncio.run(server_main(port))

def client(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        clientMUD(s, host, port).cmdloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     description="Client-server one user MUD")

    parser.add_argument('-m', '--mode', choices=['client', 'server'],
                        default='client', help="Work mode: client or server. client mode is default.")

    parser.add_argument('--host', type=str, default='localhost', help='Host, default localhost')
    parser.add_argument('--port', type=int, default=1337, help='Port, default 1337')

    args = parser.parse_args()

    if args.mode == 'client':
        print("<<< Welcome to Python-MUD 0.1 >>>")
        client(args.host, args.port)
    else:
        server(args.port)