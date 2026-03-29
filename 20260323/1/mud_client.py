#!/usr/bin/env python3
"""Асинхронный MUD клиент"""

import asyncio
import sys
import threading
import queue
from cowsay import cowsay, list_cows, read_dot_cow
from io import StringIO

class MudClient:
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
    
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.reader = None
        self.writer = None
        self.running = True
        self.input_queue = queue.Queue()
        
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.writer.write((self.username + "\n").encode())
        await self.writer.drain()
        
        response = await self.reader.readline()
        if response.decode().strip() == "ERROR":
            print("Name already taken")
            return False
        print("Connected!")
        return True
        
    async def receive_messages(self):
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = data.decode().strip()
                print(f"\n{msg}")
                print("> ", end="", flush=True)
            except:
                break
                
    def input_loop(self):
        print("Commands: up, down, left, right, addmon, attack, quit")
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
        if not await self.connect():
            return
            
        # Запускаем поток ввода
        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()
        
        # Запускаем прием сообщений
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
                print(f"Error: {e}")
                break
                
        receive_task.cancel()
        self.writer.close()
        await self.writer.wait_closed()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1337)
    args = parser.parse_args()
    
    client = MudClient(args.host, args.port, args.username)
    asyncio.run(client.run())

if __name__ == "__main__":
    main()
