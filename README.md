# 🧹 Cleaner — очистка кэшей и мусорных папок Windows

Простая программа для очистки временных файлов, кэшей браузеров и программ на Windows.
Открывается в окне, похожем на терминал, сначала показывает, что будет удалено
(в виде дерева папок с полными путями и весом), спрашивает подтверждение и только потом удаляет.

📄 **Исходный код:** [source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py) —
откройте и проверьте сами, что именно делает программа.

## 🛑 Прочитайте перед запуском

- **Обязательно проверяйте, куда ведут пути.** Перед удалением программа выводит
  список папок и файлов. Прочитайте его целиком, особенно если вы
  добавляли свои пути. Увидели что-то незнакомое или важное — ответьте
  `n` (или просто нажмите Enter), и ничего не будет удалено.
- **Не добавляйте папки с данными программ.** Чистите только то, что точно является
  кэшем или временными файлами. Например, папка
  `C:\Users\<имя>\AppData\Local\Packages` хранит данные приложений Microsoft Store
  (настройки, логины), и её целиком чистить нельзя.
- **Не запускайте от имени администратора.** Права администратора не нужны:
  программа чистит только папки вашего обычного профиля. С повышенными правами
  у неё шире доступ к файлам, а профиль может определиться не тот (например,
  профиль другой учётной записи). Поэтому программа сама откажется работать
  от имени администратора и покажет сообщение. Запускайте обычным двойным кликом.
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
кроме перечисленных папок вашего профиля. Прочитать код можно здесь:
[source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py).
Если не доверяете готовому exe — запускайте `source code.py` через Python или
соберите exe самостоятельно (см. способ 2) и проверьте свою сборку на VirusTotal.

## Что чистит по умолчанию

Только папки кэша и временные файлы. Пароли, куки, история, закладки, расширения
и сессии не затрагиваются.

- **Браузеры на движке Chromium** — Chrome, Edge, Brave, Vivaldi: кэш страниц,
  скомпилированного кода, графики (в том числе шейдерный кэш браузера) и
  `Service Worker\CacheStorage`. Профили (`Default`, `Profile 1`, `Profile 2`...)
  находятся автоматически. Также кэш Opera и Opera GX.
- **Firefox** — `cache2` и `startupCache` всех профилей (папка профиля
  ищется автоматически).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, отчёты об ошибках (WER).
- **Разработка** — кэши pip, uv, npm, Yarn, NuGet и кэши VS Code
  (`Cache`, `CachedData`, `CachedExtensionVSIXs`, `Code Cache`, `GPUCache`).
- **Приложения** — кэш Discord, Slack и встроенного браузера Steam, а также
  кэш Unsloth Studio (`.unsloth\studio\cache` в папке профиля).

Два дополнительных переключателя в начале `source code.py`. В `Cleaner.exe` они
выключены, в `CleanerNoGames.exe` включены:
- `CLEAN_SHADER_CACHES` — шейдерные кэши NVIDIA/AMD/Intel/D3D. Удаление безопасно,
  но игры потом заново компилируют шейдеры, и первый запуск может идти очень долго.
- `CLEAN_DOT_CACHE` — папка `.cache` в профиле. Там часто лежат скачанные
  модели (например, huggingface), после удаления они скачиваются заново.

Папки, которых нет на вашем компьютере, программа пропускает сама. Полный
список путей — в начале файла
[source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py).

## Как пользоваться и читать список перед удалением

1. Запустите программу (**не от имени администратора**). Она просканирует папки
   и построит список.
2. Прочитайте список. Он показывается в виде дерева:
   - **Два блока.** Сначала «ВАШИ ПАПКИ (из CUSTOM_PATHS)» — те, что вы вписали
     сами, в том порядке, как вы их записали. Потом «ОСНОВНЫЕ ПАПКИ» — встроенные
     пути, самые тяжёлые сверху.
   - **Основная папка** показана строкой с полным путём и общим весом. Пометка
     «папка останется, внутри чистится» означает, что сама папка не удаляется,
     чистится только её содержимое.
   - **Внутри папки** сначала идут подпапки с весом, потом файлы. Файл никогда не
     стоит выше папки, даже если он тяжелее.
   - **Красная метка «← УДАЛИТСЯ»** — этот объект будет удалён. **Серым** показано
     то, что лежит внутри удаляемой папки (оно исчезнет вместе с ней).
   - **«… ещё файлов: 95, 45.42 MB»** — свёрнутые элементы: показываются самые
     тяжёлые, остальные собраны в одну строку с общим весом.
   - **«[внутри ещё, свёрнуто]»** — глубже заданного уровня раскрытия.
3. Внизу программа пишет «Найдено объектов» и «Общий размер (на удаление)» —
   считаются только те объекты, которые помечены «← УДАЛИТСЯ».
4. Ответьте на вопрос: `y` / `yes` / `д` / `да` — удалить, всё остальное
   (включая просто Enter) — отмена.
5. После удаления выводится статистика: сколько удалено полностью, частично,
   сколько пропущено (занято процессами) и сколько места освобождено. Цифра
   считается по размеру удалённых файлов, поэтому свободное место в проводнике
   может вырасти чуть меньше.

## Возможности

- Окно в виде терминала: цветной вывод, прокрутка колесом мыши, перетаскиваемый
  ползунок справа, быстрая прокрутка зажатой средней кнопкой, размер окна можно
  менять — текст переносится автоматически.
- **Выделение и копирование текста:** выделяйте текст левой кнопкой мыши (если
  дотянуть выделение до верхнего или нижнего края окна, список прокручивается
  сам). `Ctrl+C` копирует выделенное, `Ctrl+A` выделяет и копирует весь текст
  окна. Сочетания работают и при русской раскладке. Длинные пути копируются
  целыми строками, без разрывов от визуального переноса. Кириллица и
  спецсимволы вставляются в другие программы без искажений. После копирования в
  углу окна появляется подсказка «Скопировано: N строк».
- **Предпросмотр-дерево перед удалением:** основные папки раскрыты, видно путь,
  вес, что удалится и что останется (см. выше).
- **Свои папки:** отдельный список `CUSTOM_PATHS` для ваших путей (способ 2),
  с поиском папок внутри папок.
- **Цветная рамка окна (Windows 11):** когда окно активно, рамка и заголовок
  зелёные; когда вы переключились на другое окно — красные. На Windows 10
  рамка остаётся обычной, это не ошибка.
- Защита от системных папок: даже при опечатке в списке путей скрипт не
  тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили
  пользователей.
- Ссылки и junction внутри папок не раскрываются, поэтому программа не удалит
  содержимое чужой папки, на которую они указывают.
- Один и тот же объект не считается дважды, даже если ваши пути пересекаются
  со встроенными.
- Отказ работать от имени администратора (см. предупреждение выше).
- Занятые процессом файлы не вызывают падение — просто пропускаются.
- Автоматическое снятие атрибута read-only перед удалением (частая
  причина сбоев в кэшах браузеров).

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

Запустите нужный файл (**не от имени администратора**), проверьте список и
подтвердите удаление. Ничего устанавливать не нужно: Python и библиотеки уже
внутри exe.

**Ограничение**: список папок в готовых сборках зафиксирован и **не
редактируется**. Хотите чистить другие папки или менять настройки — используйте
способ 2.

## Способ 2: свой .py-файл с возможностью менять пути и настройки

### Установка и запуск

1. Установите [Python 3.10+](https://www.python.org/downloads/).
2. Скачайте файл
   [source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py)
   (на странице файла нажмите кнопку **Download raw file**) или скачайте весь
   репозиторий. Если хотите свою иконку окна, положите `icon.ico` в ту же папку.
3. **Обязательно** установите библиотеки, без них код не запустится (одна
   команда в терминале):
   ```
   pip install pygame
   pip install rich
   ```
   `pygame` рисует окно программы, `rich` отвечает за цветной вывод.
4. Запустите в обычном окне терминала (**не от имени администратора**) из папки,
   где лежит файл:
   ```
   python "source code.py"
   ```

### Как добавить свои папки (список CUSTOM_PATHS)

Свои пути вписывайте **только в список `CUSTOM_PATHS`** (раздел «МОИ ПУТИ» в
файле), а не в встроенный `PATHS`. Так ваши папки всегда показываются первыми
отдельным блоком.

1. Откройте нужную папку в Проводнике, кликните в адресную строку и нажмите
   `Ctrl+C` (или `Shift` + правая кнопка по папке → «Копировать как путь»).
2. Откройте `source code.py` в любом редакторе, найдите `CUSTOM_PATHS` и добавьте
   строку между линиями «ВПИСЫВАЙТЕ СВОИ ПУТИ НИЖЕ / ВЫШЕ ЭТОЙ ЛИНИИ»:
   ```python
   CUSTOM_PATHS = [
       r"D:\Games\SomeGame\Cache",
       r"C:\Users\Имя\Мой мусор",
       # r"D:\Старое",   # строка с # выключена
   ]
   ```
3. Правила записи:
   - перед первой кавычкой обязательно буква `r`, иначе Python сломает
     обратные слэши;
   - путь пишется между кавычками (кавычки из Проводника дублировать не нужно);
   - слэш `\` в конце пути не ставьте;
   - в конце строки нужна запятая;
   - строка, начинающаяся с `#`, — комментарий, она выключена.
4. Дополнительно можно использовать:
   - звёздочку `*` как «любое имя»: `r"D:\Games\*\Cache"` — папка `Cache` во всех
     подпапках `D:\Games`;
   - переменные Windows: `r"%LOCALAPPDATA%\Temp"`.
5. Что важно знать:
   - удаляется **содержимое** папки, сама папка остаётся;
   - если путь не существует, программа молча его пропускает — проверьте
     опечатки, если вашей папки нет в списке;
   - если папка пустая, ей нечего удалять, и в списке её не будет;
   - защита остаётся в силе: системные папки и чужие профили программа не тронет,
     такие пути будут показаны в предупреждении «Заблокированы».

### Поиск папок в папках (CUSTOM_SCAN_DEPTH)

Число `CUSTOM_SCAN_DEPTH` (рядом со списком `CUSTOM_PATHS`) задаёт, на сколько
уровней вглубь программа заходит в ваших папках:

- `1` — удаляется всё, что лежит прямо в папке (подпапки целиком);
- `2` — программа заходит в каждую подпапку и удаляет то, что лежит **внутри**
  неё; сами подпапки первого уровня остаются пустыми;
- `3` и больше — то же, но глубже.

Файлы, лежащие выше нужного уровня, удаляются как обычно. Настройка действует
только на пути из `CUSTOM_PATHS`; встроенные пути работают как обычно (удаляется
всё, что лежит прямо в них).

### Остальные настройки в начале файла

- `CLEAN_SHADER_CACHES` и `CLEAN_DOT_CACHE` (`True` — чистить, `False` — не
  трогать). В файле они стоят в `False`, как в `Cleaner.exe`; для версии как
  `CleanerNoGames.exe` поставьте `True`.
- Внешний вид списка (влияет только на показ, на удаление — нет):
  - `TREE_DEPTH = 3` — сколько уровней вложенных папок раскрывать;
  - `TREE_MAX_FOLDERS = 10` — сколько папок показывать внутри одной папки;
  - `TREE_MAX_FILES = 5` — сколько файлов показывать внутри одной папки.

  Остальное сворачивается в строку «… ещё N». Увеличите числа — список станет
  подробнее, но длиннее.
- Цвета окна (Windows 11), цвета задаются как `(R, G, B)` от 0 до 255:
  - `CHANGE_BORDER_COLOR`, `BORDER_COLOR_ACTIVE`, `BORDER_COLOR_INACTIVE` — рамка;
  - `CHANGE_TITLEBAR_COLOR`, `TITLEBAR_COLOR_ACTIVE`, `TITLEBAR_COLOR_INACTIVE`,
    `TITLEBAR_TEXT_COLOR` — заголовок окна;
  - чтобы отключить, поставьте `False` в `CHANGE_BORDER_COLOR` или
    `CHANGE_TITLEBAR_COLOR`.
- Встроенный список `PATHS`: чтобы убрать путь, поставьте `#` перед строкой.
  `LOCAL` — это `AppData\Local` текущего пользователя, `ROAMING` — `AppData\Roaming`
  (подставляются автоматически). Новый браузер на Chromium добавляется строкой
  в список `CHROMIUM_BROWSERS`.

### Сборка своего .exe (необязательно)

Чтобы запускать без Python, соберите exe. Библиотеки `pygame` и `rich` из
установки должны быть поставлены до сборки, иначе они не попадут в exe:
```
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name Cleaner "source code.py"
```
`--windowed` нужен, потому что у программы своё окно и чёрная консоль рядом не
нужна. Готовый файл появится в `dist\Cleaner.exe`. Флаг `--icon` задаёт иконку
самого exe-файла; иконка окна берётся из `icon.ico`, который лежит рядом с exe.
Без иконки уберите `--icon=icon.ico` из команды.

## Частые вопросы

- **Моей папки нет в списке.** Проверьте, что путь записан верно (с `r` перед
  кавычками, без слэша в конце), что папка существует и что в ней есть что
  удалять. Заблокированные системные пути выводятся в предупреждении над списком.
- **Не работает `Ctrl+C` / `Ctrl+A`.** Сначала кликните в окно программы.
  Сочетания работают и на русской раскладке.
- **Рамка окна не меняет цвет.** Эта функция работает только на Windows 11.
  На Windows 10 окно остаётся обычным.
- **Список слишком длинный или слишком короткий.** Измените `TREE_DEPTH`,
  `TREE_MAX_FOLDERS`, `TREE_MAX_FILES` (способ 2).

## Лицензия

MIT — делайте с программой что хотите, без гарантий.

---
---

# 🧹 Cleaner — Windows Cache and Junk Folder Cleanup Tool

A simple program for cleaning up temporary files and browser/app caches on
Windows. It opens in a terminal-style window, first shows what will be deleted
(as a folder tree with full paths and sizes), asks for confirmation, and only
then deletes.

📄 **Source code:** [source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py) —
open it and check for yourself exactly what the program does.

## 🛑 Read before running

- **Always check where the paths lead.** Before deleting, the program prints
  the list of folders and files. Read it completely, especially if you added
  your own paths. If you see anything unfamiliar or important, answer `n`
  (or just press Enter) and nothing will be deleted.
- **Do not add folders that hold program data.** Only clean what is definitely
  cache or temporary files. For example, `C:\Users\<name>\AppData\Local\Packages`
  stores Microsoft Store app data (settings, logins), and it must not be
  cleaned as a whole.
- **Do not run as administrator.** Administrator rights are not needed: the
  program only cleans folders in your regular user profile. With elevated
  rights it has wider access to files, and the profile may resolve to the
  wrong one (for example, another account's profile). For that reason the
  program refuses to run as administrator and shows a message. Launch it with
  a normal double click.
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
itself to startup, and only touches the listed folders in your own
profile. You can read the code here:
[source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py).
If you don't trust the prebuilt exe, run `source code.py` with Python or build
the exe yourself (see Method 2) and scan your own build on VirusTotal.

## What it cleans by default

Only cache folders and temporary files. Passwords, cookies, history,
bookmarks, extensions, and sessions are not touched.

- **Chromium-based browsers** — Chrome, Edge, Brave, Vivaldi: page cache,
  compiled code cache, graphics cache (including the browser's shader cache),
  and `Service Worker\CacheStorage`. Profiles (`Default`, `Profile 1`,
  `Profile 2`...) are detected automatically. Also Opera and Opera GX cache.
- **Firefox** — `cache2` and `startupCache` of all profiles (the profile
  folder is found automatically).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, error reports (WER).
- **Development** — pip, uv, npm, Yarn, NuGet caches and VS Code caches
  (`Cache`, `CachedData`, `CachedExtensionVSIXs`, `Code Cache`, `GPUCache`).
- **Apps** — Discord, Slack, and Steam's built-in browser cache, plus the
  Unsloth Studio cache (`.unsloth\studio\cache` in your profile folder).

Two extra switches at the top of `source code.py`. They are off in `Cleaner.exe`
and on in `CleanerNoGames.exe`:
- `CLEAN_SHADER_CACHES` — NVIDIA/AMD/Intel/D3D shader caches. Safe to delete,
  but games have to recompile shaders afterwards, and the first launch can
  take a very long time.
- `CLEAN_DOT_CACHE` — the `.cache` folder in your profile. It often holds
  downloaded models (for example, huggingface) that will be downloaded again.

Folders that don't exist on your computer are skipped automatically. The full
list of paths is at the top of
[source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py).

## How to use it and read the list before deletion

1. Run the program (**not as administrator**). It scans the folders and builds
   the list.
2. Read the list. It is shown as a tree:
   - **Two blocks.** First "YOUR FOLDERS (from CUSTOM_PATHS)" — the ones you
     added yourself, in the order you wrote them. Then "MAIN FOLDERS" — the
     built-in paths, heaviest on top.
   - **A main folder** is shown as a line with its full path and total size.
     The note "папка останется, внутри чистится" (the folder stays, its
     contents are cleaned) means the folder itself is not deleted, only its
     contents are.
   - **Inside a folder**, subfolders (with sizes) come first, then files. A file
     never appears above a folder, even if it is heavier.
   - **The red "← УДАЛИТСЯ" label** (WILL BE DELETED) marks an item that will be
     deleted. **Gray** shows what lies inside a folder being deleted (it goes
     away together with it).
   - **"… ещё файлов: 95, 45.42 MB"** (95 more files) is a collapsed line: the
     heaviest items are shown, the rest are merged into one line with their
     total size.
   - **"[внутри ещё, свёрнуто]"** (more inside, collapsed) means content deeper
     than the configured expansion level.
3. At the bottom the program prints "Найдено объектов" (objects found) and
   "Общий размер (на удаление)" (total size to delete). Only items marked
   "← УДАЛИТСЯ" are counted.
4. Answer the prompt: `y` / `yes` / `д` / `да` to delete; anything else
   (including just Enter) cancels.
5. After deletion a summary is printed: how much was fully deleted, partially
   deleted, skipped (in use by processes), and how much space was freed. The
   figure is the total size of the deleted files, so the free space shown in
   Explorer may grow slightly less.

## Features

- Terminal-style window: colored output, mouse wheel scrolling, a draggable
  scrollbar on the right, fast scrolling with the held middle mouse button,
  and a resizable window — text wraps automatically.
- **Text selection and copying:** select text with the left mouse button
  (dragging the selection past the top or bottom edge scrolls the list
  automatically). `Ctrl+C` copies the selection, `Ctrl+A` selects and copies
  the whole window text. The shortcuts work with a Russian keyboard layout too.
  Long paths are copied as whole lines, without breaks from the visual wrapping.
  Cyrillic and special characters paste into other programs without garbling.
  After copying, a hint like "Скопировано: N строк" (copied N lines) appears in
  the corner of the window.
- **Tree preview before deletion:** main folders are expanded, so you can see
  the path, size, what will be deleted and what will stay (see above).
- **Your own folders:** a separate `CUSTOM_PATHS` list for your paths
  (Method 2), with folder-in-folder search.
- **Colored window border (Windows 11):** when the window is active, the border
  and title bar are green; when you switch to another window, they are red.
  On Windows 10 the border stays default, which is not an error.
- Protection against system folders: even with a typo in the path list,
  the script won't touch `C:\Windows`, `C:\Program Files`, drive roots,
  or other users' profiles.
- Links and junctions inside folders are not expanded, so the program will not
  delete the contents of another folder they point to.
- The same item is never counted twice, even if your paths overlap with the
  built-in ones.
- Refuses to run as administrator (see the warning above).
- Files locked by another process don't cause a crash — they're simply
  skipped.
- Automatically clears the read-only attribute before deletion (a common
  cause of failures in browser caches).

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

Run the one you chose (**not as administrator**), check the list, and confirm
the deletion. Nothing to install: Python and the libraries are already inside
the exe.

**Limitation**: the list of folders in the prebuilt exe files is fixed and
**cannot be edited**. To clean other folders or change settings, use Method 2.

## Method 2: your own .py file with editable paths and settings

### Install and run

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Download
   [source code.py](https://github.com/ZeroMiko2004/Cleaner/blob/main/source%20code.py)
   (on the file page click **Download raw file**) or download the whole
   repository. If you want your own window icon, put `icon.ico` in the same
   folder.
3. **Required:** install the libraries, the code won't run without them (one
   command in a terminal):
   ```
   pip install pygame
   pip install rich
   ```
   `pygame` draws the program window, `rich` handles the colored output.
4. Run it in a regular terminal window (**not as administrator**) from the
   folder where the file is located:
   ```
   python "source code.py"
   ```

### How to add your own folders (the CUSTOM_PATHS list)

Add your own paths **only to the `CUSTOM_PATHS` list** (the "MY PATHS" section
in the file), not to the built-in `PATHS`. That way your folders are always
shown first in their own block.

1. Open the folder in Explorer, click the address bar and press `Ctrl+C`
   (or `Shift` + right-click the folder → "Copy as path").
2. Open `source code.py` in any editor, find `CUSTOM_PATHS` and add a line
   between the "ВПИСЫВАЙТЕ СВОИ ПУТИ НИЖЕ / ВЫШЕ ЭТОЙ ЛИНИИ" (write your paths
   below / above this line) markers:
   ```python
   CUSTOM_PATHS = [
       r"D:\Games\SomeGame\Cache",
       r"C:\Users\Name\My junk",
       # r"D:\Old",   # a line with # is turned off
   ]
   ```
3. Writing rules:
   - the letter `r` before the opening quote is required, otherwise Python
     breaks the backslashes;
   - the path goes between the quotes (don't duplicate the quotes Explorer
     adds);
   - no trailing backslash `\` at the end of the path;
   - a comma is needed at the end of the line;
   - a line starting with `#` is a comment and is turned off.
4. You can also use:
   - an asterisk `*` as "any name": `r"D:\Games\*\Cache"` — the `Cache` folder
     in all subfolders of `D:\Games`;
   - Windows variables: `r"%LOCALAPPDATA%\Temp"`.
5. Good to know:
   - the folder's **contents** are deleted, the folder itself stays;
   - if a path doesn't exist, the program silently skips it — check for typos
     if your folder is missing from the list;
   - if a folder is empty, there is nothing to delete and it won't appear in
     the list;
   - protection stays in force: the program won't touch system folders or other
     users' profiles, and such paths are shown in the "Заблокированы" (blocked)
     warning.

### Folder-in-folder search (CUSTOM_SCAN_DEPTH)

The `CUSTOM_SCAN_DEPTH` number (next to the `CUSTOM_PATHS` list) sets how many
levels deep the program goes into your folders:

- `1` — everything lying directly in the folder is deleted (subfolders as a
  whole);
- `2` — the program enters each subfolder and deletes what is **inside** it; the
  first-level subfolders themselves stay, empty;
- `3` and more — the same, but deeper.

Files that lie above the target level are deleted as usual. This setting only
applies to paths from `CUSTOM_PATHS`; built-in paths work as usual (everything
lying directly inside them is deleted).

### Other settings at the top of the file

- `CLEAN_SHADER_CACHES` and `CLEAN_DOT_CACHE` (`True` — clean, `False` — leave
  alone). In the file they are `False`, like in `Cleaner.exe`; for a version like
  `CleanerNoGames.exe` set them to `True`.
- List appearance (affects only what is displayed, not what is deleted):
  - `TREE_DEPTH = 3` — how many levels of nested folders to expand;
  - `TREE_MAX_FOLDERS = 10` — how many folders to show inside one folder;
  - `TREE_MAX_FILES = 5` — how many files to show inside one folder.

  The rest is collapsed into a "… ещё N" (N more) line. Raise the numbers for a
  more detailed but longer list.
- Window colors (Windows 11); colors are `(R, G, B)` from 0 to 255:
  - `CHANGE_BORDER_COLOR`, `BORDER_COLOR_ACTIVE`, `BORDER_COLOR_INACTIVE` —
    border;
  - `CHANGE_TITLEBAR_COLOR`, `TITLEBAR_COLOR_ACTIVE`, `TITLEBAR_COLOR_INACTIVE`,
    `TITLEBAR_TEXT_COLOR` — window title bar;
  - to turn it off, set `CHANGE_BORDER_COLOR` or `CHANGE_TITLEBAR_COLOR` to
    `False`.
- The built-in `PATHS` list: to remove a path, put `#` in front of the line.
  `LOCAL` is the current user's `AppData\Local`, `ROAMING` is
  `AppData\Roaming` (filled in automatically). A new Chromium-based browser is
  added with one line in the `CHROMIUM_BROWSERS` list.

### Build your own .exe (optional)

To run without Python, build an exe. The `pygame` and `rich` libraries from the
install step must be installed before building, otherwise they won't end up in
the exe:
```
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name Cleaner "source code.py"
```
`--windowed` is needed because the program has its own window and a black
console next to it isn't wanted. The result appears at `dist\Cleaner.exe`. The
`--icon` flag sets the icon of the exe file itself; the window icon is taken
from `icon.ico` placed next to the exe. If you have no icon, remove
`--icon=icon.ico` from the command.

## FAQ

- **My folder is not in the list.** Check that the path is written correctly
  (with `r` before the quotes, no trailing backslash), that the folder exists
  and that there is something to delete in it. Blocked system paths are printed
  in the warning above the list.
- **`Ctrl+C` / `Ctrl+A` don't work.** Click inside the program window first.
  The shortcuts work with a Russian layout too.
- **The window border doesn't change color.** This feature works only on
  Windows 11. On Windows 10 the window stays default.
- **The list is too long or too short.** Change `TREE_DEPTH`,
  `TREE_MAX_FOLDERS`, `TREE_MAX_FILES` (Method 2).

## License

MIT — do whatever you want with it, no warranty.
