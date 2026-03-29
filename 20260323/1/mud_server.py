#!/usr/bin/env python3
"""Многопользовательский MUD сервер - версия 1"""

import asyncio
import argparse
from shlex import split

SIZE = (10, 10)

class GameState:
    def __init__(self):
        self.HEIGHT, self.WIDTH = SIZE
        self.players = {}  # username -> (x, y)
        self.monsters = [[None for _ in range(self.HEIGHT)] for _ in range(self.WIDTH)]
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}

class MudServer:
    def __init__(self):
        self.game = GameState()
        self.writers = {}  # username -> writer
        
    async def broadcast(self, message, exclude=None):
        for username, writer in self.writers.items():
            if username != exclude:
                try:
                    writer.write((message + "\n").encode())
                    await writer.drain()
                except:
                    pass
                    
    async def handle_client(self, reader, writer):
        # Получаем имя пользователя
        data = await reader.readline()
        username = data.decode().strip()
        
        # Проверяем уникальность
        if username in self.writers:
            writer.write("ERROR Name already taken\n".encode())
            await writer.drain()
            writer.close()
            return
            
        # Регистрируем пользователя
        self.writers[username] = writer
        self.game.players[username] = (0, 0)
        
        # Сообщаем об успехе
        writer.write("WELCOME\n".encode())
        await writer.drain()
        
        # Широковещательное сообщение о входе
        await self.broadcast(f"BROADCAST {username} entered the MUD")
        
        # Обработка команд
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                # Пока просто эхо для теста
                writer.write(f"ECHO {data.decode().strip()}\n".encode())
                await writer.drain()
        except:
            pass
        finally:
            # Очистка при отключении
            del self.writers[username]
            del self.game.players[username]
            await self.broadcast(f"BROADCAST {username} left the MUD")
            writer.close()

async def main(port):
    server = MudServer()
    srv = await asyncio.start_server(server.handle_client, '0.0.0.0', port)
    print(f"Server running on port {port}")
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=1337)
    args = parser.parse_args()
    asyncio.run(main(args.port))
