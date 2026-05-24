"""DoIt-конфигурация проекта MUD.
 
Цели верхнего уровня:
    * i18n  — полная генерация перевода (pot -> po -> mo)
    * html  — html-документация в docs/
    * test  — прогон тестов связки клиент+сервер
              (зависит от i18n: тесты опираются на русифицированные ответы)
 
Цель по умолчанию: html.
 
Очистка для каждой цели:
    * pot/po/mo — стандартное удаление generated-файлов через clean_targets
    * html      — удаление каталога docs/ через shutil.rmtree
 
Для запуска нужны пакеты: doit, Babel (для pybabel) и pdoc3.
"""
import glob
import shutil
import subprocess
from pathlib import Path
 
from doit.task import clean_targets

DOIT_CONFIG = {
    "default_tasks": ["html"],
}
 
 
# --------------------------------------------------------------------------
# Пути к артефактам перевода
# --------------------------------------------------------------------------
LOCALE_DIR = "mood/server/locales"
POT_FILE = f"{LOCALE_DIR}/messages.pot"
RU_PO = f"{LOCALE_DIR}/ru_RU/LC_MESSAGES/messages.po"
RU_MO = f"{LOCALE_DIR}/ru_RU/LC_MESSAGES/messages.mo"
 
DOCS_DIR = "docs"
 
 
# --------------------------------------------------------------------------
# i18n: цели-шаги
# --------------------------------------------------------------------------
def task_pot():
    """Извлечь сообщения для перевода в messages.pot."""
    sources = sorted(glob.glob("mood/**/*.py", recursive=True))
    return {
        "actions": [f"pybabel extract -F babel.cfg -o {POT_FILE} mood"],
        "targets": [POT_FILE],
        "file_dep": sources,
        "clean": [clean_targets],
    }
 
def task_po():
    """Создать или обновить messages.po для локали ru_RU."""
 
    def init_or_update():
        # Если .po уже есть — обновляем (update), иначе создаём (init).
        if Path(RU_PO).exists():
            subprocess.check_call([
                "pybabel", "update",
                "-i", POT_FILE,
                "-d", LOCALE_DIR,
                "-l", "ru_RU",
            ])
        else:
            subprocess.check_call([
                "pybabel", "init",
                "-i", POT_FILE,
                "-d", LOCALE_DIR,
                "-l", "ru_RU",
            ])
 
    return {
        "actions": [init_or_update],
        "targets": [RU_PO],
        "file_dep": [POT_FILE],
        "clean": [clean_targets],
    }
 
 
def task_mo():
    """Скомпилировать messages.po -> messages.mo."""
    return {
        "actions": [
            f"pybabel compile -d {LOCALE_DIR} -l ru_RU",
        ],
        "targets": [RU_MO],
        "file_dep": [RU_PO],
        "clean": [clean_targets],
    }
 
 
def task_i18n():
    """Полная генерация перевода (pot + po + mo)."""
    return {
        # Цель-агрегатор: своих действий нет, только зависимости от шагов.
        "actions": None,
        "task_dep": ["pot", "po", "mo"],
    }
 
 
# --------------------------------------------------------------------------
# html: документация
# --------------------------------------------------------------------------
def task_html():
    """Сгенерировать html-документацию пакета mood в каталог docs/."""
    return {
        "actions": [
            f"pdoc --html --force -o {DOCS_DIR} mood",
        ],
        "targets": [DOCS_DIR],
        "file_dep": sorted(glob.glob("mood/**/*.py", recursive=True)),
        # Каталог документации удаляем целиком через shutil.rmtree.
        # Второй аргумент True = ignore_errors (если каталога ещё нет).
        "clean": [(shutil.rmtree, [DOCS_DIR, True])],
    }
 
 
# --------------------------------------------------------------------------
# test: тесты связки клиент+сервер
# --------------------------------------------------------------------------
def task_test():
    """Прогон unittest-тестов связки клиент+сервер.
 
    Зависит от i18n, потому что тесты проверяют русифицированные
    ответы сервера, а для этого должен быть собран messages.mo.
    """
    return {
        "actions": [
            "python -m unittest discover -s tests -v",
        ],
        "task_dep": ["i18n"],
        # У этой цели нет генератов как файлов, очищать нечего.
    }
 
