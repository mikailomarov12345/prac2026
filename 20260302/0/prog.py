#!/usr/bin/env python3
from shlex import split

while l := input("$ "):
	print(split(l))
