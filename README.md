# 🧹 Cleaner — очистка мусорных папок Windows

Простой консольный скрипт для очистки временных файлов, кэшей и мусора на Windows.
Показывает, что будет удалено, спрашивает подтверждение, и только потом удаляет —
никаких сюрпризов.

По умолчанию чистит:
- Кэш Chrome (`Service Worker\CacheStorage`)
- Дампы падений (`CrashDumps`)
- Пользовательский `.cache`
- Временные файлы Windows (`Temp`)

Список папок легко расширить — они не привязаны к конкретному пользователю
и определяются автоматически через `USERPROFILE`.

## ⚠️ Важно

- Удаление **безвозвратное**, мимо корзины. Программа всегда сначала
  показывает полный список файлов/папок с путями и весом и спрашивает
  подтверждение (`y`/`да`) — ничего не удалится, пока вы явно не согласитесь.
- Скрипт написан и протестирован под **Windows**. На других ОС не запускался
  и не рассчитан на них.
- Используйте на свой страх и риск. Автор не несёт ответственности за
  случайно удалённые важные файлы, если вы отредактировали список путей
  на что-то более рискованное.

## Возможности

- Предпросмотр перед удалением: полный список объектов, отсортированный
  по размеру, с абсолютными путями.
- Защита от системных папок: даже при опечатке в списке путей скрипт не
  тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили
  пользователей.
- Занятые процессом файлы не вызывают падение — просто пропускаются.
- Автоматическое снятие атрибута read-only перед удалением (частая
  причина сбоев в кэшах браузеров).
- Понятная статистика в конце: сколько удалено полностью/частично,
  сколько пропущено, сколько реально освобождено места.
- Поддержка подтверждения и на латинице (`y`/`yes`), и на русском
  (`д`/`да`) — на случай, если включена русская раскладка клавиатуры.

## Как использовать

1. Установите [Python 3.10+](https://www.python.org/downloads/) (или новее).
2. При желании отредактируйте список `PATHS` в начале `cleaner.py`,
   добавив свои папки.
3. Запустите:
   ```
   python cleaner.py
   ```
4. Проверьте список, ответьте `y`/`да` для подтверждения.

## Сборка в .exe (без установки Python у получателя)

```
pip install pyinstaller
pyinstaller --onefile --console --name Cleaner cleaner.py
```

Готовый файл появится в `dist\Cleaner.exe`.

Хотите добавить свою иконку:
```
pyinstaller --onefile --console --icon=icon.ico --name Cleaner cleaner.py
```

---
---

# 🧹 Cleaner — Windows Junk Folder Cleanup Tool

A simple console script for cleaning up temporary files, caches, and junk
on Windows. It shows you exactly what will be deleted, asks for
confirmation, and only then deletes — no surprises.

By default, it cleans:
- Chrome cache (`Service Worker\CacheStorage`)
- Crash dumps (`CrashDumps`)
- User `.cache` folder
- Windows temp files (`Temp`)

The list of folders is easy to extend — paths aren't hardcoded to a
specific user and are resolved automatically via `USERPROFILE`.

## ⚠️ Important

- Deletion is **permanent**, bypassing the Recycle Bin. The program
  always shows the full list of files/folders with paths and sizes first
  and asks for confirmation (`y`/`yes`) — nothing is deleted until you
  explicitly agree.
- Written and tested for **Windows**. Not tested on or designed for
  other operating systems.
- Use at your own risk. The author is not responsible for accidentally
  deleted important files if you edit the path list to something riskier.

## Features

- Preview before deletion: full list of items sorted by size, with
  absolute paths.
- Protection against system folders: even with a typo in the path list,
  the script won't touch `C:\Windows`, `C:\Program Files`, drive roots,
  or other users' profiles.
- Files locked by another process don't cause a crash — they're simply
  skipped.
- Automatically clears the read-only attribute before deletion (a common
  cause of failures in browser caches).
- Clear summary at the end: how much was fully/partially deleted, how
  much was skipped, and how much space was actually freed.
- Accepts confirmation in both Latin (`y`/`yes`) and Russian (`д`/`да`) —
  in case a Russian keyboard layout is active.

## Usage

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Optionally edit the `PATHS` list at the top of `cleaner.py` to add
   your own folders.
3. Run:
   ```
   python cleaner.py
   ```
4. Review the list, confirm with `y`/`yes`.

## Building a .exe (no Python required for the recipient)

```
pip install pyinstaller
pyinstaller --onefile --console --name Cleaner cleaner.py
```

The resulting file will appear at `dist\Cleaner.exe`.

To add a custom icon:
```
pyinstaller --onefile --console --icon=icon.ico --name Cleaner cleaner.py
```

## License

MIT — do whatever you want with it, no warranty.
