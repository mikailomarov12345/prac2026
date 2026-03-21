#!/usr/bin/env python3
import sys
import cowsay

SIZE = 10
player = [0, 0]
monsters = {}           # (x, y) -> (hello, name)

def move(dx, dy):
    player[0] = (player[0] + dx) % SIZE
    player[1] = (player[1] + dy) % SIZE
    print(f"Moved to ({player[0]}, {player[1]})")
    if (player[0], player[1]) in monsters:
        hello, name = monsters[(player[0], player[1])]

        print(cowsay.cowsay(hello))

def addmon(x, y, name, hello):
    replaced = (x, y) in monsters
    monsters[(x, y)] = (hello, name)
    print(f"Added monster {name} to ({x}, {y}) saying {hello}")
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
    elif cmd == 'addmon' and len(parts) == 5:
        try:
            x = int(parts[1])
            y = int(parts[2])
            name = parts[3]
            hello = parts[4]
            if 0 <= x < SIZE and 0 <= y < SIZE:

                addmon(x, y, name, hello)
            else:
                print("Invalid arguments")
        except ValueError:
            print("Invalid arguments")
    else:
        print("Invalid command")

def main():
    if sys.stdin.isatty():
        while True:
            try:
                line = input(">>> ")
            except EOFError:
                break
            process_line(line)
    else:
        for line in sys.stdin:
            process_line(line)

if __name__ == "__main__":
    main()
