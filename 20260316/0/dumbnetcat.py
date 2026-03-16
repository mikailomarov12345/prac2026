import sys
import socket
import cmd

class NC(cmd.Cmd):
  promtp = "$ "

  def do_connect(self, arg):
    args = arg.split()
    match args:
       pass

  def do_info(self, arg):
    match arg:
      case "host" | "port":
        self.s.sendall(b:"info " + arg.encode() + "\n")
        print("")

  def do_print(self, arg)

  def complete_info()

  def do_EOF(self, arg):
    return 1

host = "localhost" if len(sys.argv) < 2 else sys.argv[1]
port = 1337 if len(sys.argv) < 3 else int(sys.argv[2])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
  s.connect((host, port))
  while msg := sys.stdin.buffer.readline():
    s.sendall(msg)
    print(s.recv(1024).rstrip().decode())
