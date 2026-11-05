from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.text import Text
from typing import TYPE_CHECKING
import glob
import json
import os
import pygame
import queue
import shutil
import stat
import sys
import threading
import time
import traceback

import sys

# alias so "config.X" references keep working in one file
config = sys.modules[__name__]


# ============================================================================
# MODULE: config
# ============================================================================
# ============================================================================
#  ИКОНКА ПРИЛОЖЕНИЯ
# ============================================================================

# Корень проекта — папка, где лежит Cleaner.py. Этот файл лежит на уровень
# глубже (в cleaner_app), поэтому поднимаемся на одну папку вверх.
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _script_dir() -> str:
    """Папка, где лежит наш .py или собранный .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return _ROOT_DIR


ICON_PATH = os.path.join(_script_dir(), "icon.ico")


# ============================================================================
#  НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
# ============================================================================
# ---------- Переключатели (True — чистить, False — не трогать) ----------
# Кэши шейдеров NVIDIA/AMD/Intel/D3D. Удаление безопасно, но игры потом
# заново компилируют шейдеры (первый запуск может идти очень долго).

# (Это значение по умолчанию. В программе его можно переключить командой «у»
#  на вопросе об удалении — выбор запоминается в файле Cleaner_условия.txt
#  рядом с программой. Файл можно править вручную — см. команду ф.)

CLEAN_SHADER_CACHES = True


# Папка .cache в профиле пользователя. Там часто лежат скачанные модели
# (например huggingface) — после удаления они скачиваются заново.

CLEAN_DOT_CACHE = True


# ---------- Дерево папок в списке перед удалением ----------
# Перед вопросом об удалении программа показывает основные папки, из которых что-то
# удаляется, и «раскрывает» их: какие внутри папки, сколько они весят, какие
# файлы. Эти числа влияют ТОЛЬКО на показ, на удаление — нет.
#   TREE_DEPTH       — сколько уровней вложенных папок раскрывать;
#   TREE_MAX_FOLDERS — сколько папок показывать внутри одной папки;
#   TREE_MAX_FILES   — сколько файлов показывать внутри одной папки.
# Остальное сворачивается в строку «… ещё N ...» с общим весом.

TREE_DEPTH = 3


TREE_MAX_FOLDERS = 10


TREE_MAX_FILES = 5


# ---------- Цвет рамки окна ----------
# Рамка окна меняет цвет: ЗЕЛЁНАЯ, когда окно программы активно (вы кликнули
# в него), и КРАСНАЯ, когда вы переключились на другое окно.
# Цвета задаются как (R, G, B), числа от 0 до 255.
# Работает на Windows 11 (на Windows 10 рамка просто останется обычной).
# Чтобы отключить — поставьте CHANGE_BORDER_COLOR = False.

CHANGE_BORDER_COLOR = True


BORDER_COLOR_ACTIVE = (0, 200, 0)


BORDER_COLOR_INACTIVE = (220, 0, 0)


# Заголовок окна (верхняя полоса с названием и кнопками) — тоже меняет цвет.
# Тёмные оттенки выбраны, чтобы белый текст на них хорошо читался.
# Отключить только заголовок — CHANGE_TITLEBAR_COLOR = False.

CHANGE_TITLEBAR_COLOR = True


TITLEBAR_COLOR_ACTIVE = (0, 130, 0)


TITLEBAR_COLOR_INACTIVE = (170, 0, 0)


TITLEBAR_TEXT_COLOR = (255, 255, 255)


USER_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))


LOCAL = os.environ.get("LOCALAPPDATA", USER_PROFILE + r"\AppData\Local")


ROAMING = os.environ.get("APPDATA", USER_PROFILE + r"\AppData\Roaming")


# ---------- Поиск папок Cache ----------
# На вопросе «Удалить ...?» введите п — программа НАЙДЁТ любые папки с
# названием Cache по ВСЕМ локальным дискам (C:, D:, ...) и предложит добавить
# их в список на удаление. По каждой папке можно ответить «да», «нет»,
# «да для всех оставшихся» или закончить поиск. Сам поиск ничего не удаляет:
# удаление только после «д».
#
# Что НЕ просматривается никогда: системные и защищённые места (Windows,
# Program Files, ProgramData, чужие профили в C:\Users, корзина, служебные
# папки дисков и т.п.), а также ссылки/junction. Кроме того пропускаются
# папки, где «cache» — это часть кода, а не кэш (node_modules, site-packages,
# .git, виртуальные окружения): их удаление сломало бы программы.
#
#   CACHE_SEARCH_ROOTS — где искать. ПУСТОЙ список [] = все локальные диски
#                        (так и стоит). Чтобы искать только в конкретных
#                        местах, впишите их:  r"D:\Games",
#   CACHE_FOLDER_NAMES — какие имена папок считать кэшем (регистр не важен).
#                        Можно дописать, например, ".cache" или "GPUCache".
#   CACHE_SEARCH_SKIP  — имена папок, куда поиск не заходит (дополняйте).
# Папки, которые уже входят в основной список PATHS, при поиске не
# повторяются. Удаляется СОДЕРЖИМОЕ найденной папки, сама папка остаётся.

CACHE_SEARCH_ROOTS = []


CACHE_FOLDER_NAMES = {"cache"}


CACHE_SEARCH_SKIP = {
    "node_modules", "site-packages", ".git", ".venv", "venv", ".svn",
}


# Служебные папки Windows: пропускаются на любом диске, на любой глубине.

_SEARCH_SKIP_ANYWHERE = {
    "$recycle.bin", "system volume information", "windowsapps", "winsxs",
    "$windows.~bt", "$windows.~ws", "$winreagent", "config.msi",
}


# Они же, но только когда лежат прямо в корне диска.

_SEARCH_SKIP_AT_ROOT = {
    "windows", "windows.old", "program files", "program files (x86)",
    "programdata", "recovery", "msocache", "perflogs", "boot", "efi",
}


CHROMIUM_BROWSERS = [
    LOCAL + r"\Google\Chrome\User Data",
    LOCAL + r"\Microsoft\Edge\User Data",
    LOCAL + r"\BraveSoftware\Brave-Browser\User Data",
    LOCAL + r"\Vivaldi\User Data",
]


CHROMIUM_CACHE_FOLDERS = [
    r"Cache\Cache_Data",
    r"Code Cache\js",
    r"Code Cache\wasm",
    r"GPUCache",
    r"DawnGraphiteCache",
    r"DawnWebGPUCache",
    r"Service Worker\CacheStorage",
]


PATHS = [
    LOCAL + r"\Temp",
    LOCAL + r"\CrashDumps",
    LOCAL + r"\Microsoft\Windows\INetCache",
    LOCAL + r"\Microsoft\Windows\WER\ReportArchive",
    LOCAL + r"\Microsoft\Windows\WER\ReportQueue",

    LOCAL + r"\Opera Software\Opera Stable\Cache",
    LOCAL + r"\Opera Software\Opera GX Stable\Cache",

    LOCAL + r"\pip\Cache",
    LOCAL + r"\uv\cache",
    LOCAL + r"\npm-cache",
    LOCAL + r"\Yarn\Cache",
    LOCAL + r"\NuGet\v3-cache",
    LOCAL + r"\Nuitka\Nuitka\Cache",   # C:\Users\<вы>\AppData\Local\Nuitka\Nuitka\Cache

    ROAMING + r"\Code\Cache",
    ROAMING + r"\Code\CachedData",
    ROAMING + r"\Code\CachedExtensionVSIXs",
    ROAMING + r"\Code\Code Cache",
    ROAMING + r"\Code\GPUCache",

    ROAMING + r"\discord\Cache",
    ROAMING + r"\discord\Code Cache",
    ROAMING + r"\discord\GPUCache",

    ROAMING + r"\Slack\Cache",
    ROAMING + r"\Slack\Code Cache",
    ROAMING + r"\Slack\GPUCache",
    ROAMING + r"\Slack\Service Worker\CacheStorage",

    LOCAL + r"\Steam\htmlcache",

    USER_PROFILE + r"\.unsloth\studio\cache",
]


# Кэш Redshift (Cinebench). У папки Cinebench_<код> суффикс случайный и у
# разных установок разный, поэтому ищем через маску * в обеих ветках Maxon.

for base in (ROAMING + r"\Maxon", LOCAL + r"\Maxon"):
    for cb in glob.glob(base + r"\Cinebench_*"):
        PATHS.append(cb + r"\Redshift\Cache")


for browser in CHROMIUM_BROWSERS:
    profiles = glob.glob(browser + r"\Default") + glob.glob(browser + r"\Profile *")
    for profile in profiles:
        for folder in CHROMIUM_CACHE_FOLDERS:
            PATHS.append(profile + "\\" + folder)
    for folder in (r"GrShaderCache", r"ShaderCache", r"GraphiteDawnCache",
                   r"component_crx_cache"):
        PATHS.append(browser + "\\" + folder)


for profile in glob.glob(LOCAL + r"\Mozilla\Firefox\Profiles\*"):
    PATHS.append(profile + r"\cache2")
    PATHS.append(profile + r"\startupCache")


# Эти две группы НЕ входят в PATHS: их включают/выключают в программе
# (команда «у»), см. active_paths().

SHADER_PATHS = [
    LOCAL + r"\NVIDIA\GLCache",
    LOCAL + r"\NVIDIA\DXCache",
    LOCAL + r"\NVIDIA\OptixCache",
    LOCAL + r"\AMD\DxCache",
    LOCAL + r"\AMD\GLCache",
    LOCAL + r"\AMD\VkCache",
    LOCAL + r"\Intel\ShaderCache",
    LOCAL + r"\D3DSCache",
]


DOT_CACHE_PATHS = [USER_PROFILE + r"\.cache"]


# ============================================================================
#  МОИ ПУТИ — СЮДА МОЖНО САМОМУ ВПИСЫВАТЬ СВОИ ПАПКИ
# ----------------------------------------------------------------------------
#  Как добавить свою папку:
#
#   1. Откройте папку в Проводнике, кликните в адресную строку и нажмите
#      Ctrl+C (или Shift + ПКМ по папке -> «Копировать как путь»).
#
#   2. Добавьте в список CUSTOM_PATHS ниже новую строку такого вида:
#
#          r"C:\Users\MSI\Моя папка\Кэш",
#
#      Правила:
#        - перед первой кавычкой обязательно буква r;
#        - путь между кавычками (кавычки из Проводника не дублировать);
#        - слэш в конце пути не ставить;
#        - в конце строки запятая.
#
#   3. Строка, начинающаяся с #, — комментарий (выключена). Чтобы включить
#      пример — уберите #. Чтобы отключить путь — поставьте # перед ним.
#
#   4. Удаляется СОДЕРЖИМОЕ папки, сама папка остаётся.
#
#   5. Работает звёздочка * («любое имя») и переменные Windows,
#      например r"%LOCALAPPDATA%\Temp".
#
#   6. Защита (is_forbidden) и вопрос y/N перед удалением остаются в силе.
#
#   7. ПОИСК ПАПОК В ПАПКАХ (только для путей из этого списка).
#      Число CUSTOM_SCAN_DEPTH ниже говорит, на сколько уровней вглубь
#      заходить:
#        1 — как у обычных путей: удаляется всё, что лежит прямо в папке
#            (подпапки целиком);
#        2 — программа заходит в каждую подпапку и удаляет то, что лежит
#            ВНУТРИ неё; сами подпапки первого уровня остаются пустыми;
#        3 — то же, но на уровень глубже, и т.д.
#      Файлы, лежащие выше нужного уровня, удаляются как обычно.
#
#  Внимание: чистите только папки, где лежит именно кэш/временные файлы.
#  Например, C:\Users\MSI\AppData\Local\Packages целиком чистить нельзя —
#  там данные приложений Microsoft Store (настройки, логины).
# ============================================================================

# На сколько уровней вглубь заходить в папках из CUSTOM_PATHS (см. пункт 7).

CUSTOM_SCAN_DEPTH = 2


CUSTOM_PATHS = [
    # ---------- ВПИСЫВАЙТЕ СВОИ ПУТИ НИЖЕ ЭТОЙ ЛИНИИ ----------

    # r"D:\Games\SomeGame\Cache",

    # ---------- ВПИСЫВАЙТЕ СВОИ ПУТИ ВЫШЕ ЭТОЙ ЛИНИИ ----------
]


CUSTOM_RESOLVED = []


for _p in CUSTOM_PATHS:
    _p = os.path.expandvars(_p.strip().strip('"')).rstrip("\\/")
    if not _p:
        continue
    if "*" in _p or "?" in _p:
        CUSTOM_RESOLVED += glob.glob(_p)
    else:
        CUSTOM_RESOLVED.append(_p)


PATHS += CUSTOM_RESOLVED


PATHS = [p for p in dict.fromkeys(PATHS) if os.path.isdir(p)]


SHADER_PATHS = [p for p in SHADER_PATHS if os.path.isdir(p)]


DOT_CACHE_PATHS = [p for p in DOT_CACHE_PATHS if os.path.isdir(p)]


FORBIDDEN_ROOTS = [
    "C:\\",
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Users",
]


# ============================================================================
#  ФАЙЛЫ РЯДОМ С ПРОГРАММОЙ
# ----------------------------------------------------------------------------
#  Все условия работы хранятся в обычных текстовых файлах (UTF-8) рядом с
#  программой. Их создаёт сама программа при первом запуске, внутри — подсказки.
#  Правьте в Блокноте, сохраняйте — при следующем запуске (или по команде ф
#  в программе) новые условия принимаются.
# ============================================================================

def _data_dir() -> str:
    """Папка рядом с программой (.py, .pyw или собранный .exe), куда пишутся файлы."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    if "__compiled__" in globals():          # Nuitka (в т.ч. onefile)
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return _ROOT_DIR


FILE_CONDITIONS = os.path.join(_data_dir(), "Cleaner_условия.txt")


FILE_CUSTOM = os.path.join(_data_dir(), "Cleaner_свои_пути.txt")


FILE_BLACKLIST = os.path.join(_data_dir(), "Cleaner_чёрный_список.txt")


FILE_SPEEDTEST = os.path.join(_data_dir(), "Cleaner_тест_скорости.txt")


# Где окно было при закрытии (положение, размер, развёрнуто ли). Пишет и читает
# сама программа, руками править не нужно; удалите файл — окно откроется
# по умолчанию (WINDOW_DEFAULT_SIZE в центре экрана).
FILE_WINDOW = os.path.join(_data_dir(), "Cleaner_окно.json")


WINDOW_DEFAULT_SIZE = (1000, 700)


WINDOW_MIN_SIZE = (480, 320)


LEGACY_JSON = os.path.join(_data_dir(), "cleaner_settings.json")   # старый формат


# ============================================================================
# MODULE: utils
# ============================================================================
# ============================================================================
#  ЛОГИКА ОЧИСТКИ (без UI)
# ============================================================================

def human_size(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"


def _norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def _fmt_n(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# ============================================================================
# MODULE: fsutil
# ============================================================================
# ----------------------------------------------------------------------------
#  ПОДСЧЁТ РАЗМЕРА — ЕДИНЫЕ ПРАВИЛА
# ----------------------------------------------------------------------------
#  Раньше вес считали тремя разными кусками кода (collect_items, build_tree,
#  recompute_size) с разными правилами, и числа в списке, в дереве и в итоге
#  расходились. Теперь все три используют одни и те же функции ниже.
#
#  Правила:
#    • считается размер самих файлов (логический, как «Размер» в Проводнике);
#    • ссылки (symlink) и junction НЕ раскрываются и не считаются по цели:
#      удаление ссылки не освобождает место, на которое она указывает.
#      Это важно для .cache: кэш huggingface — это снапшоты-симлинки на blobs,
#      и «следование» по ним считало одни и те же гигабайты дважды;
#    • длинные пути (> 260 символов) читаются через префикс \\?\ — иначе
#      Windows отказывает, и файл молча выпадал из подсчёта;
#    • файл, у которого не удалось узнать размер, НЕ выбрасывается из списка:
#      он считается как 0 байт, но удаление всё равно будет пробовать.
# ----------------------------------------------------------------------------

def _long(path: str) -> str:
    """Путь с длинным префиксом на Windows (снимает лимит в 260 символов)."""
    if os.name != "nt":
        return path
    p = os.path.abspath(path)
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p[2:]
    return "\\\\?\\" + p


def _is_reparse(entry) -> bool:
    """True для symlink и junction (их содержимое не раскрываем)."""
    try:
        if entry.is_symlink():
            return True
        st = entry.stat(follow_symlinks=False)
        return bool(getattr(st, "st_file_attributes", 0) & 0x400)  # REPARSE_POINT
    except OSError:
        return False


def _entry_size(entry) -> int:
    """Размер одного файла/ссылки без перехода по ссылке."""
    try:
        return entry.stat(follow_symlinks=False).st_size
    except OSError:
        return 0


def _is_link_or_junction(path: str) -> bool:
    """symlink или junction. Через атрибут REPARSE_POINT, а не os.path.isjunction
    (он есть только в Python 3.12+ — на старых junction не определялся)."""
    try:
        if os.path.islink(path):
            return True
        st = os.lstat(_long(path))
        return bool(getattr(st, "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def is_locked_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError):
        winerror = getattr(exc, "winerror", None)
        errno = getattr(exc, "errno", None)
        if winerror == 32:
            return True
        if errno in (13, 16):
            return True
    return False


# ============================================================================
# MODULE: winapi
# ============================================================================
# ============================================================================
#  БУФЕР ОБМЕНА
# ----------------------------------------------------------------------------
#  Копирование выделенного текста (Ctrl+C) и всего текста (Ctrl+A).
#  На Windows пишем в буфер напрямую через WinAPI в формате Unicode —
#  так кириллица и символы вроде ✓ гарантированно вставляются без искажений.
#  Если не вышло (или это не Windows) — пробуем средства самого pygame.
# ============================================================================

def _clipboard_put_win32(text: str) -> bool:
    import ctypes
    from ctypes import wintypes

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    # В буфере Windows переводы строк принято хранить как \r\n.
    data = (text.replace("\r\n", "\n").replace("\n", "\r\n") + "\0").encode("utf-16-le")

    # Буфер может быть на долю секунды занят другой программой — пробуем несколько раз.
    opened = False
    for _ in range(10):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.02)
    if not opened:
        return False

    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            return False
        return True  # после успеха память принадлежит системе — освобождать нельзя
    finally:
        user32.CloseClipboard()


def clipboard_put(text: str) -> bool:
    """Кладёт текст в буфер обмена. True — получилось."""
    if os.name == "nt":
        try:
            if _clipboard_put_win32(text):
                return True
        except Exception:
            pass
    try:
        if hasattr(pygame.scrap, "put_text"):          # pygame-ce
            pygame.scrap.put_text(text)
            return True
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
        return True
    except Exception:
        return False


# ============================================================================
#  ЦВЕТ РАМКИ ОКНА (Windows 11)
# ----------------------------------------------------------------------------
#  Через DwmSetWindowAttribute задаём окну цвет рамки (DWMWA_BORDER_COLOR).
#  Цвет в формате COLORREF: 0x00BBGGRR. Если система не поддерживает
#  (Windows 10 и старше) — функция тихо вернёт False, ничего не сломается.
# ============================================================================

def _dwm_set_color(attribute: int, rgb) -> bool:
    """Задать окну цветовой атрибут DWM: 34 — рамка, 35 — заголовок,
    36 — цвет текста заголовка."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd:
            return False
        r, g, b = rgb
        colorref = ctypes.c_uint32(r | (g << 8) | (b << 16))
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            attribute,
            ctypes.byref(colorref),
            ctypes.sizeof(colorref),
        )
        return result == 0
    except Exception:
        return False


def set_window_border_color(rgb) -> bool:
    return _dwm_set_color(34, rgb)


def set_window_titlebar_colors(bg_rgb, text_rgb) -> bool:
    ok_bg = _dwm_set_color(35, bg_rgb)
    ok_text = _dwm_set_color(36, text_rgb)
    return ok_bg and ok_text


# ============================================================================
#  ПОЛОЖЕНИЕ И РАЗМЕР ОКНА (для запоминания между запусками)
# ----------------------------------------------------------------------------
#  Все координаты — в «клиентской» области окна (без рамки и заголовка), в
#  экранных пикселях: именно так их понимает SDL/pygame и при создании окна
#  (SDL_VIDEO_WINDOW_POS), и при чтении, поэтому окно возвращается точно туда.
#  Вне Windows функции возвращают None — тогда запоминается только размер.
# ============================================================================

def _user32():
    import ctypes
    from ctypes import wintypes

    u = ctypes.WinDLL("user32", use_last_error=True)
    u.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.GetClientRect.restype = wintypes.BOOL
    u.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    u.ClientToScreen.restype = wintypes.BOOL
    u.IsZoomed.argtypes = [wintypes.HWND]
    u.IsZoomed.restype = wintypes.BOOL
    u.IsIconic.argtypes = [wintypes.HWND]
    u.IsIconic.restype = wintypes.BOOL
    u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    u.ShowWindow.restype = wintypes.BOOL
    u.MonitorFromRect.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD]
    u.MonitorFromRect.restype = wintypes.HANDLE
    u.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    u.GetMonitorInfoW.restype = wintypes.BOOL
    return u


def _hwnd():
    try:
        return pygame.display.get_wm_info().get("window")
    except Exception:
        return None


def get_window_geometry():
    """Текущее состояние окна: (x, y, w, h, maximized, minimized) или None.
    x, y, w, h — клиентская область в экранных пикселях."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = _hwnd()
        if not hwnd:
            return None
        u = _user32()
        h = ctypes.c_void_p(hwnd)
        rc = wintypes.RECT()
        if not u.GetClientRect(h, ctypes.byref(rc)):
            return None
        pt = wintypes.POINT(0, 0)
        if not u.ClientToScreen(h, ctypes.byref(pt)):
            return None
        return (pt.x, pt.y, rc.right - rc.left, rc.bottom - rc.top,
                bool(u.IsZoomed(h)), bool(u.IsIconic(h)))
    except Exception:
        return None


def maximize_window() -> bool:
    """Развернуть окно на весь экран (SW_MAXIMIZE)."""
    if os.name != "nt":
        return False
    try:
        import ctypes

        hwnd = _hwnd()
        if not hwnd:
            return False
        _user32().ShowWindow(ctypes.c_void_p(hwnd), 3)
        return True
    except Exception:
        return False


def work_area_near(x: int, y: int, w: int, h: int):
    """Рабочая область (без панели задач) монитора, ближайшего к прямоугольнику,
    как (left, top, right, bottom). Если монитор, где окно было раньше, отключён,
    вернётся ближайший из оставшихся. None — если определить не удалось."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD)]

        u = _user32()
        rc = wintypes.RECT(x, y, x + w, y + h)
        mon = u.MonitorFromRect(ctypes.byref(rc), 2)    # 2 = ближайший монитор
        if not mon:
            return None
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not u.GetMonitorInfoW(mon, ctypes.byref(info)):
            return None
        r = info.rcWork
        return (r.left, r.top, r.right, r.bottom)
    except Exception:
        return None


# ============================================================================
# MODULE: window_state
# ============================================================================
# Сверху над клиентской областью — заголовок окна; оставляем под него место,
# чтобы его можно было схватить мышью, даже если окно прижато к верхнему краю.
_TITLE_ALLOWANCE = 40


def load_window_state():
    """Читает сохранённое состояние. Нет файла / файл испорчен -> None."""
    try:
        with open(config.FILE_WINDOW, "r", encoding="utf-8") as f:
            raw = json.load(f)
        w, h = int(raw["w"]), int(raw["h"])
        pos = raw.get("x"), raw.get("y")
        x = int(pos[0]) if pos[0] is not None else None
        y = int(pos[1]) if pos[1] is not None else None
        return {"x": x, "y": y, "w": w, "h": h,
                "maximized": bool(raw.get("maximized", False))}
    except Exception:
        return None


def save_window_state(state: dict) -> bool:
    """Пишет состояние атомарно (во временный файл и подмена), чтобы при
    закрытии на лету файл не остался наполовину записанным."""
    path = config.FILE_WINDOW
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def fit_to_screen(state):
    """Приводит сохранённое состояние к текущим мониторам.

    Возвращает (x, y, w, h, maximized); x и y — None, если положение
    неизвестно или окно надо поставить по центру (SDL сделает это сам).
    Размер ограничивается снизу WINDOW_MIN_SIZE, сверху — рабочей областью
    монитора; окно сдвигается внутрь рабочей области, так что после смены
    монитора или разрешения оно не окажется за краем экрана."""
    dw, dh = config.WINDOW_DEFAULT_SIZE
    if not state:
        return None, None, dw, dh, False

    min_w, min_h = config.WINDOW_MIN_SIZE
    w = max(min_w, state["w"])
    h = max(min_h, state["h"])
    x, y = state["x"], state["y"]
    if x is None or y is None:
        return None, None, w, h, state["maximized"]

    area = work_area_near(x, y, w, h)
    if area is not None:
        left, top, right, bottom = area
        w = min(w, right - left)
        h = min(h, bottom - top - _TITLE_ALLOWANCE)
        x = max(left, min(x, right - w))
        y = max(top + _TITLE_ALLOWANCE, min(y, bottom - h))
    return x, y, w, h, state["maximized"]


# ============================================================================
# MODULE: admin
# ============================================================================
# ============================================================================
#  ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
# ----------------------------------------------------------------------------
#  Программа НЕ должна запускаться от имени администратора. Причины:
#    • она чистит ТОЛЬКО пользовательские кэши (AppData), для них хватает
#      обычных прав;
#    • от админа любой баг в путях может привести к удалению чего-то системного.
#
#  Проверяем через ctypes.windll.shell32.IsUserAnAdmin().
#  Если программа запущена от админа:
#    • печатаем сообщение в stdout (для .py из терминала);
#    • показываем MessageBoxW (для .pyw и .exe без консоли);
#    • завершаемся с кодом 1.
# ============================================================================

def is_admin() -> bool:
    """True, если текущий процесс запущен с правами администратора."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def refuse_admin_and_exit():
    """Сообщает о неверных правах и завершает процесс."""
    title = "Cleaner — неверные права"
    message = (
        "Программа не может быть выполнена с правами администратора.\n\n"
        "Пожалуйста, закройте это окно и запустите программу заново\n"
        "без прав администратора (обычным двойным кликом по файлу)."
    )
    try:
        print(message)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x0 | 0x10 | 0x40000)
    except Exception:
        pass
    sys.exit(1)


# ============================================================================
# MODULE: commands
# ============================================================================
# Команды вводятся по-русски. Латинские аналоги (y, a, q, s) тоже понимаются.

_YES = ("д", "да", "y", "yes")


_ALL = ("в", "все", "всё", "a", "all", "ф")


_QUIT = ("с", "стоп", "выход", "q", "quit", "й")


_SEARCH = ("п", "поиск", "найти", "s", "search", "ы")


_CONDITIONS = ("у", "условия", "настройки", "опции")


_CUSTOMMENU = ("м", "мои", "свои")


_SPEED = ("т", "тест", "скорость")


_RELOAD = ("ф", "файлы", "перечитать")


_BLMENU = ("ч", "чс", "чёрный", "черный", "блок")


_SOURCES = ("с", "c", "список", "пути", "итог", "итоги")


# ============================================================================
# MODULE: progress
# ============================================================================
# ----------------------------------------------------------------------------
#  СТРОКА ПРОВЕРКИ (прогресс 0–100 % с анимацией)
#  Progress — объект на стороне рабочего потока: считает долю работы и шлёт её
#  в окно (не чаще ~20 раз в секунду). Окно рисует закреплённую строку
#  «Проверка файлов [█████░░░] 45 %» и плавно подтягивает шкалу к реальному
#  значению. Так видно в реальном времени, что программа не зависла.
#  Доля считается иерархически: интервал папки делится поровну между её
#  подпапками, поэтому шкала идёт только вперёд и доходит до 100 %.
# ----------------------------------------------------------------------------

_PROG = None


class Progress:
    def __init__(self, ui, title: str, cancellable: bool = False, log: bool = True):
        self.ui = ui
        self.q = getattr(ui, "out_queue", None)
        self.title = title
        self.cancellable = cancellable
        self.log = log
        self.files = 0
        self.dirs = 0
        self.frac = 0.0
        self.t0 = time.monotonic()
        self._last = 0.0
        self.owner = None
        self.lo = 0.0
        self.hi = 1.0
        self.path = ""
        self._done = False
        self._lock = threading.Lock()   # tick() зовут из нескольких потоков сканера
        ev = getattr(ui, "cancel_event", None)
        if cancellable and ev is not None:
            ev.clear()
        self._send(force=True)

    def _send(self, force: bool = False):
        if self.q is None:
            return
        now = time.monotonic()
        if not force and now - self._last < 0.05:
            return
        self._last = now
        counts = f"папок {_fmt_n(self.dirs)} · файлов {_fmt_n(self.files)}"
        self.q.put(("prog", self.title, self.frac, (counts, self.path),
                    self.cancellable))

    def set(self, frac: float, path: str = None):
        if frac > self.frac:
            self.frac = min(1.0, frac)
        if path:
            self.path = path
        self._send()

    def set_span(self, lo: float, hi: float, owner: str = None):
        self.lo, self.hi, self.owner = lo, hi, owner
        self.set(lo)

    def child_progress(self, i: int, n: int):
        self.set(self.lo + (self.hi - self.lo) * i / max(1, n))

    def tick(self, path: str = None, files: int = 0, dirs: int = 0):
        with self._lock:
            self.files += files
            self.dirs += dirs
            if path:
                self.path = path
        self._send()

    def cancelled(self) -> bool:
        ev = getattr(self.ui, "cancel_event", None)
        return bool(self.cancellable and ev is not None and ev.is_set())

    def finish(self, cancelled: bool = False):
        if self._done:
            return
        self._done = True
        if not cancelled:
            self.frac = 1.0
        self._send(force=True)
        if self.q is not None:
            self.q.put(("prog_end", cancelled))
        if self.log and self.ui is not None:
            sec = time.monotonic() - self.t0
            state = "остановлено" if cancelled else "100%"
            self.ui.write(Text(
                f"  {self.title}: {state} — папок {_fmt_n(self.dirs)}, "
                f"файлов {_fmt_n(self.files)}, {sec:.1f} с", style="dim"))

    def __enter__(self):
        global _PROG
        _PROG = self
        return self

    def __exit__(self, exc_type, exc, tb):
        global _PROG
        _PROG = None
        self.finish(cancelled=bool(exc_type) or self.cancelled())
        return False


def get_active_progress():
    """Текущий индикатор проверки (или None) — его читают сканеры."""
    return _PROG


# ============================================================================
# MODULE: settings
# ============================================================================
# ============================================================================
#  УСЛОВИЯ (ВКЛ/ВЫКЛ) — меняются в программе командой «у»
# ----------------------------------------------------------------------------
#  Шесть переключателей:
#    shader   — чистить кэши шейдеров (CLEAN_SHADER_CACHES);
#    dot      — чистить папку .cache в профиле (CLEAN_DOT_CACHE);
#    s_docs / s_local / s_locallow / s_roaming — искать ли папки Cache внутри
#      Documents, AppData\Local, AppData\LocalLow, AppData\Roaming
#      (влияет только на команду поиска «п»; основной список не затрагивает).
#  Все условия записаны в ТЕКСТОВЫХ файлах рядом с программой (создаются сами
#  при первом запуске, с подсказками внутри):
#     Cleaner_условия.txt       — ВКЛ/ВЫКЛ, где искать Cache, имена кэша, глубина;
#     Cleaner_свои_пути.txt     — свои пути (обычные и с условием);
#     Cleaner_чёрный_список.txt — чёрный список.
#  Откройте файл в Блокноте, поменяйте, сохраните — при следующем запуске
#  (или по команде ф) программа примет новые условия. Удалите файл — он
#  создастся заново со значениями по умолчанию.
# ============================================================================

DOCUMENTS_DIR = USER_PROFILE + r"\Documents"


LOCAL_DIR = LOCAL


LOCALLOW_DIR = USER_PROFILE + r"\AppData\LocalLow"


ROAMING_DIR = ROAMING


SETTINGS = {
    "shader": bool(CLEAN_SHADER_CACHES),
    "dot": bool(CLEAN_DOT_CACHE),
    "s_docs": True,
    "s_local": True,
    "s_locallow": True,
    "s_roaming": True,
}


# (ключ, текст в меню, папка для переключателей поиска или None)

SETTING_OPTIONS = [
    ("shader", "Чистка кэшей шейдеров (NVIDIA / AMD / Intel / D3D)", None),
    ("dot", "Чистка папки .cache в профиле  (" + USER_PROFILE + r"\.cache)", None),
    ("s_docs", "Поиск Cache в папке  " + DOCUMENTS_DIR, DOCUMENTS_DIR),
    ("s_local", "Поиск Cache в папке  " + LOCAL_DIR, LOCAL_DIR),
    ("s_locallow", "Поиск Cache в папке  " + LOCALLOW_DIR, LOCALLOW_DIR),
    ("s_roaming", "Поиск Cache в папке  " + ROAMING_DIR, ROAMING_DIR),
]


# ---------- Свои пути (добавляются прямо в программе, команда м) ----------
# Каждый путь: {"path": "...", "mode": "normal" | "toggle", "enabled": True/False}
#   normal — обычный путь: чистится всегда;
#   toggle — путь с условием: чистится, только когда он ВКЛ.

CUSTOM_RUNTIME = []


# ---------- Чёрный список (команда ч) ----------
# ПРИОРИТЕТ над всем: путь из чёрного списка и всё, что внутри него, программа
# не ищет, не показывает и не удаляет — даже если этот путь есть в основном
# списке, в CUSTOM_PATHS, в своих путях или найден поиском Cache.

BLACKLIST = []


SETTINGS_WARNINGS = []       # непонятые строки в файлах — покажем в окне


def _warn(msg: str):
    SETTINGS_WARNINGS.append(msg)


def _read_text(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "cp1251"):      # cp1251 — если сохранили «ANSI» в Блокноте
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _write_text(path: str, text: str):
    try:
        with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(text)
    except OSError as e:
        _warn(f"Не удалось записать файл {path}: {e}")


def _append_text(path: str, text: str):
    try:
        enc = "utf-8" if os.path.exists(path) else "utf-8-sig"
        with open(path, "a", encoding=enc, newline="\r\n") as f:
            f.write(text)
    except OSError as e:
        _warn(f"Не удалось дописать файл {path}: {e}")


_ON_WORDS = ("вкл", "включен", "включён", "включено", "да", "on", "true", "1", "yes", "y")


_OFF_WORDS = ("выкл", "выключен", "выключено", "нет", "off", "false", "0", "no", "n")


def _parse_onoff(v: str):
    v = v.strip().lower()
    if v in _ON_WORDS:
        return True
    if v in _OFF_WORDS:
        return False
    return None


def _fmt_onoff(v) -> str:
    return "ВКЛ" if v else "ВЫКЛ"


# (ключ в файле, ключ в SETTINGS)

_COND_KEYS = [
    ("чистка_шейдеров", "shader"),
    ("чистка_dot_cache", "dot"),
    ("поиск_в_documents", "s_docs"),
    ("поиск_в_local", "s_local"),
    ("поиск_в_locallow", "s_locallow"),
    ("поиск_в_roaming", "s_roaming"),
]


def _conditions_text() -> str:
    S = SETTINGS
    L = []
    a = L.append
    a("# " + "=" * 74)
    a("#  CLEANER — УСЛОВИЯ РАБОТЫ")
    a("#")
    a("#  Как менять: исправьте значение справа от знака «=», сохраните файл и")
    a("#  запустите программу заново (или нажмите ф внутри программы).")
    a("#  Файл создаётся программой сам, если его нет.")
    a("#  Строки с # в начале — комментарии. Значения: ВКЛ или ВЫКЛ.")
    a("#  Если удалить строку — действует значение по умолчанию.")
    a("# " + "=" * 74)
    a("")
    a("# --- Что чистить ---")
    a("")
    a("# Чистить кэши шейдеров NVIDIA / AMD / Intel / D3D?")
    a(f"чистка_шейдеров = {_fmt_onoff(S['shader'])}")
    a("")
    a("# Чистить папку .cache в профиле пользователя?")
    a(f"чистка_dot_cache = {_fmt_onoff(S['dot'])}")
    a("")
    a("# --- Где искать папки Cache (команда п в программе) ---")
    a("")
    a("# Искать ли папки Cache внутри этих папок профиля:")
    a(f"поиск_в_Documents = {_fmt_onoff(S['s_docs'])}")
    a(f"поиск_в_Local = {_fmt_onoff(S['s_local'])}")
    a(f"поиск_в_LocalLow = {_fmt_onoff(S['s_locallow'])}")
    a(f"поиск_в_Roaming = {_fmt_onoff(S['s_roaming'])}")
    a("")
    a("# Где искать вообще. ПУСТО = все локальные диски (C:, D: и т.д.).")
    a("# Чтобы искать только в конкретных местах, впишите их через точку с запятой:")
    a(r"#     где_искать = D:\Games ; E:\Work")
    a("где_искать = " + " ; ".join(str(r) for r in CACHE_SEARCH_ROOTS))
    a("")
    a("# Какие имена папок считать кэшем (через запятую, регистр не важен).")
    a("# Например, можно дописать: cache, .cache, GPUCache")
    a("имена_кэша = " + ", ".join(sorted(CACHE_FOLDER_NAMES)))
    a("")
    a("# Папки, в которые поиск не заходит (через запятую). Там «cache» часто —")
    a("# часть кода программ, и удалять её нельзя.")
    a("не_заходить = " + ", ".join(sorted(CACHE_SEARCH_SKIP)))
    a("")
    a("# --- Свои пути ---")
    a("")
    a("# На сколько уровней вглубь чистить свои пути и CUSTOM_PATHS.")
    a("# 1 = как обычные пути: удаляется всё, что лежит прямо в папке;")
    a("# 2 = заходит в каждую подпапку и чистит то, что внутри неё (подпапки остаются).")
    a(f"глубина_своих_путей = {config.CUSTOM_SCAN_DEPTH}")
    a("")
    a("# Сами свои пути и чёрный список лежат в отдельных файлах рядом:")
    a("#     Cleaner_свои_пути.txt  и  Cleaner_чёрный_список.txt")
    a("")
    return "\n".join(L)


HEADER_CUSTOM = r"""# ==========================================================================
#  CLEANER — СВОИ ПУТИ
#
#  Здесь ваши папки для очистки. Меняйте файл в любом текстовом редакторе,
#  сохраняйте и запускайте программу заново (или нажмите ф в программе).
#
#  Формат строки:     тип | путь
#      обычный — путь чистится всегда
#      вкл     — путь с условием, сейчас ВКЛЮЧЁН
#      выкл    — путь с условием, сейчас ВЫКЛЮЧЕН
#  Можно написать просто путь без типа — он будет обычным.
#  Работают переменные Windows (%LOCALAPPDATA%) и звёздочка (D:\Temp\*).
#  Удаляется СОДЕРЖИМОЕ папки, сама папка остаётся.
#
#  Комментарии (строки с #) пишите здесь, вверху файла: ниже список
#  программа переписывает сама, когда вы меняете пути внутри программы.
#
#  Примеры (уберите # в начале строки, чтобы включить):
#  обычный | D:\Games\SomeGame\Cache
#  вкл     | %LOCALAPPDATA%\MyApp\Cache
#  выкл    | D:\Temp\*
# =========================================================================="""


HEADER_BLACKLIST = r"""# ==========================================================================
#  CLEANER — ЧЁРНЫЙ СПИСОК
#
#  Путь из этого списка и всё, что лежит внутри него, программа не ищет,
#  не показывает и не удаляет НИКОГДА — даже если этот путь есть в основном
#  списке, в своих путях или найден поиском Cache. Чёрный список главнее всего.
#
#  Формат: один путь на строку (папка или файл). Кавычки не нужны.
#  Меняйте файл в любом редакторе, сохраняйте и запускайте программу заново
#  (или нажмите ф в программе).
#
#  Комментарии (строки с #) пишите здесь, вверху файла: ниже список
#  программа переписывает сама, когда вы меняете его внутри программы.
#
#  Пример (уберите # в начале строки, чтобы включить):
#  D:\Games\Важные сохранения
# =========================================================================="""


def _custom_lines() -> list:
    out = []
    for c in CUSTOM_RUNTIME:
        kind = "обычный" if c["mode"] == "normal" else ("вкл" if c["enabled"] else "выкл")
        out.append(f"{kind:<8}| {c['path']}")
    return out


def _save_list_file(path: str, default_header: str, entry_lines: list):
    """Переписывает список, сохраняя верхний блок комментариев файла."""
    header = default_header
    try:
        if os.path.exists(path):
            keep = []
            for ln in _read_text(path).splitlines():
                if ln.strip() == "" or ln.lstrip().startswith("#"):
                    keep.append(ln)
                else:
                    break
            if any(x.strip() for x in keep):
                header = "\n".join(keep).rstrip()
    except OSError:
        pass
    text = header.rstrip() + "\n\n" + "\n".join(entry_lines) + ("\n" if entry_lines else "")
    _write_text(path, text)


def _save_conditions():
    """Меняет только значения ВКЛ/ВЫКЛ в файле условий, остальной текст не трогает."""
    if not os.path.exists(FILE_CONDITIONS):
        _write_text(FILE_CONDITIONS, _conditions_text())
        return
    try:
        lines = _read_text(FILE_CONDITIONS).splitlines()
    except OSError:
        return
    done = set()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key = s.split("=", 1)[0].strip().lower().replace(" ", "_")
        for k, sk in _COND_KEYS:
            if key == k:
                lines[i] = f"{k} = {_fmt_onoff(SETTINGS[sk])}"
                done.add(k)
    for k, sk in _COND_KEYS:
        if k not in done:
            lines.append(f"{k} = {_fmt_onoff(SETTINGS[sk])}")
    _write_text(FILE_CONDITIONS, "\n".join(lines) + "\n")


def save_settings():
    """Записывает текущие условия в файлы рядом с программой."""
    _save_conditions()
    _save_list_file(FILE_CUSTOM, HEADER_CUSTOM, _custom_lines())
    _save_list_file(FILE_BLACKLIST, HEADER_BLACKLIST, list(BLACKLIST))


def ensure_files():
    """Создаёт недостающие файлы рядом с программой (существующие не трогает)."""
    if not os.path.exists(FILE_CONDITIONS):
        _write_text(FILE_CONDITIONS, _conditions_text())
    if not os.path.exists(FILE_CUSTOM):
        _save_list_file(FILE_CUSTOM, HEADER_CUSTOM, _custom_lines())
    if not os.path.exists(FILE_BLACKLIST):
        _save_list_file(FILE_BLACKLIST, HEADER_BLACKLIST, list(BLACKLIST))


def _load_legacy_json():
    """Подхватывает настройки из старого cleaner_settings.json (один раз)."""
    try:
        import json
        with open(LEGACY_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    for k in SETTINGS:
        if isinstance(data.get(k), bool):
            SETTINGS[k] = data[k]
    for c in data.get("custom", []):
        if isinstance(c, dict) and isinstance(c.get("path"), str) and c["path"].strip():
            CUSTOM_RUNTIME.append({"path": c["path"].strip(),
                                   "mode": "toggle" if c.get("mode") == "toggle" else "normal",
                                   "enabled": bool(c.get("enabled", True))})
    for p in data.get("blacklist", []):
        if isinstance(p, str) and p.strip():
            BLACKLIST.append(p.strip())


def load_settings():
    """Читает условия из файлов рядом с программой."""
    CUSTOM_RUNTIME.clear()
    BLACKLIST.clear()

    if not any(os.path.exists(p) for p in (FILE_CONDITIONS, FILE_CUSTOM, FILE_BLACKLIST)):
        _load_legacy_json()
        return

    # ---- Cleaner_условия.txt ----
    if os.path.exists(FILE_CONDITIONS):
        name = os.path.basename(FILE_CONDITIONS)
        key_map = dict(_COND_KEYS)
        try:
            lines = _read_text(FILE_CONDITIONS).splitlines()
        except OSError as e:
            lines = []
            _warn(f"Не удалось прочитать {name}: {e}")
        for n, raw in enumerate(lines, 1):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if "=" not in s:
                _warn(f"{name}, строка {n}: нет знака «=» — пропущена: {s}")
                continue
            k, v = s.split("=", 1)
            k = k.strip().lower().replace(" ", "_")
            v = v.strip()
            if k in key_map:
                val = _parse_onoff(v)
                if val is None:
                    _warn(f"{name}, строка {n}: «{v}» — нужно ВКЛ или ВЫКЛ")
                else:
                    SETTINGS[key_map[k]] = val
            elif k == "где_искать":
                CACHE_SEARCH_ROOTS[:] = [x.strip().strip('"') for x in v.split(";")
                                      if x.strip().strip('"')]
            elif k == "имена_кэша":
                names = {x.strip() for x in v.split(",") if x.strip()}
                if names:
                    CACHE_FOLDER_NAMES.clear()
                    CACHE_FOLDER_NAMES.update(names)
                else:
                    _warn(f"{name}, строка {n}: список имён пуст — оставлено «cache»")
            elif k == "не_заходить":
                CACHE_SEARCH_SKIP.clear()
                CACHE_SEARCH_SKIP.update(x.strip() for x in v.split(",") if x.strip())
            elif k == "глубина_своих_путей":
                if v.isdigit() and 1 <= int(v) <= 6:
                    config.CUSTOM_SCAN_DEPTH = int(v)
                else:
                    _warn(f"{name}, строка {n}: глубина — число от 1 до 6")
            else:
                _warn(f"{name}, строка {n}: незнакомая настройка «{k}» — пропущена")

    # ---- Cleaner_свои_пути.txt ----
    if os.path.exists(FILE_CUSTOM):
        name = os.path.basename(FILE_CUSTOM)
        try:
            lines = _read_text(FILE_CUSTOM).splitlines()
        except OSError:
            lines = []
        seen = set()
        for n, raw in enumerate(lines, 1):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if "|" in s:
                kind, path = s.split("|", 1)
                kind = kind.strip().lower()
            else:
                kind, path = "обычный", s
            path = path.strip().strip('"')
            if not path:
                continue
            if kind in ("обычный", "обычн", "о", "normal"):
                mode, enabled = "normal", True
            elif kind in _ON_WORDS:
                mode, enabled = "toggle", True
            elif kind in _OFF_WORDS:
                mode, enabled = "toggle", False
            else:
                _warn(f"{name}, строка {n}: тип «{kind}» — нужно обычный, вкл или выкл")
                continue
            if path.lower() in seen:
                continue
            seen.add(path.lower())
            CUSTOM_RUNTIME.append({"path": path, "mode": mode, "enabled": enabled})

    # ---- Cleaner_чёрный_список.txt ----
    if os.path.exists(FILE_BLACKLIST):
        try:
            lines = _read_text(FILE_BLACKLIST).splitlines()
        except OSError:
            lines = []
        for raw in lines:
            s = raw.strip()
            if s and not s.startswith("#"):
                p = s.strip('"')
                if p and p not in BLACKLIST:
                    BLACKLIST.append(p)


load_settings()


ensure_files()


def _runtime_resolved(c) -> list:
    """Путь из «своих путей» -> список реальных путей (звёздочка * разворачивается)."""
    p = os.path.expandvars(c["path"].strip().strip('"'))
    if len(p) > 3:
        p = p.rstrip("\\/")
    if "*" in p or "?" in p:
        return glob.glob(p)
    return [p]


def active_paths():
    """Основной список очистки с учётом включённых групп (шейдеры, .cache)
    и своих путей (обычные — всегда, с условием — только если ВКЛ)."""
    paths = list(PATHS)
    if SETTINGS["shader"]:
        paths += SHADER_PATHS
    if SETTINGS["dot"]:
        paths += DOT_CACHE_PATHS
    for c in CUSTOM_RUNTIME:
        if c["mode"] == "normal" or c["enabled"]:
            paths += _runtime_resolved(c)
    return list(dict.fromkeys(paths))


def all_known_paths():
    """Все известные программе пути (и включённые, и выключенные группы):
    поиск Cache их не дублирует и не лезет внутрь выключенных."""
    paths = list(PATHS) + SHADER_PATHS + DOT_CACHE_PATHS
    for c in CUSTOM_RUNTIME:
        paths += _runtime_resolved(c)
    return list(dict.fromkeys(paths))


def custom_norms_all() -> set:
    """Пути, которые сканируются «вглубь» (CUSTOM_SCAN_DEPTH): CUSTOM_PATHS и
    свои пути из программы."""
    s = {_norm(p) for p in CUSTOM_RESOLVED}
    for c in CUSTOM_RUNTIME:
        s.update(_norm(p) for p in _runtime_resolved(c))
    return s


def search_skip_dirs():
    """Папки, где поиск Cache выключен: список (норм. путь, путь)."""
    return [(_norm(path), path) for key, _, path in SETTING_OPTIONS
            if path and not SETTINGS[key]]


# ============================================================================
# MODULE: safety
# ============================================================================
def reload_all_files():
    """Перечитывает файлы условий (если вы правили их, пока программа открыта)."""
    load_settings()
    refresh_blacklist()


# Эти значения не меняются за время работы, а is_system_forbidden вызывается
# для каждой папки при поиске по дискам (сотни тысяч раз). Раньше на КАЖДЫЙ
# вызов заново нормализовались все пути-константы — это была основная трата
# времени. Теперь они считаются один раз при импорте.
_FORBIDDEN_NORMS = frozenset(_norm(r) for r in FORBIDDEN_ROOTS)
_PROTECTED_PREFIXES = tuple(
    (_norm(r), _norm(r) + os.sep)
    for r in (r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)")
)
_USERS_PREFIX = _norm(r"C:\Users") + os.sep
_PROFILE_NORM = _norm(USER_PROFILE)
_PROFILE_PREFIX = _PROFILE_NORM + os.sep


def is_system_forbidden(path: str) -> bool:
    """Системные и чужие места: чистить нельзя никогда."""
    p = _norm(path)
    if p in _FORBIDDEN_NORMS:
        return True
    for root, prefix in _PROTECTED_PREFIXES:
        if p == root or p.startswith(prefix):
            return True
    drive, tail = os.path.splitdrive(p)
    if tail in ("\\", "/", ""):
        return True
    if p.startswith(_USERS_PREFIX):
        if not (p == _PROFILE_NORM or p.startswith(_PROFILE_PREFIX)):
            return True
    return False


# ----------------------------------------------------------------------------
#  ЧЁРНЫЙ СПИСОК (приоритет над всем)
#    • is_blacklisted(p)      — путь сам в чёрном списке или лежит внутри него;
#    • contains_blacklisted(p) — внутри пути (глубже) лежит заблокированный путь.
#  is_forbidden() = чёрный список ИЛИ системная защита, поэтому все места, где
#  программа проверяет is_forbidden (основное сканирование, поиск Cache,
#  группы, поиск по дискам), автоматически уважают чёрный список.
#  Если заблокирован путь ВНУТРИ очищаемой папки, то объекты, содержащие его,
#  разбираются на части (collect_items), и удаляется только то, что вне
#  заблокированного. Последний рубеж — проверка прямо перед удалением.
# ----------------------------------------------------------------------------

_BL_NORMS = set()


def refresh_blacklist():
    s = set()
    for p in BLACKLIST:
        p = os.path.expandvars(str(p).strip().strip('"'))
        if p:
            s.add(_norm(p))
    _BL_NORMS.clear()
    _BL_NORMS.update(s)


def is_blacklisted(path: str) -> bool:
    if not _BL_NORMS:
        return False
    n = _norm(path)
    for b in _BL_NORMS:
        if n == b or n.startswith(b.rstrip(os.sep) + os.sep):
            return True
    return False


def contains_blacklisted(path: str) -> bool:
    if not _BL_NORMS:
        return False
    n = _norm(path).rstrip(os.sep) + os.sep
    return any(b.startswith(n) for b in _BL_NORMS)


def is_forbidden(path: str) -> bool:
    return is_blacklisted(path) or is_system_forbidden(path)


refresh_blacklist()


# ============================================================================
# MODULE: scanner
# ============================================================================
def _bl_filter(items):
    """Убирает заблокированные объекты; объект, внутри которого лежит
    заблокированный путь, заменяет его содержимым (рекурсивно)."""
    if not _BL_NORMS:
        return items
    out = []
    for full, size, kind in items:
        if is_blacklisted(full):
            continue
        if kind == "папка" and contains_blacklisted(full):
            if _is_link_or_junction(full):
                continue          # в ссылки не заходим — безопаснее пропустить
            out.extend(collect_items(full) or [])
            continue
        out.append((full, size, kind))
    return out


def dir_size(path: str) -> int:
    """Полный размер папки по единым правилам (см. выше)."""
    total = 0
    stack = [path]
    prog = get_active_progress()
    while stack:
        cur = stack.pop()
        nfiles = 0
        try:
            with os.scandir(_long(cur)) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if not _is_reparse(e):
                                stack.append(os.path.join(cur, e.name))
                        else:
                            total += _entry_size(e)
                            nfiles += 1
                    except OSError:
                        pass
        except OSError:
            pass
        if prog is not None:
            prog.tick(cur, nfiles, 1)
    return total


# Сколько папок первого уровня считать одновременно. Обход диска — это в
# основном ожидание файловой системы (поток не нагружает процессор и отпускает
# GIL), поэтому несколько потоков считают заметно быстрее одного, особенно
# на SSD и когда в списке много крупных папок (Temp, кэши браузеров...).
_SCAN_WORKERS = max(2, min(8, (os.cpu_count() or 2) + 2))


def collect_items(path: str):
    if not os.path.exists(path):
        return None
    if not os.path.isdir(path):
        return []
    try:
        entries = list(os.scandir(_long(path)))
    except OSError:
        return []

    # Шаг 1: быстро (без захода внутрь) раскладываем объекты первого уровня.
    # plan — [путь, размер или None, тип]; None = папку ещё надо посчитать.
    plan = []
    to_measure = []
    for e in entries:
        full = os.path.join(path, e.name)
        try:
            is_dir = e.is_dir(follow_symlinks=False)
            if is_dir and not e.is_symlink():
                if _is_reparse(e):
                    plan.append([full, _entry_size(e), "папка"])
                else:
                    plan.append([full, None, "папка"])
                    to_measure.append(full)
            else:
                plan.append([full, _entry_size(e), "файл"])
        except OSError:
            # Не выбрасываем объект из списка, иначе он и не удалится,
            # и в вес не попадёт.
            plan.append([full, 0, "файл"])

    # Шаг 2: размеры папок считаем параллельно; порядок результатов сохраняется.
    prog = get_active_progress()
    rep = prog is not None and prog.owner == path     # этот корень «владеет» шкалой
    pool = None
    if len(to_measure) > 1:
        pool = ThreadPoolExecutor(max_workers=_SCAN_WORKERS)
        sizes = pool.map(dir_size, to_measure)
    else:
        sizes = map(dir_size, to_measure)             # ленивый: считает по ходу

    items = []
    n_entries = len(plan)
    try:
        for i, (full, size, kind) in enumerate(plan):
            if size is None:
                size = next(sizes)
            items.append((full, size, kind))
            if rep:
                prog.child_progress(i + 1, n_entries)
    finally:
        if pool is not None:
            try:
                pool.shutdown(wait=True, cancel_futures=True)
            except TypeError:                      # Python < 3.9
                pool.shutdown(wait=True)
    return _bl_filter(items)


def collect_items_nested(path: str, depth: int, parents=None):
    """Как collect_items, но заходит в подпапки на depth уровней.

    depth=1 — то же, что collect_items (объекты первого уровня).
    depth=2 — вместо подпапки первого уровня берём её содержимое.
    Ссылки и junction не раскрываем (чтобы не удалить содержимое чужой папки).

    parents — необязательный список: в него добавляются (путь, размер,
    "папка") для каждой папки, ИЗ КОТОРОЙ будет удалено содержимое (сама
    папка остаётся). Нужен только для показа в списке — удаляться не будет.
    """
    top = collect_items(path)
    if top is None:
        return top
    if parents is not None and top:
        parents.append((path, sum(sz for _, sz, _ in top), "папка"))
    if depth <= 1:
        return top
    items = []
    for full, size, kind in top:
        if kind == "папка" and not _is_link_or_junction(full):
            inner = collect_items_nested(full, depth - 1, parents)
            if inner:
                items.extend(inner)
        else:
            items.append((full, size, kind))
    return items


# ============================================================================
# MODULE: tree
# ============================================================================
def build_tree(path: str, keep_depth: int):
    """Строит дерево папки для показа: размеры считаются по всей глубине
    (по тем же правилам, что и dir_size), а сами узлы хранятся только
    на keep_depth уровней вниз."""
    node = {"path": path, "name": os.path.basename(path) or path,
            "size": 0, "dir": True, "children": [], "more": False}
    try:
        entries = list(os.scandir(_long(path)))
    except OSError:
        return node
    total = 0
    for e in entries:
        full = os.path.join(path, e.name)
        try:
            if e.is_dir(follow_symlinks=False) and not _is_reparse(e):
                child = build_tree(full, keep_depth - 1)
            else:
                child = {"path": full, "name": e.name, "size": _entry_size(e),
                         "dir": False, "children": [], "more": False}
        except OSError:
            child = {"path": full, "name": e.name, "size": 0,
                     "dir": False, "children": [], "more": False}
        total += child["size"]
        if keep_depth > 0:
            node["children"].append(child)
        else:
            node["more"] = True
    node["size"] = total
    return node


def tree_lines(root: dict, target_norms: set, root_inside: bool = False):
    """Строки (rich.Text) для показа одной папки в виде дерева.

    Помечает: что УДАЛИТСЯ, что останется (папка, из которой чистится
    содержимое), и что лежит внутри удаляемой папки (серым).
    """
    lines = []

    def tag(is_dir):
        return "[папка ] " if is_dir else "[файл  ] "

    def walk(node, prefix, inside):
        folders = sorted((c for c in node["children"] if c["dir"]),
                         key=lambda c: -c["size"])
        files = sorted((c for c in node["children"] if not c["dir"]),
                       key=lambda c: -c["size"])
        rows = [("node", c) for c in folders[:TREE_MAX_FOLDERS]]
        rows += [("node", c) for c in files[:TREE_MAX_FILES]]
        hid_f = folders[TREE_MAX_FOLDERS:]
        hid_x = files[TREE_MAX_FILES:]
        if hid_f:
            rows.append(("sum", f"… ещё папок: {len(hid_f)}, "
                                f"{human_size(sum(c['size'] for c in hid_f))}"))
        if hid_x:
            rows.append(("sum", f"… ещё файлов: {len(hid_x)}, "
                                f"{human_size(sum(c['size'] for c in hid_x))}"))

        for idx, (kind, obj) in enumerate(rows):
            last = idx == len(rows) - 1
            conn = "└─ " if last else "├─ "
            line = Text()
            line.append(prefix + conn, style="dim")
            if kind == "sum":
                line.append(obj, style="dim")
                lines.append(line)
                continue

            c = obj
            is_target = (not inside) and (_norm(c["path"]) in target_norms)
            child_inside = inside or is_target
            grey = inside and not is_target
            style_tag = "dim" if grey else ("magenta" if c["dir"] else "cyan")
            style_size = "dim" if grey else "green"
            line.append(tag(c["dir"]), style=style_tag)
            line.append(f"{human_size(c['size']):>10}", style=style_size)
            line.append(f"  {c['name']}", style="dim" if grey else "")
            if is_target:
                line.append("   ← УДАЛИТСЯ", style="bold red")
            elif c["dir"] and not inside:
                line.append("   (папка останется, внутри чистится)",
                            style="yellow")
            if c["more"]:
                line.append("   [внутри ещё, свёрнуто]", style="dim")
            lines.append(line)
            if c["dir"] and c["children"]:
                walk(c, prefix + ("   " if last else "│  "), child_inside)

    head = Text()
    head.append("\n[папка ] ", style="bold magenta")
    head.append(f"{human_size(root['size']):>10}", style="bold green")
    head.append(f"  {os.path.abspath(root['path'])}", style="bold")
    if root_inside:
        head.append("   (лежит внутри удаляемой папки)", style="dim")
    else:
        head.append("   (папка останется, внутри чистится)", style="yellow")
    lines.append(head)
    walk(root, "  ", root_inside)
    return lines


def _has_target_ancestor(norm_path: str, target_norms: set) -> bool:
    cur = norm_path
    while True:
        parent = os.path.dirname(cur)
        if not parent or parent == cur:
            return False
        if parent in target_norms:
            return True
        cur = parent


# ============================================================================
# MODULE: deleter
# ============================================================================
def delete_item(path: str, is_dir: bool, expected_size: int):
    lp = _long(path)   # длинный префикс: пути > 260 символов считаются, значит и удаляться должны

    # Junction / симлинк на папку: убираем ТОЛЬКО саму ссылку, не заходя внутрь
    # (rmtree на старых Python по junction удалил бы содержимое цели).
    if _is_link_or_junction(path) and os.path.isdir(path):
        try:
            try:
                os.rmdir(lp)          # Windows: так удаляется и junction, и symlink на папку
            except OSError:
                if not os.path.islink(path):
                    raise
                os.unlink(lp)         # не-Windows
            return True, None, expected_size
        except Exception as e:
            if is_locked_error(e):
                return False, "занято", 0
            return False, str(e), 0

    if is_dir:
        failed_paths = set()

        def _retry(function, exc_path):
            try:
                os.chmod(exc_path, stat.S_IWRITE)
                function(exc_path)
                return True
            except Exception:
                return False

        def onexc(function, exc_path, exc):
            if not _retry(function, exc_path):
                failed_paths.add(exc_path)

        try:
            shutil.rmtree(lp, onexc=onexc)
        except TypeError:
            def onerror(function, exc_path, excinfo):
                if not _retry(function, exc_path):
                    failed_paths.add(exc_path)
            shutil.rmtree(lp, onerror=onerror)
        except Exception as e:
            if is_locked_error(e):
                return False, "занято", 0
            return False, str(e), 0

        if failed_paths:
            return False, "частично занято", None
        return True, None, expected_size
    else:
        try:
            os.remove(lp)
            return True, None, expected_size
        except PermissionError:
            try:
                os.chmod(lp, stat.S_IWRITE)
                os.remove(lp)
                return True, None, expected_size
            except Exception as e:
                if is_locked_error(e):
                    return False, "занято", 0
                return False, str(e), 0
        except Exception as e:
            if is_locked_error(e):
                return False, "занято", 0
            return False, str(e), 0


def recompute_size(path: str) -> int:
    if not os.path.exists(path):
        return 0
    return dir_size(path)


# ============================================================================
#  УДАЛЕНИЕ СПИСКА ОБЪЕКТОВ И ИТОГОВЫЙ ОТЧЁТ
#  (общие для основной очистки и для поиска папок Cache)
# ============================================================================

def new_stats() -> dict:
    return {"deleted": 0, "partial": 0, "skipped": 0, "errors": 0, "freed": 0}


def delete_items(ui: "Terminal", items, stats: dict = None) -> dict:
    """Удаляет объекты (путь, размер, "папка"/"файл"), печатает ход работы.
    Если передан stats — добавляет результат к нему (для накопления итога)."""
    if stats is None:
        stats = new_stats()

    pr = Progress(ui, "Удаление", log=False)
    n_items = max(1, len(items))

    for i, (p, expected_size, t) in enumerate(items):
        pr.set(i / n_items, p)
        is_dir = (t == "папка")
        # Чёрный список главнее всего: последний рубеж перед удалением.
        if is_blacklisted(p) or contains_blacklisted(p):
            stats["skipped"] += 1
            ui.write(Text(f"  → Пропущено (чёрный список): {p}", style="yellow"))
            continue
        ok, err, freed = delete_item(p, is_dir=is_dir, expected_size=expected_size)

        if ok:
            stats["deleted"] += 1
            stats["freed"] += freed
            ui.write(Text(f"  ✓ Удалено ({human_size(expected_size)}): {p}",
                          style="green"))
        elif err == "занято":
            stats["skipped"] += 1
            ui.write(Text(f"  → Пропущено (занято): {p}", style="yellow"))
        elif err == "частично занято":
            stats["partial"] += 1
            remaining = recompute_size(p)
            freed_here = max(expected_size - remaining, 0)
            stats["freed"] += freed_here
            ui.write(Text(
                f"  ~ Удалено частично ({human_size(freed_here)} из "
                f"{human_size(expected_size)}): {p}",
                style="yellow",
            ))
        else:
            stats["errors"] += 1
            ui.write(Text(f"  ✗ Ошибка: {p} → {err}", style="red"))
    pr.finish()
    return stats


def print_report(ui: "Terminal", stats: dict, title: str = "Готово!"):
    ui.write(Text(" "))
    ui.write(Text("=" * 60, style="bold"))
    ui.write(Text(title, style="bold green"))
    ui.write(Text(f"  Удалено полностью:  {stats['deleted']}"))
    ui.write(Text(f"  Удалено частично:   {stats['partial']} (часть файлов внутри была занята)"))
    ui.write(Text(f"  Пропущено:          {stats['skipped']} (занято процессами)"))
    ui.write(Text(f"  Ошибок:             {stats['errors']}"))
    ui.write(Text(f"  Освобождено места:  {human_size(stats['freed'])}",
                  style="bold green"))
    ui.write(Text("=" * 60, style="bold"))


# ============================================================================
# MODULE: search
# ============================================================================
# ============================================================================
#  ПОИСК ПАПОК «CACHE»
# ----------------------------------------------------------------------------
#  Обходим CACHE_SEARCH_ROOTS и ищем папки, имя которых есть в
#  CACHE_FOLDER_NAMES (без учёта регистра). Правила:
#    • внутрь найденной папки Cache не заходим (вложенные не ищем);
#    • symlink и junction не раскрываем (чтобы не выйти за пределы профиля);
#    • системные места (is_forbidden) пропускаем;
#    • папки, которые уже входят в основной список PATHS (или лежат внутри
#      его папок), пропускаем — они обработаны на первом этапе;
#    • пустые папки не предлагаем — чистить там нечего.
# ============================================================================

def get_search_roots():
    """Где искать: CACHE_SEARCH_ROOTS, а если пусто — все локальные
    (несъёмные) диски Windows."""
    roots = [r for r in CACHE_SEARCH_ROOTS if str(r).strip()]
    if roots:
        return roots
    if os.name == "nt":
        try:
            import ctypes
            mask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if mask & (1 << i):
                    root = chr(65 + i) + ":\\"
                    # 3 = DRIVE_FIXED (обычный жёсткий диск/SSD)
                    if ctypes.windll.kernel32.GetDriveTypeW(root) == 3:
                        roots.append(root)
        except Exception:
            pass
    return roots or [USER_PROFILE]


def _norm_root(root: str) -> str:
    root = os.path.expandvars(str(root).strip().strip('"'))
    if len(root) <= 3 and len(root) >= 2 and root[1] == ":":
        return root[:2] + "\\"          # "C:" -> "C:\" (корень диска)
    return root.rstrip("\\/") or root


def find_cache_folders(roots, known_norms: set, progress=None, skip_norms=None,
                       prog=None):
    """Возвращает (список путей найденных папок Cache, сколько папок просмотрено).
    progress(root) — необязательная функция, вызывается при заходе в новый корень.
    prog — строка проверки (Progress): доля 0..1 и отмена по Esc."""
    names = {n.strip().lower() for n in CACHE_FOLDER_NAMES if n.strip()}
    skip_names = {n.strip().lower() for n in CACHE_SEARCH_SKIP if n.strip()}
    users_norm = _norm(r"C:\Users")
    found = []
    seen = set()
    scanned = 0

    real_roots = []
    for root in roots:
        root = _norm_root(root)
        if root and os.path.isdir(root):
            real_roots.append(root)
    n_roots = max(1, len(real_roots))

    for ri, root in enumerate(real_roots):
        if progress:
            progress(root)
        stack = [(root, ri / n_roots, (ri + 1) / n_roots)]
        while stack:
            if prog is not None and prog.cancelled():
                return found, scanned
            cur, lo, hi = stack.pop()
            scanned += 1
            if prog is not None:
                prog.set(lo, cur)
            at_drive_root = os.path.splitdrive(cur)[1] in ("\\", "/")
            try:
                with os.scandir(_long(cur)) as it:
                    entries = list(it)
            except OSError:
                continue
            subs = []
            nfiles = 0
            for e in entries:
                try:
                    if not e.is_dir(follow_symlinks=False):
                        nfiles += 1
                        continue
                    if _is_reparse(e):
                        continue
                except OSError:
                    continue
                low = e.name.lower()
                full = os.path.join(cur, e.name)

                # C:\Users целиком закрыт (чужие профили), заходим только
                # в профиль текущего пользователя.
                if low == "users" and _norm(full) == users_norm:
                    if os.path.isdir(USER_PROFILE):
                        subs.append(USER_PROFILE)
                    continue
                # Сначала дешёвые проверки по имени (без обращения к путям):
                # на большом диске это отсекает большую часть папок.
                if low in _SEARCH_SKIP_ANYWHERE or low in skip_names:
                    continue
                if at_drive_root and low in _SEARCH_SKIP_AT_ROOT:
                    continue
                n = _norm(full)          # нормализуем путь один раз, а не трижды
                if skip_norms and n in skip_norms:
                    continue          # поиск здесь выключен командой «у»
                if is_forbidden(full):
                    continue

                if low in names:
                    if n not in seen:
                        seen.add(n)
                        if not _is_covered(n, known_norms):
                            found.append(full)
                    continue          # внутрь Cache не заходим
                subs.append(full)
            if prog is not None:
                prog.tick(cur, nfiles, 1)
            # Интервал папки делим поровну между подпапками; кладём в стек
            # в обратном порядке, чтобы первая подпапка обрабатывалась первой.
            width = (hi - lo) / max(1, len(subs))
            for k in range(len(subs) - 1, -1, -1):
                stack.append((subs[k], lo + width * k, lo + width * (k + 1)))
    return found, scanned


def cache_search_collect(ui: "Terminal", known_norms: set):
    """Поиск папок Cache. НИЧЕГО НЕ УДАЛЯЕТ: по каждой найденной папке
    спрашивает, добавить ли её содержимое в список на удаление, и возвращает
    список добавленных объектов. known_norms пополняется принятыми папками,
    чтобы повторный поиск их не предлагал."""
    ui.write(Text(" "))
    ui.write(Text("=" * 60, style="bold cyan"))
    ui.write(Text("  Поиск папок Cache", style="bold cyan"))
    ui.write(Text("=" * 60, style="bold cyan"))
    roots = get_search_roots()
    ui.write(Text("Где ищем (системные и защищённые папки пропускаются):",
                  style="dim"))
    for r in roots:
        ui.write(Text(f"    - {r}", style="dim"))
    ui.write(Text("Идёт поиск, на больших дисках это может занять несколько "
                  "минут...", style="yellow"))

    off_dirs = search_skip_dirs()
    if off_dirs:
        ui.write(Text("Поиск ВЫКЛЮЧЕН в папках (команда у — изменить):",
                      style="yellow"))
        for _, d in off_dirs:
            ui.write(Text(f"    - {d}", style="yellow"))

    with Progress(ui, "Поиск папок Cache", cancellable=True) as pr:
        found, scanned = find_cache_folders(
            roots, known_norms,
            progress=lambda r: ui.write(Text(f"  Просматриваю: {r}", style="dim")),
            skip_norms={n for n, _ in off_dirs}, prog=pr)
        was_cancelled = pr.cancelled()
    if was_cancelled:
        ui.write(Text("Поиск остановлен (Esc): показаны папки, найденные до "
                      "остановки.", style="yellow"))
    ui.write(Text(f"Просмотрено папок: {scanned}, найдено папок Cache: "
                  f"{len(found)}", style="dim"))

    # Считаем содержимое каждой найденной папки; пустые не предлагаем.
    candidates = []
    empty = 0
    with Progress(ui, "Подсчёт размера найденных папок") as pr2:
        for i, p in enumerate(found):
            pr2.set(i / max(1, len(found)), p)
            items = collect_items(p)
            if not items:
                empty += 1
                continue
            candidates.append((p, items, sum(s for _, s, _ in items)))
    candidates.sort(key=lambda c: -c[2])

    if empty:
        ui.write(Text(f"Пустых папок Cache пропущено: {empty}", style="dim"))
    if not candidates:
        ui.write(Text("Новых папок Cache с содержимым не найдено.",
                      style="bold"))
        return []

    total = sum(c[2] for c in candidates)
    ui.write(Text(f"\nНайдено папок Cache с содержимым: {len(candidates)}, "
                  f"общий вес {human_size(total)}", style="bold"))
    for p, _, size in candidates:
        ui.write(Text(f"  {human_size(size):>10}  {p}", style="green"))
    ui.write(Text("\nВнимание: проверяйте, что это именно кэш, а не нужные "
                  "данные программы или проекта. Сейчас ничего не удаляется: "
                  "вы только выбираете, что добавить в список на удаление.",
                  style="yellow"))

    added = []
    accepted = declined = 0
    approve_all = False
    n_total = len(candidates)

    for i, (p, items, size) in enumerate(candidates, 1):
        if not approve_all:
            target_norms = {_norm(it[0]) for it in items}
            node = build_tree(p, 1)
            for line in tree_lines(node, target_norms):
                ui.write(line)
            ans = ui.ask(f"[{i}/{n_total}] > ", hint=[
                Text(f"Папка {i} из {n_total}: {p}", style="bold"),
                Text(f"Содержимое {human_size(size)}. Добавить в список "
                     f"на удаление?", style=""),
                Text("  д — да    н — отклонить (Enter тоже)", style="cyan"),
                Text("  в — да, и всем оставшимся    с — закончить поиск",
                     style="cyan"),
            ]).strip().lower()

            if ans in _QUIT:
                ui.write(Text("Поиск остановлен.", style="yellow"))
                break
            if ans in _ALL:
                approve_all = True
            elif ans not in _YES:
                declined += 1
                ui.write(Text(f"  — Отклонено: {p}", style="yellow"))
                continue
        added.extend(items)
        known_norms.add(_norm(p))
        EXTRA_ROOTS[_norm(p)] = p
        accepted += 1
        ui.write(Text(f"  + Добавлено: {p}", style="green"))

    ui.write(Text(f"\nПоиск завершён: добавлено папок {accepted}, "
                  f"отклонено {declined}.", style="bold"))
    return added


# ============================================================================
# MODULE: items
# ============================================================================
def _is_covered(norm_path: str, known_norms: set) -> bool:
    """True, если путь сам входит в known_norms или лежит внутри такой папки."""
    cur = norm_path
    while True:
        if cur in known_norms:
            return True
        parent = os.path.dirname(cur)
        if not parent or parent == cur:
            return False
        cur = parent


def merge_items(old_items, new_items):
    """Объединяет списки на удаление без дублей: если папка целиком попала в
    новый список, её вложенные объекты из старого списка убираются (и
    наоборот), иначе вес посчитался бы дважды, а удаление шло бы по
    уже удалённому."""
    combined = {}
    for it in list(old_items) + list(new_items):
        combined.setdefault(_norm(it[0]), it)
    norms = set(combined)
    return [it for n, it in combined.items()
            if not _has_target_ancestor(n, norms)]


# Папки Cache, принятые при поиске (норм. путь -> путь): нужны, чтобы итог по
# источникам показывал их отдельными строками.

EXTRA_ROOTS = {}


def print_sources(ui: "Terminal", all_items):
    """Итог по каждому пути: сколько объектов и сколько места освободится.
    Без развёрнутых файлов — только пути и суммы. Сумма == общему размеру."""
    roots = {_norm(p): p for p in all_known_paths()}
    roots.update(EXTRA_ROOTS)
    ordered = sorted(roots, key=len, reverse=True)

    agg = {}
    for path, size, _ in all_items:
        n = _norm(path)
        label = "(прочее)"
        for rn in ordered:
            if n.startswith(rn + os.sep):
                label = roots[rn]
                break
        rec = agg.setdefault(label, [0, 0])
        rec[0] += size
        rec[1] += 1

    ui.write(Text("\nИтого по путям (без развёрнутых файлов):", style="bold"))
    if not agg:
        ui.write(Text("  Список пуст.", style="dim"))
        return
    for label, (sz, cnt) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        ui.write(Text(f"  {human_size(sz):>10}  {cnt:>5} об.  {label}",
                      style="green"))
    total = sum(v[0] for v in agg.values())
    count = sum(v[1] for v in agg.values())
    ui.write(Text(f"  {'-' * 10}", style="dim"))
    ui.write(Text(f"  {human_size(total):>10}  {count:>5} об.  ВСЕГО на удаление",
                  style="bold green"))


def scan_roots(paths, ui=None):
    """Пересканирование списка путей -> список объектов на удаление
    (с чёрным списком, дублями и вложенностью, как при запуске).
    Если передан ui — показывает строку проверки 0–100 %."""
    custom_norms = custom_norms_all()
    items = []
    paths = list(paths)
    n = max(1, len(paths))
    with Progress(ui, "Проверка файлов") as pr:
        for i, path in enumerate(paths):
            pr.set_span(i / n, (i + 1) / n, owner=path)
            if is_forbidden(path):
                continue
            if _norm(path) in custom_norms:
                res = collect_items_nested(path, config.CUSTOM_SCAN_DEPTH)
            else:
                res = collect_items(path)
            if res:
                items.extend(res)
            pr.set((i + 1) / n, path)
    return merge_items([], items)


def rebuild_items(ui: "Terminal", all_items, known_norms: set):
    """Пересчитывает список после изменения своих путей / чёрного списка."""
    ui.write(Text("Пересчитываю список...", style="yellow"))
    for k, v in list(EXTRA_ROOTS.items()):
        if is_forbidden(v):
            del EXTRA_ROOTS[k]
    roots = active_paths() + list(EXTRA_ROOTS.values())
    all_items[:] = scan_roots(roots, ui)
    known_norms.clear()
    known_norms.update(_norm(p) for p in all_known_paths())
    known_norms.update(EXTRA_ROOTS)


def _apply_group(all_items, paths, enabled: bool):
    """Добавляет в список (или убирает из него) объекты группы путей."""
    norms = {_norm(p) for p in paths}
    if not enabled:
        return [it for it in all_items if not _is_covered(_norm(it[0]), norms)]
    new = []
    for p in paths:
        if is_forbidden(p):
            continue
        res = collect_items(p)
        if res:
            new.extend(res)
    return merge_items(all_items, new)


# ============================================================================
# MODULE: menus
# ============================================================================
def _clean_path_input(s: str) -> str:
    s = os.path.expandvars(s.strip().strip('"').strip("'").strip())
    if len(s) == 2 and s[1] == ":":
        return s + "\\"
    return s.rstrip("\\/") if len(s) > 3 else s


def _ask_path(ui: "Terminal", title: str) -> str:
    return _clean_path_input(ui.ask("Путь > ", hint=[
        Text(title, style="bold"),
        Text("  Вставьте полный путь (кавычки не нужны), например:", style="cyan"),
        Text("  D:\\Games\\Cache   или   %LOCALAPPDATA%\\MyApp\\Cache", style="cyan"),
        Text("  Пустой ввод (просто Enter) — отмена", style="yellow"),
    ]))


def print_custom_paths(ui: "Terminal"):
    ui.write(Text(f"Свои пути ({len(CUSTOM_RUNTIME)}):", style="bold"))
    if not CUSTOM_RUNTIME:
        ui.write(Text("  (пока пусто)", style="dim"))
    for i, c in enumerate(CUSTOM_RUNTIME, 1):
        line = Text()
        line.append(f"  {i}  ", style="dim")
        if c["mode"] == "normal":
            line.append("[ОБЫЧНЫЙ]", style="bold cyan")
        elif c["enabled"]:
            line.append("[ ВКЛ  ]", style="bold green")
        else:
            line.append("[ ВЫКЛ ]", style="bold red")
        line.append("  " + c["path"])
        if is_blacklisted(c["path"]):
            line.append("   ← В ЧЁРНОМ СПИСКЕ, не чистится", style="bold yellow")
        elif "*" not in c["path"] and not os.path.isdir(os.path.expandvars(c["path"])):
            line.append("   (папка не найдена)", style="dim")
        ui.write(line)


def custom_menu(ui: "Terminal") -> bool:
    """Свои пути: обычные (чистятся всегда) и с условием (ВКЛ/ВЫКЛ).
    Возвращает True, если что-то изменилось."""
    import re
    changed = False
    while True:
        ui.write(Text(" "))
        print_custom_paths(ui)
        ans = ui.ask("Свои пути > ", hint=[
            Text("СВОИ ПУТИ. Команды:", style="bold"),
            Text("  о — добавить ОБЫЧНЫЙ путь (чистится всегда)", style="cyan"),
            Text("  у — добавить путь С УСЛОВИЕМ (можно включать/выключать)",
                 style="cyan"),
            Text("  номер — переключить ВКЛ/ВЫКЛ у пути с условием", style="cyan"),
            Text("  т номер — сменить тип: обычный ⇄ с условием", style="cyan"),
            Text("  х номер — убрать путь из списка", style="cyan"),
            Text("  Enter — назад", style="yellow"),
        ]).strip().lower()

        if not ans:
            return changed

        m = re.match(r"^([тх])\s*(\d+)$", ans)
        if ans.isdigit() or m:
            idx = int(ans if ans.isdigit() else m.group(2))
            if not (1 <= idx <= len(CUSTOM_RUNTIME)):
                ui.write(Text(f"  Нет пути с номером {idx}.", style="yellow"))
                continue
            c = CUSTOM_RUNTIME[idx - 1]
            if ans.isdigit():
                if c["mode"] != "toggle":
                    ui.write(Text("  Это обычный путь — он чистится всегда. "
                                  f"Чтобы его можно было выключать: т {idx}",
                                  style="yellow"))
                    continue
                c["enabled"] = not c["enabled"]
            elif m.group(1) == "т":
                c["mode"] = "toggle" if c["mode"] == "normal" else "normal"
                if c["mode"] == "toggle":
                    c["enabled"] = True
            else:
                CUSTOM_RUNTIME.pop(idx - 1)
            save_settings()
            changed = True
            continue

        if ans in ("о", "у"):
            title = ("Добавить ОБЫЧНЫЙ путь (чистится всегда):" if ans == "о"
                     else "Добавить путь С УСЛОВИЕМ (ВКЛ/ВЫКЛ):")
            p = _ask_path(ui, title)
            if not p:
                continue
            problem = None
            if not os.path.isabs(p):
                problem = "нужен полный путь (с буквой диска)"
            elif is_blacklisted(p):
                problem = "этот путь в чёрном списке (команда ч)"
            elif "*" not in p and not os.path.isdir(p):
                problem = "папка не найдена"
            elif "*" not in p and is_system_forbidden(p):
                problem = "защищённый системный путь, чистить его нельзя"
            elif _norm(p) in {_norm(c["path"]) for c in CUSTOM_RUNTIME}:
                problem = "такой путь уже есть в списке"
            if problem:
                ui.write(Text(f"  Не добавлено: {problem}.", style="yellow"))
                continue
            CUSTOM_RUNTIME.append({"path": p,
                                   "mode": "normal" if ans == "о" else "toggle",
                                   "enabled": True})
            save_settings()
            changed = True
            ui.write(Text(f"  + Добавлено: {p}", style="green"))
            continue

        ui.write(Text(f"  Не понял «{ans}».", style="yellow"))


def blacklist_menu(ui: "Terminal") -> bool:
    """Чёрный список: заблокированные пути не ищутся и не удаляются никогда."""
    import re
    changed = False
    while True:
        ui.write(Text(" "))
        ui.write(Text(f"Чёрный список ({len(BLACKLIST)}) — приоритет над всем:",
                      style="bold"))
        if not BLACKLIST:
            ui.write(Text("  (пока пусто)", style="dim"))
        for i, p in enumerate(BLACKLIST, 1):
            line = Text()
            line.append(f"  {i}  ", style="dim")
            line.append("[ЗАБЛОКИРОВАН]", style="bold red")
            line.append("  " + p)
            if not os.path.exists(os.path.expandvars(p)):
                line.append("   (сейчас не существует)", style="dim")
            ui.write(line)

        ans = ui.ask("Чёрный список > ", hint=[
            Text("ЧЁРНЫЙ СПИСОК. Заблокированный путь и всё внутри него не "
                 "ищется и не удаляется.", style="bold"),
            Text("  б — заблокировать путь (папку или файл)", style="cyan"),
            Text("  х номер — убрать путь из чёрного списка", style="cyan"),
            Text("  Enter — назад", style="yellow"),
        ]).strip().lower()

        if not ans:
            return changed

        m = re.match(r"^х\s*(\d+)$", ans)
        if m:
            idx = int(m.group(1))
            if not (1 <= idx <= len(BLACKLIST)):
                ui.write(Text(f"  Нет пути с номером {idx}.", style="yellow"))
                continue
            removed = BLACKLIST.pop(idx - 1)
            refresh_blacklist()
            save_settings()
            changed = True
            ui.write(Text(f"  Разблокировано: {removed}", style="green"))
            continue

        if ans == "б":
            p = _ask_path(ui, "Заблокировать путь (папку или файл):")
            if not p:
                continue
            if not os.path.isabs(p):
                ui.write(Text("  Не добавлено: нужен полный путь (с буквой диска).",
                              style="yellow"))
                continue
            if _norm(p) in {_norm(os.path.expandvars(b)) for b in BLACKLIST}:
                ui.write(Text("  Не добавлено: такой путь уже заблокирован.",
                              style="yellow"))
                continue
            BLACKLIST.append(p)
            refresh_blacklist()
            save_settings()
            changed = True
            ui.write(Text(f"  ⛔ Заблокировано: {p}", style="bold red"))
            continue

        ui.write(Text(f"  Не понял «{ans}».", style="yellow"))


def flush_warnings(ui: "Terminal"):
    """Показывает (и очищает) замечания по файлам условий."""
    if not SETTINGS_WARNINGS:
        return
    ui.write(Text("\n[!] Замечания к файлам условий:", style="bold yellow"))
    for w in SETTINGS_WARNINGS:
        ui.write(Text(f"    - {w}", style="yellow"))
    SETTINGS_WARNINGS.clear()


def print_files_info(ui: "Terminal"):
    ui.write(Text("\nУсловия работы записаны в файлах рядом с программой — "
                  "правьте их в Блокноте; новые значения принимаются при "
                  "следующем запуске (или командой ф):", style="dim"))
    for f in (FILE_CONDITIONS, FILE_CUSTOM, FILE_BLACKLIST):
        ui.write(Text(f"    {f}", style="dim"))
    flush_warnings(ui)


def print_conditions(ui: "Terminal"):
    ui.write(Text("Условия (команда у — изменить):", style="bold"))
    for i, (key, title, _) in enumerate(SETTING_OPTIONS, 1):
        on = SETTINGS[key]
        line = Text()
        line.append(f"  {i}  ", style="dim")
        line.append("[ ВКЛ ]" if on else "[ВЫКЛ ]",
                    style="bold green" if on else "bold red")
        line.append("  " + title, style="" if on else "dim")
        ui.write(line)
    for c in CUSTOM_RUNTIME:
        if c["mode"] != "toggle":
            continue
        line = Text()
        line.append("     ", style="dim")
        line.append("[ ВКЛ ]" if c["enabled"] else "[ВЫКЛ ]",
                    style="bold green" if c["enabled"] else "bold red")
        line.append("  Свой путь: " + c["path"],
                    style="" if c["enabled"] else "dim")
        ui.write(line)
    ui.write(Text(f"  Свои пути: {len(CUSTOM_RUNTIME)} (команда м)    "
                  f"Чёрный список: {len(BLACKLIST)} (команда ч)", style="dim"))


def settings_menu(ui: "Terminal"):
    """Меню условий: номер переключает ВКЛ/ВЫКЛ, Enter — назад."""
    while True:
        ui.write(Text(" "))
        print_conditions(ui)
        ans = ui.ask("Номер > ", hint=[
            Text("УСЛОВИЯ: введите номер, чтобы переключить ВКЛ/ВЫКЛ.",
                 style="bold"),
            Text("  Можно несколько через пробел, например:  1 3 4",
                 style="cyan"),
            Text("  Пустой ввод (просто Enter) — назад", style="yellow"),
        ]).strip()
        if not ans:
            return
        changed = False
        for tok in ans.replace(",", " ").split():
            if tok.isdigit() and 1 <= int(tok) <= len(SETTING_OPTIONS):
                key = SETTING_OPTIONS[int(tok) - 1][0]
                SETTINGS[key] = not SETTINGS[key]
                changed = True
            else:
                ui.write(Text(f"  Не понял: {tok}", style="yellow"))
        if changed:
            save_settings()


# ============================================================================
# MODULE: speedtest
# ============================================================================
def speed_test(ui: "Terminal"):
    """Тест скорости: обходит папки и считает файлы, ИГНОРИРУЯ чёрный список.
    Только чтение: ничего не удаляется и не меняется. Нужен для проверки
    скорости обхода. Результат дописывается в Cleaner_тест_скорости.txt."""
    ans = ui.ask("Область > ", hint=[
        Text("ТЕСТ СКОРОСТИ — только чтение, НИЧЕГО не удаляется.", style="bold"),
        Text(f"Чёрный список игнорируется (путей в нём: {len(BLACKLIST)}) — "
             f"тест нужен только для проверки скорости.", style="yellow"),
        Text("  1 — пути основного списка очистки (быстро)", style="cyan"),
        Text("  2 — все локальные диски, любые файлы (может быть долго)",
             style="cyan"),
        Text("  Enter — отмена.  Во время теста Esc — остановить.", style="yellow"),
    ]).strip()

    if ans == "1":
        roots = [p for p in active_paths() if os.path.isdir(p)]
        scope = "пути основного списка очистки"
    elif ans == "2":
        roots = get_search_roots()
        scope = "все локальные диски: " + ", ".join(str(r) for r in roots)
    else:
        ui.write(Text("Тест отменён.", style="yellow"))
        return

    ui.write(Text(f"\nТЕСТ СКОРОСТИ: {scope}", style="bold cyan"))
    ui.write(Text("Только чтение. Чёрный список игнорируется.", style="dim"))

    names = {n.strip().lower() for n in CACHE_FOLDER_NAMES if n.strip()}
    total_bytes = errors = links = cache_dirs = 0
    t0 = time.perf_counter()

    real_roots = []
    for r in roots:
        r = _norm_root(r)
        if r and os.path.isdir(r):
            real_roots.append(r)
    n_roots = max(1, len(real_roots))

    with Progress(ui, "Тест скорости", cancellable=True, log=False) as pr:
        for ri, root in enumerate(real_roots):
            stack = [(root, ri / n_roots, (ri + 1) / n_roots)]
            while stack:
                if pr.cancelled():
                    break
                cur, lo, hi = stack.pop()
                pr.set(lo, cur)
                try:
                    with os.scandir(_long(cur)) as it:
                        entries = list(it)
                except OSError:
                    errors += 1
                    continue
                subs = []
                nfiles = 0
                for e in entries:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if _is_reparse(e):
                                links += 1
                                continue
                            subs.append(os.path.join(cur, e.name))
                            if e.name.lower() in names:
                                cache_dirs += 1
                        else:
                            total_bytes += _entry_size(e)
                            nfiles += 1
                    except OSError:
                        errors += 1
                pr.tick(cur, nfiles, 1)
                width = (hi - lo) / max(1, len(subs))
                for k in range(len(subs) - 1, -1, -1):
                    stack.append((subs[k], lo + width * k, lo + width * (k + 1)))
            if pr.cancelled():
                break
        was_cancelled = pr.cancelled()

    sec = max(time.perf_counter() - t0, 1e-9)
    dirs, files = pr.dirs, pr.files
    lines = [
        ("Остановлен пользователем (Esc)" if was_cancelled else "Тест завершён",
         "bold yellow" if was_cancelled else "bold green"),
        (f"  Время:        {sec:.2f} с", ""),
        (f"  Папок:        {_fmt_n(dirs)}   ({_fmt_n(int(dirs / sec))} в секунду)", ""),
        (f"  Файлов:       {_fmt_n(files)}   ({_fmt_n(int(files / sec))} в секунду)", ""),
        (f"  Общий размер: {human_size(total_bytes)}", ""),
        (f"  Недоступно: {_fmt_n(errors)},  ссылок пропущено: {_fmt_n(links)},  "
         f"папок Cache: {_fmt_n(cache_dirs)}", "dim"),
    ]
    ui.write(Text(" "))
    ui.write(Text("=" * 60, style="bold"))
    for txt, style in lines:
        ui.write(Text(txt, style=style))
    ui.write(Text("=" * 60, style="bold"))

    report = [f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===",
              f"Область: {scope}",
              "Чёрный список: игнорировался (тест только для скорости)"]
    report += [txt.strip() for txt, _ in lines]
    report.append("")
    _append_text(FILE_SPEEDTEST, "\n".join(report) + "\n")
    ui.write(Text(f"Результат дописан в файл: {FILE_SPEEDTEST}", style="dim"))
    flush_warnings(ui)


# ============================================================================
# MODULE: workflow
# ============================================================================
def confirm_loop(ui: "Terminal", all_items, known_norms: set):
    """Вопрос перед удалением с командами:
         д — удалить всё из списка;
         п — найти все папки Cache и выбрать, какие добавить в список;
         у — условия: включить/выключить чистку шейдеров, .cache и поиск
             в Documents / Local / LocalLow / Roaming;
         всё остальное — отмена.
       После п и у вопрос задаётся снова, уже с новым итогом."""
    while True:
        total_size = sum(s for _, s, _ in all_items)
        flush_warnings(ui)
        ui.write(Text(" "))
        ui.write(Text("=" * 60, style="bold"))
        print_conditions(ui)
        ui.write(Text("-" * 60, style="dim"))
        ui.write(Text(f"В списке на удаление объектов: {len(all_items)}"))
        ui.write(Text(f"Общий размер: {human_size(total_size)}",
                      style="bold green"))
        ui.write(Text("=" * 60, style="bold"))

        answer = ui.ask("Команда > ", hint=[
            Text("Введите команду и нажмите Enter:", style="bold"),
            Text(f"  д — удалить всё из списка "
                 f"({len(all_items)} объектов, {human_size(total_size)})",
                 style="bold green"),
            Text("  с — показать пути и итог по каждому (без файлов)",
                 style="cyan"),
            Text("  п — найти все папки Cache на дисках", style="cyan"),
            Text("  у — условия: включить / выключить", style="cyan"),
            Text("  м — свои пути (обычные и с условием ВКЛ/ВЫКЛ)", style="cyan"),
            Text("  ч — чёрный список путей (главнее всего)", style="cyan"),
            Text("  т — тест скорости (только чтение, чёрный список игнорируется)",
                 style="cyan"),
            Text("  ф — перечитать файлы условий (если правили их вручную)",
                 style="cyan"),
            Text("  н — отмена", style="yellow"),
        ]).strip().lower()

        if answer in _CONDITIONS:
            before = (SETTINGS["shader"], SETTINGS["dot"])
            settings_menu(ui)
            if SETTINGS["shader"] != before[0]:
                all_items[:] = _apply_group(all_items, SHADER_PATHS,
                                            SETTINGS["shader"])
            if SETTINGS["dot"] != before[1]:
                all_items[:] = _apply_group(all_items, DOT_CACHE_PATHS,
                                            SETTINGS["dot"])
            continue

        if answer in _SPEED:
            speed_test(ui)
            continue

        if answer in _RELOAD:
            reload_all_files()
            ui.write(Text("Файлы условий перечитаны.", style="green"))
            flush_warnings(ui)
            rebuild_items(ui, all_items, known_norms)
            continue

        if answer in _CUSTOMMENU:
            if custom_menu(ui):
                rebuild_items(ui, all_items, known_norms)
            continue

        if answer in _BLMENU:
            if blacklist_menu(ui):
                rebuild_items(ui, all_items, known_norms)
            continue

        if answer in _SOURCES:
            print_sources(ui, all_items)
            continue

        if answer in _SEARCH:
            added = cache_search_collect(ui, known_norms)
            if added:
                all_items[:] = merge_items(all_items, added)
            continue

        if answer in _YES:
            if not all_items:
                ui.write(Text("Список пуст — удалять нечего.", style="bold"))
                return
            stats = delete_items(ui, all_items)
            print_report(ui, stats)
            return

        if answer in ("", "н", "нет", "n", "no"):
            ui.write(Text("Отменено.", style="yellow"))
            return

        ui.write(Text(f"Не понял команду «{answer}». Допустимо: д, с, п, у, м, ч, т, ф, н.",
                      style="yellow"))


def main_cleanup(ui: Terminal):
    """Основная очистка по списку PATHS (этап 1)."""
    ui.write(Text("=" * 60, style="bold cyan"))
    ui.write(Text("  Очистка содержимого папок (занятые файлы пропускаются)",
                  style="bold cyan"))
    ui.write(Text("=" * 60, style="bold cyan"))
    ui.write(Text("Подсказки: колесо мыши — прокрутка, ползунок справа — "
                  "перетаскивание, средняя кнопка (зажать) — быстрая прокрутка "
                  "(вверх/вниз от центра окна). Окно можно тянуть за угол — "
                  "текст переносится автоматически.", style="dim"))
    print_files_info(ui)
    ui.write(Text("Сканирование папок, подождите...", style="yellow"))

    all_items = []
    missing = []
    blocked = []
    bl_blocked = []
    scanned_roots = []
    custom_norms = custom_norms_all()

    roots_to_scan = active_paths()
    n_roots = max(1, len(roots_to_scan))
    with Progress(ui, "Проверка файлов") as pr:
        for idx, path in enumerate(roots_to_scan):
            pr.set_span(idx / n_roots, (idx + 1) / n_roots, owner=path)
            if is_blacklisted(path):
                bl_blocked.append(path)
                continue
            if is_system_forbidden(path):
                blocked.append(path)
                continue
            if _norm(path) in custom_norms:
                result = collect_items_nested(path, config.CUSTOM_SCAN_DEPTH)
            else:
                result = collect_items(path)
            if result is None:
                missing.append(path)
                continue
            if result:
                scanned_roots.append(path)
            all_items.extend(result)
            pr.set((idx + 1) / n_roots, path)

    # Убираем дубли и объекты, чьи родительские папки уже в списке
    # (иначе один и тот же вес посчитался бы дважды).
    _seen = set()
    _uniq = []
    for it in all_items:
        n = _norm(it[0])
        if n not in _seen:
            _seen.add(n)
            _uniq.append((n, it))

    def _parent_in_list(n: str) -> bool:
        cur = n
        while True:
            parent = os.path.dirname(cur)
            if not parent or parent == cur:
                return False
            if parent in _seen:
                return True
            cur = parent

    all_items = [it for n, it in _uniq if not _parent_in_list(n)]

    if bl_blocked:
        ui.write(Text("\n[!] В ЧЁРНОМ СПИСКЕ (пропущены, команда ч — изменить):",
                      style="bold yellow"))
        for p in bl_blocked:
            ui.write(Text(f"    - {p}", style="yellow"))

    if blocked:
        ui.write(Text("\n[!] Заблокированы (системные корни, удаление запрещено):",
                      style="bold yellow"))
        for p in blocked:
            ui.write(Text(f"    - {p}", style="yellow"))

    if missing:
        ui.write(Text("\n[!] Не найдены следующие пути (пропущены):",
                      style="dim"))
        for p in missing:
            ui.write(Text(f"    - {p}", style="dim"))

    known_norms = {_norm(p) for p in all_known_paths()}

    if not all_items:
        ui.write(Text("\nПо основному списку удалять нечего.", style="bold"))
        confirm_loop(ui, all_items, known_norms)
        return

    total_size = sum(s for _, s, _ in all_items)

    # Дерево: основные папки (самые тяжёлые сверху), внутри каждой —
    # сначала папки, потом файлы. Красным помечено то, что реально удалится.
    ui.write(Text("\nСписок того, что будет удалено:", style="bold"))
    ui.write(Text("  Основные папки раскрыты: внутри каждой сначала подпапки "
                  "(с весом), потом файлы. Метка «← УДАЛИТСЯ» — то, что будет "
                  "удалено; серое — лежит внутри удаляемой папки.",
                  style="dim"))
    ui.write(Text("Строю дерево папок, подождите...", style="yellow"))

    target_norms = {_norm(it[0]) for it in all_items}
    custom_roots = [p for p in scanned_roots if _norm(p) in custom_norms]
    other_roots = [p for p in scanned_roots if _norm(p) not in custom_norms]

    # Сначала ВАШИ папки (из CUSTOM_PATHS) — в том порядке, как вы их вписали,
    # потом остальные, самые тяжёлые сверху.
    groups = []
    all_tree_roots = custom_roots + other_roots
    with Progress(ui, "Построение дерева папок") as pr3:
        done_roots = [0]

        def _tree(p):
            pr3.set(done_roots[0] / max(1, len(all_tree_roots)), p)
            node = build_tree(p, TREE_DEPTH)
            done_roots[0] += 1
            return node

        if custom_roots:
            groups.append(("ВАШИ ПАПКИ (CUSTOM_PATHS и свои пути)",
                           [_tree(p) for p in custom_roots]))
        if other_roots:
            trees = [_tree(p) for p in other_roots]
            trees.sort(key=lambda n: -n["size"])
            groups.append(("ОСНОВНЫЕ ПАПКИ", trees))

    for title, trees in groups:
        ui.write(Text(f"\n{'#' * 60}", style="bold cyan"))
        ui.write(Text(f"  {title}: {len(trees)} шт.", style="bold cyan"))
        ui.write(Text("#" * 60, style="bold cyan"))
        for node in trees:
            inside = _has_target_ancestor(_norm(node["path"]), target_norms)
            for line in tree_lines(node, target_norms, inside):
                ui.write(line)

    print_sources(ui, all_items)

    confirm_loop(ui, all_items, known_norms)


def cleaner_worker(ui: Terminal):
    """Весь сценарий. Поиск Cache, условия и итог по путям — команды на
    вопросе об удалении (см. confirm_loop)."""
    main_cleanup(ui)
    ui.ask("Нажмите Enter, чтобы закрыть окно...")


# ============================================================================
# MODULE: terminal
# ============================================================================
def _plural_lines(n: int) -> str:
    """1 строка, 2 строки, 5 строк."""
    if n % 10 == 1 and n % 100 != 11:
        return "строка"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "строки"
    return "строк"


# ============================================================================
#  TERMINAL — окно Pygame, прикидывающееся терминалом
# ============================================================================

class Terminal:
    # ----- Цвета и размеры сцены -----
    BG = (12, 12, 12)
    FG = (222, 222, 222)

    # Ползунок прокрутки справа
    SCROLLBAR_W = 14
    SCROLLBAR_MIN_THUMB = 30
    SCROLLBAR_TRACK_COLOR = (26, 26, 26)
    SCROLLBAR_THUMB_COLOR = (85, 85, 85)
    SCROLLBAR_THUMB_ACTIVE = (150, 150, 150)

    # Сколько отрисованных строк держать в памяти. Одна строка — это целая
    # картинка (~50 КБ), поэтому без лимита кэш рос по мере прокрутки лога
    # и занимал сотни МБ. На экране помещается ~40 строк, 400 с запасом.
    LINE_CACHE_MAX = 400

    # Цвет подсветки выделенного текста.
    SELECTION_COLOR = (38, 79, 120)

    # Строка проверки (прогресс 0–100 %).
    PROG_BG = (18, 24, 30)
    PROG_TRACK = (45, 52, 60)
    PROG_FILL = (46, 160, 67)
    PROG_BORDER = (110, 120, 130)

    # Закреплённая панель подсказки над строкой ввода: что вводить.
    HINT_BG = (22, 28, 36)
    HINT_LINE = (70, 90, 110)
    HINT_MAX_LINES = 12

    def __init__(self, title: str = "Cleaner"):
        pygame.init()
        pygame.display.set_caption(title)

        if os.path.isfile(ICON_PATH):
            try:
                icon = pygame.image.load(ICON_PATH)
                pygame.display.set_icon(icon)
            except Exception:
                pass

        # Окно открывается там и того размера, где было закрыто в прошлый раз.
        x, y, w, h, maximized = fit_to_screen(load_window_state())
        if x is not None and y is not None:
            os.environ["SDL_VIDEO_WINDOW_POS"] = f"{x},{y}"
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        os.environ.pop("SDL_VIDEO_WINDOW_POS", None)   # только для первого показа
        if maximized:
            maximize_window()
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()

        # Слежение за положением окна (см. _track_window): последнее «обычное»
        # (не развёрнутое) положение и то, что уже записано в файл.
        self._normal_geom = (x, y, w, h)
        self._maximized = bool(maximized)
        self._saved_state = load_window_state()
        self._geom_changed_at = None
        self._next_geom_poll = 0.0

        # Перерисовка только по необходимости (см. _need_draw).
        self._dirty = True
        self._toast_was_on = False
        self._blink_phase = None
        self._border_focused = None   # None = цвет рамки ещё не задавали

        # Моноширинный шрифт
        self.font = None
        self.font_bold = None
        for name in ("consolas", "dejavusansmono", "couriernew", "liberationmono"):
            path = pygame.font.match_font(name)
            if path:
                self.font = pygame.font.Font(path, 16)
                self.font_bold = pygame.font.Font(path, 16)
                self.font_bold.set_bold(True)
                break
        if self.font is None:
            self.font = pygame.font.Font(None, 18)
            self.font_bold = pygame.font.Font(None, 18)
            self.font_bold.set_bold(True)

        self.line_h = self.font.get_linesize()
        self.char_w = max(1, self.font.size("M")[0])

        # ---- Содержимое терминала ----
        # content — «сырьё»: список элементов, из которых можно заново
        #   собрать lines под любую ширину.
        #   Элемент — ("rich", renderable) или ("plain", text, style_dict).
        # lines — уже отрендеренные строки под ТЕКУЩУЮ ширину окна.
        #   Каждая строка — список сегментов [(текст, стиль), ...].
        self.content = []
        self.lines = []
        self.scroll = 0
        self._line_cache = OrderedDict()

        # Запоминаем ширину в СИМВОЛАХ, под которую сейчас отрендерены lines.
        # Нужно, чтобы при ресайзе перерендерить только при реальном изменении
        # числа символов, а не на каждый пиксель перетаскивания.
        self._rendered_width_chars = self._console_width()

        # ---- Поле ввода ----
        self.input_active = False
        self.input_text = ""
        self.input_prompt = ""
        # Подсказка «что вводить»: закреплена над строкой ввода, пока идёт ввод.
        self.hint_src = []      # исходные Rich-объекты (для пересборки при ресайзе)
        self.hint_surfs = []    # готовые картинки строк панели
        # Строка проверки: None или словарь (см. _drain_queue, "prog").
        self.prog = None
        self.cancel_event = threading.Event()   # Esc во время долгой проверки
        self.cursor_blink_ms = 0

        # ---- Быстрое листание средней кнопкой ----
        self.fast_scroll_active = False
        self.fast_scroll_speed = 6

        # ---- Ползунок ----
        self.scrollbar_dragging = False
        self.scrollbar_drag_offset = 0
        self.scrollbar_hover = False

        # ---- Выделение текста ----
        # Позиции — пары (номер строки в self.lines, номер символа в строке).
        self.sel_anchor = None   # где нажали кнопку мыши
        self.sel_caret = None    # где мышь сейчас
        self.selecting = False   # кнопка мыши зажата

        # ---- Короткая подсказка в углу («Скопировано») ----
        self.toast_text = ""
        self.toast_until = 0

        # ---- Флаги и очереди общения с воркером ----
        self.running = True
        self.out_queue = queue.Queue()
        self.in_queue = queue.Queue()

        # ---- Rich Console ----
        self.console = Console(
            color_system="truecolor",
            no_color=False,
            force_terminal=True,
            width=self._console_width(),
        )

    # ------------------------------------------------------------------
    #  Ширина консоли Rich
    # ------------------------------------------------------------------
    def _console_width(self) -> int:
        """Сколько символов влезает в текущую ширину окна."""
        w, _ = self.screen.get_size()
        usable = w - self.SCROLLBAR_W - 16
        return max(40, usable // self.char_w)

    # ------------------------------------------------------------------
    #  Публичный API, которым пользуется воркер
    # ------------------------------------------------------------------
    def write(self, renderable):
        """Напечатать Rich-объект (Text, Table, Panel, ...)."""
        self.out_queue.put(("render", renderable))

    def write_text(self, text: str, style: str = None):
        self.write(Text(text, style=style) if style else Text(text))

    def ask(self, prompt: str, hint=None) -> str:
        """Запросить ввод. prompt — КОРОТКОЕ приглашение в строке ввода,
        hint — список Rich-объектов (Text), которые закрепляются над строкой
        ввода и объясняют, что можно ввести."""
        self.out_queue.put(("ask", prompt, hint))
        return self.in_queue.get()

    def close(self):
        self.out_queue.put(("close", None))

    # ------------------------------------------------------------------
    #  Rich → список строк с сегментами
    # ------------------------------------------------------------------
    def _render_renderable(self, renderable):
        """
        Прогоняем Rich-объект через рендер и получаем список строк
        с сегментами. Хвостовые пробелы обрезаем, иначе Rich-паддинг
        растянет фон.
        """
        width = self._console_width()
        options = self.console.options.update_width(width)
        try:
            rich_lines = self.console.render_lines(renderable, options)
        except Exception:
            return []

        out = []
        for line in rich_lines:
            segs = []
            for seg in line:
                if not seg.text:
                    continue
                segs.append([seg.text, self._style_to_dict(seg.style)])
            while segs:
                stripped = segs[-1][0].rstrip()
                if stripped:
                    segs[-1][0] = stripped
                    break
                segs.pop()
            out.append([(t, s) for t, s in segs])
        return out

    @staticmethod
    def _style_to_dict(style):
        d = {"fg": None, "bg": None, "bold": False, "dim": False}
        if style is None:
            return d
        if style.bold:
            d["bold"] = True
        if style.dim:
            d["dim"] = True
        if style.color is not None:
            try:
                c = style.color.get_truecolor()
                d["fg"] = (c.red, c.green, c.blue)
            except Exception:
                pass
        if style.bgcolor is not None:
            try:
                c = style.bgcolor.get_truecolor()
                d["bg"] = (c.red, c.green, c.blue)
            except Exception:
                pass
        return d

    # ------------------------------------------------------------------
    #  Пересборка lines под текущую ширину
    # ------------------------------------------------------------------
    def _rebuild_lines(self):
        """
        Заново строит self.lines из self.content под актуальную ширину окна.
        Нужно после ресайза, когда число символов в строке изменилось
        и все переносы надо пересчитать.
        """
        self.lines = []
        self._line_cache.clear()
        self._clear_selection()
        for item in self.content:
            if item[0] == "rich":
                self.lines.extend(self._render_renderable(item[1]))
            else:
                # ("plain", text, style_dict) — эхо введённой строки.
                _, text, style = item
                self.lines.append([(text, style)])
        self._rendered_width_chars = self._console_width()
        if self.hint_src:
            self._set_hint(self.hint_src)

    # ------------------------------------------------------------------
    #  Главный цикл
    # ------------------------------------------------------------------
    def run(self, worker):
        t = threading.Thread(target=_wrap_worker, args=(self, worker), daemon=True)
        t.start()

        try:
            while self.running:
                self._drain_queue()
                self._handle_events()
                self._update_border()
                self._apply_fast_scroll()
                self._apply_selection_autoscroll()
                self._track_window()
                self.cursor_blink_ms = int(time.monotonic() * 1000) % 1000
                if self._need_draw():
                    self._dirty = False
                    self._draw()
                self.clock.tick(30)
        finally:
            self._track_window(final=True)    # положение окна при закрытии
            pygame.quit()

    # ------------------------------------------------------------------
    #  Перерисовка только когда есть что менять
    # ------------------------------------------------------------------
    def _need_draw(self) -> bool:
        """Раньше окно перерисовывалось 30 раз в секунду всегда, даже когда
        ничего не менялось (лишняя нагрузка на процессор). Теперь — только если:
        пришло событие / сообщение от воркера, идёт анимация (шкала, листание,
        выделение), сменилась фаза мигания курсора или пропала подсказка."""
        if self._dirty:
            return True
        if self.prog is not None:
            return True
        if self.fast_scroll_active or self.selecting or self.scrollbar_dragging:
            return True
        toast_on = bool(self.toast_text) and pygame.time.get_ticks() < self.toast_until
        if toast_on != self._toast_was_on:
            self._toast_was_on = toast_on
            return True
        if self.input_active:
            phase = (self.cursor_blink_ms // 500) % 2
            if phase != self._blink_phase:
                self._blink_phase = phase
                return True
        return False

    # ------------------------------------------------------------------
    #  Запоминание положения и размера окна
    # ------------------------------------------------------------------
    def _track_window(self, final: bool = False):
        """Раз в полсекунды смотрит, где окно, и после того как его перестали
        двигать/тянуть (~1 с) записывает в файл. Так положение сохраняется
        и при обычном закрытии, и если программу завершили принудительно."""
        now = time.monotonic()
        if not final and now < self._next_geom_poll:
            return
        self._next_geom_poll = now + 0.5

        geom = get_window_geometry()
        if geom is not None:
            x, y, w, h, maximized, minimized = geom
            if minimized and not final:
                return                      # у свёрнутого окна координаты ложные
            if not minimized:
                self._maximized = maximized
                if not maximized:
                    self._normal_geom = (x, y, w, h)
        else:
            # не Windows: положение неизвестно, помним только размер
            w, h = self.screen.get_size()
            self._normal_geom = (None, None, w, h)

        x, y, w, h = self._normal_geom
        state = {"x": x, "y": y, "w": w, "h": h, "maximized": self._maximized}
        if state == self._saved_state:
            self._geom_changed_at = None
            return
        if final:
            if save_window_state(state):
                self._saved_state = state
            return
        if self._geom_changed_at is None:
            self._geom_changed_at = now
        elif now - self._geom_changed_at >= 1.0:
            if save_window_state(state):
                self._saved_state = state
            self._geom_changed_at = None

    def _update_border(self):
        """Зелёные рамка и заголовок у активного окна, красные — у неактивного."""
        if not (CHANGE_BORDER_COLOR or CHANGE_TITLEBAR_COLOR):
            return
        try:
            focused = bool(pygame.key.get_focused())
        except Exception:
            return
        if focused != self._border_focused:
            self._border_focused = focused
            if CHANGE_BORDER_COLOR:
                set_window_border_color(
                    BORDER_COLOR_ACTIVE if focused else BORDER_COLOR_INACTIVE
                )
            if CHANGE_TITLEBAR_COLOR:
                set_window_titlebar_colors(
                    TITLEBAR_COLOR_ACTIVE if focused else TITLEBAR_COLOR_INACTIVE,
                    TITLEBAR_TEXT_COLOR,
                )

    def _drain_queue(self):
        """Забираем всё, что воркер положил в out_queue, и применяем к UI."""
        while True:
            try:
                msg = self.out_queue.get_nowait()
            except queue.Empty:
                break
            kind = msg[0]
            self._dirty = True
            if kind == "render":
                renderable = msg[1]
                # Запоминаем «сырьё», чтобы уметь пересобрать при ресайзе.
                self.content.append(("rich", renderable))
                self.lines.extend(self._render_renderable(renderable))
                if not self.selecting:
                    self.scroll = 10 ** 9
            elif kind == "ask":
                self.input_active = True
                self.input_text = ""
                self.input_prompt = msg[1]
                self._set_hint(msg[2] if len(msg) > 2 else None)
                if not self.selecting:
                    self.scroll = 10 ** 9
            elif kind == "prog":
                _, title, frac, detail, cancellable = msg
                p = self.prog
                if p is None or p["closing"] or p["title"] != title:
                    p = {"title": title, "target": 0.0, "shown": 0.0,
                         "detail": ("", ""), "t0": time.monotonic(),
                         "closing": False, "close_at": None,
                         "cancellable": cancellable}
                    self.prog = p
                if frac is not None:
                    p["target"] = max(p["target"], min(1.0, frac))
                if detail is not None:
                    p["detail"] = detail
                if not self.selecting:
                    self.scroll = 10 ** 9
            elif kind == "prog_end":
                p = self.prog
                if p is not None:
                    cancelled = len(msg) > 1 and msg[1]
                    if not cancelled:
                        p["target"] = 1.0
                    p["closing"] = True
            elif kind == "close":
                self.running = False
                try:
                    self.in_queue.put_nowait("")
                except queue.Full:
                    pass

    def _visible_text_lines(self) -> int:
        _, h = self.screen.get_size()
        n = max(1, h // self.line_h)
        if self.prog is not None:
            n -= 1
        if self.input_active:
            n -= 1 + len(self.hint_surfs)
        return max(1, n)

    # ------------------------------------------------------------------
    #  Строка проверки с анимацией
    # ------------------------------------------------------------------
    def _update_progress(self):
        """Плавно подтягивает показанное значение к реальному; убирает строку
        через короткую паузу после завершения."""
        p = self.prog
        if p is None:
            return
        now = time.monotonic()
        if p["shown"] < p["target"]:
            step = max((p["target"] - p["shown"]) * 0.18, 0.004)
            p["shown"] = min(p["target"], p["shown"] + step)
        if p["closing"] and p["shown"] >= p["target"] - 1e-6:
            if p["close_at"] is None:
                p["close_at"] = now + (0.9 if p["target"] >= 0.999 else 0.2)
            elif now >= p["close_at"]:
                self.prog = None

    def _fit_text(self, text: str, max_w: int) -> str:
        """Обрезает слева (в пути важен конец) с многоточием, чтобы влезло в max_w."""
        if max_w <= 20 or not text:
            return ""
        if self.font.size(text)[0] <= max_w:
            return text
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.font.size("…" + text[len(text) - mid:])[0] <= max_w:
                lo = mid
            else:
                hi = mid - 1
        return "…" + text[len(text) - lo:] if lo else "…"

    def _draw_progress(self, w: int, y: int):
        p = self.prog
        now = time.monotonic()
        usable = max(200, w - self.SCROLLBAR_W)
        pygame.draw.rect(self.screen, self.PROG_BG, (0, y, usable, self.line_h))

        pct = min(100, int(p["shown"] * 100 + 0.5))
        spin = "|/-\\"[int(now * 10) % 4]
        label = self.font_bold.render(f"{spin} {p['title']}", True, self.FG)
        x = 8
        self.screen.blit(label, (x, y))
        x += label.get_width() + 12

        elapsed = int(now - p["t0"])
        right_txt = f"{pct:3d}%  {elapsed // 60}:{elapsed % 60:02d}"
        if p.get("cancellable"):
            right_txt += "  Esc — остановить"
        right = self.font_bold.render(right_txt, True, self.FG)

        bar_w = max(120, int(usable * 0.28))
        bar_h = max(8, self.line_h - 8)
        bar_y = y + (self.line_h - bar_h) // 2
        pygame.draw.rect(self.screen, self.PROG_TRACK, (x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * p["shown"])
        if fill_w > 0:
            pygame.draw.rect(self.screen, self.PROG_FILL, (x, bar_y, fill_w, bar_h))
            # бегущие светлые полосы — «живая» анимация шкалы
            shimmer = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            off = int(now * 45) % 20
            for sx in range(-bar_h + off, fill_w, 20):
                pygame.draw.polygon(shimmer, (255, 255, 255, 38),
                                    [(sx, bar_h), (sx + 10, bar_h),
                                     (sx + 10 + bar_h, 0), (sx + bar_h, 0)])
            self.screen.blit(shimmer, (x, bar_y))
        pygame.draw.rect(self.screen, self.PROG_BORDER, (x, bar_y, bar_w, bar_h), 1)
        x += bar_w + 10

        self.screen.blit(right, (x, y))
        x += right.get_width() + 14

        counts, path = p.get("detail") or ("", "")
        if counts:
            cs = self.font.render(counts, True, (170, 180, 190))
            self.screen.blit(cs, (x, y))
            x += cs.get_width() + 14
        path = self._fit_text(path, usable - x - 8)
        if path:
            self.screen.blit(self.font.render(path, True, (120, 130, 140)), (x, y))

    # ------------------------------------------------------------------
    #  Закреплённая панель подсказки
    # ------------------------------------------------------------------
    def _segs_to_surface(self, segs):
        """Список сегментов [(текст, стиль), ...] -> картинка одной строки."""
        rendered = []
        total_w = 0
        for text, style in segs:
            if not text:
                continue
            font = self.font_bold if style.get("bold") else self.font
            surf = font.render(text, True, self._effective_fg(style))
            rendered.append(surf)
            total_w += surf.get_width()
        line_surf = pygame.Surface((max(1, total_w), self.line_h), pygame.SRCALPHA)
        x = 0
        for surf in rendered:
            line_surf.blit(surf, (x, 0))
            x += surf.get_width()
        return line_surf

    def _set_hint(self, hint):
        """Запоминает подсказку и готовит её строки под текущую ширину окна."""
        self.hint_src = list(hint) if hint else []
        lines = []
        for r in self.hint_src:
            lines.extend(self._render_renderable(r))
        self.hint_surfs = [self._segs_to_surface(s)
                           for s in lines[:self.HINT_MAX_LINES]]

    # ------------------------------------------------------------------
    #  События мыши и клавиатуры
    # ------------------------------------------------------------------
    def _handle_events(self):
        for e in pygame.event.get():
            self._dirty = True
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                # Пользователь потянул окно. Пересоздаём surface и — что
                # важно — проверяем, не изменилась ли ШИРИНА В СИМВОЛАХ.
                # Если да, все строки надо пересобрать с новыми переносами.
                # В pygame 2 поверхность окна меняет размер сама — повторный
                # set_mode на каждый пиксель перетаскивания (как было раньше)
                # только пересоздавал её и тормозил растягивание окна.
                self.screen = pygame.display.get_surface()
                self._border_focused = None   # после ресайза задать цвет заново
                new_chars = self._console_width()
                if new_chars != self._rendered_width_chars:
                    self._rebuild_lines()
            elif e.type == pygame.MOUSEWHEEL:
                self.scroll -= e.y * 3
                if self.scroll < 0:
                    self.scroll = 0
            elif e.type == pygame.MOUSEMOTION:
                self._on_mouse_motion(e)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(e)
            elif e.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(e)
            elif e.type == pygame.KEYDOWN:
                if e.mod & pygame.KMOD_CTRL and self._handle_ctrl_key(e):
                    continue
                if self.input_active:
                    self._on_input_key(e)
                elif (e.key == pygame.K_ESCAPE and self.prog is not None
                      and self.prog.get("cancellable")):
                    self.cancel_event.set()        # Esc — остановить долгую проверку
                else:
                    self._on_scroll_key(e)

    def _on_mouse_down(self, e):
        if e.button == 2:
            self.fast_scroll_active = True
            return
        if e.button == 1:
            track, thumb, max_scroll, _ = self._scrollbar_geometry()
            if not track.collidepoint(e.pos):
                # Клик по тексту (не по ползунку) — начинаем выделение.
                self._start_selection(e.pos)
                return
            if max_scroll <= 0:
                return
            if thumb.collidepoint(e.pos):
                self.scrollbar_dragging = True
                self.scrollbar_drag_offset = e.pos[1] - thumb.y
            elif track.collidepoint(e.pos):
                self._set_scroll_from_thumb_y(e.pos[1] - thumb.h // 2,
                                              track, thumb, max_scroll)

    def _on_mouse_up(self, e):
        if e.button == 2:
            self.fast_scroll_active = False
        elif e.button == 1:
            self.scrollbar_dragging = False
            if self.selecting:
                self.selecting = False
                if self._selection_range() is None:
                    # Просто клик без протягивания — снимаем выделение.
                    self._clear_selection()

    def _on_mouse_motion(self, e):
        track, thumb, max_scroll, _ = self._scrollbar_geometry()
        self.scrollbar_hover = bool(max_scroll > 0 and thumb.collidepoint(e.pos))
        if self.scrollbar_dragging:
            new_thumb_y = e.pos[1] - self.scrollbar_drag_offset
            self._set_scroll_from_thumb_y(new_thumb_y, track, thumb, max_scroll)
        if self.selecting:
            self.sel_caret = self._hit_test(e.pos)

    def _on_scroll_key(self, e):
        if e.key == pygame.K_UP:
            self.scroll = max(0, self.scroll - 1)
        elif e.key == pygame.K_DOWN:
            self.scroll += 1
        elif e.key == pygame.K_PAGEUP:
            self.scroll = max(0, self.scroll - self._visible_text_lines())
        elif e.key == pygame.K_PAGEDOWN:
            self.scroll += self._visible_text_lines()
        elif e.key == pygame.K_HOME:
            self.scroll = 0
        elif e.key == pygame.K_END:
            self.scroll = 10 ** 9

    def _apply_fast_scroll(self):
        """Быстрое листание, пока зажата средняя кнопка мыши."""
        if not self.fast_scroll_active:
            return
        _, h = self.screen.get_size()
        _, my = pygame.mouse.get_pos()
        center = h // 2
        dead_zone = 40
        if my < center - dead_zone:
            self.scroll -= self.fast_scroll_speed
        else:
            self.scroll += self.fast_scroll_speed
        if self.scroll < 0:
            self.scroll = 0
        elif self.scroll > 10 ** 9:
            self.scroll = 10 ** 9

    def _on_input_key(self, e):
        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            result = self.input_text
            self.input_active = False
            self.input_text = ""
            self._set_hint(None)
            style = {"fg": None, "bg": None, "bold": False, "dim": False}
            echo = self.input_prompt + result
            # Сохраняем эхо в content, чтобы при ресайзе оно не потерялось.
            self.content.append(("plain", echo, style))
            self.lines.append([(echo, style)])
            self.in_queue.put(result)
            self.scroll = 10 ** 9
        elif e.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif e.key == pygame.K_ESCAPE:
            self.input_text = ""
        else:
            ch = e.unicode
            if ch and ch.isprintable():
                self.input_text += ch

    # ------------------------------------------------------------------
    #  Выделение текста и копирование
    # ------------------------------------------------------------------
    def _clamp_scroll(self):
        """Приводит прокрутку к допустимому значению (10**9 = «в самый низ»)."""
        max_scroll = max(0, len(self.lines) - self._visible_text_lines())
        self.scroll = max(0, min(self.scroll, max_scroll))

    def _line_text(self, idx: int) -> str:
        return "".join(t for t, _ in self.lines[idx])

    def _col_to_x(self, idx: int, col: int) -> int:
        """Расстояние в пикселях от начала текста строки до символа номер col."""
        x = 0
        for text, style in self.lines[idx]:
            font = self.font_bold if style.get("bold") else self.font
            if col >= len(text):
                x += font.size(text)[0]
                col -= len(text)
            else:
                x += font.size(text[:col])[0]
                break
        return x

    def _x_to_col(self, idx: int, x: float) -> int:
        """Какой символ строки находится под точкой x (в пикселях от начала текста)."""
        col = 0
        acc = 0
        for text, style in self.lines[idx]:
            font = self.font_bold if style.get("bold") else self.font
            seg_w = font.size(text)[0]
            if x >= acc + seg_w:
                acc += seg_w
                col += len(text)
                continue
            prev = 0
            for i in range(1, len(text) + 1):
                w = font.size(text[:i])[0]
                if x < acc + (prev + w) / 2:   # ближе к левому краю символа
                    return col + i - 1
                prev = w
            return col + len(text)
        return col

    def _hit_test(self, pos):
        """Точка на экране -> (номер строки, номер символа)."""
        self._clamp_scroll()
        x, y = pos
        row = max(0, min(self._visible_text_lines() - 1, y // self.line_h))
        idx = max(0, min(len(self.lines) - 1, self.scroll + row))
        return (idx, self._x_to_col(idx, x - 8))

    def _start_selection(self, pos):
        if not self.lines:
            return
        point = self._hit_test(pos)
        self.sel_anchor = point
        self.sel_caret = point
        self.selecting = True

    def _clear_selection(self):
        self.sel_anchor = None
        self.sel_caret = None
        self.selecting = False

    def _selection_range(self):
        """((строка, символ) начала, (строка, символ) конца) или None, если ничего не выделено."""
        a, b = self.sel_anchor, self.sel_caret
        if a is None or b is None or a == b:
            return None
        return (a, b) if a <= b else (b, a)

    def _select_all(self):
        if not self.lines:
            return
        last = len(self.lines) - 1
        self.sel_anchor = (0, 0)
        self.sel_caret = (last, len(self._line_text(last)))
        self.selecting = False

    def _all_text(self) -> str:
        """
        Весь текст программы. Берём исходные строки, а не перенесённые под
        ширину окна — иначе длинные пути в буфере были бы разорваны пополам.
        Если сейчас ждём ввод — в конец добавляем и строку с вопросом.
        """
        chunks = []
        for item in self.content:
            if item[0] == "rich":
                r = item[1]
                if isinstance(r, Text):
                    chunks.append(r.plain)
                else:
                    chunks.append("\n".join(
                        "".join(t for t, _ in line)
                        for line in self._render_renderable(r)))
            else:
                chunks.append(item[1])
        if self.input_active:
            chunks.append(self.input_prompt + self.input_text)
        text = "\n".join(chunks)
        return "\n".join(line.rstrip() for line in text.split("\n")).rstrip()

    def _selected_text(self) -> str:
        rng = self._selection_range()
        if rng is None:
            return ""
        (l1, c1), (l2, c2) = rng
        last = len(self.lines) - 1
        if (l1, c1) == (0, 0) and (l2, c2) == (last, len(self._line_text(last))):
            return self._all_text()   # выделено всё — отдаём без разрывов от переноса
        parts = []
        for i in range(l1, l2 + 1):
            t = self._line_text(i)
            a = c1 if i == l1 else 0
            b = c2 if i == l2 else len(t)
            parts.append(t[a:b])
        return "\n".join(parts)

    def _copy_text(self, text: str):
        if not text:
            self._toast("Нечего копировать")
        elif clipboard_put(text):
            n = text.count("\n") + 1
            self._toast(f"Скопировано: {n} {_plural_lines(n)}")
        else:
            self._toast("Не удалось скопировать")

    def _handle_ctrl_key(self, e) -> bool:
        """
        Ctrl+A — выделить и скопировать весь текст, Ctrl+C — скопировать выделенное.
        Клавиша определяется по физическому положению (scancode), поэтому
        работает и при русской раскладке, где вместо A/C приходят «ф»/«с».
        """
        sc = getattr(e, "scancode", None)
        if e.key == pygame.K_a or sc == pygame.KSCAN_A:
            self._select_all()
            self._copy_text(self._all_text())
            return True
        if e.key == pygame.K_c or sc == pygame.KSCAN_C:
            text = self._selected_text()
            if text:
                self._copy_text(text)
            else:
                self._toast("Нет выделенного текста (Ctrl+A — выделить всё)")
            return True
        return False

    def _apply_selection_autoscroll(self):
        """Если тянуть выделение за верхний/нижний край окна — текст прокручивается."""
        if not self.selecting:
            return
        _, h = self.screen.get_size()
        mx, my = pygame.mouse.get_pos()
        if my <= 1:
            self.scroll = max(0, self.scroll - 1)
        elif my >= h - 2:
            self.scroll += 1
        else:
            return
        self.sel_caret = self._hit_test((mx, my))

    def _toast(self, text: str):
        self.toast_text = text
        self.toast_until = pygame.time.get_ticks() + 1600

    def _draw_selection(self, start: int, end: int):
        rng = self._selection_range()
        if rng is None:
            return
        (l1, c1), (l2, c2) = rng
        for row, i in enumerate(range(start, end)):
            if i < l1 or i > l2:
                continue
            a = c1 if i == l1 else 0
            b = c2 if i == l2 else len(self._line_text(i))
            x0 = self._col_to_x(i, a)
            x1 = self._col_to_x(i, b)
            if i < l2:
                x1 += self.char_w // 2   # показываем, что захвачен и перевод строки
            if x1 > x0:
                pygame.draw.rect(self.screen, self.SELECTION_COLOR,
                                 (8 + x0, row * self.line_h, x1 - x0, self.line_h))

    def _draw_toast(self):
        if not self.toast_text or pygame.time.get_ticks() >= self.toast_until:
            return
        w, _ = self.screen.get_size()
        surf = self.font.render(self.toast_text, True, (240, 240, 240))
        pad = 8
        box = pygame.Rect(0, 0, surf.get_width() + 2 * pad, surf.get_height() + 2 * pad)
        box.topright = (w - self.SCROLLBAR_W - 10, 10)
        pygame.draw.rect(self.screen, (45, 45, 45), box, border_radius=6)
        pygame.draw.rect(self.screen, (110, 110, 110), box, width=1, border_radius=6)
        self.screen.blit(surf, (box.x + pad, box.y + pad))

    # ------------------------------------------------------------------
    #  Ползунок
    # ------------------------------------------------------------------
    def _scrollbar_geometry(self):
        w, h = self.screen.get_size()
        text_fit = self._visible_text_lines()
        total_lines = len(self.lines)
        max_scroll = max(0, total_lines - text_fit)
        track = pygame.Rect(w - self.SCROLLBAR_W, 0, self.SCROLLBAR_W, h)

        if total_lines <= text_fit or max_scroll == 0:
            thumb = pygame.Rect(track.x + 3, 0, track.w - 6, h)
            return track, thumb, 0, text_fit

        thumb_h = max(self.SCROLLBAR_MIN_THUMB, int(h * text_fit / total_lines))
        thumb_h = min(thumb_h, h)
        denom = max(1, h - thumb_h)
        thumb_y = int((self.scroll / max_scroll) * denom)
        thumb_y = max(0, min(h - thumb_h, thumb_y))
        thumb = pygame.Rect(track.x + 3, thumb_y, track.w - 6, thumb_h)
        return track, thumb, max_scroll, text_fit

    def _set_scroll_from_thumb_y(self, thumb_y, track, thumb, max_scroll):
        if max_scroll <= 0:
            self.scroll = 0
            return
        denom = max(1, track.h - thumb.h)
        thumb_y = max(0, min(track.h - thumb.h, thumb_y))
        self.scroll = int((thumb_y / denom) * max_scroll)
        self.scroll = max(0, min(max_scroll, self.scroll))

    # ------------------------------------------------------------------
    #  Отрисовка
    # ------------------------------------------------------------------
    def _draw(self):
        self.screen.fill(self.BG)
        w, h = self.screen.get_size()
        self._update_progress()
        text_fit = self._visible_text_lines()

        max_scroll = max(0, len(self.lines) - text_fit)
        if self.scroll > max_scroll:
            self.scroll = max_scroll
        if self.scroll < 0:
            self.scroll = 0

        start = self.scroll
        end = min(len(self.lines), start + text_fit)
        self._draw_selection(start, end)
        y = 0
        for i in range(start, end):
            surf = self._get_line_surface(i)
            self.screen.blit(surf, (8, y))
            y += self.line_h

        prog_rows = 1 if self.prog is not None else 0
        if prog_rows:
            self._draw_progress(w, text_fit * self.line_h)

        if self.input_active:
            top = (text_fit + prog_rows) * self.line_h
            rows = len(self.hint_surfs)
            if rows:
                # Закреплённая панель: подсказка + строка ввода под ней.
                panel_w = max(1, w - self.SCROLLBAR_W)
                pygame.draw.rect(self.screen, self.HINT_BG,
                                 (0, top, panel_w, max(1, h - top)))
                pygame.draw.line(self.screen, self.HINT_LINE,
                                 (0, top), (panel_w, top), 2)
                for i, hs in enumerate(self.hint_surfs):
                    self.screen.blit(hs, (8, top + i * self.line_h))
            self._draw_input_line(8, top + rows * self.line_h)

        self._draw_scrollbar()
        self._draw_toast()
        pygame.display.flip()

    def _draw_scrollbar(self):
        track, thumb, max_scroll, _ = self._scrollbar_geometry()
        pygame.draw.rect(self.screen, self.SCROLLBAR_TRACK_COLOR, track)
        if max_scroll <= 0:
            return
        if self.scrollbar_dragging or self.scrollbar_hover:
            color = self.SCROLLBAR_THUMB_ACTIVE
        else:
            color = self.SCROLLBAR_THUMB_COLOR
        pygame.draw.rect(self.screen, color, thumb, border_radius=4)

    def _cache_put(self, idx: int, surf: pygame.Surface) -> None:
        """Кладёт строку в кэш и выбрасывает самые давно не нужные."""
        self._line_cache[idx] = surf
        while len(self._line_cache) > self.LINE_CACHE_MAX:
            self._line_cache.popitem(last=False)

    def _get_line_surface(self, idx: int) -> pygame.Surface:
        cached = self._line_cache.get(idx)
        if cached is not None:
            self._line_cache.move_to_end(idx)
            return cached

        segs = self.lines[idx]
        rendered = []
        total_w = 0
        for text, style in segs:
            if not text:
                continue
            font = self.font_bold if style.get("bold") else self.font
            fg = self._effective_fg(style)
            surf = font.render(text, True, fg)
            rendered.append((surf, style.get("bg")))
            total_w += surf.get_width()

        if total_w == 0:
            surf = pygame.Surface((1, self.line_h), pygame.SRCALPHA)
            self._cache_put(idx, surf)
            return surf

        line_surf = pygame.Surface((total_w, self.line_h), pygame.SRCALPHA)
        x = 0
        for seg_surf, bg in rendered:
            if bg:
                pygame.draw.rect(line_surf, bg,
                                 (x, 0, seg_surf.get_width(), self.line_h))
            line_surf.blit(seg_surf, (x, 0))
            x += seg_surf.get_width()

        self._cache_put(idx, line_surf)
        return line_surf

    def _effective_fg(self, style) -> tuple:
        fg = style.get("fg")
        if fg is None:
            fg = (128, 128, 128) if style.get("dim") else self.FG
        elif style.get("dim"):
            fg = (fg[0] * 3 // 5, fg[1] * 3 // 5, fg[2] * 3 // 5)
        return fg

    def _draw_input_line(self, x: int, y: int):
        text = self.input_prompt + self.input_text
        surf = self.font.render(text, True, self.FG)
        self.screen.blit(surf, (x, y))
        if (self.cursor_blink_ms // 500) % 2 == 0:
            cx = x + surf.get_width() + 1
            pygame.draw.rect(self.screen, self.FG, (cx, y + 2, 2, self.line_h - 6))


# ============================================================================
#  ВОРКЕР
# ============================================================================

def _wrap_worker(ui: Terminal, worker):
    try:
        worker(ui)
    except Exception as e:
        try:
            ui.write(Text(f"Ошибка в воркере: {e}", style="bold red"))
            ui.write(Text(traceback.format_exc(), style="red"))
        except Exception:
            pass
    finally:
        ui.close()


# ============================================================================
# MODULE: app
# ============================================================================
# ============================================================================
#  ТОЧКА ВХОДА
# ============================================================================

def main():
    if is_admin():
        refuse_admin_and_exit()
        return

    ui = Terminal("Cleaner")
    try:
        ui.run(cleaner_worker)
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
