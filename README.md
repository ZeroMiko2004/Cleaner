# 🧹 Cleaner — очистка кэшей и мусорных папок Windows

Простая программа для очистки временных файлов, кэшей браузеров и программ на Windows.  
Открывается в окне, похожем на терминал, сначала показывает, что будет удалено (в виде дерева папок с полными путями и весом), спрашивает подтверждение и только потом удаляет.

📄 **Исходный код** лежит в релизе **Source Code.rar** — откройте и проверьте сами, что именно делает программа.

## 🛑 Прочитайте перед запуском

- **Обязательно проверяйте, куда ведут пути.** Перед удалением программа выводит список папок и файлов. Прочитайте его целиком, особенно если вы добавляли свои пути. Увидели что-то незнакомое или важное — не подтверждайте удаление, и ничего не будет удалено.
- **Не добавляйте папки с данными программ.** Чистите только то, что точно является кэшем или временными файлами. Например, папка `C:\Users\<имя>\AppData\Local\Packages` хранит данные приложений Microsoft Store (настройки, логины), и её целиком чистить нельзя.
- **Не запускайте от имени администратора.** Права администратора не нужны: программа чистит только папки вашего обычного профиля. С повышенными правами у неё шире доступ к файлам, а профиль может определиться не тот. Поэтому программа сама откажется работать от имени администратора и покажет сообщение. Запускайте обычным двойным кликом.
- **Программа проверялась только на моём компьютере.** На других системах и конфигурациях Windows она не тестировалась, поведение может отличаться.
- **Никаких гарантий и никакой ответственности.** Вы используете программу на свой страх и риск. Автор не отвечает за потерянные данные, удалённые файлы и любой другой ущерб (см. лицензию MIT).
- Удаление **безвозвратное**, мимо корзины.
- Написано под **Windows**. На других ОС не запускалось и не рассчитано на них.

## ⚠️ Про ложные срабатывания антивирусов

Некоторые антивирусы (Microsoft Defender, Avast, Cynet и др.) могут помечать `.exe` из архива **Cleaner.rar** как подозрительные или даже как троян (детекты вида `Wacatac` / `MalwareX`). Это **generic-эвристика**, а не реальный вредоносный код: антивирусы реагируют на признаки самого файла — упаковка cx_Freeze, отсутствие цифровой подписи издателя и массовое удаление файлов — именно так выглядят и вредоносные «wiper»-программы.

Исходный код открыт специально, чтобы вы могли убедиться сами: программа не лезет в сеть, не пишет в реестр, не добавляет себя в автозагрузку и не трогает ничего, кроме папок кэша в вашем профиле и собственных файлов настроек рядом с программой. Если не доверяете готовому `.exe` из **Cleaner.rar**, скачайте **Source Code.rar** и соберите программу самостоятельно через `build_exe.bat` (сборка через cx_Freeze), затем проверьте свою сборку на VirusTotal.

## Что чистит

Только папки кэша и временные файлы. Пароли, куки, история, закладки, расширения и сессии не затрагиваются.

- **Браузеры на движке Chromium** — Chrome, Edge, Brave, Vivaldi, Opera и др.: кэш страниц, скомпилированного кода, графики и `Service Worker\CacheStorage`. Профили (`Default`, `Profile 1`, `Profile 2`...) находятся автоматически.
- **Firefox** — кэш всех профилей (папка профиля ищется автоматически).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, отчёты об ошибках (WER).
- **Разработка** — кэши pip, uv, npm, Yarn, NuGet и VS Code.
- **Приложения** — кэш Discord, Slack, встроенного браузера Steam и других программ.

**По умолчанию** программа чистит только тот набор путей, который заложен в её штатную работу. Дополнительная функция **поиска папок с кэшем** предназначена для тех случаев, когда нужно найти ещё что-то: найденные папки не удаляются автоматически, вы сами выбираете, добавлять ли их к очистке. Если поиск не нужен, можно ничего не добавлять и работать только со штатным списком.

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
3. Внизу программа пишет количество найденных объектов и общий размер на удаление — считаются только объекты с пометкой «← УДАЛИТСЯ».
4. Подтвердите удаление (например, `y` / `yes` / `д` / `да`). Удаление начинается только после явного подтверждения.
5. После удаления выводится статистика: сколько удалено полностью, частично, сколько пропущено (занято процессами) и сколько места освобождено. Цифра считается по размеру удалённых файлов, поэтому свободное место в проводнике может вырасти чуть меньше.

## Возможности

- Окно в виде терминала: цветной вывод, прокрутка колесом мыши, перетаскиваемый ползунок справа, быстрая прокрутка зажатой средней кнопкой, размер окна можно менять — текст переносится автоматически.
- **Выделение и копирование текста:** выделяйте текст левой кнопкой мыши (если дотянуть выделение до верхнего или нижнего края окна, список прокручивается сам). `Ctrl+C` копирует выделенное, `Ctrl+A` выделяет и копирует весь текст окна. Сочетания работают и при русской раскладке. Длинные пути копируются целыми строками, без разрывов от визуального переноса.
- **Предпросмотр-дерево перед удалением:** видно путь, вес, что удалится и что останется.
- **Поиск папок с кэшем:** отдельная функция для поиска дополнительных папок с кэшем. Найденные папки не удаляются сами — вы выбираете, добавлять ли их к очистке. По умолчанию программа чистит только штатный набор путей, заложенный в неё.
- **Свои папки:** можно добавить собственные пути для очистки.
- **Цветная рамка окна (Windows 11):** когда окно активно, рамка и заголовок зелёные; когда вы переключились на другое окно — красные. На Windows 10 рамка остаётся обычной, это не ошибка.
- Защита от системных папок: даже при опечатке в списке путей программа не тронет `C:\Windows`, `C:\Program Files`, корни дисков или чужие профили пользователей.
- Ссылки и junction внутри папок не раскрываются, поэтому программа не удалит содержимое чужой папки, на которую они указывают.
- Один и тот же объект не считается дважды, даже если пути пересекаются.
- Отказ работать от имени администратора (см. предупреждение выше).
- Занятые процессом файлы не вызывают падение — просто пропускаются.
- Автоматическое снятие атрибута read-only перед удалением.

Набор дополнительных настроек (свои папки, исключения, необязательные пункты очистки и др.) зависит от версии программы. Подробности смотрите в комментариях в начале файла с исходным кодом и в подсказках внутри самой программы.

## 📥 Что скачивать

В разделе **Releases** лежат два архива:

1. **Cleaner.rar** — готовая программа.  
   Скачивайте **первым**, если хотите просто запустить Cleaner. Внутри уже собранная программа, Python и библиотеки отдельно устанавливать не нужно.
2. **Source Code.rar** — исходный код.  
   Для тех, кто хочет проверить код, изменить настройки или собрать `.exe` самостоятельно. Внутри есть `build_exe.bat` для сборки через cx_Freeze.

### Если нужна готовая программа

1. Скачайте **Cleaner.rar** из Releases.
2. Распакуйте архив.
3. Запустите программу **не от имени администратора**.
4. Прочитайте список путей и подтвердите удаление.

### Если нужен исходный код

1. Скачайте **Source Code.rar** из Releases.
2. Распакуйте архив.
3. Для запуска из исходников нужен Python 3.10+ и зависимости, указанные в исходном коде.
4. Для сборки `.exe` запустите `build_exe.bat` — он выполняет сборку через cx_Freeze сам.

## Лицензия

MIT — делайте с программой что хотите, без гарантий.

# 🧹 Cleaner — Windows Cache and Junk Folder Cleanup Tool

A simple program for cleaning temporary files and browser/app caches on Windows.  
It opens in a terminal-style window, first shows what will be deleted (as a folder tree with full paths and sizes), asks for confirmation, and only then deletes.

📄 **The source code** is in the **Source Code.rar** release — open it and check for yourself exactly what the program does.

## 🛑 Read before running

- **Always check where the paths lead.** Before deleting, the program prints the list of folders and files. Read it completely, especially if you added your own paths. If you see anything unfamiliar or important, do not confirm the deletion and nothing will be deleted.
- **Do not add folders that hold program data.** Only clean what is definitely cache or temporary files. For example, `C:\Users\<name>\AppData\Local\Packages` stores Microsoft Store app data (settings, logins), and it must not be cleaned as a whole.
- **Do not run as administrator.** Administrator rights are not needed: the program only cleans folders in your regular user profile. With elevated rights it has wider access to files, and the profile may resolve to the wrong one. For that reason the program refuses to run as administrator and shows a message. Launch it with a normal double click.
- **The program has only been tested on my own computer.** It has not been tested on other systems or Windows configurations, and behavior may differ.
- **No warranty and no liability.** You use it at your own risk. The author is not responsible for lost data, deleted files, or any other damage (see the MIT license).
- Deletion is **permanent**, bypassing the Recycle Bin.
- Written for **Windows**. Not tested on or designed for other operating systems.

## ⚠️ About antivirus false positives

Some antivirus engines (Microsoft Defender, Avast, Cynet, etc.) may flag the `.exe` from **Cleaner.rar** as suspicious or even as a trojan (`Wacatac` / `MalwareX` detections). This is **generic heuristic detection**, not actual malicious code: antivirus engines react to characteristics of the file itself — cx_Freeze packaging, no publisher's digital signature, and bulk file deletion, which is also how malicious "wiper" tools look.

The source code is open specifically so you can verify it yourself: the program makes no network requests, doesn't touch the registry, doesn't add itself to startup, and only touches cache folders in your own profile and its own settings files next to the program. If you don't trust the prebuilt `.exe` from **Cleaner.rar**, download **Source Code.rar** and build the program yourself via `build_exe.bat` (a cx_Freeze build), then scan your own build on VirusTotal.

## What it cleans

Only cache folders and temporary files. Passwords, cookies, history, bookmarks, extensions, and sessions are not touched.

- **Chromium-based browsers** — Chrome, Edge, Brave, Vivaldi, Opera, etc.: page cache, compiled code cache, graphics cache, and `Service Worker\CacheStorage`. Profiles (`Default`, `Profile 1`, `Profile 2`...) are detected automatically.
- **Firefox** — the cache of all profiles (the profile folder is found automatically).
- **Windows** — `Temp`, `CrashDumps`, `INetCache`, error reports (WER).
- **Development** — pip, uv, npm, Yarn, NuGet and VS Code caches.
- **Apps** — Discord, Slack, Steam's built-in browser and other programs' caches.

**By default**, the program cleans only the set of paths built into its standard operation. The additional **cache folder search** function is for cases when you need to find something else: found folders are not deleted automatically — you choose whether to add them to the cleanup. If you don't need the search, you can add nothing and work only with the standard list.

Optionally, you can also enable:
- cleaning GPU shader caches (NVIDIA/AMD/Intel/D3D). Safe to delete, but games have to recompile shaders afterwards, and the first launch can take a very long time;
- cleaning the `.cache` folder in your profile. It often holds downloaded models (for example, huggingface) that will be downloaded again.

If you play games, it is better to leave these two options off.

Folders that don't exist on your computer are skipped automatically. The full list of paths and settings is at the top of the source code file.

## How to read the list before deletion

1. Run the program (**not as administrator**). It scans the folders and builds the list.
2. Read the list. It is shown as a tree:
   - **A main folder** is shown as a line with its full path and total size. The note "папка останется, внутри чистится" (the folder stays, its contents are cleaned) means the folder itself is not deleted, only its contents are.
   - **Inside a folder**, subfolders (with sizes) come first, then files. A file never appears above a folder, even if it is heavier.
   - **The red "← УДАЛИТСЯ" label** (WILL BE DELETED) marks an item that will be deleted. **Gray** shows what lies inside a folder being deleted (it goes away together with it).
   - **"… ещё файлов: 95, 45.42 MB"** (95 more files) is a collapsed line: the heaviest items are shown, the rest are merged into one line with their total size.
   - **"[внутри ещё, свёрнуто]"** (more inside, collapsed) means content deeper than the configured expansion level.
3. At the bottom the program prints the number of objects found and the total size to delete. Only items marked "← УДАЛИТСЯ" are counted.
4. Confirm the deletion (for example, `y` / `yes` / `д` / `да`). Deletion starts only after explicit confirmation.
5. After deletion a summary is printed: how much was fully deleted, partially deleted, skipped (in use by processes), and how much space was freed. The figure is the total size of the deleted files, so the free space shown in Explorer may grow slightly less.

## Features

- Terminal-style window: colored output, mouse wheel scrolling, a draggable scrollbar on the right, fast scrolling with the held middle mouse button, and a resizable window — text wraps automatically.
- **Text selection and copying:** select text with the left mouse button (dragging the selection past the top or bottom edge scrolls the list automatically). `Ctrl+C` copies the selection, `Ctrl+A` selects and copies the whole window text. The shortcuts work with a Russian keyboard layout too. Long paths are copied as whole lines, without breaks from the visual wrapping.
- **Tree preview before deletion:** you can see the path, size, what will be deleted and what will stay.
- **Cache folder search:** a separate function for finding additional cache folders. Found folders are not deleted by themselves — you choose whether to add them to the cleanup. By default, the program cleans only the standard set of paths built into it.
- **Your own folders:** you can add your own paths for cleaning.
- **Colored window border (Windows 11):** when the window is active, the border and title bar are green; when you switch to another window, they are red. On Windows 10 the border stays default, which is not an error.
- Protection against system folders: even with a typo in the path list, the program won't touch `C:\Windows`, `C:\Program Files`, drive roots, or other users' profiles.
- Links and junctions inside folders are not expanded, so the program will not delete the contents of another folder they point to.
- The same item is never counted twice, even if paths overlap.
- Refuses to run as administrator (see the warning above).
- Files locked by another process don't cause a crash — they're simply skipped.
- Automatically clears the read-only attribute before deletion.

The set of additional settings (your own folders, exclusions, optional cleanup items, etc.) depends on the program version. See the comments at the top of the source code file and the hints inside the program itself for details.

## 📥 What to download

The **Releases** section contains two archives:

1. **Cleaner.rar** — the ready-to-use program.  
   Download this **first** if you just want to run Cleaner. It contains the already-built program; Python and libraries do not need to be installed separately.
2. **Source Code.rar** — the source code.  
   For those who want to check the code, change settings, or build the `.exe` themselves. It contains `build_exe.bat` for building via cx_Freeze.

### If you need the ready-to-use program

1. Download **Cleaner.rar** from Releases.
2. Unpack the archive.
3. Run the program **not as administrator**.
4. Read the list of paths and confirm the deletion.

### If you need the source code

1. Download **Source Code.rar** from Releases.
2. Unpack the archive.
3. To run from source, you need Python 3.10+ and the dependencies specified in the source code.
4. To build the `.exe`, run `build_exe.bat` — it performs the cx_Freeze build itself.

## License

MIT — do whatever you want with it, no warranty.
