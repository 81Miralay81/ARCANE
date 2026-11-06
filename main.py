"""Kanatix Arcade - başlatıcı.

Çalıştırmak için:  python main.py
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _log_dir():
    for env in ("ANDROID_PRIVATE", "APPDATA"):
        if os.environ.get(env):
            return os.environ[env]
    return os.path.expanduser("~")


def show_crash(tb):
    """Hata olursa sessizce kapanmak yerine hatayı ekranda göster ve dosyaya yaz."""
    print("KANATIX HATA:\n" + tb, flush=True)
    try:
        with open(os.path.join(_log_dir(), "kanatix_hata.txt"), "w", encoding="utf-8") as f:
            f.write(tb)
    except Exception:
        pass
    try:
        import pygame
        pygame.init()
        try:
            screen = pygame.display.get_surface() or pygame.display.set_mode((1280, 720))
        except Exception:
            screen = pygame.display.set_mode((0, 0))
        f = pygame.font.Font(None, 26)
        clock = pygame.time.Clock()
        lines = ["Kanatix Arcade bir hatayla karşılaştı. Bu ekranın fotoğrafını gönder:", ""] + tb.splitlines()[-22:]
        for _ in range(60 * 60):
            for e in pygame.event.get():
                if e.type in (pygame.QUIT, pygame.KEYDOWN):
                    return
            screen.fill((30, 0, 20))
            for i, ln in enumerate(lines):
                screen.blit(f.render(ln[:110], True, (255, 230, 230)), (20, 20 + i * 28))
            pygame.display.flip()
            clock.tick(30)
    except Exception:
        pass


def main():
    print("Kanatix Arcade başlıyor", flush=True)
    from engine.core import App
    from engine.menu import MainMenu
    app = App()
    try:
        from engine.updater import check_update_async
        check_update_async(app)
    except Exception:
        traceback.print_exc()
    app.run(MainMenu(app))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        show_crash(traceback.format_exc())
