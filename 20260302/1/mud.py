#!/usr/bin/env python3
import sys
import shlex
import cowsay
import io

# ASCII-арт для jgsbat
JGSBAT_ART = r'''
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
'''

# Регистрация кастомного монстра
cowsay.read_dot_cow(io.StringIO(JGSBAT_ART), 'jgsbat')
ALL_COWS = cowsay.list_cows()

SIZE = 10
player = [0, 0]
monsters = {}           # (x, y) -> (hello, name, hp)

def move(dx, dy):
    player[0] = (player[0] + dx) % SIZE
    player[1] = (player[1] + dy) % SIZE
    print(f"Moved to ({player[0]}, {player[1]})")
    if (player[0], player[1]) in monsters:
        hello, name, hp = monsters[(player[0], player[1])]
        print(cowsay.cowsay(hello, cow=name))

def addmon(x, y, name, hello, hp):
    replaced = (x, y) in monsters
    monsters[(x, y)] = (hello, name, hp)
    print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp")
    if replaced:
        print("Replaced the old monster")

def process_line(line):
    if not line.strip():
        return
    try:
        parts = shlex.split(line)
    except ValueError:
        print("Invalid arguments")
        return
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
    elif cmd == 'addmon':
        # Парсим именованные параметры
        params = {}
        i = 1
        while i < len(parts):
            if parts[i] == 'hello':
                if i+1 >= len(parts):
                    print("Invalid arguments")
                    return
                params['hello'] = parts[i+1]
                i += 2
            elif parts[i] == 'hp':
                if i+1 >= len(parts):
                    print("Invalid arguments")
                    return
                try:
                    params['hp'] = int(parts[i+1])
                except ValueError:
                    print("Invalid arguments")
                    return
                i += 2
            elif parts[i] == 'coords':
                if i+2 >= len(parts):
                    print("Invalid arguments")
                    return
                try:
                    x = int(parts[i+1])
                    y = int(parts[i+2])
                    params['coords'] = (x, y)
                except ValueError:
                    print("Invalid arguments")
                    return
                i += 3
            else:
                # Первый параметр (имя монстра)
                params['name'] = parts[i]
                i += 1
        
        if not all(k in params for k in ('name', 'hello', 'hp', 'coords')):
            print("Invalid arguments")
            return
        
        name = params['name']
        hello = params['hello']
        hp = params['hp']
        x, y = params['coords']
        
        if not (0 <= x < SIZE and 0 <= y < SIZE):
            print("Invalid arguments")
            return
        
        if name not in ALL_COWS:
            print("Cannot add unknown monster")
            return
        
        addmon(x, y, name, hello, hp)
    else:
        print("Invalid command")

def main():
    print("<<< Welcome to Python-MUD 0.1 >>>")
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
