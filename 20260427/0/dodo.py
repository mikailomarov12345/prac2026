#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile

DOIT_CONFIG = {"default_tasks": ["docs"]}

def task_docs():
	"""Create documentation"""

	rstpy = list(Path(".").glob("**/*.rst")) + list(Path(".").glob("**/*py"))

	return {
		"actions": ["cd doc && sphinx-build -M html . _build"],
		"targets": ["doc/_build/html/index.html"],
		"file_dep": rstpy,
	}

def task_erase():
	"""Clean all junk"""

	return {
		"actions": ["rm -rf doc/_build *.zip"]
	}

def task_zip():
	"""Create ZIP archive of docs"""

	def create_zip(filename, files):
		with ZipFile(filename, "w") as zf:
			for f in files:
				zf.write(f)

	files = list(Path("doc/_build/html").glob("**"))

	return {
		"actions": [(create_zip, ["docs.zip", files])],
		"task_dep": ["docs"]
	}