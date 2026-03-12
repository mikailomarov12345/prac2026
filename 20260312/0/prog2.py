import cmd
from shlex import split
from pathlib import Path

class SizeCmdl(cmd.Cmd):
	prompt = "$ "

	def do_size(self, arg):
		"""
		"""
		args = split(arg)
		for name in args:
			print(f"{name}: {Path(name).stat().st_size}")

	def do_EOF(self, arg):
		return 1

if __name__ == "__main__":
	SizeCmdl().cmdloop()
