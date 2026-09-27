import os
import shutil
import stat
import sys

# ============================================================
# ПРОСТО ДОБАВЛЯЙ СТРОКИ С ПУТЯМИ К ПАПКАМ
# ============================================================

# Автоматически определяем папку текущего пользователя Windows
# (C:\Users\ИмяПользователя) — так пути работают у любого человека,
# запускающего программу, без ручной правки.
USER_PROFILE = os.environ.get("USERPROFILE", os.path.expanduser("~"))

PATHS = [
    os.path.join(USER_PROFILE, r"AppData\Local\Google\Chrome\User Data\Default\Service Worker\CacheStorage"),
    os.path.join(USER_PROFILE, r"AppData\Local\CrashDumps"),
    os.path.join(USER_PROFILE, ".cache"),
    os.path.join(USER_PROFILE, r"AppData\Local\Temp"),
    # Добавляй сюда свои пути, например:
    # r"D:\Мусор",
]

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

    # Группируем превью по исходной родительской папке, чтобы было видно,
    # "куда ведут пути"
    print(f"\nНайдено объектов: {len(all_items)}")
    print(f"Общий размер (на удаление): {human_size(total_size)}\n")
    print("Список того, что будет удалено:")
    for p, s, t in sorted(all_items, key=lambda x: -x[1]):
        print(f"  [{t:6}] {human_size(s):>10}  {os.path.abspath(p)}")

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