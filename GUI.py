import tkinter as tk
from tkinter import messagebox
import ctypes
from datetime import datetime
from Controller import PlannerController
from PIL import Image, ImageTk
import os

# =============================================================================
# HIGH-DPI SCALING & Icon
# =============================================================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

try:
    myappid = "studium.kitstudie.devpulseplanner.v1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# =============================================================================
# CUSTOM SCROLLABLE FRAME MIT EIGENER CANVAS-SCROLLBAR
# =============================================================================
class ScrollableFrame(tk.Frame):
    """ScrollableFrame mit komplett selbst gezeichneter Scrollbar.

    Warum nicht tk.Scrollbar?
    - Die native Windows/Tk-Scrollbar ignoriert je nach Theme oft bg/troughcolor.
    - Deshalb wird die Scrollbar hier per Canvas gezeichnet.
    - Ergebnis: Dark Theme bleibt wirklich dunkel.
    """

    def __init__(
        self,
        parent,
        bg,
        scrollbar_bg="#C8CDD3",
        scrollbar_trough="#F3F4F6",
        scrollbar_active="#AEB4BD",
        scrollbar_width=12,
        **kwargs,
    ):
        super().__init__(parent, bg=bg, **kwargs)

        self.bg = bg
        self.scrollbar_bg = scrollbar_bg
        self.scrollbar_trough = scrollbar_trough
        self.scrollbar_active = scrollbar_active
        self.scrollbar_width = scrollbar_width
        self._scrollbar_dragging = False
        self._scrollbar_drag_offset = 0
        self._last_scroll = (0.0, 1.0)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.scrollbar_canvas = tk.Canvas(
            self,
            width=scrollbar_width,
            bg=scrollbar_trough,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_canvas_scroll)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_canvas.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Enter>", lambda event: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda event: self.canvas.unbind_all("<MouseWheel>"))

        self.scrollbar_canvas.bind("<ButtonPress-1>", self._on_scrollbar_press)
        self.scrollbar_canvas.bind("<B1-Motion>", self._on_scrollbar_drag)
        self.scrollbar_canvas.bind("<ButtonRelease-1>", self._on_scrollbar_release)
        self.scrollbar_canvas.bind("<Enter>", self._on_scrollbar_enter)
        self.scrollbar_canvas.bind("<Leave>", self._on_scrollbar_leave)

    # === Reaktion auf Canvas-Größenänderung ===
    def _on_canvas_resize(self, event):
        """Passt die Breite des inneren Frames an und zeichnet Scrollbar neu"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._draw_scrollbar(*self._last_scroll)

    # === Reaktion auf inneren Frame-Größenänderung ===
    def _on_inner_configure(self, event=None):
        """Aktualisiert Scroll-Region, Sichtbarkeit und Scrollbar-Darstellung"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar_visibility()
        self._draw_scrollbar(*self._last_scroll)

    # === Reaktion auf Canvas-Scroll-Ereignis ===
    def _on_canvas_scroll(self, first, last):
        """Speichert Scroll-Position und zeichnet Scrollbar neu basierend auf Scroll-Status"""
        first = float(first)
        last = float(last)
        self._last_scroll = (first, last)
        self._update_scrollbar_visibility()
        self._draw_scrollbar(first, last)

    # === Prüfe ob Scrollbar sichtbar sein soll ===
    def _update_scrollbar_visibility(self):
        """Zeigt oder verbirgt die Scrollbar je nachdem ob Inhalt scrollbar ist"""
        bbox = self.canvas.bbox("all")
        needs_scrollbar = bool(bbox and bbox[3] > self.canvas.winfo_height())
        if needs_scrollbar:
            if not self.scrollbar_canvas.winfo_ismapped():
                self.scrollbar_canvas.pack(side="right", fill="y")
        else:
            if self.scrollbar_canvas.winfo_ismapped():
                self.scrollbar_canvas.pack_forget()

    # === Zeichne die Scrollbar neu ===
    def _draw_scrollbar(self, first=0.0, last=1.0, active=False):
        """Zeichnet die Scrollbar mit Thumb basierend auf Scroll-Position first/last"""
        self.scrollbar_canvas.delete("all")
        height = max(self.scrollbar_canvas.winfo_height(), 1)
        width = self.scrollbar_width

        # Zeichne Hintergrund der Scrollbar
        self.scrollbar_canvas.create_rectangle(0, 0, width, height, fill=self.scrollbar_trough, outline="")

        # Wenn komplett sichtbar, keine Thumb-Anzeige
        if last - first >= 0.999:
            return

        # Berechne Thumb-Position und Höhe mit Mindesthöhe
        min_thumb_height = 34
        thumb_top = int(first * height)
        thumb_bottom = int(last * height)
        if thumb_bottom - thumb_top < min_thumb_height:
            thumb_bottom = min(height, thumb_top + min_thumb_height)
            if thumb_bottom == height:
                thumb_top = max(0, height - min_thumb_height)

        # Zeichne Thumb mit aktiver oder inaktiver Farbe
        pad = 3
        color = self.scrollbar_active if active or self._scrollbar_dragging else self.scrollbar_bg
        self.scrollbar_canvas.create_rectangle(
            pad,
            thumb_top + 2,
            width - pad,
            thumb_bottom - 2,
            fill=color,
            outline="",
        )
        self._thumb_top = thumb_top
        self._thumb_bottom = thumb_bottom

    # === Scrollbar Drag-Start ===
    def _on_scrollbar_press(self, event):
        """Startet Drag auf Thumb oder springt zur Klick-Position in der Spur"""
        height = max(self.scrollbar_canvas.winfo_height(), 1)
        thumb_top = getattr(self, "_thumb_top", 0)
        thumb_bottom = getattr(self, "_thumb_bottom", height)
        if thumb_top <= event.y <= thumb_bottom:
            self._scrollbar_dragging = True
            self._scrollbar_drag_offset = event.y - thumb_top
        else:
            # Klick in die Spur: sofort zur Position springen
            first, last = self._last_scroll
            page = last - first
            target = max(0.0, min(1.0 - page, event.y / height - page / 2))
            self.canvas.yview_moveto(target)
        self._draw_scrollbar(*self._last_scroll, active=True)

    # === Scrollbar Drag-Bewegung ===
    def _on_scrollbar_drag(self, event):
        """Bewegt Thumb während Drag und aktualisiert Canvas-Scroll-Position"""
        if not self._scrollbar_dragging:
            return
        height = max(self.scrollbar_canvas.winfo_height(), 1)
        first, last = self._last_scroll
        page = max(last - first, 0.01)
        thumb_height = max(getattr(self, "_thumb_bottom", 0) - getattr(self, "_thumb_top", 0), 34)
        movable = max(height - thumb_height, 1)
        new_top = max(0, min(movable, event.y - self._scrollbar_drag_offset))
        target = max(0.0, min(1.0 - page, new_top / movable * (1.0 - page)))
        self.canvas.yview_moveto(target)

    # === Scrollbar Drag-Ende ===
    def _on_scrollbar_release(self, event):
        """Beendet das Drag-Modus und zeichnet Scrollbar neu"""
        self._scrollbar_dragging = False
        self._draw_scrollbar(*self._last_scroll)

    # === Scrollbar Maus-Enter ===
    def _on_scrollbar_enter(self, event=None):
        """Hebt die Scrollbar hervor wenn die Maus drüber geht"""
        self._draw_scrollbar(*self._last_scroll, active=True)

    # === Scrollbar Maus-Leave ===
    def _on_scrollbar_leave(self, event=None):
        """Entfernt die Hervorhebung wenn die Maus weg geht (nur wenn nicht dragging)"""
        if not self._scrollbar_dragging:
            self._draw_scrollbar(*self._last_scroll, active=False)

    # === Mausrad-Scrollen ===
    def _on_mousewheel(self, event):
        """Scrollt Canvas mit Mausrad wenn über der Scrollbar und scrollbar nötig"""
        bbox = self.canvas.bbox("all")
        if bbox and bbox[3] > self.canvas.winfo_height():
            try:
                # Standard-Delta (Windows/Mac kompatibel behandeln)
                delta = -1 * (event.delta // 120) if hasattr(event, "delta") else (1 if event.num == 5 else -1)
                self.canvas.yview_scroll(delta, "units")
            except Exception:
                pass


# =============================================================================
# TOOLTIP
# =============================================================================
class Tooltip:
    """Zeigt einen Tooltip wenn die Maus über ein Widget geht"""

    def __init__(self, widget, text, bg="#1A1A1A", fg="#FFFFFF"):
        """Speichert Tooltip-Einstellungen und bindet Enter/Leave Events"""
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    # === Tooltip anzeigen ===
    def show(self, event=None):
        """Erstellt und zeigt das Tooltip-Fenster an der Maus-Position"""
        if self.tip:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except tk.TclError:
            return
        try:
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(self.tip, text=self.text, bg=self.bg, fg=self.fg, font=("Segoe UI", 9), padx=10, pady=5, relief="flat", bd=0).pack()
        except tk.TclError:
            self.tip = None

    # === Tooltip verstecken ===
    def hide(self, event=None):
        """Zerstört das Tooltip-Fenster"""
        if self.tip:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None


# =============================================================================
# HAUPTANWENDUNG
# =============================================================================
class DevPulsePlanner(tk.Tk):
    """Die Hauptanwendung für die Aufgabenverwaltung mit Kanban-Board"""
    
    STATUSES = ("offen", "in_bearbeitung", "erledigt")

    # === Initialisierung der Hauptanwendung ===
    def __init__(self):
        """Erstellt das Hauptfenster, initialisiert UI und lädt Demo-Daten via PlannerController"""
        super().__init__()
        self.title("DevPulse Planner")
        self.geometry("1440x900")
        self.minsize(1000, 650)
        self.resizable(True, True)

        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self.is_fullscreen = False

        # Initialisiere Controller (aus Controller.py) - dieser verwaltet TaskManager und Datenspeicherung
        self.controller = PlannerController(view=self, storage_path=os.path.join(os.path.dirname(__file__), "daten.json"))

        # Fenster-Icon setzen - lädt Logo.png oder nutzt Canvas-Fallback
        try:
            icon_image = Image.open("Logo.png")
            self.app_icon = ImageTk.PhotoImage(icon_image)
            self.iconphoto(False, self.app_icon)
        except Exception as e:
            print(f"Fenster-Icon konnte nicht geladen werden: {e}")

        # Theme-Definitionen für Hell- und Dunkel-Modus
        self.themes = {
            "light": {
                "bg": "#F0F2F5", "sidebar": "#FFFFFF", "sidebar_top": "#0A1628",
                "text_main": "#0D1117", "text_sub": "#7D8590", "text_inv": "#FFFFFF",
                "accent": "#1A73E8", "accent2": "#00C896", "card": "#FFFFFF",
                "card_hover": "#F6F8FF", "border": "#E2E8F0", "border_focus": "#1A73E8",
                "topbar": "#0A1628", "col_open": "#EEF2FF", "col_wip": "#FFF7ED", "col_done": "#F0FDF4",
                "tag_high": "#FF4D6D", "tag_med": "#FF9A3C", "tag_low": "#1A73E8",
                "shadow": "#00000018", "btn_add": "#1A73E8", "btn_demo": "#6366F1", "btn_theme": "#374151",
                "badge_open": "#3B82F6", "badge_wip": "#F59E0B", "badge_done": "#10B981",
                "scrollbar_thumb": "#C8CDD3", "scrollbar_trough": "#EDF0F3", "scrollbar_active": "#AEB4BD",
            },
            "dark": {
                "bg": "#0D1117", "sidebar": "#161B22", "sidebar_top": "#0D1117",
                "text_main": "#E6EDF3", "text_sub": "#8B949E", "text_inv": "#E6EDF3",
                "accent": "#58A6FF", "accent2": "#3FB950", "card": "#161B22",
                "card_hover": "#1C2128", "border": "#30363D", "border_focus": "#58A6FF",
                "topbar": "#0D1117", "col_open": "#161B22", "col_wip": "#1C1811", "col_done": "#0F1A12",
                "tag_high": "#FF4D6D", "tag_med": "#FF9A3C", "tag_low": "#58A6FF",
                "shadow": "#00000040", "btn_add": "#238636", "btn_demo": "#6E40C9", "btn_theme": "#30363D",
                "badge_open": "#1D4ED8", "badge_wip": "#D97706", "badge_done": "#059669",
                "scrollbar_thumb": "#47515C", "scrollbar_trough": "#161B22", "scrollbar_active": "#6B7785",
            },
        }
        self.current_theme = "light"
        self.ui_elements = {}
        self.card_images = []
        self._task_count = {"offen": 0, "in_bearbeitung": 0, "erledigt": 0}
        self.current_view = "Board"

        # Performance-Caches für Drag-&-Drop und Rendering
        self._drop_zones = {}
        self._columns = {}
        self._column_scrolls = {}
        self._column_count_labels = {}
        self._card_widgets = {}
        self._visible_task_ids = set()
        self._search_after_id = None

        # Drag-&-Drop Zustand
        self._drag_data = None
        self._last_drop_status = None
        self._drag_preview = None
        self._drag_preview_after_id = None
        self._drag_preview_pending_xy = None

        self._setup_styles()
        self._build_layout()
        self._populate_layout()
        self.load_initial_data()

    # === Schriftarten und Styles konfigurieren ===
    def _setup_styles(self):
        """Definiert alle Schriftarten und Größen für die gesamte Anwendung"""
        self.FONT_DISPLAY = ("Segoe UI Black", 22, "bold")
        self.FONT_TITLE = ("Segoe UI Semibold", 14)
        self.FONT_HEAD = ("Segoe UI Bold", 11)
        self.FONT_BODY = ("Segoe UI", 10)
        self.FONT_SMALL = ("Segoe UI", 9)
        self.FONT_MICRO = ("Segoe UI", 8)
        self.FONT_MONO = ("Consolas", 9)
        self.FONT_NAV = ("Segoe UI Semibold", 10)
        self.FONT_BADGE = ("Segoe UI Bold", 8)

    # === Hauptlayout aufbauen ===
    def _build_layout(self):
        """Erstellt die Grundstruktur des Fensters: Sidebar (links) + Main Area (rechts)"""
        colors = self.themes[self.current_theme]
        self.config(bg=colors["bg"])
        
        # Erstelle Sidebar mit fester Breite
        self.sidebar = tk.Frame(self, width=240, bg=colors["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Erstelle Main Area die den Rest ausfüllt
        self.main_area = tk.Frame(self, bg=colors["bg"])
        self.main_area.pack(side="left", fill="both", expand=True)
        
        self.ui_elements["sidebar"] = self.sidebar
        self.ui_elements["main_area"] = self.main_area

    # === UI-Komponenten füllen ===
    def _populate_layout(self):
        """Füllt Sidebar (Logo, Suche, Nav, Stats, Buttons) und Main Area (Topbar, Board) mit Inhalten"""
        colors = self.themes[self.current_theme]

        # === SIDEBAR HEADER MIT LOGO ===
        brand_frame = tk.Frame(self.sidebar, bg=colors["sidebar_top"], height=72)
        brand_frame.pack(fill="x")
        brand_frame.pack_propagate(False)
        self.ui_elements["brand_frame"] = brand_frame
        self.load_logo(brand_frame)

        # === SUCHFELD ===
        search_outer = tk.Frame(self.sidebar, bg=colors["sidebar"], pady=8, padx=12)
        search_outer.pack(fill="x")
        search_frame = tk.Frame(search_outer, bg=colors["border"], padx=2, pady=2)
        search_frame.pack(fill="x")
        search_inner = tk.Frame(search_frame, bg=colors["card"])
        search_inner.pack(fill="x")
        tk.Label(search_inner, text="🔍", font=self.FONT_BODY, bg=colors["card"], fg=colors["text_sub"]).pack(side="left", padx=(8, 4), pady=6)

        self.search_var = tk.StringVar(value="Suchen…")
        search_entry = tk.Entry(search_inner, textvariable=self.search_var, font=self.FONT_SMALL, bg=colors["card"], fg=colors["text_sub"], relief="flat", bd=0, insertbackground=colors["accent"])
        search_entry.pack(side="left", fill="x", expand=True, pady=6, padx=(0, 8))

        # Bind Focus-Events für Placeholder-Text
        def on_focus_in(event=None):
            try:
                if self.search_var.get() == "Suchen…":
                    self.search_var.set("")
                search_entry.config(fg=colors["text_main"])
            except tk.TclError:
                pass

        def on_focus_out(event=None):
            try:
                if not self.search_var.get():
                    self.search_var.set("Suchen…")
                    search_entry.config(fg=colors["text_sub"])
            except tk.TclError:
                pass

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)

        # Globaler Focus-Handler für Klicks außerhalb des Suchfelds
        def global_focus_handler(event=None):
            try:
                widget = event.widget if event else None
                if widget is not search_entry and not self._is_child_of(widget, search_entry):
                    self._safe_focus(self)
            except Exception:
                pass

        self.bind("<Button-1>", global_focus_handler, add="+")

        # Bind Search-Variable zur Live-Suche (mit Verzögerung)
        self.search_var.trace_add("write", self._on_search)
        self.ui_elements["search_entry"] = search_entry

        # === NAVIGATION ===
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)
        nav_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        nav_container.pack(fill="x", pady=(8, 0))
        self.ui_elements["nav_container"] = nav_container
        self._build_nav(nav_container)

        # === STATISTIKEN ===
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12, pady=(8, 0))
        stats_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=10)
        stats_frame.pack(fill="x")
        self.ui_elements["stats_frame"] = stats_frame
        self._build_stats_once(stats_frame)

        # === BUTTONS (unten in Sidebar) ===
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)
        btn_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=12)
        btn_frame.pack(fill="x", side="bottom")
        self.ui_elements["btn_frame"] = btn_frame
        self._build_sidebar_buttons(btn_frame)

        # === TOPBAR (in Main Area) ===
        topbar = tk.Frame(self.main_area, bg=colors["topbar"], height=72)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.ui_elements["topbar"] = topbar
        self._build_topbar(topbar)

        # === BOARD AREA (in Main Area) ===
        board_outer = tk.Frame(self.main_area, bg=colors["bg"])
        board_outer.pack(fill="both", expand=True)
        self.ui_elements["board_outer"] = board_outer

        # Board Header mit Titel und Woche
        board_padding = 16
        board_header_outer = tk.Frame(board_outer, bg=colors["bg"])
        board_header_outer.pack(fill="x", padx=board_padding, pady=(20, 0))
        board_header = tk.Frame(board_header_outer, bg=colors["bg"])
        board_header.pack(fill="x")
        tk.Label(board_header, text="Sprint Board", font=("Segoe UI Black", 20), bg=colors["bg"], fg=colors["text_main"]).pack(side="left")
        date_lbl = tk.Label(board_header, text=datetime.now().strftime("KW %W  ·  %d.%m.%Y"), font=self.FONT_SMALL, bg=colors["bg"], fg=colors["text_sub"])
        date_lbl.pack(side="right", pady=6)
        self.ui_elements["date_lbl"] = date_lbl
        tk.Frame(board_outer, bg=colors["border"], height=1).pack(fill="x", padx=board_padding, pady=(8, 10))

        # Board Spalten (Offen, In Bearbeitung, Erledigt)
        cols_frame = tk.Frame(board_outer, bg=colors["bg"])
        cols_frame.pack(fill="both", expand=True, padx=board_padding, pady=16)
        cols_frame.columnconfigure((0, 1, 2), weight=1, uniform="col")
        cols_frame.rowconfigure(0, weight=1)
        self.ui_elements["cols_frame"] = cols_frame
        self._build_board_columns_once(cols_frame)

        # Wenn aktuelle View nicht "Board" ist, wechsel zur aktiven View
        if getattr(self, "current_view", "Board") != "Board":
            self._switch_view(self.current_view)

    # === Prüfe ob Widget Kind von Parent ist ===
    def _is_child_of(self, widget, parent):
        """Robuste rekursive Prüfung ob ein Widget ein Kind-Widget von parent ist"""
        current = widget
        while current:
            if current == parent:
                return True
            try:
                current = getattr(current, "master", None)
            except Exception:
                break
        return False

    # === Sicheres Fokus setzen ===
    def _safe_focus(self, widget):
        """Setzt den Fokus auf ein Widget wenn es noch existiert (TclError-safe)"""
        try:
            if widget and getattr(widget, "winfo_exists", lambda: False)():
                widget.focus_set()
        except tk.TclError:
            pass

    # === Logo laden und anzeigen ===
    def load_logo(self, parent):
        """Lädt Logo.png und zeigt es in der Sidebar mit Text 'DevPulse Planner'"""
        colors = self.themes[self.current_theme]
        
        try:
            # Bild laden und auf exakte Größe (32x32 Pixel) skalieren
            img = Image.open("Logo.png").resize((32, 32), Image.Resampling.LANCZOS)
            
            # WICHTIG: Die Referenz an 'self' binden, da Tkinter das Bild sonst 
            # sofort wieder aus dem Arbeitsspeicher löscht (Garbage Collection)!
            self.logo_tk = ImageTk.PhotoImage(img)
            
            # Das Bild in einem Label anzeigen
            logo_label = tk.Label(parent, image=self.logo_tk, bg=colors["sidebar_top"], bd=0)
            logo_label.pack(side="left", padx=(16, 8), pady=20)
            
        except Exception as e:
            # Sicherheits-Fallback, falls die Datei "Logo.png" nicht gefunden wird
            print(f"Hinweis: Logo.png konnte nicht geladen werden ({e}). Nutze Fallback-Canvas.")
            cv = tk.Canvas(parent, width=32, height=32, bg=colors["sidebar_top"], highlightthickness=0)
            cv.pack(side="left", padx=(16, 8), pady=20)
            cv.create_oval(2, 2, 30, 30, fill=colors["accent"], outline="")
            cv.create_text(16, 16, text="D", fill="white", font=("Segoe UI Black", 14))

        # Der Text "DevPulse" daneben
        name = tk.Frame(parent, bg=colors["sidebar_top"])
        name.pack(side="left")
        tk.Label(name, text="Dev", font=("Segoe UI Black", 15),
                 bg=colors["sidebar_top"], fg=colors["accent"]).pack(side="left")
        tk.Label(name, text="Pulse Planner", font=("Segoe UI Semibold", 15),
                 bg=colors["sidebar_top"], fg="#FFFFFF").pack(side="left")

    # === Navigationsmenü bauen ===
    def _build_nav(self, parent):
        """Erstellt alle Navigations-Items (Board, Analysen, Kalender, Einstellungen)"""
        self._nav_items = {} 
        for icon, label in [("📋", "Board"), ("📈", "Analysen"), ("🗓️", "Kalender"), ("⚙️", "Einstellungen")]:
            active = (label == getattr(self, "current_view", "Board"))
            self._make_nav_item(parent, icon, label, active)

    # === Einzelnes Navigations-Item erstellen ===
    def _make_nav_item(self, parent, icon, label, active):
        """Erstellt ein einzelnes Navigations-Element mit Styling und Click-Handler"""
        colors = self.themes[self.current_theme]
        bg = colors["col_open"] if active else colors["sidebar"]
        fg = colors["accent"] if active else colors["text_sub"]
        bar_color = colors["accent"] if active else colors["sidebar"]
        
        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)
        
        bar = tk.Frame(row, bg=bar_color, width=3)
        bar.pack(side="left", fill="y")
        
        lbl = tk.Label(row, text=f"  {icon}  {label}", font=self.FONT_NAV, bg=bg, fg=fg, anchor="w")
        lbl.pack(side="left", fill="x", expand=True, ipady=11, padx=4)

        # Bind Click-Event auf alle Widgets des Nav-Items
        for widget in (row, bar, lbl):
            widget.bind("<Button-1>", lambda e, l=label: self._switch_view(l))

        self._nav_items[label] = {"row": row, "bar": bar, "lbl": lbl, "icon": icon}

    # === View umschalten ===
    def _switch_view(self, view_name):
        """Wechselt zwischen Views: Board, Analysen, Kalender, Einstellungen
        - Aktualisiert Sidebar-Styling (aktive Nav-Item)
        - Versteckt/zeigt Board oder zeigt Placeholder 'Coming Soon'"""
        self.current_view = view_name
        colors = self.themes[self.current_theme]

        # 1. Aktualisiere Sidebar-Navigation visuell
        for name, widgets in self._nav_items.items():
            active = (name == view_name)
            bg = colors["col_open"] if active else colors["sidebar"]
            fg = colors["accent"] if active else colors["text_sub"]
            bar_color = colors["accent"] if active else colors["sidebar"]

            widgets["row"].config(bg=bg)
            widgets["bar"].config(bg=bar_color)
            widgets["lbl"].config(bg=bg, fg=fg)

        # 2. Aktualisiere Hauptbereich
        board_outer = self.ui_elements.get("board_outer")
        
        if view_name == "Board":
            # Zeige Board
            if hasattr(self, "placeholder_outer") and self.placeholder_outer.winfo_exists():
                self.placeholder_outer.pack_forget()
            if board_outer:
                board_outer.pack(fill="both", expand=True)
        else:
            # Verstecke Board und zeige Placeholder
            if board_outer:
                board_outer.pack_forget()

            if hasattr(self, "placeholder_outer") and self.placeholder_outer.winfo_exists():
                self.placeholder_outer.destroy()

            self.placeholder_outer = tk.Frame(self.main_area, bg=colors["bg"])
            self.placeholder_outer.pack(fill="both", expand=True)

            # Placeholder-Inhalt
            board_padding = 16
            header_outer = tk.Frame(self.placeholder_outer, bg=colors["bg"])
            header_outer.pack(fill="x", padx=board_padding, pady=(20, 0))
            tk.Label(header_outer, text=view_name, font=("Segoe UI Black", 20), bg=colors["bg"], fg=colors["text_main"]).pack(side="left")
            tk.Frame(self.placeholder_outer, bg=colors["border"], height=1).pack(fill="x", padx=board_padding, pady=(8, 10))

            content = tk.Frame(self.placeholder_outer, bg=colors["bg"])
            content.pack(fill="both", expand=True)
            tk.Label(content, text="Coming Soon", font=("Segoe UI Black", 36), bg=colors["bg"], fg=colors["text_sub"]).pack(expand=True)

    # === Statistiken aufbauen ===
    def _build_stats_once(self, parent):
        """Erstellt die Statistik-Anzeige (Offen, Aktiv, Fertig, Überfällig)
        - Löscht alte Widgets
        - Erstellt Counts und Überprüfungs-Label"""
        colors = self.themes[self.current_theme]
        self._stat_value_labels = {}
        self._overdue_label = None
        
        # Lösche alte Widgets
        for child in parent.winfo_children():
            child.destroy()
        
        # Überschrift ÜBERSICHT
        tk.Label(parent, text="ÜBERSICHT", font=self.FONT_BADGE, bg=colors["sidebar"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 8))
        
        # Task-Count Statistiken (3 Spalten)
        stat_row = tk.Frame(parent, bg=colors["sidebar"])
        stat_row.pack(fill="x")
        for index, (status_key, label, color) in enumerate([
            ("offen", "Offen", colors["badge_open"]),
            ("in_bearbeitung", "Aktiv", colors["badge_wip"]),
            ("erledigt", "Fertig", colors["badge_done"]),
        ]):
            cell = tk.Frame(stat_row, bg=colors["card"], highlightbackground=colors["border"], highlightthickness=1)
            cell.pack(side="left", expand=True, fill="x", padx=(0, 0 if index == 2 else 4))
            value_lbl = tk.Label(cell, text="0", font=("Segoe UI Black", 18), bg=colors["card"], fg=color)
            value_lbl.pack(pady=(8, 0))
            tk.Label(cell, text=label, font=self.FONT_MICRO, bg=colors["card"], fg=colors["text_sub"]).pack(pady=(0, 6))
            self._stat_value_labels[status_key] = value_lbl
        
        self.ui_elements["stat_row"] = stat_row
        
        # Überfällige Aufgaben
        tk.Label(parent, text="ÜBERFÄLLIG", font=self.FONT_BADGE, bg=colors["sidebar"], fg=colors["text_sub"]).pack(anchor="w", pady=(12, 8))
        
        overdue_cell = tk.Frame(parent, bg=colors["card"], highlightbackground=colors["border"], highlightthickness=1)
        overdue_cell.pack(fill="x")
        self._overdue_label = tk.Label(overdue_cell, text="0", font=("Segoe UI Black", 18), bg=colors["card"], fg=colors["text_sub"])
        self._overdue_label.pack(pady=(8, 6))

    # === Nur Statistiken aktualisieren ===
    def _update_stats_only(self):
        """Aktualisiert Statistik-Zahlen ohne Layout-Rebuild
        - Updated Task-Counts (Offen, Aktiv, Fertig)
        - Updated Überprüfungscount mit Farbwechsel wenn > 0"""
        for status, value in self._task_count.items():
            label = getattr(self, "_stat_value_labels", {}).get(status)
            if label and label.winfo_exists():
                label.config(text=str(value))
        
        overdue_count = self._count_overdue_tasks()
        colors = self.themes[self.current_theme]
        
        if self._overdue_label and self._overdue_label.winfo_exists():
            self._overdue_label.config(text=str(overdue_count))
            if overdue_count > 0:
                self._overdue_label.config(fg=colors["tag_high"]) 
                self._overdue_label.master.config(highlightbackground=colors["tag_high"])
            else:
                self._overdue_label.config(fg=colors["text_sub"]) 
                self._overdue_label.master.config(highlightbackground=colors["border"])

    # === Überfällige Tasks zählen ===
    def _count_overdue_tasks(self):
        """Zählt überfällige Tasks via PlannerController.get_overdue_count()
        - Nutzt Controller API wenn verfügbar
        - Fallback: zählt lokal für Status 'offen' und 'in_bearbeitung'"""
        try:
            return int(self.controller.get_overdue_count()) if hasattr(self.controller, "get_overdue_count") else 0
        except Exception:
            # Fallback: berechne lokal
            overdue = 0
            today = datetime.now().date()
            for status in ["offen", "in_bearbeitung"]:
                try:
                    tasks = self.controller.get_tasks_by_status(status)
                except Exception:
                    continue
                for task in tasks:
                    if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
                        task_date = task.get_faelligkeitsdatum().date()
                        if task_date < today:
                            overdue += 1
            return overdue

    # === Sidebar-Buttons aufbauen ===
    def _build_sidebar_buttons(self, parent):
        """Erstellt Aktions-Buttons am unteren Ende der Sidebar:
        - ➕ Neue Aufgabe: öffnet _add_task_dialog()
        - 🎲 Demo laden: ruft _load_demo() auf
        - 🌙 Theme wechseln: ruft toggle_theme() auf"""
        colors = self.themes[self.current_theme]

        def styled_btn(text, bg, command, tooltip_text=None):
            btn = tk.Button(parent, text=text, command=command, font=("Segoe UI Bold", 9), bg=bg, fg="#FFFFFF", relief="flat", bd=0, padx=12, pady=10, cursor="hand2", activebackground=bg, activeforeground="#FFFFFF")
            btn.pack(fill="x", pady=3)
            if tooltip_text:
                Tooltip(btn, tooltip_text, bg=colors["topbar"], fg=colors["text_inv"])
            return btn

        styled_btn("➕  Neue Aufgabe", colors["btn_add"], self._add_task_dialog)
        styled_btn("🎲  Demo laden", colors["btn_demo"], self._load_demo, "Beispieldaten laden")
        styled_btn("🌙  Theme wechseln", colors["btn_theme"], self.toggle_theme, "Hell / Dunkel umschalten")
        tk.Label(parent, text="F11 Vollbild · ESC Beenden", font=("Segoe UI", 7), bg=colors["sidebar"], fg=colors["text_sub"]).pack(pady=(10, 0))

    # === Topbar aufbauen ===
    def _build_topbar(self, topbar):
        """Erstellt die obere Navigationsleiste mit Fokus-Handler für Suchfeld"""
        colors = self.themes[self.current_theme]
        tk.Label(topbar, font=("Segoe UI Semibold", 12), bg=colors["topbar"], fg="#FFFFFF").pack(side="left", padx=16, pady=18)
        right = tk.Frame(topbar, bg=colors["topbar"])
        right.pack(side="right", padx=16)

        def remove_search_focus(event=None):
            try:
                search_entry = self.ui_elements.get("search_entry")
                widget = event.widget if event else None
                if search_entry and widget is not search_entry and not self._is_child_of(widget, search_entry):
                    self._safe_focus(self)
            except Exception:
                pass

        topbar.bind("<Button-1>", remove_search_focus, add="+")

    # === Board-Spalten aufbauen ===
    def _build_board_columns_once(self, cols_frame):
        """Erstellt die drei Board-Spalten (Offen, In Bearbeitung, Erledigt) mit:
        - Header mit Status-Titel und Task-Count Badge
        - ScrollableFrame mit Custom Scrollbar
        - Drop-Zones für Drag-&-Drop"""
        colors = self.themes[self.current_theme]
        self._drop_zones = {}
        self._columns = {}
        self._column_scrolls = {}
        self._column_count_labels = {}
        
        for col_idx, (status_key, title, col_bg, badge_color) in enumerate([
            ("offen", "📥  Offen", colors["col_open"], colors["badge_open"]),
            ("in_bearbeitung", "⚡  In Bearbeitung", colors["col_wip"], colors["badge_wip"]),
            ("erledigt", "✅  Erledigt", colors["col_done"], colors["badge_done"]),
        ]):
            grid_padx = (0, 8) if col_idx < 2 else (0, 0)
            wrapper = tk.Frame(cols_frame, bg=col_bg, highlightbackground=colors["border"], highlightthickness=1)
            wrapper.grid(row=0, column=col_idx, sticky="nsew", padx=grid_padx, pady=4)
            self._drop_zones[status_key] = wrapper
            self._columns[status_key] = wrapper
            
            # Column Header mit Titel und Badge
            header = tk.Frame(wrapper, bg=col_bg, padx=14, pady=12)
            header.pack(fill="x")
            tk.Label(header, text=title, font=self.FONT_HEAD, bg=col_bg, fg=colors["text_main"]).pack(side="left")
            badge = tk.Label(header, text="0", font=self.FONT_BADGE, bg=badge_color, fg="#FFFFFF", padx=7, pady=2)
            badge.pack(side="right")
            self._column_count_labels[status_key] = badge
            
            tk.Frame(wrapper, bg=colors["border"], height=1).pack(fill="x", padx=10)
            
            # ScrollableFrame für Tasks
            scroll = ScrollableFrame(wrapper, bg=col_bg, scrollbar_bg=colors["scrollbar_thumb"], scrollbar_trough=colors["scrollbar_trough"], scrollbar_active=colors["scrollbar_active"])
            scroll.pack(fill="both", expand=True)
            self._column_scrolls[status_key] = scroll

    # =========================================================================
    # DATEN & BOARD - PERFORMANCEOPTIMIERT
    # =========================================================================

    # === Initiale Daten laden ===
    def load_initial_data(self):
        """Lädt Demo-Daten via PlannerController.load_demo_data() und zeigt sie an"""
        self.controller.load_demo_data()
        self.refresh_board()

    # === Suchfeld-Platzhalter löschen ===
    def _clear_search_placeholder(self, event=None):
        """Löscht den Placeholder-Text aus dem Suchfeld wenn Fokus gesetzt wird"""
        if self.search_var.get() == "Suchen…":
            self.search_var.set("")

    # === Suchfeld-Platzhalter wiederherstellen ===
    def _restore_search_placeholder(self, event=None):
        """Zeigt den Placeholder-Text wieder wenn Suchfeld leer ist"""
        if not self.search_var.get():
            self.search_var.set("Suchen…")

    # === Suche verarbeiten ===
    def _on_search(self, *args):
        """Startet die Suche mit Verzögerung (180ms) um Performance zu verbessern
        - Nutzt after_cancel() um vorherige Anfrage zu stornieren
        - Ruft refresh_board() mit aktuellem Suchbegriff auf"""
        if "cols_frame" not in self.ui_elements:
            return
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(180, self.refresh_board)

    # === Board aktualisieren ===
    def refresh_board(self):
        """Aktualisiert alle Tasks auf dem Board basierend auf aktuellem Such-Filter
        - Holt alle Tasks vom Controller
        - Filtert nach Suchbegriff (nutzt Controller.search_tasks() wenn verfügbar)
        - Erstellt/Updated/Destroys Task-Karten für optimales Rendering
        - Updated Task-Counts in Badges"""
        if not self._column_scrolls:
            return

        raw = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        if raw.lower() == "suchen…":
            raw = ""
        query = raw.strip()

        # Hole alle Tasks von PlannerController - entweder via get_all_tasks() oder pro Status
        try:
            all_tasks = list(self.controller.get_all_tasks()) if hasattr(self.controller, "get_all_tasks") else []
        except Exception:
            all_tasks = []
            for status in self.STATUSES:
                try:
                    all_tasks.extend(self.controller.get_tasks_by_status(status))
                except Exception:
                    pass
        all_existing_ids = set(t.get_id() for t in all_tasks)

        # Baue tasks_by_status abhängig davon ob Suche aktiv ist
        tasks_by_status = {s: [] for s in self.STATUSES}
        if query:
            # Suche nutze Controller.search_tasks() wenn verfügbar, sonst lokal
            try:
                if hasattr(self.controller, "search_tasks"):
                    matching = list(self.controller.search_tasks(query))
                else:
                    ql = query.lower()
                    matching = [t for t in all_tasks if ql in (t.get_titel() or "").lower() or ql in ((t.get_beschreibung() or "").lower())]
            except Exception:
                matching = []
            for s in self.STATUSES:
                tasks_by_status[s] = [t for t in matching if getattr(t, "get_status", lambda: "")() == s]
                self._task_count[s] = len(tasks_by_status[s])
        else:
            # Keine Suche: zeige alle Tasks pro Status
            for status in self.STATUSES:
                try:
                    tasks = list(self.controller.get_tasks_by_status(status))
                except Exception:
                    tasks = []
                tasks_by_status[status] = tasks
                self._task_count[status] = len(tasks)

        # Entferne Karten für gelöschte Tasks
        for task_id in list(self._card_widgets.keys()):
            if task_id not in all_existing_ids:
                self._destroy_card_widget(task_id)

        # Rendere/Update sichtbare Karten
        visible_ids = set()
        for status in self.STATUSES:
            col_bg = self._get_column_bg(status)
            for task in tasks_by_status[status]:
                if task is None:
                    continue
                task_id = task.get_id()
                if not task_id:
                    continue
                if task_id not in visible_ids:
                    visible_ids.add(task_id)
                card_state = self._card_widgets.get(task_id)
                if card_state is None:
                    # Neue Karte erstellen
                    self._create_card_from_task(task, status, col_bg)
                elif card_state.get("status") != status:
                    # Karte ist in falscher Spalte - Delete und Recreate
                    self._destroy_card_widget(task_id)
                    self._create_card_from_task(task, status, col_bg)
                else:
                    # Bestehende Karte - nur Content aktualisieren
                    self._update_card_content(task_id, task)
                self._show_card_in_order(task_id)

        # Verstecke Karten die gefiltert wurden
        for task_id in list(self._card_widgets.keys()):
            if task_id not in visible_ids:
                self._hide_card(task_id)

        self._visible_task_ids = visible_ids
        self._update_counts_only()

    # === Spalten-Hintergrundfarbe abrufen ===
    def _get_column_bg(self, status):
        """Gibt die Hintergrundfarbe für eine bestimmte Status-Spalte aus Theme zurück"""
        colors = self.themes[self.current_theme]
        return {"offen": colors["col_open"], "in_bearbeitung": colors["col_wip"], "erledigt": colors["col_done"]}[status]

    # === Nur Counts aktualisieren ===
    def _update_counts_only(self):
        """Aktualisiert nur die Task-Zähler Badges ohne vollständiges Redraw
        - Updated Column Badges (3 Spalten)
        - Updated Sidebar Stats via _update_stats_only()"""
        for status, count in self._task_count.items():
            badge = self._column_count_labels.get(status)
            if badge and badge.winfo_exists():
                badge.config(text=str(count))
        self._update_stats_only()

    # === Task-Anzeigendaten vorbereiten ===
    def _task_view_data(self, task):
        """Extrahiert alle notwendigen Informationen aus einer Task (von ToDoListeKlassen.Task):
        - ID via task.get_id()
        - Titel via task.get_titel()
        - Beschreibung via task.get_beschreibung()
        - Priorität via task.get_prio() (1=Low, 3=Medium, 5=High)
        - Fälligkeitsdatum via task.get_faelligkeitsdatum()
        - Gibt Dictionary mit formatiertem Datum zurück"""
        prio_map = {1: "Low", 3: "Medium", 5: "High"}
        task_prio = task.get_prio() if hasattr(task, "get_prio") else 3
        prio = prio_map.get(task_prio, "Medium")
        date = "–"
        if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
            date = task.get_faelligkeitsdatum().strftime("%d.%m.%Y")
        return {"title": task.get_titel(), "desc": task.get_beschreibung() or "", "prio": prio, "date": date, "task_id": task.get_id()}

    # === Task-Karte aus Task erstellen ===
    def _create_card_from_task(self, task, status, col_bg):
        """Erstellt eine Karten-UI für eine einzelne Task:
        - Extrahiert Task-Daten via _task_view_data()
        - Holt Parent ScrollableFrame.inner aus _column_scrolls
        - Ruft _create_card() auf um visuelle Karte zu erstellen"""
        data = self._task_view_data(task)
        parent = self._column_scrolls[status].inner
        self._create_card(parent, data, status, col_bg)

    # === Task-Karte aufbauen ===
    def _create_card(self, parent, data, current_status, col_bg):
        """Erstellt die vollständige visuelle Darstellung einer Task-Karte mit:
        - Äußeres Frame (Padding, Hintergrund)
        - Karten-Frame mit Border und Hover-Effekt
        - Header: Prioritäts-Label + Delete-Button (✕)
        - Titel-Label mit Wrapping
        - Beschreibung-Label (optional)
        - Trennlinie
        - Footer: Datum-Label + Action-Buttons (✓ Erledigt, ✎ Bearbeiten)
        - Speichert Referenz in _card_widgets und bindet Drag-&-Drop"""
        colors = self.themes[self.current_theme]
        task_id = data["task_id"]
        outer = tk.Frame(parent, bg=col_bg, padx=10, pady=4)
        card = tk.Frame(outer, bg=colors["card"], highlightbackground=colors["border"], highlightthickness=1, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x")

        # Hover-Effekte
        def on_enter(event=None):
            if not self._drag_data:
                card.config(highlightbackground=colors["border_focus"], bg=colors["card_hover"])
                self._update_child_backgrounds(card, colors["card"], colors["card_hover"])

        def on_leave(event=None):
            if not self._drag_data:
                card.config(highlightbackground=colors["border"], bg=colors["card"])
                self._update_child_backgrounds(card, colors["card_hover"], colors["card"])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        # Header mit Prio und Delete-Button
        header = tk.Frame(card, bg=colors["card"])
        header.pack(fill="x")
        prio_colors = {"High": colors["tag_high"], "Medium": colors["tag_med"], "Low": colors["tag_low"]}
        prio_label = tk.Label(header, text=f"● {data['prio']}", font=("Segoe UI Bold", 7), bg=colors["card"], fg=prio_colors.get(data["prio"], colors["tag_low"]))
        prio_label.pack(side="left")
        tk.Button(header, text="✕", font=("Segoe UI Bold", 8), bg=colors["card"], fg=colors["text_sub"], relief="flat", bd=0, cursor="hand2", activeforeground="#FF4D6D", activebackground=colors["card"], command=lambda tid=task_id: self._delete_task(tid)).pack(side="right")
        
        # Titel
        title_label = tk.Label(card, text=data["title"], font=("Segoe UI Semibold", 10), bg=colors["card"], fg=colors["text_main"], anchor="w", wraplength=240, justify="left")
        title_label.pack(fill="x", pady=(6, 2))
        
        # Beschreibung (optional)
        desc_label = None
        if data["desc"]:
            desc_label = tk.Label(card, text=data["desc"], font=self.FONT_MICRO, bg=colors["card"], fg=colors["text_sub"], anchor="w", wraplength=240, justify="left")
            desc_label.pack(fill="x", pady=(0, 8))
        
        # Trennlinie
        tk.Frame(card, bg=colors["border"], height=1).pack(fill="x", pady=(4, 6))
        
        # Footer mit Datum und Buttons
        footer = tk.Frame(card, bg=colors["card"])
        footer.pack(fill="x")
        
        date_bg = self._get_date_display_bg(data["task_id"], data["date"])
        date_fg = self._get_date_display_color(data["task_id"], data["date"])
        date_label = tk.Label(footer, text=f"📅 {data['date']}", font=self.FONT_MICRO, bg=date_bg, fg=date_fg, relief="solid" if date_bg != colors["card"] else "flat", bd=1 if date_bg != colors["card"] else 0, padx=4, pady=2)
        date_label.pack(side="left")
        
        tk.Button(footer, text="✓ Erledigt", font=("Segoe UI Bold", 7), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", bd=0, padx=7, pady=2, cursor="hand2", command=lambda tid=task_id: self._complete_task(tid)).pack(side="right", padx=(4, 0))
        tk.Button(footer, text="✎ Bearbeiten", font=("Segoe UI Bold", 7), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", bd=0, padx=7, pady=2, cursor="hand2", command=lambda tid=task_id: self._bearbeitung_task(tid)).pack(side="right", padx=(0, 4))

        # Speichere Widget-Referenzen für spätere Updates
        self._card_widgets[task_id] = {"outer": outer, "card": card, "status": current_status, "data": data.copy(), "labels": {"prio": prio_label, "title": title_label, "desc": desc_label, "date": date_label}}
        self._bind_card_drag(card, task_id, data["title"], current_status, root_card=card, card_info=data.copy())

    # === Task-Karten-Inhalt aktualisieren ===
    def _update_card_content(self, task_id, task):
        """Aktualisiert den Inhalt einer bestehenden Task-Karte ohne Neuaufbau:
        - Vergleicht neue Daten mit gespeicherten Daten
        - Wenn gleich: Keine Änderung nötig
        - Wenn Beschreibung hinzugekommen/weggefallenlen: Destroy und Recreate
        - Sonst: Update einzelner Labels (Prio, Titel, Datum)"""
        state = self._card_widgets.get(task_id)
        if not state:
            return
        new_data = self._task_view_data(task)
        old_data = state.get("data", {})
        if new_data == old_data:
            return
        colors = self.themes[self.current_theme]
        labels = state["labels"]
        prio_colors = {"High": colors["tag_high"], "Medium": colors["tag_med"], "Low": colors["tag_low"]}
        labels["prio"].config(text=f"● {new_data['prio']}", fg=prio_colors.get(new_data["prio"], colors["tag_low"]))
        labels["title"].config(text=new_data["title"])
        labels["date"].config(text=f"📅 {new_data['date']}")
        desc_label = labels.get("desc")
        if new_data["desc"]:
            if desc_label and desc_label.winfo_exists():
                desc_label.config(text=new_data["desc"])
            else:
                status = state["status"]
                self._destroy_card_widget(task_id)
                self._create_card_from_task(task, status, self._get_column_bg(status))
                return
        elif desc_label and desc_label.winfo_exists():
            status = state["status"]
            self._destroy_card_widget(task_id)
            self._create_card_from_task(task, status, self._get_column_bg(status))
            return
        state["data"] = new_data.copy()

    # === Karte in korrekter Reihenfolge anzeigen ===
    def _show_card_in_order(self, task_id):
        """Zeigt eine Karte an und positioniert sie durch pack_forget() + pack()"""
        state = self._card_widgets.get(task_id)
        if state and state["outer"].winfo_exists():
            state["outer"].pack_forget()
            state["outer"].pack(fill="x")

    # === Karte verstecken ===
    def _hide_card(self, task_id):
        """Verbirgt eine Karte ohne sie zu löschen (pack_forget)"""
        state = self._card_widgets.get(task_id)
        if state and state["outer"].winfo_exists():
            state["outer"].pack_forget()

    # === Karte zerstören ===
    def _destroy_card_widget(self, task_id):
        """Löscht eine Task-Karte vollständig aus _card_widgets und zerstört das Widget"""
        state = self._card_widgets.pop(task_id, None)
        if state and state["outer"].winfo_exists():
            state["outer"].destroy()

    # === Task löschen ===
    def _delete_task(self, task_id):
        """Löscht eine Task über PlannerController.delete_task() und aktualisiert Board"""
        self.controller.delete_task(task_id)
        self.refresh_board()

    # === Task als erledigt markieren ===
    def _complete_task(self, task_id):
        """Markiert eine Task als 'erledigt' via PlannerController.complete_task()"""
        self.controller.complete_task(task_id)
        self.refresh_board()

    # === Task in Bearbeitung setzen ===
    def _bearbeitung_task(self, task_id):
        """Setzt eine Task auf Status 'in_bearbeitung' via PlannerController.bearbeitung_task()"""
        self.controller.bearbeitung_task(task_id)
        self.refresh_board()

    # === Drag-&-Drop Binding für Karte ===
    def _bind_card_drag(self, widget, task_id, title, current_status, root_card=None, card_info=None):
        """Bindet Drag-&-Drop Events (Press, Motion, Release) an eine Karte und ihre Kind-Widgets"""
        if not task_id or isinstance(widget, tk.Button):
            return
        if root_card is None:
            root_card = widget
        if card_info is None:
            card_info = {"title": title, "desc": "", "prio": "Medium", "date": "–", "task_id": task_id}
        try:
            widget.config(cursor="hand2")
        except tk.TclError:
            pass
        widget.bind("<ButtonPress-1>", lambda event: self._start_drag(event, task_id, title, current_status, root_card, card_info), add="+")
        widget.bind("<B1-Motion>", self._drag_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._drop_task, add="+")
        for child in widget.winfo_children():
            self._bind_card_drag(child, task_id, title, current_status, root_card, card_info)

    # === Drag-Start ===
    def _start_drag(self, event, task_id, title, current_status, root_card, card_info):
        """Initialisiert das Ziehen einer Task-Karte:
        - Speichert Start-Position, Offset, Source-Status
        - Nutzt gecachten Status aus _card_widgets"""
        cached = self._card_widgets.get(task_id, {})
        current_status = cached.get("status", current_status)
        self._drag_data = {"task_id": task_id, "title": title, "source_status": current_status, "start_x": event.x_root, "start_y": event.y_root, "offset_x": event.x_root - root_card.winfo_rootx(), "offset_y": event.y_root - root_card.winfo_rooty(), "dragging": False, "root_card": root_card, "card_info": card_info}
        self._last_drop_status = None

    # === Drag-Motion ===
    def _drag_motion(self, event):
        """Verarbeitet die Bewegung während des Ziehens:
        - Prüft ob Mindest-Distanz überschritten (5px) für echten Drag
        - Erstellt Drag-Preview Fenster
        - Updated Position des Previews kontinuierlich (16ms)
        - Ermittelt Drop-Zone und hebt sie hervor"""
        if not self._drag_data:
            return
        dx = abs(event.x_root - self._drag_data["start_x"])
        dy = abs(event.y_root - self._drag_data["start_y"])
        if not self._drag_data["dragging"]:
            if dx < 5 and dy < 5:
                return
            self._drag_data["dragging"] = True
            self._set_original_card_drag_state(True)
            self._create_drag_preview(event)
        self._schedule_drag_preview_move(event)
        target_status = self._get_drop_status_at(event.x_root, event.y_root)
        if target_status != self._last_drop_status:
            self._last_drop_status = target_status
            self._highlight_drop_zone(target_status)

    # === Drop/Release ===
    def _drop_task(self, event):
        """Verarbeitet das Loslassen einer Task beim Drag-&-Drop:
        - Ermittelt Ziel-Status
        - Zerstört Drag-Preview
        - Reset Original-Karte und Drop-Zones
        - Wenn echten Drag und Status geändert: Ruft _move_task_to_status() auf"""
        if not self._drag_data:
            return
        target_status = self._get_drop_status_at(event.x_root, event.y_root)
        source_status = self._drag_data["source_status"]
        task_id = self._drag_data["task_id"]
        was_dragging = self._drag_data["dragging"]
        self._destroy_drag_preview()
        self._set_original_card_drag_state(False)
        self._reset_drop_zone_highlights()
        self._drag_data = None
        self._last_drop_status = None
        if was_dragging and target_status and target_status != source_status:
            self._move_task_to_status(task_id, target_status)

    # === Drag-Preview erstellen ===
    def _create_drag_preview(self, event):
        """Erstellt ein Vorschau-Fenster während des Ziehens:
        - Toplevel Window mit overrideredirect (borderless)
        - Zeigt Task-Daten (Prio, Titel, Beschreibung, Datum)
        - Semi-transparent (0.94 alpha) wenn möglich"""
        if not self._drag_data or self._drag_preview:
            return
        colors = self.themes[self.current_theme]
        info = self._drag_data.get("card_info", {})
        root_card = self._drag_data.get("root_card")
        width = max(root_card.winfo_width() if root_card and root_card.winfo_exists() else 260, 240)
        preview = tk.Toplevel(self)
        preview.overrideredirect(True)
        preview.attributes("-topmost", True)
        try:
            preview.attributes("-alpha", 0.94)
        except tk.TclError:
            pass
        outer = tk.Frame(preview, bg=colors["border"], padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=colors["card"], padx=14, pady=12)
        card.pack(fill="both", expand=True)
        prio = info.get("prio", "Medium")
        prio_colors = {"High": colors["tag_high"], "Medium": colors["tag_med"], "Low": colors["tag_low"]}
        tk.Label(card, text=f"● {prio}", font=("Segoe UI Bold", 7), bg=colors["card"], fg=prio_colors.get(prio, colors["tag_low"]), anchor="w").pack(fill="x")
        tk.Label(card, text=info.get("title", self._drag_data.get("title", "")), font=("Segoe UI Semibold", 10), bg=colors["card"], fg=colors["text_main"], anchor="w", justify="left", wraplength=max(width - 35, 200)).pack(fill="x", pady=(6, 2))
        desc = info.get("desc")
        if desc:
            tk.Label(card, text=desc, font=self.FONT_MICRO, bg=colors["card"], fg=colors["text_sub"], anchor="w", justify="left", wraplength=max(width - 35, 200)).pack(fill="x", pady=(0, 8))
        tk.Frame(card, bg=colors["border"], height=1).pack(fill="x", pady=(4, 6))
        tk.Label(card, text=f"📅 {info.get('date', '–')}", font=self.FONT_MICRO, bg=colors["card"], fg=colors["text_sub"], anchor="w").pack(fill="x")
        preview.update_idletasks()
        self._drag_preview = preview
        self._schedule_drag_preview_move(event, immediate=True)

    # === Drag-Preview Position aktualisieren ===
    def _schedule_drag_preview_move(self, event, immediate=False):
        """Plant die Positionsaktualisierung des Drag-Preview:
        - Speichert neue Position in _drag_preview_pending_xy
        - Wenn immediate=True: sofort anwenden
        - Sonst: plant Update alle 16ms (60 FPS) um Performance zu sparen"""
        if not self._drag_preview or not self._drag_data:
            return
        x = event.x_root - self._drag_data.get("offset_x", 20)
        y = event.y_root - self._drag_data.get("offset_y", 20)
        self._drag_preview_pending_xy = (x, y)
        if immediate:
            self._apply_drag_preview_move()
            return
        if self._drag_preview_after_id is None:
            self._drag_preview_after_id = self.after(16, self._apply_drag_preview_move)

    # === Drag-Preview Position anwenden ===
    def _apply_drag_preview_move(self):
        """Setzt die neue Position des Drag-Preview Fensters via geometry()"""
        self._drag_preview_after_id = None
        if self._drag_preview and self._drag_preview_pending_xy:
            x, y = self._drag_preview_pending_xy
            self._drag_preview.geometry(f"+{x}+{y}")

    # === Drag-Preview zerstören ===
    def _destroy_drag_preview(self):
        """Löscht das Drag-Preview Fenster und räumt after_id auf"""
        if self._drag_preview_after_id:
            self.after_cancel(self._drag_preview_after_id)
            self._drag_preview_after_id = None
        if self._drag_preview:
            self._drag_preview.destroy()
            self._drag_preview = None
        self._drag_preview_pending_xy = None

    # === Drag-Status der Original-Karte setzen ===
    def _set_original_card_drag_state(self, active):
        """Aktualisiert das Styling der gezogenen Karte:
        - active=True: fette Border, Hover-Hintergrund
        - active=False: normale Border, normaler Hintergrund"""
        colors = self.themes[self.current_theme]
        card = self._drag_data.get("root_card") if self._drag_data else None
        if not card or not card.winfo_exists():
            return
        if active:
            card.config(highlightbackground=colors["accent"], highlightthickness=2, bg=colors["card_hover"])
            self._update_child_backgrounds(card, colors["card"], colors["card_hover"])
        else:
            card.config(highlightbackground=colors["border"], highlightthickness=1, bg=colors["card"])
            self._update_child_backgrounds(card, colors["card_hover"], colors["card"])

    # === Drop-Zone bei Koordinaten ermitteln ===
    def _get_drop_status_at(self, x_root, y_root):
        """Ermittelt welche Spalte sich unter den gegebenen Root-Koordinaten befindet:
        - Prüft ob y-Koordinate innerhalb Board-Bereich + 80px Puffer
        - Iteriert über _drop_zones und prüft x-Koordinate"""
        cols_frame = self.ui_elements.get("cols_frame") if hasattr(self, "ui_elements") else None
        if cols_frame and cols_frame.winfo_exists():
            top = cols_frame.winfo_rooty()
            bottom = top + cols_frame.winfo_height()
            if not (top - 80 <= y_root <= bottom + 80):
                return None
        for status, zone in self._drop_zones.items():
            if not zone.winfo_exists():
                continue
            left = zone.winfo_rootx()
            right = left + zone.winfo_width()
            if left <= x_root <= right:
                return status
        return None

    # === Drop-Zone hervorheben ===
    def _highlight_drop_zone(self, target_status):
        """Hebt die Ziel-Drop-Zone während des Ziehens hervor:
        - Ziel: fette Border (thickness=2), Accent-Farbe
        - Andere: normale Border, Border-Farbe"""
        colors = self.themes[self.current_theme]
        for status, zone in self._drop_zones.items():
            if not zone.winfo_exists():
                continue
            if status == target_status:
                zone.config(highlightbackground=colors["accent"], highlightthickness=2)
            else:
                zone.config(highlightbackground=colors["border"], highlightthickness=1)

    # === Drop-Zone-Hervorhebung zurücksetzen ===
    def _reset_drop_zone_highlights(self):
        """Entfernt die Hervorhebung aller Drop-Zonen auf normale Border"""
        colors = self.themes[self.current_theme]
        for zone in self._drop_zones.values():
            if zone.winfo_exists():
                zone.config(highlightbackground=colors["border"], highlightthickness=1)

    # === Task zu neuem Status verschieben ===
    def _move_task_to_status(self, task_id, target_status):
        """Verschiebt eine Task zu einem neuen Status:
        - Versucht PlannerController.move_task() wenn verfügbar
        - Fallback: nutzt spezifische Methoden (complete_task, bearbeitung_task)
        - Speichert via Controller.save() oder speichere_daten()
        - Aktualisiert Board oder zeigt Fehler"""
        moved = False
        try:
            if hasattr(self.controller, "move_task"):
                moved = bool(self.controller.move_task(task_id, target_status))
        except Exception:
            moved = False

        if not moved:
            # Versuche spezifische Helpers aus PlannerController
            try:
                if target_status == "erledigt" and hasattr(self.controller, "complete_task"):
                    moved = bool(self.controller.complete_task(task_id))
                elif target_status == "in_bearbeitung" and hasattr(self.controller, "bearbeitung_task"):
                    moved = bool(self.controller.bearbeitung_task(task_id))
            except Exception:
                moved = False

        if moved:
            try:
                if hasattr(self.controller, "save"):
                    self.controller.save()
                elif hasattr(self.controller, "speichere_daten"):
                    self.controller.speichere_daten()
            except Exception:
                pass
            self.refresh_board()
        else:
            try:
                messagebox.showwarning("Verschieben fehlgeschlagen", "Status konnte nicht geändert werden. Bitte Controller prüfen.")
            except Exception:
                pass

    # === Alternative Move-Methode versuchen ===
    def _call_existing_controller_move_method(self, task_id, target_status):
        """Versucht verschiedene mögliche Controller-Methodennamen zum Verschieben"""
        for name in ("move_task", "move_task_to_status", "update_task_status", "set_task_status", "change_task_status", "change_status", "update_status", "set_status"):
            method = getattr(self.controller, name, None)
            if not callable(method):
                continue
            for call in (
                lambda: method(task_id, target_status),
                lambda: method(task_id=task_id, status=target_status),
                lambda: method(task_id=task_id, neuer_status=target_status),
                lambda: method(id=task_id, status=target_status),
            ):
                try:
                    call()
                    return True
                except TypeError:
                    continue
        return False

    # === Task nach ID finden ===
    def _find_task_by_id(self, task_id):
        """Sucht eine Task im Controller nach ihrer ID via verschiedene Methoden"""
        if hasattr(self.controller, "get_tasks_by_status"):
            for status in self.STATUSES:
                try:
                    tasks = self.controller.get_tasks_by_status(status)
                except Exception:
                    continue
                for task in tasks:
                    if self._task_has_id(task, task_id):
                        return task
        for attr_name in ("tasks", "_tasks", "aufgaben", "_aufgaben", "task_list", "_task_list"):
            found = self._find_task_in_container(getattr(self.controller, attr_name, None), task_id)
            if found:
                return found
        return None

    # === Task in Container finden ===
    def _find_task_in_container(self, container, task_id):
        """Durchsucht einen Container (Dict, List, etc.) nach einer Task mit gegebener ID"""
        if container is None:
            return None
        if isinstance(container, dict):
            for key, value in container.items():
                if key == task_id and self._looks_like_task(value):
                    return value
                found = self._find_task_in_container(value, task_id)
                if found:
                    return found
        elif isinstance(container, (list, tuple, set)):
            for item in container:
                if self._task_has_id(item, task_id):
                    return item
        return None

    # === Prüfe ob Objekt Task ist ===
    def _looks_like_task(self, obj):
        """Prüft ob ein Objekt ein Task-ähnliches Objekt mit ID-Attribut ist"""
        return hasattr(obj, "get_id") or any(hasattr(obj, name) for name in ("id", "_id", "task_id", "_task_id"))

    # === Prüfe ob Task richtige ID hat ===
    def _task_has_id(self, task, task_id):
        """Prüft ob eine Task die gesuchte ID hat via Getter-Methoden oder Attribute"""
        for getter_name in ("get_id", "get_task_id"):
            getter = getattr(task, getter_name, None)
            if callable(getter):
                try:
                    if getter() == task_id:
                        return True
                except Exception:
                    pass
        for attr_name in ("id", "_id", "task_id", "_task_id"):
            if hasattr(task, attr_name):
                try:
                    if getattr(task, attr_name) == task_id:
                        return True
                except Exception:
                    pass
        return False

    # === Task-Status direkt setzen ===
    def _set_task_status_direct(self, task, target_status):
        """Setzt den Status direkt auf dem Task-Objekt via Setter oder Attribut"""
        for setter_name in ("set_status", "set_zustand", "set_state", "set_status_key", "set_status_name", "set_bearbeitungsstatus"):
            setter = getattr(task, setter_name, None)
            if callable(setter):
                try:
                    setter(target_status)
                    return True
                except TypeError:
                    continue
        for attr_name in ("status", "_status", "zustand", "_zustand", "state", "_state", "bearbeitungsstatus", "_bearbeitungsstatus"):
            if hasattr(task, attr_name):
                try:
                    setattr(task, attr_name, target_status)
                    return True
                except Exception:
                    continue
        return False

    # === Controller über Status-Änderung benachrichtigen ===
    def _notify_controller_after_status_change(self):
        """Benachrichtigt den Controller dass Änderungen gemacht wurden (save, refresh, etc.)"""
        for method_name in ("save", "save_tasks", "speichern", "persist", "refresh", "notify_change"):
            method = getattr(self.controller, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass

    # === Hintergrundfabe von Kind-Widgets aktualisieren ===
    def _update_child_backgrounds(self, parent, old_bg, new_bg):
        """Aktualisiert die Hintergrundfarbe aller Kind-Widgets rekursiv von old_bg zu new_bg"""
        for child in parent.winfo_children():
            try:
                if child.cget("bg") == old_bg:
                    child.config(bg=new_bg)
            except tk.TclError:
                pass
            self._update_child_backgrounds(child, old_bg, new_bg)

    # === Dialog zum Hinzufügen einer Task ===
    def _add_task_dialog(self):
        """Zeigt einen Dialog zum Erstellen einer neuen Task:
        - Eingabe: Titel (erforderlich), Beschreibung, Priorität (Low/Medium/High), Datum
        - Validierung: Titel nicht leer, Datum im Format TT.MM.YYYY
        - Bei Submit: ruft PlannerController.add_task() auf und aktualisiert Board"""
        win = tk.Toplevel(self)
        win.title("Neue Aufgabe")
        win.geometry("420x600")
        win.resizable(False, False)
        win.grab_set()
        win.transient(self)
        colors = self.themes[self.current_theme]
        win.config(bg=colors["card"])
        pad = {"padx": 24, "pady": 6}
        tk.Label(win, text="Neue Aufgabe erstellen", font=("Segoe UI Bold", 14), bg=colors["card"], fg=colors["text_main"]).pack(padx=24, pady=(20, 4))
        tk.Frame(win, bg=colors["border"], height=1).pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(win, text="Titel *", font=self.FONT_SMALL, bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        title_var = tk.StringVar()
        title_entry = tk.Entry(win, textvariable=title_var, font=self.FONT_BODY, bg=colors["bg"], fg=colors["text_main"], relief="flat", insertbackground=colors["accent"], bd=1, highlightthickness=1, highlightbackground=colors["border"], highlightcolor=colors["border_focus"])
        title_entry.pack(fill="x", **pad, ipady=6)
        title_entry.focus()
        tk.Label(win, text="Beschreibung", font=self.FONT_SMALL, bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        desc_text = tk.Text(win, font=self.FONT_BODY, bg=colors["bg"], fg=colors["text_main"], relief="flat", bd=1, height=4, wrap="word", insertbackground=colors["accent"], highlightthickness=1, highlightbackground=colors["border"], highlightcolor=colors["border_focus"])
        desc_text.pack(fill="x", **pad)
        tk.Label(win, text="Priorität", font=self.FONT_SMALL, bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        prio_var = tk.IntVar(value=3)
        prio_frame = tk.Frame(win, bg=colors["card"])
        prio_frame.pack(anchor="w", **pad)
        for label, value, color in [("● Low", 1, colors["tag_low"]), ("● Medium", 3, colors["tag_med"]), ("● High", 5, colors["tag_high"] )]:
            tk.Radiobutton(prio_frame, text=label, variable=prio_var, value=value, font=("Segoe UI Bold", 9), bg=colors["card"], fg=color, activebackground=colors["card"], selectcolor=colors["card"]).pack(side="left", padx=(0, 10))
        tk.Label(win, text="Datum (TT.MM.JJ)", font=self.FONT_SMALL, bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        date_var = tk.StringVar()

        date_entry = tk.Entry(
            win,
            textvariable=date_var,
            font=self.FONT_BODY,
            bg=colors["bg"],
            fg=colors["text_main"],
            relief="flat",
            insertbackground=colors["accent"],
            bd=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["border_focus"])
        
        date_entry.pack(fill="x", **pad, ipady=6)

        def submit():
            title = title_var.get().strip()
            if not title:
                messagebox.showerror("Ungültiger Titel", "Bitte einen Titel eingeben.")
                try:
                    title_entry.focus_set()
                except Exception:
                    pass
                return
            date_obj = None
            date_text = date_var.get().strip()
            if date_text:
                try:
                    date_obj = datetime.strptime(date_text, "%d.%m.%Y")
                except ValueError:
                    messagebox.showerror("Ungültiges Datum", "Bitte Datum im Format TT.MM.JJJJ eingeben oder leer lassen.")
                    try:
                        date_entry.focus_set()
                    except Exception:
                        pass
                    return
            desc = desc_text.get("1.0", "end").strip()
            try:
                self.controller.add_task(title, desc, prio=prio_var.get(), faellig=date_obj)
            except Exception:
                messagebox.showerror("Fehler", "Aufgabe konnte nicht hinzugefügt werden.")
            win.destroy()
            self.refresh_board()

        tk.Frame(win, bg=colors["border"], height=1).pack(fill="x", padx=24, pady=(10, 0))
        btn_row = tk.Frame(win, bg=colors["card"])
        btn_row.pack(fill="x", padx=24, pady=10)
        tk.Button(btn_row, text="Abbrechen", command=win.destroy, font=self.FONT_SMALL, bg=colors["btn_theme"], fg="#FFFFFF", relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="➕ Hinzufügen", command=submit, font=("Segoe UI Bold", 9), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right")

    # === Demo-Task hinzufügen ===
    def _add_demo_task(self):
        """Fügt eine Test-Task zum Testen der Scroll-Funktionalität via Controller hinzu"""
        try:
            self.controller.add_task("Demo-Aufgabe", "Diese Demo-Karte dient zum Testen der Scrollfunktion.", prio=3)
        except Exception:
            pass
        self.refresh_board()

    # === Demo-Daten laden ===
    def _load_demo(self):
        """Lädt Beispieldaten über PlannerController.load_demo_data()"""
        try:
            self.controller.load_demo_data()
        except Exception:
            # Fallback: clear via controller wenn load_demo_data fehlt
            if hasattr(self.controller, "clear_all_tasks"):
                try:
                    self.controller.clear_all_tasks()
                    self.controller.load_demo_data()
                except Exception:
                    pass
        self.refresh_board()

    # === Farbe für Datum-Anzeige abrufen ===
    def _get_date_display_color(self, task_id, date_str):
        """Gibt die Schriftfarbe für die Datum-Anzeige basierend auf Status:
        - Wenn Task erledigt: text_sub (grau)
        - Wenn überfällig: tag_high (rot)
        - Sonst: text_sub (grau)"""
        colors = self.themes[self.current_theme]
        task = None
        try:
            task = getattr(self.controller, "get_task", lambda tid: None)(task_id)
        except Exception:
            task = None

        if task and getattr(task, "get_status", lambda: None)() == "erledigt":
            return colors["text_sub"]

        if date_str == "–":
            return colors["text_sub"]

        try:
            task_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            today = datetime.now().date()
            if task_date < today:
                return colors["tag_high"]
            return colors["text_sub"]
        except ValueError:
            return colors["text_sub"]

    # === Hintergrundfarbe für Datum-Anzeige abrufen ===
    def _get_date_display_bg(self, task_id, date_str):
        """Gibt die Hintergrundfarbe für die Datum-Anzeige basierend auf Status:
        - Wenn Task erledigt: card (normal)
        - Wenn überfällig: rötliche Hintergrundfarbe
        - Sonst: card (normal)"""
        colors = self.themes[self.current_theme]
        task = None
        try:
            task = getattr(self.controller, "get_task", lambda tid: None)(task_id)
        except Exception:
            task = None

        if task and getattr(task, "get_status", lambda: None)() == "erledigt":
            return colors["card"]

        if date_str == "–":
            return colors["card"]

        try:
            task_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            today = datetime.now().date()
            if task_date < today:
                return "#FFE5E5" if self.current_theme == "light" else "#3D1F1F"
            return colors["card"]
        except ValueError:
            return colors["card"]

    # === Theme umschalten ===
    def toggle_theme(self):
        """Wechselt zwischen Hell- und Dunkel-Theme:
        - Ändert current_theme
        - Zerstört und recreated alle Widgets (kompletter Rebuild)
        - Aktualisiert Board mit neuem Theme"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.card_images = []
        self._card_widgets = {}
        self._columns = {}
        self._column_scrolls = {}
        self._column_count_labels = {}
        for widget in self.winfo_children():
            widget.destroy()
        self.ui_elements = {}
        self._build_layout()
        self._populate_layout()
        self.refresh_board()

    # === Vollbildmodus aktivieren ===
    def _toggle_fullscreen(self, event=None):
        """Schaltet Vollbildmodus ein und aus via -fullscreen Fenster-Attribute"""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    # === Vollbildmodus deaktivieren ===
    def _exit_fullscreen(self, event=None):
        """Schaltet Vollbildmodus aus wenn aktiv"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)


if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()