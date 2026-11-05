# 🧹 Cleaner — очистка кэшей и мусорных папок Windows

Простая программа для очистки временных файлов, кэшей браузеров и программ на Windows.
Открывается в окне, похожем на терминал, сначала показывает, что будет удалено
(в виде дерева папок с полными путями и весом), спрашивает подтверждение и только потом удаляет.

📄 **Исходный код** лежит в этом репозитории — откройте и проверьте сами, что именно делает программа.

## 🛑 Прочитайте перед запуском

- **Обязательно проверяйте, куда ведут пути.** Перед удалением программа выводит
  список папок и файлов. Прочитайте его целиком, особенно если вы добавляли
  свои пути. Увидели что-то незнакомое или важное — не подтверждайте удаление,
  и ничего не будет удалено.
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

Исходный код открыт специально, чтобы вы могли убедиться сами: программа не лезет
в сеть, не пишет в реестр, не добавляет себя в автозагрузку и не трогает ничего,
кроме папок кэша в вашем профиле и собственных файлов настроек рядом с программой.
Если не доверяете готовому exe — запустите исходный код через Python или соберите
exe самостоятельно (см. способ 2) и проверьте свою сборку на VirusTotal.

## Что чистит

Только папки кэша и временные файлы. Пароли, куки, история, закладки, расширения
и сессии не затрагиваются.

- **Браузеры на движке Chromium** — Chrome, Edge, Brave, Vivaldi, Opera и др.: кэш страниц,
  скомпилированного кода, графики и `Service Worker\CacheStorage`. Профили
  (`Default`, `Profile 1`, `Profile 2`...) находятся автоматически.
- **Firefox** — кэш всех профилей (папка профиля ищется автоматически).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, отчёты об ошибках (WER).
- **Разработка** — кэши pip, uv, npm, Yarn, NuGet и VS Code.
- **Приложения** — кэш Discord, Slack, встроенного браузера Steam и других программ.

Дополнительно, **по желанию**, можно включить:
- чистку шейдерных кэшей видеокарты (NVIDIA/AMD/Intel/D3D). Удаление безопасно,
  но игры потом заново компилируют шейдеры, и первый запуск может идти очень долго;
- чистку папки `.cache` в профиле. Там часто лежат скачанные модели
  (например, huggingface), после удаления они скачиваются заново.

Если вы играете, эти два пункта лучше не включать.

Папки, которых нет на вашем компьютере, программа пропускает сама. Полный
список путей и настроек находится в начале файла с исходным кодом.

## Как читать список перед удалением

1. Запустите программу (**не от имени администратора**). Она просканирует папки
   и построит список.
2. Прочитайте список. Он показывается в виде дерева:
   - **Основная папка** показана строкой с полным путём и общим весом. Пометка
     «папка останется, внутри чистится» означает, что сама папка не удаляется,
     чистится только её содержимое.
   - **Внутри папки** сначала идут подпапки с весом, потом файлы. Файл никогда не
     стоит выше папки, даже если он тяжелее.
   - **Красная метка «← УДАЛИТСЯ»** — этот объект будет удалён. **Серым** показано
     то, что лежит внутри удаляемой папки (оно исчезнет вместе с ней).
   - **«… ещё файлов: 95, 45.42 MB»** — свёрнутые элементы: показываются самые
     тяжёлые, остальные собраны в одну строку с общим весом.
   - **«[внутри ещё, свёрнуто]»** — содержимое глубже заданного уровня раскрытия.
3. Внизу программа пишет количество найденных объектов и общий размер на
   удаление — считаются только объекты с пометкой «← УДАЛИТСЯ».
4. Подтвердите удаление (например, `y` / `yes` / `д` / `да`). Удаление начинается
   только после явного подтверждения.
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
  целыми строками, без разрывов от визуального переноса.
- **Предпросмотр-дерево перед удалением:** видно путь, вес, что удалится и что останется.
- **Свои папки:** можно добавить собственные пути для очистки.
- **Цветная рамка окна (Windows 11):** когда окно активно, рамка и заголовок
  зелёные; когда вы переключились на другое окно — красные. На Windows 10
  рамка остаётся обычной, это не ошибка.
- Защита от системных папок: даже при опечатке в списке путей программа не
  тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили
  пользователей.
- Ссылки и junction внутри папок не раскрываются, поэтому программа не удалит
  содержимое чужой папки, на которую они указывают.
- Один и тот же объект не считается дважды, даже если пути пересекаются.
- Отказ работать от имени администратора (см. предупреждение выше).
- Занятые процессом файлы не вызывают падение — просто пропускаются.
- Автоматическое снятие атрибута read-only перед удалением (частая
  причина сбоев в кэшах браузеров).

Набор дополнительных настроек (свои папки, исключения, необязательные пункты
очистки и др.) зависит от версии программы. Подробности смотрите в комментариях
в начале файла с исходным кодом и в подсказках внутри самой программы.

## Способ 1: скачать готовый .exe

Готовые сборки лежат в разделе [Releases](../../releases). Скачайте файл,
запустите его (**не от имени администратора**), проверьте список и подтвердите
удаление. Ничего устанавливать не нужно: Python и библиотеки уже внутри exe.

Описание каждой сборки смотрите на странице релиза. Набор настроек в готовом
exe зафиксирован. Если хотите менять список папок или настройки, используйте
способ 2.

## Способ 2: запуск из исходного кода

1. Установите [Python 3.10+](https://www.python.org/downloads/).
2. Скачайте файлы из репозитория (кнопка **Code → Download ZIP**) или нужный
   `.py`-файл целиком. Если хотите свою иконку окна, положите `icon.ico` в ту же папку.
3. Установите библиотеки (одна команда в терминале):
   ```
   pip install pygame-ce rich
   ```
   `pygame-ce` рисует окно программы, `rich` отвечает за цветной вывод.
4. Запустите в обычном окне терминала (**не от имени администратора**) из папки,
   где лежит файл:
   ```
   python Cleaner.py
   ```

### Как добавить свои папки

Свои пути добавляются либо в программе, либо в разделе пользовательских
настроек в начале файла с исходным кодом (зависит от версии).

1. Откройте нужную папку в Проводнике, кликните в адресную строку и нажмите
   `Ctrl+C` (или `Shift` + правая кнопка по папке → «Копировать как путь»).
2. Добавьте путь туда, где задаются свои папки. Если путь вписывается в `.py`-файл:
   ```python
   r"D:\Games\SomeGame\Cache",
   r"C:\Users\Имя\Мой мусор",
   # r"D:\Старое",   # строка с # выключена
   ```
3. Правила записи:
   - перед первой кавычкой обязательно буква `r`, иначе Python сломает
     обратные слэши;
   - путь пишется между кавычками (кавычки из Проводника дублировать не нужно);
   - слэш `\` в конце пути не ставьте;
   - в конце строки нужна запятая;
   - строка, начинающаяся с `#`, — комментарий, она выключена.
4. Дополнительно можно использовать:
   - звёздочку `*` как «любое имя»: `r"D:\Games\*\Cache"`;
   - переменные Windows: `r"%LOCALAPPDATA%\Temp"`.
5. Что важно знать:
   - удаляется **содержимое** папки, сама папка остаётся;
   - если путь не существует, программа молча его пропускает — проверьте
     опечатки, если вашей папки нет в списке;
   - если папка пустая, ей нечего удалять, и в списке её не будет;
   - защита остаётся в силе: системные папки и чужие профили программа не тронет,
     такие пути будут показаны в предупреждении.

### Сборка своего .exe (необязательно)

Чтобы запускать без Python, соберите exe. Библиотеки из установки должны быть
поставлены до сборки, иначе они не попадут в exe:
```
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=icon.ico --name Cleaner Cleaner.py
```
`--noconsole` нужен, потому что у программы своё окно и чёрная консоль рядом не
нужна. Готовый файл появится в `dist\Cleaner.exe`. Иконка окна берётся из
`icon.ico`, который лежит рядом с exe. Без иконки уберите `--icon=icon.ico`
из команды.

## Частые вопросы

- **Моей папки нет в списке.** Проверьте, что путь записан верно, что папка
  существует и что в ней есть что удалять. Заблокированные системные пути
  выводятся в предупреждении над списком.
- **Не работает `Ctrl+C` / `Ctrl+A`.** Сначала кликните в окно программы.
  Сочетания работают и на русской раскладке.
- **Рамка окна не меняет цвет.** Эта функция работает только на Windows 11.
  На Windows 10 окно остаётся обычным.
- **Антивирус ругается на exe.** См. раздел про ложные срабатывания выше.

## Лицензия

MIT — делайте с программой что хотите, без гарантий.

---
---

# 🧹 Cleaner — Windows Cache and Junk Folder Cleanup Tool

A simple program for cleaning up temporary files and browser/app caches on
Windows. It opens in a terminal-style window, first shows what will be deleted
(as a folder tree with full paths and sizes), asks for confirmation, and only
then deletes.

📄 **The source code** is in this repository — open it and check for yourself
exactly what the program does.

## 🛑 Read before running

- **Always check where the paths lead.** Before deleting, the program prints
  the list of folders and files. Read it completely, especially if you added
  your own paths. If you see anything unfamiliar or important, do not confirm
  the deletion and nothing will be deleted.
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
program makes no network requests, doesn't touch the registry, doesn't add
itself to startup, and only touches cache folders in your own profile and its
own settings files next to the program. If you don't trust the prebuilt exe,
run the source code with Python or build the exe yourself (see Method 2) and
scan your own build on VirusTotal.

## What it cleans

Only cache folders and temporary files. Passwords, cookies, history,
bookmarks, extensions, and sessions are not touched.

- **Chromium-based browsers** — Chrome, Edge, Brave, Vivaldi, Opera, etc.: page
  cache, compiled code cache, graphics cache, and `Service Worker\CacheStorage`.
  Profiles (`Default`, `Profile 1`, `Profile 2`...) are detected automatically.
- **Firefox** — the cache of all profiles (the profile folder is found
  automatically).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, error reports (WER).
- **Development** — pip, uv, npm, Yarn, NuGet and VS Code caches.
- **Apps** — Discord, Slack, Steam's built-in browser and other programs' caches.

Optionally, you can also enable:
- cleaning GPU shader caches (NVIDIA/AMD/Intel/D3D). Safe to delete, but games
  have to recompile shaders afterwards, and the first launch can take a very
  long time;
- cleaning the `.cache` folder in your profile. It often holds downloaded
  models (for example, huggingface) that will be downloaded again.

If you play games, it is better to leave these two options off.

Folders that don't exist on your computer are skipped automatically. The full
list of paths and settings is at the top of the source code file.

## How to read the list before deletion

1. Run the program (**not as administrator**). It scans the folders and builds
   the list.
2. Read the list. It is shown as a tree:
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
3. At the bottom the program prints the number of objects found and the total
   size to delete. Only items marked "← УДАЛИТСЯ" are counted.
4. Confirm the deletion (for example, `y` / `yes` / `д` / `да`). Deletion
   starts only after explicit confirmation.
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
- **Tree preview before deletion:** you can see the path, size, what will be
  deleted and what will stay.
- **Your own folders:** you can add your own paths for cleaning.
- **Colored window border (Windows 11):** when the window is active, the border
  and title bar are green; when you switch to another window, they are red.
  On Windows 10 the border stays default, which is not an error.
- Protection against system folders: even with a typo in the path list,
  the program won't touch `C:\Windows`, `C:\Program Files`, drive roots,
  or other users' profiles.
- Links and junctions inside folders are not expanded, so the program will not
  delete the contents of another folder they point to.
- The same item is never counted twice, even if paths overlap.
- Refuses to run as administrator (see the warning above).
- Files locked by another process don't cause a crash — they're simply
  skipped.
- Automatically clears the read-only attribute before deletion (a common
  cause of failures in browser caches).

The set of additional settings (your own folders, exclusions, optional cleanup
items, etc.) depends on the program version. See the comments at the top of the
source code file and the hints inside the program itself for details.

## Method 1: download the ready-made .exe

Prebuilt files are in [Releases](../../releases). Download the file, run it
(**not as administrator**), check the list, and confirm the deletion. Nothing
to install: Python and the libraries are already inside the exe.

See the release page for the description of each build. The settings in a
prebuilt exe are fixed. To change the folder list or settings, use Method 2.

## Method 2: run from source

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Download the files from the repository (**Code → Download ZIP** button) or
   the needed `.py` file on its own. If you want your own window icon, put
   `icon.ico` in the same folder.
3. Install the libraries (one command in a terminal):
   ```
   pip install pygame-ce rich
   ```
   `pygame-ce` draws the program window, `rich` handles the colored output.
4. Run it in a regular terminal window (**not as administrator**) from the
   folder where the file is located:
   ```
   python Cleaner.py
   ```

### How to add your own folders

Your own paths are added either inside the program or in the user settings
section at the top of the source code file (depends on the version).

1. Open the folder in Explorer, click the address bar and press `Ctrl+C`
   (or `Shift` + right-click the folder → "Copy as path").
2. Add the path where your own folders are defined. If the path goes into the
   `.py` file:
   ```python
   r"D:\Games\SomeGame\Cache",
   r"C:\Users\Name\My junk",
   # r"D:\Old",   # a line with # is turned off
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
   - an asterisk `*` as "any name": `r"D:\Games\*\Cache"`;
   - Windows variables: `r"%LOCALAPPDATA%\Temp"`.
5. Good to know:
   - the folder's **contents** are deleted, the folder itself stays;
   - if a path doesn't exist, the program silently skips it — check for typos
     if your folder is missing from the list;
   - if a folder is empty, there is nothing to delete and it won't appear in
     the list;
   - protection stays in force: the program won't touch system folders or other
     users' profiles, and such paths are shown in the warning.

### Build your own .exe (optional)

To run without Python, build an exe. The libraries from the install step must
be installed before building, otherwise they won't end up in the exe:
```
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=icon.ico --name Cleaner Cleaner.py
```
`--noconsole` is needed because the program has its own window and a black
console next to it isn't wanted. The result appears at `dist\Cleaner.exe`. The
window icon is taken from `icon.ico` placed next to the exe. If you have no
icon, remove `--icon=icon.ico` from the command.

## FAQ

- **My folder is not in the list.** Check that the path is written correctly,
  that the folder exists and that there is something to delete in it. Blocked
  system paths are printed in the warning above the list.
- **`Ctrl+C` / `Ctrl+A` don't work.** Click inside the program window first.
  The shortcuts work with a Russian layout too.
- **The window border doesn't change color.** This feature works only on
  Windows 11. On Windows 10 the window stays default.
- **My antivirus flags the exe.** See the antivirus false positives section
  above.

## License

MIT — do whatever you want with it, no warranty.
