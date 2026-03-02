#!/usr/bin/env python3
from shlex import split, join

while l := input("$ "):
	print(join(split(l)))
