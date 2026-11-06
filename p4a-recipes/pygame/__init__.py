"""python-for-android için pygame 2.6.1 tarifi.

Varsayılan tarif pygame 2.1.0 kullanıyor; o sürüm Python 3.11 ile derlenemiyor.
PyPI'deki 2.6.1 kaynak paketi Cython 3 ile üretilmiş C dosyalarını içerir.
"""
from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = ("https://files.pythonhosted.org/packages/49/cc/"
           "08bba60f00541f62aaa252ce0cfbd60aebd04616c0b9574f755b583e45ae/pygame-2.6.1.tar.gz")


recipe = Pygame261Recipe()
