#!/usr/bin/env python3
import gettext
import locale
from . import PATH

locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
translation = gettext.translation("prog1", PATH, fallback=True)
ngettext = translation.ngettext

words = input().split()
n = len(words)
print(ngettext("Entered {} word", "Entered {} words", n).format(n))
