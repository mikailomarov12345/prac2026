#!/usr/bin/env python3

import asyncio
import argparse
from shlex import split

SIZE = (10, 10)

class GameState:
    """Состояние игры"""
    def __init__(self):
        self.HEIGHT, self.WIDTH = SIZE
        # Позиции игроков: {username: (x, y)}
        self.players = {}
        # Монстры: [[(name, hello, hp) or None, ...], ...]
        self.monsters = [[None for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}

class MudServer:
    def __init__(self):
        self.game = GameState()
        self.writers = {}  # username -> writer
        self.positions = {}  # username -> (x, y)
        
    async def broadcast(self, message, exclude=None):
        """Отправить сообщение всем клиентам"""
        for username, writer in self.writers.items():
            if username != exclude:
                try:
                    writer.write((message + "\n").encode())
                    await writer.drain()
                except:
                    pass
                    
    async def send_to_user(self, username, message):
        """Отправить сообщение конкретному пользователю"""
        if username in self.writers:
            try:
                self.writers[username].write((message + "\n").encode())
                await self.writers[username].drain()
            except:
                pass
                
    async def handle_move(self, username, dx, dy):
        """Обработка перемещения"""
        x, y = self.positions[username]
        new_x = (x + dx + self.game.WIDTH) % self.game.WIDTH
        new_y = (y + dy + self.game.HEIGHT) % self.game.HEIGHT
        
        self.positions[username] = (new_x, new_y)
        self.game.players[username] = (new_x, new_y)
        
        monster = self.game.monsters[new_x][new_y]
        if monster:
            name, hello, hp = monster
            await self.send_to_user(username, f"ENCOUNTER {name} {hello}")
        else:
            await self.send_to_user(username, f"MOVED {new_x} {new_y}")
            
    async def handle_addmon(self, username, x, y, name, hello, hp):
        """Обработка добавления монстра"""
        old_monster = self.game.monsters[x][y] is not None
        old_name = self.game.monsters[x][y][0] if old_monster else None
        
        self.game.monsters[x][y] = (name, hello, hp)
        
        await self.send_to_user(username, f"ADDMON {x} {y} {name} {hello} {hp}")
        
        if old_monster:
            await self.broadcast(f"BROADCAST {username} replaced {old_name} with {name} at ({x},{y}) (HP:{hp})")
        else:
            await self.broadcast(f"BROADCAST {username} placed {name} at ({x},{y}) (HP:{hp})")
            
    async def handle_attack(self, username, monster_name, weapon):
        """Обработка атаки"""
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
            await self.send_to_user(username, f"ATTACK KILL {name} {damage}")
            await self.broadcast(f"BROADCAST {username} killed {name} with {weapon}")
        else:
            self.game.monsters[x][y] = (name, hello, new_hp)
            await self.send_to_user(username, f"ATTACK HIT {name} {damage} {new_hp}")
            await self.broadcast(f"BROADCAST {username} attacked {name} with {weapon}, {new_hp} HP left")
            
    async def handle_client(self, reader, writer):
        """Обработка подключения клиента"""
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
        
        await self.send_to_user(username, f"POSITION 0 0")
        
        await self.broadcast(f"BROADCAST {username} entered the MUD")
        
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
                    
                elif command == "addmon" and len(args) == 5:
                    x, y = int(args[0]), int(args[1])
                    name, hello, hp = args[2], args[3], int(args[4])
                    if 0 <= x < self.game.WIDTH and 0 <= y < self.game.HEIGHT:
                        await self.handle_addmon(username, x, y, name, hello, hp)
                    else:
                        await self.send_to_user(username, "ERROR Invalid coordinates")
                        
                elif command == "attack" and len(args) == 2:
                    monster_name, weapon = args[0], args[1]
                    if weapon in self.game.weapons:
                        await self.handle_attack(username, monster_name, weapon)
                    else:
                        await self.send_to_user(username, "ERROR Unknown weapon")
                        
                elif command == "sayall" and len(args) >= 1:
                    message = ' '.join(args)
                    message = message.strip('"\'')
                    await self.broadcast(f"CHAT {username}: {message}")
                else:
                    await self.send_to_user(username, f"ERROR Unknown command: {command}")
                    
        except Exception as e:
            print(f"Error handling {username}: {e}")
            
        finally:
            if username in self.writers:
                del self.writers[username]
            if username in self.positions:
                del self.positions[username]
            if username in self.game.players:
                del self.game.players[username]
            
            await self.broadcast(f"BROADCAST {username} left the MUD")
            writer.close()
            await writer.wait_closed()

async def main(port):
    server = MudServer()
    async def client_connected(reader, writer):
        await server.handle_client(reader, writer)
        
    srv = await asyncio.start_server(client_connected, '0.0.0.0', port)
    print(f"MUD Server running on port {port}")
    print(f"Players can connect with: python mud_client.py <username> --host <ip> --port {port}")
    
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-user MUD Server")
    parser.add_argument('--port', type=int, default=1337, help='Port to listen on (default: 1337)')
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        print("\nServer shutdown")
