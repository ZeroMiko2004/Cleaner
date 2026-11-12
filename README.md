# 🧹 Cleaner — очистка кэшей и мусорных папок Windows

**Русский** · [English]

Простая программа для очистки временных файлов, кэшей браузеров и программ в Windows.
Открывается в окне, похожем на терминал, сначала показывает, что будет удалено (в виде дерева папок с полными путями и весом), спрашивает подтверждение и только потом удаляет.

📄 **Исходный код** лежит в релизе **Source Code.rar**: откройте и проверьте сами, что именно делает программа.

## 🚀 Быстрый старт

1. Скачайте **Cleaner.rar** из раздела **Releases**. Архивы `.rar` открываются через WinRAR или 7-Zip.
2. Распакуйте архив **целиком** в обычную папку, например на рабочий стол или в «Документы». Не распаковывайте в `Program Files`: программа хранит свои настройки рядом с собой.
3. Запустите `Cleaner.exe` из распакованной папки обычным двойным кликом, **не от имени администратора**. Не копируйте один exe отдельно: рядом лежат нужные ему файлы.
4. Прочитайте список путей и подтвердите удаление. Python и библиотеки устанавливать не нужно.

## 🛑 Прочитайте перед запуском

- **Обязательно проверяйте, куда ведут пути.** Перед удалением программа выводит список папок и файлов. Прочитайте его целиком, особенно если вы добавляли свои пути. Увидели что-то незнакомое или важное — не подтверждайте удаление, и ничего не будет удалено.
- **Не добавляйте папки с данными программ.** Чистите только то, что точно является кэшем или временными файлами. Например, папка `C:\Users\<имя>\AppData\Local\Packages` хранит данные приложений Microsoft Store (настройки, логины), и её целиком чистить нельзя.
- **Не запускайте от имени администратора.** Права администратора не нужны: программа чистит только папки вашего обычного профиля. С повышенными правами у неё шире доступ к файлам, а профиль может определиться не тот. Поэтому программа сама откажется работать от имени администратора и покажет сообщение.
- **Закройте браузеры и приложения, кэш которых чистите.** Занятые файлы пропускаются, и очистка получится неполной. После очистки первый запуск этих программ может быть чуть медленнее: кэш создаётся заново.
- **Программа проверялась только на моём компьютере.** На других системах и конфигурациях Windows она не тестировалась, поведение может отличаться.
- **Никаких гарантий и никакой ответственности.** Вы используете программу на свой страх и риск. Автор не отвечает за потерянные данные, удалённые файлы и любой другой ущерб (см. лицензию MIT).
- Удаление **безвозвратное**, мимо корзины.
- Программа написана под **Windows**. На других ОС не запускалась и не рассчитана на них.

## ⚠️ Про ложные срабатывания антивирусов

Некоторые антивирусы (Microsoft Defender, Avast, Cynet и др.) могут помечать `.exe` из архива **Cleaner.rar** как подозрительные или даже как троян (детекты вида `Wacatac` / `MalwareX`). Это **generic-эвристика**, а не реальный вредоносный код: антивирусы реагируют на признаки самого файла — упаковка cx_Freeze, отсутствие цифровой подписи издателя и массовое удаление файлов. Именно так выглядят и вредоносные «wiper»-программы.

Исходный код открыт специально, чтобы вы могли убедиться сами: программа не лезет в сеть, не пишет в реестр, не добавляет себя в автозагрузку и не трогает ничего, кроме папок кэша в вашем профиле и собственных файлов настроек рядом с программой.

Что можно сделать, если сомневаетесь:

- Сверьте **SHA-256** скачанного архива с тем, что указан в Releases рядом с файлом.
- Проверьте архив на [VirusTotal](https://www.virustotal.com).
- Не доверяете готовому `.exe`? Скачайте **Source Code.rar**, соберите программу сами (см. раздел «Сборка из исходного кода») и проверьте свою сборку на VirusTotal.

## Что чистит

Только папки кэша и временные файлы. Пароли, куки, история, закладки, расширения и сессии не затрагиваются.

- **Браузеры на движке Chromium** — Chrome, Edge, Brave, Vivaldi, Opera и др.: кэш страниц, скомпилированного кода, графики и `Service Worker\CacheStorage`. Профили (`Default`, `Profile 1`, `Profile 2`...) находятся автоматически.
- **Firefox** — кэш всех профилей (папка профиля ищется автоматически).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, отчёты об ошибках (WER).
- **Разработка** — кэши pip, uv, npm, Yarn, NuGet и VS Code.
- **Приложения** — кэш Discord, Slack, встроенного браузера Steam и других программ.

**По умолчанию** программа чистит только тот набор путей, который заложен в неё. Если нужно найти что-то ещё, есть отдельная функция **поиска папок с кэшем**: найденные папки не удаляются автоматически, вы сами выбираете, добавлять ли их к очистке. Если поиск не нужен, работайте только со штатным списком.

Дополнительно, **по желанию**, можно включить:

- чистку шейдерных кэшей видеокарты (NVIDIA/AMD/Intel/D3D). Удаление безопасно, но игры потом заново компилируют шейдеры, и первый запуск может идти очень долго;
- чистку папки `.cache` в профиле. Там часто лежат скачанные модели (например, huggingface), после удаления они скачиваются заново.

Если вы играете, эти два пункта лучше не включать.

Папки, которых нет на вашем компьютере, программа пропускает сама. Полный список путей и настроек находится в начале файла с исходным кодом.

## Как читать список перед удалением

1. Запустите программу (**не от имени администратора**). Она просканирует папки и построит список.
2. Прочитайте список. Он показывается в виде дерева:
   - **Основная папка** показана строкой с полным путём и общим весом. Пометка «папка останется, внутри чистится» означает, что сама папка не удаляется, чистится только её содержимое.
   - **Внутри папки** сначала идут подпапки с весом, потом файлы. Файл никогда не стоит выше папки, даже если он тяжелее.
   - **Красная метка «← УДАЛИТСЯ»** — этот объект будет удалён. **Серым** показано то, что лежит внутри удаляемой папки (оно исчезнет вместе с ней).
   - **«… ещё файлов: 95, 45.42 MB»** — свёрнутые элементы: показываются самые тяжёлые, остальные собраны в одну строку с общим весом.
   - **«[внутри ещё, свёрнуто]»** — содержимое глубже заданного уровня раскрытия.
3. Внизу программа пишет количество найденных объектов и общий размер на удаление. Считаются только объекты с пометкой «← УДАЛИТСЯ».
4. Подтвердите удаление (например, `y` / `yes` / `д` / `да`). Удаление начинается только после явного подтверждения.
5. После удаления выводится статистика: сколько удалено полностью, частично, сколько пропущено (занято процессами) и сколько места освобождено. Цифра считается по размеру удалённых файлов, поэтому свободное место в проводнике может вырасти чуть меньше.

## Возможности

- **Окно в виде терминала:** цветной вывод, прокрутка колесом мыши, перетаскиваемый ползунок справа, быстрая прокрутка зажатой средней кнопкой. Размер окна можно менять, текст переносится автоматически.
- **Выделение и копирование текста:** выделяйте текст левой кнопкой мыши (если дотянуть выделение до верхнего или нижнего края окна, список прокручивается сам). `Ctrl+C` копирует выделенное, `Ctrl+A` выделяет и копирует весь текст окна. Сочетания работают и при русской раскладке. Длинные пути копируются целыми строками, без разрывов от визуального переноса.
- **Предпросмотр-дерево перед удалением:** видно путь, вес, что удалится и что останется.
- **Поиск папок с кэшем** (см. выше): найденное добавляется к очистке только по вашему выбору.
- **Свои папки:** можно добавить собственные пути для очистки.
- **Цветная рамка окна (Windows 11):** когда окно активно, рамка и заголовок зелёные, когда вы переключились на другое окно — красные. На Windows 10 рамка остаётся обычной, это не ошибка.
- **Защита от системных папок:** даже при опечатке в списке путей программа не тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили пользователей.
- **Ссылки и junction** внутри папок не раскрываются, поэтому программа не удалит содержимое чужой папки, на которую они указывают.
- Один и тот же объект не считается дважды, даже если пути пересекаются.
- Занятые процессом файлы не вызывают падение, они просто пропускаются.
- Атрибут read-only снимается автоматически перед удалением.
- Отказ работать от имени администратора (см. предупреждение выше).

Набор дополнительных настроек (свои папки, исключения, необязательные пункты очистки и др.) может отличаться от версии к версии. Подробности смотрите в комментариях в начале файла с исходным кодом и в подсказках внутри самой программы.

## 🗂 Файлы настроек

При первом запуске программа создаёт рядом с собой несколько файлов (поэтому не кладите её в папку, куда у вас нет прав записи):

- `Cleaner_условия.txt` — условия очистки;
- `Cleaner_свои_пути.txt` — ваши собственные папки;
- `Cleaner_чёрный_список.txt` — исключения;
- `Cleaner_окно.json` — размер и положение окна.

Внутри текстовых файлов есть подсказки. Правьте их в Блокноте и сохраняйте: новые настройки применятся при следующем запуске (или по команде `ф` в программе).

## 📥 Что скачивать

В разделе **Releases** лежат два архива:

1. **Cleaner.rar** — готовая программа.
   Скачивайте **первым**, если хотите просто запустить Cleaner. Внутри уже собранная программа, Python и библиотеки отдельно устанавливать не нужно.
2. **Source Code.rar** — исходный код.
   Для тех, кто хочет проверить код, изменить настройки или собрать программу самостоятельно. Внутри есть `build_exe.bat` для сборки через cx_Freeze.

## 🔧 Сборка из исходного кода

1. Скачайте **Source Code.rar** из Releases и распакуйте архив.
2. **Запуск без сборки:** нужен Python 3.10+ и две библиотеки:
   ```
   pip install pygame-ce rich
   python Cleaner.py
   ```
3. **Сборка программы:** при установке Python включите лаунчер `py`, затем запустите `build_exe.bat`. Нужен интернет. Скрипт сам создаёт чистое окружение `.venv_build`, ставит в него только то, что нужно для сборки (`cx_Freeze`, `pygame-ce`, `rich`, `pillow`), и собирает программу через cx_Freeze по настройкам из `setup_cx.py`.
4. Готовая программа появится в папке `dist\Cleaner`. Чтобы перенести её на другой ПК, копируйте папку **целиком**, а не один exe.

## Лицензия

MIT — делайте с программой что хотите, без гарантий.

# 🧹 Cleaner — cleaning caches and junk folders in Windows

[Русский] · **English**

A simple program for cleaning temporary files, browser caches, and program caches in Windows.
It opens in a terminal-like window, first shows what will be deleted (as a folder tree with full paths and sizes), asks for confirmation, and only then deletes.

📄 **The source code** is in the **Source Code.rar** release: open it and check for yourself exactly what the program does.

## 🚀 Quick start

1. Download **Cleaner.rar** from the **Releases** section. `.rar` archives can be opened with WinRAR or 7-Zip.
2. Extract the archive **completely** into a regular folder, for example on your Desktop or in Documents. Do not extract into `Program Files`: the program stores its settings next to itself.
3. Run `Cleaner.exe` from the extracted folder by normal double-click, **not as administrator**. Do not copy just the exe by itself: the files it needs are next to it.
4. Read the list of paths and confirm deletion. You do not need to install Python or libraries.

## 🛑 Read before launching

- **Always check where the paths lead.** Before deletion, the program displays a list of folders and files. Read it in full, especially if you added your own paths. If you see something unfamiliar or important, do not confirm deletion, and nothing will be deleted.
- **Do not add folders containing program data.** Clean only what is definitely cache or temporary files. For example, the folder `C:\Users\<name>\AppData\Local\Packages` stores Microsoft Store app data (settings, logins), and it must not be cleaned entirely.
- **Do not run as administrator.** Administrator rights are not needed: the program only cleans folders in your regular user profile. With elevated rights it has broader access to files, and the wrong profile may be detected. Therefore the program will refuse to run as administrator and show a message.
- **Close the browsers and applications whose cache you are cleaning.** In-use files are skipped, and the cleanup will be incomplete. After cleanup, the first launch of these programs may be slightly slower: the cache is recreated.
- **The program has only been tested on my computer.** It has not been tested on other systems and Windows configurations; behavior may differ.
- **No guarantees and no liability.** You use the program at your own risk. The author is not responsible for lost data, deleted files, or any other damage (see the MIT license).
- Deletion is **permanent**, bypassing the Recycle Bin.
- The program is written for **Windows**. It has not been run on other OSes and is not intended for them.

## ⚠️ About antivirus false positives

Some antiviruses (Microsoft Defender, Avast, Cynet, etc.) may flag the `.exe` from **Cleaner.rar** as suspicious or even as a Trojan (detections such as `Wacatac` / `MalwareX`). This is a **generic heuristic**, not real malicious code: antiviruses react to characteristics of the file itself — cx_Freeze packaging, absence of a publisher's digital signature, and mass file deletion. That is exactly what malicious "wiper" programs look like too.

The source code is open specifically so you can verify for yourself: the program does not access the network, does not write to the registry, does not add itself to startup, and does not touch anything except cache folders in your profile and its own settings files next to the program.

What you can do if you are unsure:

- Compare the **SHA-256** of the downloaded archive with the one listed in Releases next to the file.
- Check the archive on [VirusTotal](https://www.virustotal.com).
- Do not trust the ready-made `.exe`? Download **Source Code.rar**, build the program yourself (see the "Building from source code" section), and check your build on VirusTotal.

## What it cleans

Only cache folders and temporary files. Passwords, cookies, history, bookmarks, extensions, and sessions are not affected.

- **Chromium-based browsers** — Chrome, Edge, Brave, Vivaldi, Opera, etc.: page cache, compiled code cache, graphics cache, and `Service Worker\CacheStorage`. Profiles (`Default`, `Profile 1`, `Profile 2`...) are found automatically.
- **Firefox** — cache of all profiles (the profile folder is found automatically).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, error reports (WER).
- **Development** — caches for pip, uv, npm, Yarn, NuGet, and VS Code.
- **Applications** — cache of Discord, Slack, Steam's built-in browser, and other programs.

**By default**, the program cleans only the set of paths built into it. If you need to find something else, there is a separate **cache folder search** function: found folders are not deleted automatically; you decide whether to add them to cleanup. If you do not need the search, work only with the standard list.

Additionally, **optionally**, you can enable:

- cleaning GPU shader caches (NVIDIA/AMD/Intel/D3D). Deletion is safe, but games will then recompile shaders, and the first launch may take a very long time;
- cleaning the `.cache` folder in the profile. It often contains downloaded models (for example, huggingface); after deletion they will be downloaded again.

If you play games, it is better not to enable these two items.

Folders that do not exist on your computer are skipped by the program automatically. The full list of paths and settings is at the beginning of the source code file.

## How to read the list before deletion

1. Run the program (**not as administrator**). It will scan the folders and build the list.
2. Read the list. It is shown as a tree:
   - **The main folder** is shown as a line with the full path and total size. The note "folder will remain, contents are cleaned" means that the folder itself is not deleted; only its contents are cleaned.
   - **Inside the folder**, subfolders with their sizes come first, then files. A file never appears above a folder, even if it is larger.
   - The **red label “← WILL BE DELETED”** means this object will be deleted. **Gray** shows what is inside a folder being deleted (it will disappear together with it).
   - **“… more files: 95, 45.42 MB”** — collapsed items: the heaviest are shown, the rest are collected into one line with the total size.
   - **“[more inside, collapsed]”** — content deeper than the specified expansion level.
3. At the bottom, the program reports the number of objects found and the total size to be deleted. Only objects marked “← WILL BE DELETED” are counted.
4. Confirm deletion (for example, `y` / `yes` / `д` / `да`). Deletion starts only after explicit confirmation.
5. After deletion, statistics are displayed: how many were deleted fully, partially, how many were skipped (in use by processes), and how much space was freed. The figure is calculated from the size of deleted files, so free space in File Explorer may increase slightly less.

## Features

- **Terminal-like window:** color output, mouse wheel scrolling, draggable slider on the right, fast scrolling while holding the middle mouse button. The window can be resized; text wraps automatically.
- **Selecting and copying text:** select text with the left mouse button (if you drag the selection to the top or bottom edge of the window, the list scrolls automatically). `Ctrl+C` copies the selection, `Ctrl+A` selects and copies all text in the window. The shortcuts also work with the Russian keyboard layout. Long paths are copied as whole lines, without breaks caused by visual wrapping.
- **Preview tree before deletion:** you can see the path, size, what will be deleted, and what will remain.
- **Cache folder search** (see above): found items are added to cleanup only at your choice.
- **Your own folders:** you can add your own paths for cleaning.
- **Colored window border (Windows 11):** when the window is active, the border and title bar are green; when you switch to another window, they are red. On Windows 10 the border remains normal; this is not a bug.
- **Protection against system folders:** even with a typo in the path list, the program will not touch `C:\Windows`, `C:\Program Files`, drive roots, or other users' profiles.
- **Links and junctions** inside folders are not expanded, so the program will not delete the contents of another folder they point to.
- The same object is not counted twice, even if paths overlap.
- Files locked by a process do not cause a crash; they are simply skipped.
- The read-only attribute is removed automatically before deletion.
- Refusal to run as administrator (see the warning above).

The set of additional settings (your own folders, exclusions, optional cleanup items, etc.) may differ from version to version. For details, see the comments at the beginning of the source code file and the hints inside the program itself.

## 🗂 Settings files

On first launch, the program creates several files next to itself (so do not put it in a folder where you do not have write permissions):

- `Cleaner_условия.txt` — cleanup conditions;
- `Cleaner_свои_пути.txt` — your own folders;
- `Cleaner_чёрный_список.txt` — exclusions;
- `Cleaner_окно.json` — window size and position.

The text files contain hints. Edit them in Notepad and save: the new settings will be applied on the next launch (or by the `ф` command in the program).

## 📥 What to download

In the **Releases** section there are two archives:

1. **Cleaner.rar** — the ready-to-use program.
   Download it **first** if you just want to run Cleaner. It contains the already built program; Python and libraries do not need to be installed separately.
2. **Source Code.rar** — the source code.
   For those who want to check the code, change settings, or build the program themselves. It contains `build_exe.bat` for building via cx_Freeze.

## 🔧 Building from source code

1. Download **Source Code.rar** from Releases and extract the archive.
2. **Running without building:** requires Python 3.10+ and two libraries:
   ```
   pip install pygame-ce rich
   python Cleaner.py
   ```
3. **Building the program:** when installing Python, enable the `py` launcher, then run `build_exe.bat`. An internet connection is required. The script itself creates a clean environment `.venv_build`, installs only what is needed for building (`cx_Freeze`, `pygame-ce`, `rich`, `pillow`), and builds the program via cx_Freeze using the settings from `setup_cx.py`.
4. The built program will appear in the `dist\Cleaner` folder. To transfer it to another PC, copy the **entire** folder, not just one exe.

## License

MIT — do whatever you want with the program, with no warranties.
