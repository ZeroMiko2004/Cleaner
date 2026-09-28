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
import traceback

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

CLEAN_SHADER_CACHES = True

# Папка .cache в профиле пользователя. Там часто лежат скачанные модели
# (например huggingface) — после удаления они скачиваются заново.

CLEAN_DOT_CACHE = True

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
]

for browser in CHROMIUM_BROWSERS:
    profiles = glob.glob(browser + r"\Default") + glob.glob(browser + r"\Profile *")
    for profile in profiles:
        for folder in CHROMIUM_CACHE_FOLDERS:
            PATHS.append(profile + "\\" + folder)
    for folder in (r"GrShaderCache", r"ShaderCache", r"GraphiteDawnCache"):
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
        self._line_cache = {}

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
        self._line_cache = {}
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
            self._apply_fast_scroll()
            self._draw()
            self.clock.tick(30)
            self.cursor_blink_ms = (self.cursor_blink_ms + 33) % 1000
        pygame.quit()

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
                self.scroll = 10 ** 9
            elif kind == "ask":
                self.input_active = True
                self.input_text = ""
                self.input_prompt = msg[1]
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

    def _on_mouse_motion(self, e):
        track, thumb, max_scroll, _ = self._scrollbar_geometry()
        self.scrollbar_hover = bool(max_scroll > 0 and thumb.collidepoint(e.pos))
        if self.scrollbar_dragging:
            new_thumb_y = e.pos[1] - self.scrollbar_drag_offset
            self._set_scroll_from_thumb_y(new_thumb_y, track, thumb, max_scroll)

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
        y = 0
        for i in range(start, end):
            surf = self._get_line_surface(i)
            self.screen.blit(surf, (8, y))
            y += self.line_h

        if self.input_active:
            y = text_fit * self.line_h
            self._draw_input_line(8, y)

        self._draw_scrollbar()
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

    def _get_line_surface(self, idx: int) -> pygame.Surface:
        cached = self._line_cache.get(idx)
        if cached is not None:
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
            self._line_cache[idx] = surf
            return surf

        line_surf = pygame.Surface((total_w, self.line_h), pygame.SRCALPHA)
        x = 0
        for seg_surf, bg in rendered:
            if bg:
                pygame.draw.rect(line_surf, bg,
                                 (x, 0, seg_surf.get_width(), self.line_h))
            line_surf.blit(seg_surf, (x, 0))
            x += seg_surf.get_width()

        self._line_cache[idx] = line_surf
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

    ui.write(Text("\nСписок того, что будет удалено:", style="bold"))
    for p, s, t in sorted(all_items, key=lambda x: -x[1]):
        line = Text()
        line.append(f"  [{t:6}] ", style="cyan" if t == "файл" else "magenta")
        line.append(f"{human_size(s):>10}", style="green")
        line.append(f"  {os.path.abspath(p)}")
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
