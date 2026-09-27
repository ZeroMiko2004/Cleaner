# 🧹 Cleaner — очистка мусорных папок Windows

Простой скрипт для очистки временных файлов, кэшей и мусора на Windows.
Показывает, что будет удалено, спрашивает подтверждение, и только потом удаляет —
никаких сюрпризов.

По умолчанию чистит:
- Кэш Chrome (`Service Worker\CacheStorage`)
- Дампы падений (`CrashDumps`)
- Пользовательский `.cache`
- Временные файлы Windows (`Temp`)

## ⚠️ Про ложные срабатывания антивирусов

Некоторые антивирусы (Microsoft Defender, Avast, Cynet и др.) могут помечать
`Cleaner.exe` как подозрительный или даже как троян (детекты вида
`Wacapew`/`Wacatec`/`MalwareX`). Это **generic-эвристика**, а не реальный
вредоносный код: антивирусы реагируют на само поведение — программа без
цифровой подписи автора массово и безвозвратно удаляет файлы пользователя,
а именно так же выглядит поведение и вредоносных "wiper"-программ.

Исходный код открыт специально, чтобы вы могли убедиться сами: скрипт не
лезет в сеть, не пишет в реестр, не добавляет себя в автозагрузку и не
трогает ничего, кроме перечисленных папок вашего профиля (см. `cleaner.py`).
Если хотите — соберите exe самостоятельно (см. способ 2 ниже) и проверьте
на VirusTotal свою же сборку.

## ⚠️ Важно

- Удаление **безвозвратное**, мимо корзины. Программа всегда сначала
  показывает полный список файлов/папок с путями и весом и спрашивает
  подтверждение (`y`/`да`) — ничего не удалится, пока вы явно не согласитесь.
- Скрипт написан и протестирован под **Windows**. На других ОС не запускался
  и не рассчитан на них.
- Используйте на свой страх и риск. Автор не несёт ответственности за
  случайно удалённые важные файлы.

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

## Способ 1: скачать готовый .exe (без заморочек)

Просто скачайте готовую сборку из [Releases](../../releases), запустите
и подтвердите удаление. Ничего устанавливать не нужно.

**Ограничение**: список папок для очистки в готовой сборке зафиксирован
(Chrome cache, CrashDumps, `.cache`, Temp) и **не редактируется** — если
хотите чистить другие папки, используйте способ 2.

## Способ 2: свой .py-файл с возможностью менять пути удаления

Так вы сможете сами добавить или убрать любые папки в списке `PATHS`
внутри `cleaner.py`, а затем при желании собрать из него свой exe.

1. Установите [Python 3.10+](https://www.python.org/downloads/).
2. Откройте `cleaner.py` любым текстовым редактором и отредактируйте
   список `PATHS` в начале файла — допишите свои пути построчно:
   ```python
   PATHS = [
       os.path.join(USER_PROFILE, r"AppData\Local\Google\Chrome\User Data\Default\Service Worker\CacheStorage"),
       os.path.join(USER_PROFILE, r"AppData\Local\CrashDumps"),
       os.path.join(USER_PROFILE, ".cache"),
       os.path.join(USER_PROFILE, r"AppData\Local\Temp"),
       r"D:\Мусор",  # свой путь — просто пример
   ]
   ```
3. Запустите и проверьте, что всё работает:
   ```
   python cleaner.py
   ```
4. (Опционально) Соберите свой exe из отредактированного файла:
   ```
   pip install pyinstaller
   pyinstaller --onefile --console --name Cleaner cleaner.py
   ```
   Готовый файл появится в `dist\Cleaner.exe`.

   Чтобы добавить свою иконку:
   ```
   pyinstaller --onefile --console --icon=icon.ico --name Cleaner cleaner.py
   ```

---
---

# 🧹 Cleaner — Windows Junk Folder Cleanup Tool

A simple script for cleaning up temporary files, caches, and junk on
Windows. It shows you exactly what will be deleted, asks for
confirmation, and only then deletes — no surprises.

By default, it cleans:
- Chrome cache (`Service Worker\CacheStorage`)
- Crash dumps (`CrashDumps`)
- User `.cache` folder
- Windows temp files (`Temp`)

## ⚠️ About antivirus false positives

Some antivirus engines (Microsoft Defender, Avast, Cynet, etc.) may flag
`Cleaner.exe` as suspicious or even as a trojan (`Wacapew`/`Wacatec`/`MalwareX`
detections). This is **generic heuristic detection**, not actual malicious
code: antivirus engines react to the *behavior* itself — an unsigned
program that bulk-deletes user files without confirmation from a known
publisher looks the same as a malicious "wiper" tool from a purely
behavioral standpoint.

The source code is open specifically so you can verify it yourself: the
script makes no network requests, doesn't touch the registry, doesn't add
itself to startup, and only touches the folders listed in your own
profile (see `cleaner.py`). If you'd like, build the exe yourself
(see Method 2 below) and scan your own build on VirusTotal.

## ⚠️ Important

- Deletion is **permanent**, bypassing the Recycle Bin. The program
  always shows the full list of files/folders with paths and sizes first
  and asks for confirmation (`y`/`yes`) — nothing is deleted until you
  explicitly agree.
- Written and tested for **Windows**. Not tested on or designed for
  other operating systems.
- Use at your own risk. The author is not responsible for accidentally
  deleted important files.

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

## Method 1: download the ready-made .exe (no hassle)

Just download the build from [Releases](../../releases), run it, and
confirm the deletion. Nothing to install.

**Limitation**: the list of folders to clean in the prebuilt exe is fixed
(Chrome cache, CrashDumps, `.cache`, Temp) and **cannot be edited** — if
you want to clean other folders, use Method 2.

## Method 2: your own .py file with editable deletion paths

This lets you add or remove any folders in the `PATHS` list inside
`cleaner.py`, and optionally build your own exe from it afterward.

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Open `cleaner.py` in any text editor and edit the `PATHS` list at the
   top of the file — add your own paths, one per line:
   ```python
   PATHS = [
       os.path.join(USER_PROFILE, r"AppData\Local\Google\Chrome\User Data\Default\Service Worker\CacheStorage"),
       os.path.join(USER_PROFILE, r"AppData\Local\CrashDumps"),
       os.path.join(USER_PROFILE, ".cache"),
       os.path.join(USER_PROFILE, r"AppData\Local\Temp"),
       r"D:\Junk",  # your own path — just an example
   ]
   ```
3. Run it and check that everything works:
   ```
   python cleaner.py
   ```
4. (Optional) Build your own exe from the edited file:
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
