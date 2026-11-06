"""Kanatix Arcade - başlatıcı.

Çalıştırmak için:  python main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core import App  # noqa: E402
from engine.menu import MainMenu  # noqa: E402


def main():
    app = App()
    try:
        from engine.updater import check_update_async
        check_update_async(app)
    except Exception:
        pass
    app.run(MainMenu(app))


if __name__ == "__main__":
    main()
