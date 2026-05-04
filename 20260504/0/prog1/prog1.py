#!/usr/bin/env python3

import gettext
import locale


if __name__ == "__main__":
  locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
  translation = gettext.translation("prog1", "po", fallback=True)
  tolmatch = gettext.translation("prog1_story", "po", fallback=True)
  # _, ngettext = translation.gettext, translation.ngettext
  _, ngettext = tolmatch.gettext, tolmatch.ngettext

  words = input().split()
  N = len(words)
  # print(_("Entered {} words").format(N))
  print(ngettext("Entered {} word", "Entered {} words", N).format(N))
