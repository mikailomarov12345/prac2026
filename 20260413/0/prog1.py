import gettext, locale

locale.setlocale(locale.LC_ALL, locale.getlocale())
transcode = gettext.translation("prog1", localedir="po", fallback=True)
transtext = gettext.translation("prog1_story", localedir="po", fallback=True)
ngettext1 = transcode.ngettext
ngettext2 = transtext.ngettext

words = input().split()
n = len(words)
print(ngettext1("Entered {} word", "Entered {} word(s)", n).format(n))
print(ngettext2("Entered {} word", "Entered {} word(s)", n).format(n))
