# 🧹 Cleaner — очистка кэшей и мусорных папок Windows

Простой скрипт для очистки временных файлов, кэшей браузеров и программ на Windows.
Сначала показывает, что будет удалено (с полными путями и весом), спрашивает
подтверждение и только потом удаляет.

## 🛑 Прочитайте перед запуском

- **Обязательно проверяйте, куда ведут пути.** Перед удалением программа выводит
  полный список папок и файлов. Прочитайте его целиком, особенно если вы
  редактировали список путей. Увидели что-то незнакомое или важное — ответьте
  `n` (или просто нажмите Enter), и ничего не будет удалено.
- **Не запускайте от имени администратора.** Права администратора не нужны:
  программа чистит только папки вашего обычного профиля. С повышенными правами
  у неё шире доступ к файлам, а профиль может определиться не тот (например,
  профиль другой учётной записи). Запускайте двойным кликом, без пункта
  «Запуск от имени администратора».
- **Программа проверялась только на моём компьютере.** На других системах и
  конфигурациях Windows она не тестировалась, поведение может отличаться.
- **Никаких гарантий и никакой ответственности.** Вы используете программу на
  свой страх и риск. Автор не отвечает за потерянные данные, удалённые файлы и
  любой другой ущерб (см. лицензию MIT).
- Удаление **безвозвратное**, мимо корзины.
- Написано под **Windows**. На других ОС не запускалось и не рассчитано на них.

## ⚠️ Про ложные срабатывания антивирусов

Некоторые антивирусы (Microsoft Defender, Avast, Cynet и др.) могут помечать
готовые `.exe`-файлы как подозрительные или даже как троян (детекты вида
`Wacatac` / `MalwareX`). Это **generic-эвристика**, а не реальный вредоносный код:
антивирусы реагируют на признаки самого файла — упаковка PyInstaller,
отсутствие цифровой подписи издателя и массовое удаление файлов — именно так
выглядят и вредоносные «wiper»-программы.

Исходный код открыт специально, чтобы вы могли убедиться сами: скрипт не лезет
в сеть, не пишет в реестр, не добавляет себя в автозагрузку и не трогает ничего,
кроме перечисленных папок вашего профиля (см. `cleaner.py`). Если не доверяете
готовому exe — запускайте `cleaner.py` через Python или соберите exe
самостоятельно (см. способ 2) и проверьте свою сборку на VirusTotal.

## Что чистит по умолчанию

Только папки кэша и временные файлы. Пароли, куки, история, закладки, расширения
и сессии не затрагиваются.

- **Браузеры на движке Chromium** — Chrome, Edge, Brave, Vivaldi: кэш страниц,
  скомпилированного кода, графики и `Service Worker\CacheStorage`. Профили
  (`Default`, `Profile 1`, `Profile 2`...) находятся автоматически. Также
  кэш Opera и Opera GX.
- **Firefox** — `cache2` и `startupCache` всех профилей (папка профиля
  ищется автоматически).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, отчёты об ошибках (WER).
- **Разработка** — кэши pip, uv, npm, Yarn, NuGet и кэши VS Code
  (`Cache`, `CachedData`, `CachedExtensionVSIXs`, `Code Cache`, `GPUCache`).
- **Приложения** — кэш Discord, Slack и встроенного браузера Steam.

Два дополнительных переключателя в начале `cleaner.py`. В `Cleaner.exe` они
выключены, в `CleanerNoGames.exe` включены:
- `CLEAN_SHADER_CACHES` — шейдерные кэши NVIDIA/AMD/Intel/D3D. Удаление безопасно,
  но игры потом заново компилируют шейдеры, и первый запуск может идти очень долго.
- `CLEAN_DOT_CACHE` — папка `.cache` в профиле. Там часто лежат скачанные
  модели (например, huggingface), после удаления они скачиваются заново.

Полный список путей — в начале файла `cleaner.py`.

## Возможности

- Предпросмотр перед удалением: полный список объектов, отсортированный
  по размеру, с абсолютными путями и итоговым весом.
- Защита от системных папок: даже при опечатке в списке путей скрипт не
  тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили
  пользователей.
- Занятые процессом файлы не вызывают падение — просто пропускаются.
- Автоматическое снятие атрибута read-only перед удалением (частая
  причина сбоев в кэшах браузеров).
- Статистика в конце: сколько удалено полностью/частично, сколько пропущено,
  сколько места освобождено.
- Подтверждение принимается и на латинице (`y`/`yes`), и на русском
  (`д`/`да`) — на случай, если включена русская раскладка.

## Способ 1: скачать готовый .exe

В [Releases](../../releases) доступны две сборки — выберите подходящую:

| Файл | Что чистит |
|---|---|
| `Cleaner.exe` | Обычные кэши и временные файлы: браузеры, Windows, инструменты разработки, приложения. Шейдерные кэши игр и папку `.cache` **не трогает** — подходит всем, в том числе игрокам |
| `CleanerNoGames.exe` | То же самое **плюс** шейдерные кэши видеокарты (NVIDIA/AMD/Intel/D3D) и папку `.cache` в профиле (там часто лежат скачанные модели, например huggingface) |

Если вы играете, берите `Cleaner.exe`. `CleanerNoGames.exe` освободит больше
места, но игры после него заново компилируют шейдеры (первый запуск может идти
очень долго), а скачанные в `.cache` модели придётся загружать снова.
Берите его, только если на компьютере нет игр или вас это не смущает.

Запустите нужный файл (**не от имени администратора**), проверьте список путей
и подтвердите удаление. Ничего устанавливать не нужно.

**Ограничение**: список папок в готовых сборках зафиксирован и **не
редактируется**. Хотите чистить другие папки — используйте способ 2.

## Способ 2: свой .py-файл с возможностью менять пути

1. Установите [Python 3.10+](https://www.python.org/downloads/).
2. Откройте `cleaner.py` в любом редакторе. В начале файла есть список `PATHS`:
   чтобы убрать путь — поставьте `#` перед строкой, чтобы добавить — допишите
   строку (в конце запятая):
   ```python
   PATHS = [
       LOCAL + r"\Temp",
       LOCAL + r"\CrashDumps",
       # LOCAL + r"\Microsoft\Windows\INetCache",   # закомментировано — не чистится
       r"D:\Мусор",  # свой путь — просто пример
   ]
   ```
   `LOCAL` — это `AppData\Local` текущего пользователя, `ROAMING` — `AppData\Roaming`
   (подставляются автоматически). Новый браузер на Chromium добавляется строкой
   в список `CHROMIUM_BROWSERS`.
3. Запустите в обычном окне терминала (**не от имени администратора**):
   ```
   python cleaner.py
   ```
4. (Опционально) Соберите свой exe (чтобы получить версию как `CleanerNoGames.exe`, поставьте
   `CLEAN_SHADER_CACHES = True` и `CLEAN_DOT_CACHE = True` перед сборкой):
   ```
   pip install pyinstaller
   pyinstaller --onefile --console --name Cleaner cleaner.py
   ```
   Готовый файл появится в `dist\Cleaner.exe`. Со своей иконкой:
   ```
   pyinstaller --onefile --console --icon=icon.ico --name Cleaner cleaner.py
   ```

---
---

# 🧹 Cleaner — Windows Cache and Junk Folder Cleanup Tool

A simple script for cleaning up temporary files and browser/app caches on
Windows. It first shows what will be deleted (full paths and sizes), asks for
confirmation, and only then deletes.

## 🛑 Read before running

- **Always check where the paths lead.** Before deleting, the program prints
  the full list of folders and files. Read it completely, especially if you
  edited the path list. If you see anything unfamiliar or important, answer
  `n` (or just press Enter) and nothing will be deleted.
- **Do not run as administrator.** Administrator rights are not needed: the
  program only cleans folders in your regular user profile. With elevated
  rights it has wider access to files, and the profile may resolve to the
  wrong one (for example, another account's profile). Launch it with a
  normal double click, without "Run as administrator".
- **The program has only been tested on my own computer.** It has not been
  tested on other systems or Windows configurations, and behavior may differ.
- **No warranty and no liability.** You use it at your own risk. The author
  is not responsible for lost data, deleted files, or any other damage
  (see the MIT license).
- Deletion is **permanent**, bypassing the Recycle Bin.
- Written for **Windows**. Not tested on or designed for other operating systems.

## ⚠️ About antivirus false positives

Some antivirus engines (Microsoft Defender, Avast, Cynet, etc.) may flag
the prebuilt `.exe` files as suspicious or even as a trojan (`Wacatac` / `MalwareX`
detections). This is **generic heuristic detection**, not actual malicious
code: antivirus engines react to characteristics of the file itself — a
PyInstaller package, no publisher's digital signature, and bulk file
deletion, which is also how malicious "wiper" tools look.

The source code is open specifically so you can verify it yourself: the
script makes no network requests, doesn't touch the registry, doesn't add
itself to startup, and only touches the folders listed in your own
profile (see `cleaner.py`). If you don't trust the prebuilt exe, run
`cleaner.py` with Python or build the exe yourself (see Method 2) and scan
your own build on VirusTotal.

## What it cleans by default

Only cache folders and temporary files. Passwords, cookies, history,
bookmarks, extensions, and sessions are not touched.

- **Chromium-based browsers** — Chrome, Edge, Brave, Vivaldi: page cache,
  compiled code cache, graphics cache, and `Service Worker\CacheStorage`.
  Profiles (`Default`, `Profile 1`, `Profile 2`...) are detected
  automatically. Also Opera and Opera GX cache.
- **Firefox** — `cache2` and `startupCache` of all profiles (the profile
  folder is found automatically).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, error reports (WER).
- **Development** — pip, uv, npm, Yarn, NuGet caches and VS Code caches
  (`Cache`, `CachedData`, `CachedExtensionVSIXs`, `Code Cache`, `GPUCache`).
- **Apps** — Discord, Slack, and Steam's built-in browser cache.

Two extra switches at the top of `cleaner.py`. They are off in `Cleaner.exe`
and on in `CleanerNoGames.exe`:
- `CLEAN_SHADER_CACHES` — NVIDIA/AMD/Intel/D3D shader caches. Safe to delete,
  but games have to recompile shaders afterwards, and the first launch can
  take a very long time.
- `CLEAN_DOT_CACHE` — the `.cache` folder in your profile. It often holds
  downloaded models (for example, huggingface) that will be downloaded again.

The full list of paths is at the top of `cleaner.py`.

## Features

- Preview before deletion: full list of items sorted by size, with
  absolute paths and the total size.
- Protection against system folders: even with a typo in the path list,
  the script won't touch `C:\Windows`, `C:\Program Files`, drive roots,
  or other users' profiles.
- Files locked by another process don't cause a crash — they're simply
  skipped.
- Automatically clears the read-only attribute before deletion (a common
  cause of failures in browser caches).
- Summary at the end: how much was fully/partially deleted, how much was
  skipped, and how much space was freed.
- Confirmation is accepted in both Latin (`y`/`yes`) and Russian (`д`/`да`) —
  in case a Russian keyboard layout is active.

## Method 1: download the ready-made .exe

[Releases](../../releases) has two builds — pick the one you need:

| File | What it cleans |
|---|---|
| `Cleaner.exe` | Regular caches and temporary files: browsers, Windows, dev tools, apps. Does **not** touch game shader caches or the `.cache` folder — fine for everyone, including gamers |
| `CleanerNoGames.exe` | The same **plus** GPU shader caches (NVIDIA/AMD/Intel/D3D) and the `.cache` folder in your profile (it often holds downloaded models, e.g. huggingface) |

If you play games, use `Cleaner.exe`. `CleanerNoGames.exe` frees more space,
but games will recompile shaders afterwards (the first launch can take a very
long time), and models downloaded into `.cache` will have to be downloaded
again. Use it only if you have no games or don't mind.

Run the one you chose (**not as administrator**), check the list of paths, and
confirm the deletion. Nothing to install.

**Limitation**: the list of folders in the prebuilt exe files is fixed and
**cannot be edited**. To clean other folders, use Method 2.

## Method 2: your own .py file with editable paths

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Open `cleaner.py` in any editor. At the top there is a `PATHS` list:
   to remove a path, put `#` in front of the line; to add one, add a
   line (with a trailing comma):
   ```python
   PATHS = [
       LOCAL + r"\Temp",
       LOCAL + r"\CrashDumps",
       # LOCAL + r"\Microsoft\Windows\INetCache",   # commented out — not cleaned
       r"D:\Junk",  # your own path — just an example
   ]
   ```
   `LOCAL` is the current user's `AppData\Local`, `ROAMING` is
   `AppData\Roaming` (filled in automatically). A new Chromium-based browser
   is added with one line in the `CHROMIUM_BROWSERS` list.
3. Run it in a regular terminal window (**not as administrator**):
   ```
   python cleaner.py
   ```
4. (Optional) Build your own exe (to get the `CleanerNoGames.exe` variant, set
   `CLEAN_SHADER_CACHES = True` and `CLEAN_DOT_CACHE = True` before building):
   ```
   pip install pyinstaller
   pyinstaller --onefile --console --name Cleaner cleaner.py
   ```
   The resulting file will appear at `dist\Cleaner.exe`. With a custom icon:
   ```
   pyinstaller --onefile --console --icon=icon.ico --name Cleaner cleaner.py
   ```

## License

MIT — do whatever you want with it, no warranty.
