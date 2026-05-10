import gettext
import os

# Компилируем .po в .mo
os.system("python -c \"import gettext; gettext.install('messages', localedir='mood/server/locales')\"")
