import calendar, sys
"""The documentation"""

def fun():
	"""Something."""

	year = int(sys.argv[1])
	mon = int(sys.argv[2])

	calend = calendar.month(theyear = year, themonth = mon).split("\n")
	calend[0] = ".. tables:" + calend[0][4::] + "\n"

	calend[1] = (" "*4 + "== "*7 + "\n" + " "*4 + calend[1] + "\n" + " "*4 + "== "*7)

	calend[-1] += "== "*7

	count = sum(1 for char in calend[2] if not char.isspace())
	index = next((i for i, char in enumerate(calend[2]) if not char.isspace()), -1)

	empty_days = 7 - count

	row = list(calend[2])

	for i in range(empty_days):
		pos = i * 3
		if pos < index:
			row[pos] = ' '
			row[pos + 1] = '\\'
			row[pos + 2] = ' '

	calend[2] = ''.join(row)

	for i in range(2, len(calend)):
		calend[i] = " "*4 + calend[i]

	print("\n".join(calend))
