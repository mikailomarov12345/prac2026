import cmd
from shlex import split
from pathlib import Path

class SizeCmdl(cmd.Cmd):
	prompt = "~/$ "

	def do_size(self, arg):
		"""Print file sizes"""
		args = split(arg)
		for name in args:
			print(f"{name}: {Path(name).stat().st_size}")

	def complete_size(self, text, line, begidx, endidx):
		return [str(p) for p in Path("").glob(f"{text}*")]

	def do_EOF(self, arg):
		print("\nBYE\n")
		return 1

if __name__ == "__main__":
	SizeCmdl().cmdloop()
