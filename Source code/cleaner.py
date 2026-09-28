import glob
import os
import shutil
import stat
import sys

# ============================================================
# НАСТРОЙКИ — всё, что нужно менять, находится в этом блоке
# ============================================================

# ---------- Переключатели (True — чистить, False — не трогать) ----------
# Кэши шейдеров NVIDIA/AMD/Intel/D3D. Удаление безопасно, но игры потом
# заново компилируют шейдеры (первый запуск может идти очень долго).
CLEAN_SHADER_CACHES = False

# Папка .cache в профиле пользователя. Там часто лежат скачанные модели
# (например huggingface) — после удаления они скачиваются заново.
CLEAN_DOT_CACHE = False

# ---------- Системные папки (определяются сами для любого пользователя) ----------
USER_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))
LOCAL = os.environ.get("LOCALAPPDATA", USER_PROFILE + r"\AppData\Local")     # ...\AppData\Local
ROAMING = os.environ.get("APPDATA", USER_PROFILE + r"\AppData\Roaming")      # ...\AppData\Roaming

# ---------- Браузеры на движке Chromium ----------
# Профили (Default, Profile 1, Profile 2, Profile 3...) ищутся автоматически.
# Добавить браузер — допишите строку в первый список.
# Добавить папку кэша — допишите строку во второй список.
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

# ---------- Ручной список путей ----------
# Убрать путь — поставьте # перед строкой.
# Добавить — скопируйте любую строку и поменяйте путь (в конце запятая).
PATHS = [
    # ---------- Windows ----------
    LOCAL + r"\Temp",
    LOCAL + r"\CrashDumps",
    LOCAL + r"\Microsoft\Windows\INetCache",
    LOCAL + r"\Microsoft\Windows\WER\ReportArchive",
    LOCAL + r"\Microsoft\Windows\WER\ReportQueue",

    # ---------- Opera / Opera GX ----------
    LOCAL + r"\Opera Software\Opera Stable\Cache",
    LOCAL + r"\Opera Software\Opera GX Stable\Cache",

    # ---------- Разработка ----------
    LOCAL + r"\pip\Cache",
    LOCAL + r"\uv\cache",
    LOCAL + r"\npm-cache",
    LOCAL + r"\Yarn\Cache",
    LOCAL + r"\NuGet\v3-cache",

    # ---------- VS Code ----------
    ROAMING + r"\Code\Cache",
    ROAMING + r"\Code\CachedData",
    ROAMING + r"\Code\CachedExtensionVSIXs",
    ROAMING + r"\Code\Code Cache",
    ROAMING + r"\Code\GPUCache",

    # ---------- Discord ----------
    ROAMING + r"\discord\Cache",
    ROAMING + r"\discord\Code Cache",
    ROAMING + r"\discord\GPUCache",

    # ---------- Slack ----------
    ROAMING + r"\Slack\Cache",
    ROAMING + r"\Slack\Code Cache",
    ROAMING + r"\Slack\GPUCache",
    ROAMING + r"\Slack\Service Worker\CacheStorage",

    # ---------- Steam (кэш встроенного браузера) ----------
    LOCAL + r"\Steam\htmlcache",

    # Добавляй сюда свои пути, например:
    # r"D:\Мусор",
]

# ---------- Автоматический поиск: браузеры Chromium (все профили) ----------
for browser in CHROMIUM_BROWSERS:
    profiles = glob.glob(browser + r"\Default") + glob.glob(browser + r"\Profile *")
    for profile in profiles:
        for folder in CHROMIUM_CACHE_FOLDERS:
            PATHS.append(profile + "\\" + folder)
    # кэши шейдеров самого браузера лежат в корне User Data
    for folder in (r"GrShaderCache", r"ShaderCache", r"GraphiteDawnCache"):
        PATHS.append(browser + "\\" + folder)

# ---------- Автоматический поиск: Firefox (случайное имя папки профиля) ----------
for profile in glob.glob(LOCAL + r"\Mozilla\Firefox\Profiles\*"):
    PATHS.append(profile + r"\cache2")
    PATHS.append(profile + r"\startupCache")

# ---------- Переключатели ----------
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

# Оставляем только реально существующие папки и убираем дубли, чтобы у
# других людей не было десятков строк "не найдены". Не нужно — удалите строку.
PATHS = [p for p in dict.fromkeys(PATHS) if os.path.isdir(p)]

# Пути, которые нельзя трогать НИКОГДА, даже если случайно попадут в PATHS
# (сюда стоит добавить корни дисков и системные папки)
FORBIDDEN_ROOTS = [
    "C:\\",
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Users",
]
# ============================================================


def human_size(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"


def _norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def is_forbidden(path: str) -> bool:
    """
    Проверяет, что путь не является системным корнем или чужим профилем.
    В отличие от простого сравнения, проверяет и ВЛОЖЕННОСТЬ:
    C:\\Windows\\System32 запрещён так же, как и сам C:\\Windows.
    """
    p = _norm(path)

    # точные запрещённые корни (например "C:\")
    if p in {_norm(r) for r in FORBIDDEN_ROOTS}:
        return True

    # системные каталоги: запрещаем и сами, и всё, что внутри них
    for root in (r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)"):
        r = _norm(root)
        if p == r or p.startswith(r + os.sep):
            return True

    # корни любых дисков: C:\, D:\ и т.п.
    drive, tail = os.path.splitdrive(p)
    if tail in ("\\", "/", ""):
        return True

    # C:\Users: разрешаем только текущий профиль пользователя,
    # всё остальное внутри (чужие профили) — запрещаем
    users = _norm(r"C:\Users")
    if p.startswith(users + os.sep):
        profile = _norm(USER_PROFILE)
        if not (p == profile or p.startswith(profile + os.sep)):
            return True

    return False


def collect_items(path: str):
    """Собирает только содержимое папки (файлы и подпапки первого уровня)."""
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


def is_locked_error(exc: Exception) -> bool:
    """Определяет, что файл/папка занята другим процессом."""
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError):
        winerror = getattr(exc, "winerror", None)
        errno = getattr(exc, "errno", None)
        if winerror == 32:          # ERROR_SHARING_VIOLATION
            return True
        if errno in (13, 16):       # EACCES, EBUSY
            return True
    return False


def delete_item(path: str, is_dir: bool, expected_size: int):
    """
    Пытается удалить.
    Возвращает: (успех, сообщение_об_ошибке_или_None, реально_освобождённый_объём)

    Для папок объём считается по сумме размеров файлов, которые
    подтверждённо удалены (через колбэк onexc отслеживаем сбои),
    а не просто "expected_size если rmtree не бросил исключение".
    """
    if is_dir:
        failed_paths = set()

        def _retry_after_clearing_readonly(function, exc_path):
            """Снимает read-only и пробует ту же операцию ещё раз."""
            try:
                os.chmod(exc_path, stat.S_IWRITE)
                function(exc_path)
                return True
            except Exception:
                return False

        def onexc(function, exc_path, exc):
            if not _retry_after_clearing_readonly(function, exc_path):
                failed_paths.add(exc_path)

        try:
            shutil.rmtree(path, onexc=onexc)
        except TypeError:
            # На случай Python < 3.12, где onexc ещё не появился
            def onerror(function, exc_path, excinfo):
                if not _retry_after_clearing_readonly(function, exc_path):
                    failed_paths.add(exc_path)
            shutil.rmtree(path, onerror=onerror)
        except Exception as e:
            if is_locked_error(e):
                return False, "занято", 0
            return False, str(e), 0

        if failed_paths:
            # Часть содержимого не удалилась — папка удалена частично
            return False, "частично занято", None  # None -> посчитаем ниже пересчётом
        return True, None, expected_size

    else:
        try:
            os.remove(path)
            return True, None, expected_size
        except PermissionError:
            # Частая причина в кэшах браузеров — файл помечен read-only.
            # Снимаем атрибут и пробуем удалить ещё раз, прежде чем
            # считать это "занято" или ошибкой.
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
    """Пересчитывает, сколько осталось на диске (для частично удалённых папок)."""
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


def main():
    print("=" * 60)
    print("  Очистка содержимого папок (занятые файлы пропускаются)")
    print("=" * 60)

    all_items = []
    missing = []
    blocked = []

    for path in PATHS:
        if is_forbidden(path):
            blocked.append(path)
            continue
        result = collect_items(path)
        if result is None:
            missing.append(path)
            continue
        all_items.extend(result)

    if blocked:
        print("\n[!] Заблокированы (системные корни, удаление запрещено):")
        for p in blocked:
            print(f"    - {p}")

    if missing:
        print("\n[!] Не найдены следующие пути (пропущены):")
        for p in missing:
            print(f"    - {p}")

    if not all_items:
        print("\nНечего удалять.")
        return

    total_size = sum(s for _, s, _ in all_items)

    print("\nСписок того, что будет удалено:")
    for p, s, t in sorted(all_items, key=lambda x: -x[1]):
        print(f"  [{t:6}] {human_size(s):>10}  {os.path.abspath(p)}")

    # Итог выводим ПОСЛЕ списка, чтобы он был виден прямо над вопросом
    # и не терялся при прокрутке длинного списка
    print()
    print("=" * 60)
    print(f"Найдено объектов: {len(all_items)}")
    print(f"Общий размер (на удаление): {human_size(total_size)}")
    print("=" * 60)
    print()
    print("(Если ответ 'y' не срабатывает — проверьте раскладку клавиатуры,")
    print(" либо просто введите 'да'.)")
    answer = input(f"Удалить {len(all_items)} объектов общим весом "
                    f"{human_size(total_size)}? (y/N): ").strip().lower()
    # Принимаем и латинское y/yes, и русское д/да — на случай, если
    # физически нажатая клавиша "y" даёт кириллицу из-за раскладки
    if answer not in ("y", "yes", "д", "да"):
        print("Отменено.")
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
            print(f"  ✓ Удалено ({human_size(expected_size)}): {p}")
        elif err == "занято":
            skipped += 1
            print(f"  → Пропущено (занято): {p}")
        elif err == "частично занято":
            partial += 1
            remaining = recompute_size(p)
            freed_here = max(expected_size - remaining, 0)
            freed_bytes += freed_here
            print(f"  ~ Удалено частично ({human_size(freed_here)} из "
                  f"{human_size(expected_size)}): {p}")
        else:
            errors += 1
            print(f"  ✗ Ошибка: {p} → {err}")

    print("\n" + "=" * 60)
    print("Готово!")
    print(f"  Удалено полностью:  {deleted}")
    print(f"  Удалено частично:   {partial} (часть файлов внутри была занята)")
    print(f"  Пропущено:          {skipped} (занято процессами)")
    print(f"  Ошибок:             {errors}")
    print(f"  Освобождено места:  {human_size(freed_bytes)}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        main()
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {e}")
    finally:
        input("\nНажмите Enter, чтобы закрыть окно...")
