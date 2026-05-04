#!/usr/bin/env python3
from pathlib import Path
import locale
import gettext
PROJECT = "prog1"
lang = "ru_RU.UTF-8"

def task_erase():
    return {
        'actions': ["rm -rf prog1/*/*/*.mo"]
    }

def task_dist():
    return {
        'actions': ["pyproject-build -s"],
        'task_dep': ["erase"]
    }

def task_mo():
    '''Compile .mo for all languages'''
    SPATH = Path(".") / "po" / lang / "LC_MESSAGES"
    DPATH = Path(".") / PROJECT / lang / "LC_MESSAGES"
    DPATH.mkdir(parents=True, exist_ok=True)
    return {
        'actions': [f"pybabel compile -D{PROJECT} -l{lang} -i {SPATH}/{PROJECT}.po -d {PROJECT}"],
        'file_dep': [f"{SPATH}/{PROJECT}.po"],
        'targets': [f"{DPATH}/{PROJECT}.mo"],
    }

def task_wheel():
    return {
        'actions': ["pyproject-build -w"],
        'task_dep': ["mo"]
    }