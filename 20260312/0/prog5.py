import cmd
from shlex import split
from pathlib import Path
import calendar


class Cmdl(cmd.Cmd):
	prompt = "$ "
	#months = list(cal)

	def do_month(self, arg):
		"""Print a month’s calendar as returned by formatmonth()."""
		args = split(arg)
		try:
			print(calendar.TextCalendar().prmonth(int(args[0]), int(args[1])))
		except Exception as E:
			print(E)

	def complete_month(self, text, line, bigidx, endidx):
		pass

	def do_year(self, arg):
		"""Print the calendar for an entire year as returned by formatyear()."""
		args = split(arg)
		print(calendar.TextCalendar().pryear(int(args[0])))

	def do_EOF(self, arg):
		print("\nBYE")
		return 1

if __name__ == "__main__":
	Cmdl().cmdloop()
