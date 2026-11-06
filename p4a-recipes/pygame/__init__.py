"""python-for-android için pygame 2.6.1 tarifi.

Varsayılan tarif pygame 2.1.0 kullanıyor; o sürüm Python 3.11 ile derlenemiyor.
PyPI'deki 2.6.1 kaynak paketi Cython 3 ile üretilmiş C dosyalarını içerir.

Düzeltme: pygame 2.6.1'in Android yapılandırmasında (Setup.Android.SDL2.in) "surface"
modülü SIMD blit dosyalarını içermiyor. Bu yüzden surface.so telefonda
"alphablit_alpha_sse2_argb_surf_alpha" sembolünü bulamıyor ve oyun açılırken kapanıyordu.
"""
from pythonforandroid.recipes.pygame import Pygame2Recipe
from pythonforandroid.toolchain import current_directory


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = ("https://files.pythonhosted.org/packages/49/cc/"
           "08bba60f00541f62aaa252ce0cfbd60aebd04616c0b9574f755b583e45ae/pygame-2.6.1.tar.gz")

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup = open("Setup").read()
            old = "surface src_c/surface.c"
            new = "surface src_c/simd_blitters_sse2.c src_c/simd_blitters_avx2.c src_c/surface.c"
            if old in setup and "simd_blitters_sse2" not in setup:
                setup = setup.replace(old, new)
                open("Setup", "w").write(setup)
            # kontrol için kayda yaz
            print("pygame Setup surface satırı:", [ln for ln in setup.splitlines() if ln.startswith("surface")])


recipe = Pygame261Recipe()
