#!/usr/bin/env python3
"""Entry point for the MUD game server."""

import argparse
import asyncio

from mood.server.main import MudServer


async def run_server(port):
    """Запуск сервера на указанном порту.

    Args:
        port: Номер порта
    """
    server = MudServer()

    async def client_connected(reader, writer):
        await server.handle_client(reader, writer)

    srv = await asyncio.start_server(client_connected, '0.0.0.0', port)
    print(f"MUD Server running on port {port}")
    print(f"Run client: python -m mood.client <username> --host localhost --port {port}")

    async with srv:
        await srv.serve_forever()


def main():
    """Запуск сервера с параметрами командной строки."""
    parser = argparse.ArgumentParser(description="MUD сервер")
    parser.add_argument('--port', type=int, default=1337, help='Port (default: 1337)')
    args = parser.parse_args()

    try:
        asyncio.run(run_server(args.port))
    except KeyboardInterrupt:
        print("\nServer shutdown")


if __name__ == "__main__":
    main()
