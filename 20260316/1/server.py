import asyncio
import sys

class GameState:
    def __init__(self):
        self.width = 5
        self.height = 5
        self.player_x = 2
        self.player_y = 2
        self.monsters = {
            (3, 2): ("Goblin", 10),
            (2, 3): ("Orc", 15),
        }
        print(f"Game initialized. Player at ({self.player_x}, {self.player_y})")

    def process_command(self, cmd: str) -> str:
        # ВАЖНО: выводим каждую команду
        print(f"Processing command: {cmd}")
        
        parts = cmd.strip().split()
        if not parts:
            return "Empty command\n"
        
        if parts[0] == "move" and len(parts) == 3:
            try:
                dx, dy = int(parts[1]), int(parts[2])
                return self._move(dx, dy)
            except ValueError:
                return "Invalid move parameters\n"
                
        elif parts[0] == "attack" and len(parts) == 3:
            name = parts[1]
            try:
                damage = int(parts[2])
                return self._attack(name, damage)
            except ValueError:
                return "Invalid attack damage\n"
                
        else:
            return f"Unknown command: {cmd}\n"

    def _move(self, dx, dy):
        nx = self.player_x + dx
        ny = self.player_y + dy
        
        if 0 <= nx < self.width and 0 <= ny < self.height:
            self.player_x, self.player_y = nx, ny
            print(f"Player moved to ({nx}, {ny})")
            
            if (nx, ny) in self.monsters:
                monster_name, health = self.monsters[(nx, ny)]
                print(f"Encountered {monster_name}")
                return f"encounter {monster_name}\nYou see a {monster_name}!\n"
            else:
                return f"Moved to ({nx}, {ny})\n"
        else:
            return f"Can't move to ({nx}, {ny})\n"

    def _attack(self, name, damage):
        pos = (self.player_x, self.player_y)
        print(f"Attacking {name} at {pos} with damage {damage}")
        
        if pos in self.monsters and self.monsters[pos][0] == name:
            mon_name, health = self.monsters[pos]
            health -= damage
            print(f"{mon_name} health now: {health}")
            
            if health <= 0:
                del self.monsters[pos]
                return f"{mon_name} dies!\n"
            else:
                self.monsters[pos] = (mon_name, health)
                return f"Hit {mon_name} for {damage} damage, remaining health: {health}\n"
        else:
            return f"No {name} here\n"

async def handle_client(reader, writer, game_state):
    peername = writer.get_extra_info('peername')
    print(f"Client connected from {peername}")
    
    try:
        while True:
            # Читаем строку от клиента
            data = await reader.readline()
            if not data:
                print(f"Client {peername} disconnected (no data)")
                break
                
            # Декодируем команду
            cmd = data.decode().strip()
            print(f"Received from {peername}: '{cmd}'")  # ВАЖНО: выводим полученную команду
            
            # Обрабатываем команду
            response = game_state.process_command(cmd)
            print(f"Sending response: '{response.strip()}'")  # ВАЖНО: выводим ответ
            
            # Отправляем ответ
            writer.write(response.encode())
            await writer.drain()
            
    except Exception as e:
        print(f"Error handling client {peername}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Client {peername} disconnected")

async def main():
    print("Starting server...")
    game_state = GameState()
    
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, game_state),
        '127.0.0.1', 8888
    )
    
    print("Server running on 127.0.0.1:8888")
    print("Waiting for connections...")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
