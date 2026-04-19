import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

project = 'MOOD'
copyright = '2026, Mikail'
author = 'Mikail'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'
html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
