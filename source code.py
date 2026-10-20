# ============================================================================
#  CLEANER — очистка кэшей Windows (консольная версия)
# ----------------------------------------------------------------------------
#  Что делает программа (для тех, кто открыл файл впервые):
#
#  1. Собирает СПИСОК ПАПОК (PATHS), содержимое которых можно безопасно
#     удалить. Часть списка задана руками, часть — достраивается
#     автоматически: у браузеров на движке Chromium профили имеют
#     произвольные имена (Default, Profile 1, Profile 2, ...), а у Firefox
#     вообще имя папки профиля случайное — их проще найти через glob.
#
#  2. Для каждой папки проверяет, что она НЕ системная и НЕ чужая
#     (см. is_forbidden). Это защита от опечатки в PATHS: даже если кто-то
#     впишет туда C:\Windows — программа откажется это трогать.
#
#  3. Собирает список объектов первого уровня (файлы и подпапки), считает
#     их суммарный размер и показывает пользователю.
#
#  4. Спрашивает подтверждение (y/N).
#
#  5. Удаляет. Аккуратно:
#       • «занято другим процессом» — не ошибка, а нормальная ситуация,
#         просто пропускаем;
#       • «read-only» атрибут — снимаем и пробуем снова;
#       • папка удалилась частично (часть файлов была занята) —
#         пересчитываем реально освобождённое место и честно печатаем.
# ============================================================================


import os
import sys
import glob
import shutil
import stat
import queue
import threading
import time
import traceback
from collections import OrderedDict

import pygame

from rich.console import Console
from rich.text import Text


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
#  ИКОНКА ПРИЛОЖЕНИЯ
# ============================================================================

def _script_dir() -> str:
    """Папка, где лежит наш .py или собранный .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


ICON_PATH = os.path.join(_script_dir(), "icon.ico")


# ============================================================================
#  НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
# ============================================================================
# ---------- Переключатели (True — чистить, False — не трогать) ----------
# Кэши шейдеров NVIDIA/AMD/Intel/D3D. Удаление безопасно, но игры потом
# заново компилируют шейдеры (первый запуск может идти очень долго).

CLEAN_SHADER_CACHES = False

# Папка .cache в профиле пользователя. Там часто лежат скачанные модели
# (например huggingface) — после удаления они скачиваются заново.

CLEAN_DOT_CACHE = False

# ---------- Дерево папок в списке перед удалением ----------
# Перед вопросом (y/N) программа показывает основные папки, из которых что-то
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

if CLEAN_SHADER_CACHES:
    PATHS += [
        LOCAL + r"\NVIDIA\GLCache",
        LOCAL + r"\NVIDIA\DXCache",
        LOCAL + r"\NVIDIA\OptixCache",
        LOCAL + r"\AMD\DxCache",
        LOCAL + r"\AMD\GLCache",
        LOCAL + r"\AMD\VkCache",
        LOCAL + r"\Intel\ShaderCache",
        LOCAL + r"\D3DSCache",
    ]

if CLEAN_DOT_CACHE:
    PATHS.append(USER_PROFILE + r"\.cache")

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

FORBIDDEN_ROOTS = [
    "C:\\",
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Users",
]


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


def is_forbidden(path: str) -> bool:
    p = _norm(path)
    if p in {_norm(r) for r in FORBIDDEN_ROOTS}:
        return True
    for root in (r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)"):
        r = _norm(root)
        if p == r or p.startswith(r + os.sep):
            return True
    drive, tail = os.path.splitdrive(p)
    if tail in ("\\", "/", ""):
        return True
    users = _norm(r"C:\Users")
    if p.startswith(users + os.sep):
        profile = _norm(USER_PROFILE)
        if not (p == profile or p.startswith(profile + os.sep)):
            return True
    return False


def collect_items(path: str):
    if not os.path.exists(path):
        return None
    if not os.path.isdir(path):
        return []
    items = []
    try:
        names = os.listdir(path)
    except OSError:
        return []
    for name in names:
        full = os.path.join(path, name)
        try:
            if os.path.isfile(full) or os.path.islink(full):
                size = os.path.getsize(full)
                items.append((full, size, "файл"))
            elif os.path.isdir(full):
                total = 0
                for root, _, files in os.walk(full):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except OSError:
                            pass
                items.append((full, total, "папка"))
        except OSError:
            continue
    return items


def _is_link_or_junction(path: str) -> bool:
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    return bool(isjunction and isjunction(path))


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


def delete_item(path: str, is_dir: bool, expected_size: int):
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
            shutil.rmtree(path, onexc=onexc)
        except TypeError:
            def onerror(function, exc_path, excinfo):
                if not _retry(function, exc_path):
                    failed_paths.add(exc_path)
            shutil.rmtree(path, onerror=onerror)
        except Exception as e:
            if is_locked_error(e):
                return False, "занято", 0
            return False, str(e), 0

        if failed_paths:
            return False, "частично занято", None
        return True, None, expected_size
    else:
        try:
            os.remove(path)
            return True, None, expected_size
        except PermissionError:
            try:
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
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
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def build_tree(path: str, keep_depth: int):
    """Строит дерево папки для показа: размеры считаются по всей глубине,
    а сами узлы хранятся только на keep_depth уровней вниз."""
    node = {"path": path, "name": os.path.basename(path) or path,
            "size": 0, "dir": True, "children": [], "more": False}
    try:
        entries = list(os.scandir(path))
    except OSError:
        return node
    total = 0
    for e in entries:
        try:
            is_link = e.is_symlink() or bool(
                getattr(e, "is_junction", lambda: False)())
            if e.is_dir(follow_symlinks=False) and not is_link:
                child = build_tree(e.path, keep_depth - 1)
            else:
                size = 0 if is_link else e.stat(follow_symlinks=False).st_size
                child = {"path": e.path, "name": e.name, "size": size,
                         "dir": False, "children": [], "more": False}
        except OSError:
            continue
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
#  БУФЕР ОБМЕНА
# ----------------------------------------------------------------------------
#  Копирование выделенного текста (Ctrl+C) и всего текста (Ctrl+A).
#  На Windows пишем в буфер напрямую через WinAPI в формате Unicode —
#  так кириллица и символы вроде ✓ гарантированно вставляются без искажений.
#  Если не вышло (или это не Windows) — пробуем средства самого pygame.
# ============================================================================

def _plural_lines(n: int) -> str:
    """1 строка, 2 строки, 5 строк."""
    if n % 10 == 1 and n % 100 != 11:
        return "строка"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "строки"
    return "строк"


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

    def __init__(self, title: str = "Cleaner"):
        pygame.init()
        pygame.display.set_caption(title)

        if os.path.isfile(ICON_PATH):
            try:
                icon = pygame.image.load(ICON_PATH)
                pygame.display.set_icon(icon)
            except Exception:
                pass

        self.screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
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

    def ask(self, prompt: str) -> str:
        self.out_queue.put(("ask", prompt))
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

    # ------------------------------------------------------------------
    #  Главный цикл
    # ------------------------------------------------------------------
    def run(self, worker):
        t = threading.Thread(target=_wrap_worker, args=(self, worker), daemon=True)
        t.start()

        while self.running:
            self._drain_queue()
            self._handle_events()
            self._update_border()
            self._apply_fast_scroll()
            self._apply_selection_autoscroll()
            self._draw()
            self.clock.tick(30)
            self.cursor_blink_ms = (self.cursor_blink_ms + 33) % 1000
        pygame.quit()

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
                if not self.selecting:
                    self.scroll = 10 ** 9
            elif kind == "close":
                self.running = False
                try:
                    self.in_queue.put_nowait("")
                except queue.Full:
                    pass

    def _visible_text_lines(self) -> int:
        _, h = self.screen.get_size()
        n = max(1, h // self.line_h)
        if self.input_active:
            n -= 1
        return max(1, n)

    # ------------------------------------------------------------------
    #  События мыши и клавиатуры
    # ------------------------------------------------------------------
    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                # Пользователь потянул окно. Пересоздаём surface и — что
                # важно — проверяем, не изменилась ли ШИРИНА В СИМВОЛАХ.
                # Если да, все строки надо пересобрать с новыми переносами.
                self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
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
                chunks.append(getattr(r, "plain", None) or str(r))
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
        _, h = self.screen.get_size()
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

        if self.input_active:
            y = text_fit * self.line_h
            self._draw_input_line(8, y)

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


def cleaner_worker(ui: Terminal):
    ui.write(Text("=" * 60, style="bold cyan"))
    ui.write(Text("  Очистка содержимого папок (занятые файлы пропускаются)",
                  style="bold cyan"))
    ui.write(Text("=" * 60, style="bold cyan"))
    ui.write(Text("Подсказки: колесо мыши — прокрутка, ползунок справа — "
                  "перетаскивание, средняя кнопка (зажать) — быстрая прокрутка "
                  "(вверх/вниз от центра окна). Окно можно тянуть за угол — "
                  "текст переносится автоматически.", style="dim"))
    ui.write(Text("Сканирование папок, подождите...", style="yellow"))

    all_items = []
    missing = []
    blocked = []
    scanned_roots = []
    custom_norms = {_norm(p) for p in CUSTOM_RESOLVED}

    for path in PATHS:
        if is_forbidden(path):
            blocked.append(path)
            continue
        if _norm(path) in custom_norms:
            result = collect_items_nested(path, CUSTOM_SCAN_DEPTH)
        else:
            result = collect_items(path)
        if result is None:
            missing.append(path)
            continue
        if result:
            scanned_roots.append(path)
        all_items.extend(result)

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

    if not all_items:
        ui.write(Text("\nНечего удалять.", style="bold"))
        ui.ask("Нажмите Enter, чтобы закрыть окно...")
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
    if custom_roots:
        groups.append(("ВАШИ ПАПКИ (из CUSTOM_PATHS)",
                       [build_tree(p, TREE_DEPTH) for p in custom_roots]))
    if other_roots:
        trees = [build_tree(p, TREE_DEPTH) for p in other_roots]
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

    ui.write(Text(" "))
    ui.write(Text("=" * 60, style="bold"))
    ui.write(Text(f"Найдено объектов: {len(all_items)}"))
    ui.write(Text(f"Общий размер (на удаление): {human_size(total_size)}",
                  style="bold green"))
    ui.write(Text("=" * 60, style="bold"))

    answer = ui.ask(
        f"Удалить {len(all_items)} объектов общим весом "
        f"{human_size(total_size)}? (y/N): "
    )
    if answer.strip().lower() not in ("y", "yes", "д", "да"):
        ui.write(Text("Отменено.", style="yellow"))
        ui.ask("Нажмите Enter, чтобы закрыть окно...")
        return

    deleted = 0
    skipped = 0
    partial = 0
    errors = 0
    freed_bytes = 0

    for p, expected_size, t in all_items:
        is_dir = (t == "папка")
        ok, err, freed = delete_item(p, is_dir=is_dir, expected_size=expected_size)

        if ok:
            deleted += 1
            freed_bytes += freed
            ui.write(Text(f"  ✓ Удалено ({human_size(expected_size)}): {p}",
                          style="green"))
        elif err == "занято":
            skipped += 1
            ui.write(Text(f"  → Пропущено (занято): {p}", style="yellow"))
        elif err == "частично занято":
            partial += 1
            remaining = recompute_size(p)
            freed_here = max(expected_size - remaining, 0)
            freed_bytes += freed_here
            ui.write(Text(
                f"  ~ Удалено частично ({human_size(freed_here)} из "
                f"{human_size(expected_size)}): {p}",
                style="yellow",
            ))
        else:
            errors += 1
            ui.write(Text(f"  ✗ Ошибка: {p} → {err}", style="red"))

    ui.write(Text(" "))
    ui.write(Text("=" * 60, style="bold"))
    ui.write(Text("Готово!", style="bold green"))
    ui.write(Text(f"  Удалено полностью:  {deleted}"))
    ui.write(Text(f"  Удалено частично:   {partial} (часть файлов внутри была занята)"))
    ui.write(Text(f"  Пропущено:          {skipped} (занято процессами)"))
    ui.write(Text(f"  Ошибок:             {errors}"))
    ui.write(Text(f"  Освобождено места:  {human_size(freed_bytes)}",
                  style="bold green"))
    ui.write(Text("=" * 60, style="bold"))

    ui.ask("Нажмите Enter, чтобы закрыть окно...")


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
