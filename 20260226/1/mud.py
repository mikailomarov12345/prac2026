#!/usr/bin/env python3
import sys
import cowsay

SIZE = 10
player = [0, 0]
monsters = {}           # (x, y) -> hello

def move(dx, dy):
    player[0] = (player[0] + dx) % SIZE
    player[1] = (player[1] + dy) % SIZE
    print(f"Moved to ({player[0]}, {player[1]})")
    if (player[0], player[1]) in monsters:
        hello = monsters[(player[0], player[1])]
        print(cowsay.cowsay(hello))

def addmon(x, y, hello):
    replaced = (x, y) in monsters
    monsters[(x, y)] = hello
    print(f"Added monster to ({x}, {y}) saying {hello}")
    if replaced:
        print("Replaced the old monster")

def process_line(line):
    parts = line.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()
    if cmd == 'up':
        move(0, -1)
    elif cmd == 'down':
        move(0, 1)
    elif cmd == 'left':
        move(-1, 0)
    elif cmd == 'right':
        move(1, 0)
    elif cmd == 'addmon' and len(parts) == 4:
        try:
            x = int(parts[1])
            y = int(parts[2])
            hello = parts[3]
            if 0 <= x < SIZE and 0 <= y < SIZE:
                addmon(x, y, hello)
            else:
                print("Invalid arguments")
        except ValueError:
            print("Invalid arguments")
    else:
        print("Invalid command")

def main():
    if sys.stdin.isatty():
        # Интерактивный режим
        while True:
            try:
                line = input(">>> ")
            except EOFError:
                break
            process_line(line)
    else:
        # Пакетный режим
        for line in sys.stdin:
            process_line(line)

if __name__ == "__main__":
    main()
