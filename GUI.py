import tkinter as tk
from tkinter import messagebox, simpledialog
import ctypes
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from Controller import PlannerController
from datetime import datetime
import math

# =============================================================================
# HIGH-DPI SCALING
# =============================================================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


# =============================================================================
# CUSTOM SCROLLABLE FRAME
# =============================================================================
class ScrollableFrame(tk.Frame):
    """Ein Frame mit vertikalem Scrollbalken"""
    def __init__(self, parent, bg, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# =============================================================================
# TOOLTIP KLASSE
# =============================================================================
class Tooltip:
    def __init__(self, widget, text, bg="#1A1A1A", fg="#FFFFFF"):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg=self.bg, fg=self.fg,
                 font=("Segoe UI", 9), padx=10, pady=5,
                 relief="flat", bd=0).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# =============================================================================
# HAUPTANWENDUNG
# =============================================================================
class DevPulsePlanner(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DevPulse Planner")
        self.geometry("1440x900")
        self.minsize(1000, 650)
        self.resizable(True, True)

        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self.is_fullscreen = False

        self.controller = PlannerController(view=self)

        # ===== THEMES =====
        self.themes = {
            "light": {
                "bg":           "#F0F2F5",
                "sidebar":      "#FFFFFF",
                "sidebar_top":  "#0A1628",   # Dunkle obere Seitenleiste
                "text_main":    "#0D1117",
                "text_sub":     "#7D8590",
                "text_inv":     "#FFFFFF",    # Invertierter Text (für dunkle Flächen)
                "accent":       "#1A73E8",
                "accent2":      "#00C896",
                "card":         "#FFFFFF",
                "card_hover":   "#F6F8FF",
                "border":       "#E2E8F0",
                "border_focus": "#1A73E8",
                "topbar":       "#0A1628",
                "col_open":     "#EEF2FF",   # Spalte: Offen
                "col_wip":      "#FFF7ED",   # Spalte: In Arbeit
                "col_done":     "#F0FDF4",   # Spalte: Erledigt
                "tag_high":     "#FF4D6D",
                "tag_med":      "#FF9A3C",
                "tag_low":      "#1A73E8",
                "shadow":       "#00000018",
                "btn_add":      "#1A73E8",
                "btn_demo":     "#6366F1",
                "btn_theme":    "#374151",
                "badge_open":   "#3B82F6",
                "badge_wip":    "#F59E0B",
                "badge_done":   "#10B981",
            },
            "dark": {
                "bg":           "#0D1117",
                "sidebar":      "#161B22",
                "sidebar_top":  "#0D1117",
                "text_main":    "#E6EDF3",
                "text_sub":     "#7D8590",
                "text_inv":     "#E6EDF3",
                "accent":       "#58A6FF",
                "accent2":      "#3FB950",
                "card":         "#161B22",
                "card_hover":   "#1C2128",
                "border":       "#30363D",
                "border_focus": "#58A6FF",
                "topbar":       "#010409",
                "col_open":     "#161B22",
                "col_wip":      "#1C1811",
                "col_done":     "#0F1A12",
                "tag_high":     "#FF4D6D",
                "tag_med":      "#FF9A3C",
                "tag_low":      "#58A6FF",
                "shadow":       "#00000040",
                "btn_add":      "#238636",
                "btn_demo":     "#6E40C9",
                "btn_theme":    "#30363D",
                "badge_open":   "#1D4ED8",
                "badge_wip":    "#D97706",
                "badge_done":   "#059669",
            }
        }
        self.current_theme = "light"

        self.ui_elements = {}
        self.card_images = []
        self._task_count = {"offen": 0, "in_bearbeitung": 0, "erledigt": 0}

        self._setup_styles()
        self._build_layout()
        self._populate_layout()
        self.load_initial_data()

    # =========================================================================
    # SETUP & LAYOUT
    # =========================================================================
    def _setup_styles(self):
        """Font-Konstanten"""
        self.FONT_DISPLAY = ("Segoe UI Black", 22, "bold")
        self.FONT_TITLE   = ("Segoe UI Semibold", 14)
        self.FONT_HEAD    = ("Segoe UI Bold", 11)
        self.FONT_BODY    = ("Segoe UI", 10)
        self.FONT_SMALL   = ("Segoe UI", 9)
        self.FONT_MICRO   = ("Segoe UI", 8)
        self.FONT_MONO    = ("Consolas", 9)
        self.FONT_NAV     = ("Segoe UI Semibold", 10)
        self.FONT_BADGE   = ("Segoe UI Bold", 8)

    def _build_layout(self):
        colors = self.themes[self.current_theme]
        self.config(bg=colors["bg"])

        # Sidebar (schmal, links)
        self.sidebar = tk.Frame(self, width=240, bg=colors["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Hauptbereich
        self.main_area = tk.Frame(self, bg=colors["bg"])
        self.main_area.pack(side="left", fill="both", expand=True)

        self.ui_elements["sidebar"] = self.sidebar
        self.ui_elements["main_area"] = self.main_area

    def _populate_layout(self):
        colors = self.themes[self.current_theme]

        # ── SIDEBAR: Branding-Block ──────────────────────────────────────────
        brand_frame = tk.Frame(self.sidebar, bg=colors["sidebar_top"], height=72)
        brand_frame.pack(fill="x")
        brand_frame.pack_propagate(False)
        self.ui_elements["brand_frame"] = brand_frame

        self._draw_logo(brand_frame)

        # ── SIDEBAR: Suchfeld ────────────────────────────────────────────────
        search_outer = tk.Frame(self.sidebar, bg=colors["sidebar"], pady=8, padx=12)
        search_outer.pack(fill="x")

        search_frame = tk.Frame(search_outer, bg=colors["border"], padx=2, pady=2)
        search_frame.pack(fill="x")

        search_inner = tk.Frame(search_frame, bg=colors["card"])
        search_inner.pack(fill="x")

        tk.Label(search_inner, text="🔍", font=self.FONT_BODY,
                 bg=colors["card"], fg=colors["text_sub"]).pack(side="left", padx=(8, 4), pady=6)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(search_inner, textvariable=self.search_var,
                                 font=self.FONT_SMALL, bg=colors["card"],
                                 fg=colors["text_main"], relief="flat", bd=0,
                                 insertbackground=colors["accent"])
        search_entry.pack(side="left", fill="x", expand=True, pady=6, padx=(0, 8))
        search_entry.insert(0, "Suchen…")
        search_entry.bind("<FocusIn>",  lambda e: search_entry.delete(0, "end")
                          if search_entry.get() == "Suchen…" else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "Suchen…")
                          if not search_entry.get() else None)
        self.ui_elements["search_entry"] = search_entry

        # ── SIDEBAR: Navigation ──────────────────────────────────────────────
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)

        nav_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        nav_container.pack(fill="x", pady=(8, 0))
        self.ui_elements["nav_container"] = nav_container

        self._build_nav(nav_container)

        # ── SIDEBAR: Statistiken ─────────────────────────────────────────────
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12, pady=(8, 0))

        stats_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=10)
        stats_frame.pack(fill="x")
        self.ui_elements["stats_frame"] = stats_frame
        self._build_stats(stats_frame)

        # ── SIDEBAR: Aktionsknöpfe ───────────────────────────────────────────
        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)

        btn_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=12)
        btn_frame.pack(fill="x", side="bottom")
        self.ui_elements["btn_frame"] = btn_frame
        self._build_sidebar_buttons(btn_frame)

        # ── MAIN AREA: TopBar ────────────────────────────────────────────────
        topbar = tk.Frame(self.main_area, bg=colors["topbar"], height=72)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.ui_elements["topbar"] = topbar
        self._build_topbar(topbar)

        # ── MAIN AREA: Kanban Board ──────────────────────────────────────────
        board_outer = tk.Frame(self.main_area, bg=colors["bg"])
        board_outer.pack(fill="both", expand=True)
        self.ui_elements["board_outer"] = board_outer

        board_padding = 16

        board_header_outer = tk.Frame(board_outer, bg=colors["bg"])
        board_header_outer.pack(fill="x", padx=board_padding, pady=(20, 0))

        board_header = tk.Frame(board_header_outer, bg=colors["bg"])
        board_header.pack(fill="x")

        tk.Label(board_header, text="Sprint Board",
                 font=("Segoe UI Black", 20), bg=colors["bg"],
                 fg=colors["text_main"]).pack(side="left")

        date_lbl = tk.Label(board_header,
                            text=datetime.now().strftime("KW %W  ·  %d. %B %Y"),
                            font=self.FONT_SMALL, bg=colors["bg"],
                            fg=colors["text_sub"])
        date_lbl.pack(side="right", pady=6)
        self.ui_elements["date_lbl"] = date_lbl

        tk.Frame(board_outer, bg=colors["border"], height=1).pack(
            fill="x", padx=board_padding, pady=(8, 10))

        cols_frame = tk.Frame(board_outer, bg=colors["bg"])
        cols_frame.pack(fill="both", expand=True, padx=board_padding, pady=16)
        cols_frame.columnconfigure((0, 1, 2), weight=1, uniform="col")
        cols_frame.rowconfigure(0, weight=1)
        self.ui_elements["cols_frame"] = cols_frame

    # =========================================================================
    # UI BAUSTEINE
    # =========================================================================
    def _draw_logo(self, parent):
        colors = self.themes[self.current_theme]
        try:
            img = Image.open("Logo.png").resize((32, 32), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(img)
            tk.Label(parent, image=self.logo_tk,
                     bg=colors["sidebar_top"], bd=0).pack(side="left", padx=(16, 8), pady=20)
        except Exception:
            cv = tk.Canvas(parent, width=32, height=32,
                           bg=colors["sidebar_top"], highlightthickness=0)
            cv.pack(side="left", padx=(16, 8), pady=20)
            cv.create_oval(2, 2, 30, 30, fill=colors["accent"], outline="")
            cv.create_text(16, 16, text="D", fill="white",
                           font=("Segoe UI Black", 14))

        name = tk.Frame(parent, bg=colors["sidebar_top"])
        name.pack(side="left")
        tk.Label(name, text="Dev", font=("Segoe UI Black", 15),
                 bg=colors["sidebar_top"], fg=colors["accent"]).pack(side="left")
        tk.Label(name, text="Pulse", font=("Segoe UI Semibold", 15),
                 bg=colors["sidebar_top"], fg="#FFFFFF").pack(side="left")

    def _build_nav(self, parent):
        colors = self.themes[self.current_theme]
        self.nav_items = [
            ("📋", "Board",     True),
            ("📈", "Analysen",  False),
            ("🗓️", "Kalender",  False),
            ("⚙️", "Einstellungen", False),
        ]
        for icon, label, active in self.nav_items:
            self._make_nav_item(parent, icon, label, active)

    def _make_nav_item(self, parent, icon, label, active):
        colors = self.themes[self.current_theme]
        bg = colors["col_open"] if active else colors["sidebar"]
        fg = colors["accent"] if active else colors["text_sub"]
        bar_color = colors["accent"] if active else colors["sidebar"]

        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)

        # Aktiver Balken
        bar = tk.Frame(row, bg=bar_color, width=3)
        bar.pack(side="left", fill="y")

        tk.Label(row, text=f"  {icon}  {label}", font=self.FONT_NAV,
                 bg=bg, fg=fg, anchor="w").pack(
                 side="left", fill="x", expand=True, ipady=11, padx=4)

    def _build_stats(self, parent):
        colors = self.themes[self.current_theme]

        for child in parent.winfo_children():
            child.destroy()

        tk.Label(parent, text="ÜBERSICHT",
             font=self.FONT_BADGE, bg=colors["sidebar"],
             fg=colors["text_sub"]).pack(anchor="w", pady=(0, 8))

        stat_row = tk.Frame(parent, bg=colors["sidebar"])
        stat_row.pack(fill="x")

        stats = [
            ("Offen",   str(self._task_count["offen"]),         colors["badge_open"]),
            ("Aktiv",   str(self._task_count["in_bearbeitung"]), colors["badge_wip"]),
            ("Fertig",  str(self._task_count["erledigt"]),       colors["badge_done"]),
        ]
        for i, (lbl, val, clr) in enumerate(stats):
            cell = tk.Frame(stat_row, bg=colors["card"],
                            highlightbackground=colors["border"], highlightthickness=1)
            cell.pack(side="left", expand=True, fill="x",
                      padx=(0, 0 if i == 2 else 4))

            tk.Label(cell, text=val, font=("Segoe UI Black", 18),
                     bg=colors["card"], fg=clr).pack(pady=(8, 0))
            tk.Label(cell, text=lbl, font=self.FONT_MICRO,
                     bg=colors["card"], fg=colors["text_sub"]).pack(pady=(0, 6))

        self.ui_elements["stat_row"] = stat_row

    def _build_sidebar_buttons(self, parent):
        colors = self.themes[self.current_theme]

        def styled_btn(text, bg, cmd, tooltip_text=None):
            btn = tk.Button(parent, text=text, command=cmd,
                            font=("Segoe UI Bold", 9), bg=bg, fg="#FFFFFF",
                            relief="flat", bd=0, padx=12, pady=10,
                            cursor="hand2", activebackground=bg,
                            activeforeground="#FFFFFF")
            btn.pack(fill="x", pady=3)
            if tooltip_text:
                Tooltip(btn, tooltip_text,
                        bg=colors["topbar"], fg=colors["text_inv"])
            return btn

        styled_btn("➕  Neue Aufgabe", colors["btn_add"],
                   self._add_task_dialog, "Neue Task erstellen (Strg+N)")
        styled_btn("🎲  Demo laden",   colors["btn_demo"],
                   self._load_demo,    "Beispieldaten laden")
        styled_btn("🌙  Theme wechseln", colors["btn_theme"],
                   self.toggle_theme,  "Hell / Dunkel umschalten (F10)")

        tk.Label(parent, text="F11 Vollbild · ESC Beenden",
                 font=("Segoe UI", 7), bg=colors["sidebar"],
                 fg=colors["text_sub"]).pack(pady=(10, 0))

    def _build_topbar(self, topbar):
        colors = self.themes[self.current_theme]
        tk.Label(topbar, text="Sprint Board",
                 font=("Segoe UI Semibold", 12),
                 bg=colors["topbar"], fg="#FFFFFF").pack(
                 side="left", padx=16, pady=18)

        # Rechte Seite: Quick-Action-Knöpfe
        right = tk.Frame(topbar, bg=colors["topbar"])
        right.pack(side="right", padx=16)

        tk.Button(right, text="➕ Task", command=self._add_task_dialog,
                  font=self.FONT_BADGE, bg=colors["btn_add"], fg="#FFFFFF",
                  relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=4)

        tk.Button(right, text="🔄 Refresh", command=self.refresh_board,
                  font=self.FONT_BADGE, bg=colors["btn_theme"], fg="#FFFFFF",
                  relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=4)

    # =========================================================================
    # DATEN & BOARD
    # =========================================================================
    def load_initial_data(self):
        self.controller.load_demo_data()

    def _on_search(self, *args):
        self.refresh_board()

    def refresh_board(self):
        colors = self.themes[self.current_theme]
        cols_frame = self.ui_elements["cols_frame"]

        for w in cols_frame.winfo_children():
            w.destroy()

        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        if query == "suchen…":
            query = ""

        def filtered(tasks):
            if not query:
                return tasks
            return [t for t in tasks if
                    query in t.get_titel().lower() or
                    query in (t.get_beschreibung() or "").lower()]

        offen     = filtered(self.controller.get_tasks_by_status("offen"))
        in_arb    = filtered(self.controller.get_tasks_by_status("in_bearbeitung"))
        erledigt  = filtered(self.controller.get_tasks_by_status("erledigt"))

        self._task_count = {
            "offen": len(offen),
            "in_bearbeitung": len(in_arb),
            "erledigt": len(erledigt),
        }

        # Stats aktualisieren
        if "stat_row" in self.ui_elements:
            self.ui_elements["stat_row"].destroy()
        if "stats_frame" in self.ui_elements:
            self._build_stats(self.ui_elements["stats_frame"])

        columns = [
            ("📥  Offen",        offen,    colors["col_open"],  colors["badge_open"]),
            ("⚡  In Bearbeitung", in_arb,  colors["col_wip"],   colors["badge_wip"]),
            ("✅  Erledigt",      erledigt, colors["col_done"],  colors["badge_done"]),
        ]

        for col_idx, (title, tasks, col_bg, badge_color) in enumerate(columns):
            if col_idx < 2:
                grid_padx = (0, 8)
            else:
                grid_padx = (0, 0)

            wrapper = tk.Frame(cols_frame, bg=col_bg,
                               highlightbackground=colors["border"],
                               highlightthickness=1)
            wrapper.grid(row=0, column=col_idx, sticky="nsew",
                         padx=grid_padx, pady=4)

            # Spalten-Header
            header = tk.Frame(wrapper, bg=col_bg, padx=14, pady=12)
            header.pack(fill="x")

            tk.Label(header, text=title, font=self.FONT_HEAD,
                     bg=col_bg, fg=colors["text_main"]).pack(side="left")

            badge = tk.Label(header, text=str(len(tasks)),
                         font=self.FONT_BADGE, bg=badge_color,
                         fg="#FFFFFF", padx=7, pady=2)
            badge.pack(side="right")

            tk.Frame(wrapper, bg=colors["border"], height=1).pack(fill="x", padx=10)

            # Scrollbarer Kartenbereich
            scroll = ScrollableFrame(wrapper, bg=col_bg)
            scroll.pack(fill="both", expand=True, padx=0, pady=0)

            if tasks:
                for task in tasks:
                    prio_map = {1: "Low", 3: "Medium", 5: "High"}
                    prio = prio_map.get(
                        task.get_prio() if hasattr(task, "get_prio") else 3, "Medium")
                    datum = "–"
                    if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
                        datum = task.get_faelligkeitsdatum().strftime("%d.%m.%Y")

                    self._create_card(scroll.inner, task.get_titel(),
                                  task.get_beschreibung(), prio,
                                  datum, task.get_id(), col_bg)
            else:
                empty = tk.Frame(scroll.inner, bg=col_bg)
                empty.pack(fill="x", padx=14, pady=30)
                tk.Label(empty, text="🗒", font=("Segoe UI", 28),
                     bg=col_bg, fg=colors["text_sub"]).pack()
                tk.Label(empty, text="Keine Aufgaben",
                     font=self.FONT_SMALL, bg=col_bg,
                     fg=colors["text_sub"]).pack(pady=(4, 0))

    def _create_card(self, parent, title, desc, prio, date, task_id, col_bg):
        colors = self.themes[self.current_theme]

        outer = tk.Frame(parent, bg=col_bg, padx=10, pady=4)
        outer.pack(fill="x")

        card = tk.Frame(outer, bg=colors["card"],
                        highlightbackground=colors["border"],
                        highlightthickness=1,
                        padx=14, pady=12,
                        cursor="hand2")
        card.pack(fill="x")

        # Hover-Effekt
        def on_enter(e):
            card.config(highlightbackground=colors["border_focus"],
                        bg=colors["card_hover"])
            for c in card.winfo_children():
                try:
                    if c.cget("bg") == colors["card"]:
                        c.config(bg=colors["card_hover"])
                except Exception:
                    pass

        def on_leave(e):
            card.config(highlightbackground=colors["border"],
                        bg=colors["card"])
            for c in card.winfo_children():
                try:
                    if c.cget("bg") == colors["card_hover"]:
                        c.config(bg=colors["card"])
                except Exception:
                    pass

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        # ── Card: Header ─────────────────────────────────────────────────────
        header = tk.Frame(card, bg=colors["card"])
        header.pack(fill="x")

        prio_colors = {"High": colors["tag_high"],
                       "Medium": colors["tag_med"],
                       "Low": colors["tag_low"]}
        p_clr = prio_colors.get(prio, colors["tag_low"])

        tk.Label(header, text=f"● {prio}",
                 font=("Segoe UI Bold", 7), bg=colors["card"],
                 fg=p_clr).pack(side="left")

        if task_id:
            del_btn = tk.Button(header, text="✕",
                                font=("Segoe UI Bold", 8),
                                bg=colors["card"], fg=colors["text_sub"],
                                relief="flat", bd=0, cursor="hand2",
                                activeforeground="#FF4D6D",
                                activebackground=colors["card"],
                                command=lambda: self.controller.delete_task(task_id))
            del_btn.pack(side="right")

        # ── Card: Titel ──────────────────────────────────────────────────────
        tk.Label(card, text=title, font=("Segoe UI Semibold", 10),
                 bg=colors["card"], fg=colors["text_main"],
                 anchor="w", wraplength=240, justify="left").pack(
                 fill="x", pady=(6, 2))

        # ── Card: Beschreibung ───────────────────────────────────────────────
        if desc:
            tk.Label(card, text=desc, font=self.FONT_MICRO,
                     bg=colors["card"], fg=colors["text_sub"],
                     anchor="w", wraplength=240, justify="left").pack(
                     fill="x", pady=(0, 8))

        # ── Card: Trennlinie ─────────────────────────────────────────────────
        tk.Frame(card, bg=colors["border"], height=1).pack(fill="x", pady=(4, 6))

        # ── Card: Footer ─────────────────────────────────────────────────────
        footer = tk.Frame(card, bg=colors["card"])
        footer.pack(fill="x")

        tk.Label(footer, text=f"📅 {date}",
                 font=self.FONT_MICRO, bg=colors["card"],
                 fg=colors["text_sub"]).pack(side="left")

        if task_id:
            done_btn = tk.Button(footer, text="✓ Erledigt",
                                 font=("Segoe UI Bold", 7),
                                 bg=colors["btn_add"], fg="#FFFFFF",
                                 relief="flat", bd=0, padx=7, pady=2,
                                 cursor="hand2",
                                 command=lambda: self.controller.complete_task(task_id))
            done_btn.pack(side="right")

    # =========================================================================
    # DIALOGE
    # =========================================================================
    def _add_task_dialog(self):
        win = tk.Toplevel(self)
        win.title("Neue Aufgabe")
        win.geometry("420x360")
        win.resizable(False, False)
        win.grab_set()
        win.transient(self)

        colors = self.themes[self.current_theme]
        win.config(bg=colors["card"])

        pad = dict(padx=24, pady=6)

        tk.Label(win, text="Neue Aufgabe erstellen",
                 font=("Segoe UI Bold", 14),
                 bg=colors["card"], fg=colors["text_main"]).pack(**pad, pady=(20, 4))
        tk.Frame(win, bg=colors["border"], height=1).pack(fill="x", padx=24, pady=(0, 10))

        # Titel
        tk.Label(win, text="Titel *", font=self.FONT_SMALL,
                 bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        title_var = tk.StringVar()
        title_entry = tk.Entry(win, textvariable=title_var,
                               font=self.FONT_BODY, bg=colors["bg"],
                               fg=colors["text_main"], relief="flat",
                               insertbackground=colors["accent"], bd=1,
                               highlightthickness=1,
                               highlightbackground=colors["border"],
                               highlightcolor=colors["border_focus"])
        title_entry.pack(fill="x", **pad, ipady=6)
        title_entry.focus()

        # Beschreibung
        tk.Label(win, text="Beschreibung", font=self.FONT_SMALL,
                 bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        desc_text = tk.Text(win, font=self.FONT_BODY, bg=colors["bg"],
                            fg=colors["text_main"], relief="flat",
                            bd=1, height=4, wrap="word",
                            insertbackground=colors["accent"],
                            highlightthickness=1,
                            highlightbackground=colors["border"],
                            highlightcolor=colors["border_focus"])
        desc_text.pack(fill="x", **pad)

        # Priorität
        tk.Label(win, text="Priorität", font=self.FONT_SMALL,
                 bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", **pad)
        prio_var = tk.IntVar(value=3)
        prio_frame = tk.Frame(win, bg=colors["card"])
        prio_frame.pack(anchor="w", **pad)
        for label, val, clr in [("● Low", 1, colors["tag_low"]),
                                  ("● Medium", 3, colors["tag_med"]),
                                  ("● High", 5, colors["tag_high"])]:
            tk.Radiobutton(prio_frame, text=label, variable=prio_var, value=val,
                           font=("Segoe UI Bold", 9), bg=colors["card"],
                           fg=clr, activebackground=colors["card"],
                           selectcolor=colors["card"]).pack(side="left", padx=(0, 10))

        def _submit():
            titel = title_var.get().strip()
            if not titel:
                title_entry.config(highlightbackground=colors["tag_high"])
                return
            desc = desc_text.get("1.0", "end").strip()
            self.controller.add_task(titel, desc, prio=prio_var.get())
            win.destroy()

        tk.Frame(win, bg=colors["border"], height=1).pack(fill="x", padx=24, pady=(10, 0))
        btn_row = tk.Frame(win, bg=colors["card"])
        btn_row.pack(fill="x", padx=24, pady=10)

        tk.Button(btn_row, text="Abbrechen", command=win.destroy,
                  font=self.FONT_SMALL, bg=colors["btn_theme"], fg="#FFFFFF",
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="➕ Hinzufügen", command=_submit,
                  font=("Segoe UI Bold", 9), bg=colors["btn_add"], fg="#FFFFFF",
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right")

    def _load_demo(self):
        self.controller.load_demo_data()

    # =========================================================================
    # THEME TOGGLE
    # =========================================================================
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.card_images = []

        # Sidebar & Main vollständig neu aufbauen
        for w in self.winfo_children():
            w.destroy()

        self.ui_elements = {}
        self._build_layout()
        self._populate_layout()

        # Suche zurücksetzen
        self.refresh_board()

    # =========================================================================
    # FULLSCREEN
    # =========================================================================
    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes('-fullscreen', self.is_fullscreen)

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes('-fullscreen', False)


if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()