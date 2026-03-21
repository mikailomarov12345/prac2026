import asyncio
import sys

async def main():
    print("Connecting to server...")
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
        print("Connected!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    try:
        while True:
            # Получаем ввод пользователя
            print("\nEnter command: ", end='', flush=True)
            user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not user_input:
                break
                
            user_input = user_input.strip()
            print(f"[DEBUG] User entered: '{user_input}'")
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            # Преобразуем команду
            if user_input == 'up':
                cmd = "move 0 -1"
            elif user_input == 'down':
                cmd = "move 0 1"
            elif user_input == 'left':
                cmd = "move -1 0"
            elif user_input == 'right':
                cmd = "move 1 0"
            elif user_input.startswith('attack'):
                parts = user_input.split()
                if len(parts) >= 2:
                    name = parts[1]
                    cmd = f"attack {name} 5"
                else:
                    print("Usage: attack <monster_name>")
                    continue
            else:
                print(f"Unknown command: {user_input}")
                continue
            
            print(f"[DEBUG] Sending: '{cmd}'")
            writer.write(f"{cmd}\n".encode())
            await writer.drain()
            print("[DEBUG] Sent, waiting for response...")
            
            # Ждем ответ
            response = await reader.readline()
            if not response:
                print("Server disconnected")
                break
            
            response_text = response.decode().strip()
            print(f"[DEBUG] Received: '{response_text}'")
            print(f"\n>>> {response_text}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
