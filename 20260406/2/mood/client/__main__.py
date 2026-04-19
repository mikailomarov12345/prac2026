#!/usr/bin/env python3
"""Entry point for the MUD game client."""

import argparse
import asyncio

from mood.client.main import MudClient


def main():
    """Запуск клиента с параметрами командной строки."""
    parser = argparse.ArgumentParser(description="MUD клиент")
    parser.add_argument('username', help="Имя пользователя")
    parser.add_argument('--host', default='localhost', help="Хост сервера")
    parser.add_argument('--port', type=int, default=1337, help="Порт сервера")
    args = parser.parse_args()

    client = MudClient(args.host, args.port, args.username)
    asyncio.run(client.run())


if __name__ == "__main__":
    main()
