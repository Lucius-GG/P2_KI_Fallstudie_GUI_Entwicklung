import tkinter as tk
import ctypes
from datetime import datetime
from Controller import PlannerController

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

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._draw_scrollbar(*self._last_scroll)

    def _on_inner_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar_visibility()
        self._draw_scrollbar(*self._last_scroll)

    def _on_canvas_scroll(self, first, last):
        first = float(first)
        last = float(last)
        self._last_scroll = (first, last)
        self._update_scrollbar_visibility()
        self._draw_scrollbar(first, last)

    def _update_scrollbar_visibility(self):
        bbox = self.canvas.bbox("all")
        needs_scrollbar = bool(bbox and bbox[3] > self.canvas.winfo_height())
        if needs_scrollbar:
            if not self.scrollbar_canvas.winfo_ismapped():
                self.scrollbar_canvas.pack(side="right", fill="y")
        else:
            if self.scrollbar_canvas.winfo_ismapped():
                self.scrollbar_canvas.pack_forget()

    def _draw_scrollbar(self, first=0.0, last=1.0, active=False):
        self.scrollbar_canvas.delete("all")
        height = max(self.scrollbar_canvas.winfo_height(), 1)
        width = self.scrollbar_width

        self.scrollbar_canvas.create_rectangle(0, 0, width, height, fill=self.scrollbar_trough, outline="")

        if last - first >= 0.999:
            return

        min_thumb_height = 34
        thumb_top = int(first * height)
        thumb_bottom = int(last * height)
        if thumb_bottom - thumb_top < min_thumb_height:
            thumb_bottom = min(height, thumb_top + min_thumb_height)
            if thumb_bottom == height:
                thumb_top = max(0, height - min_thumb_height)

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

    def _on_scrollbar_press(self, event):
        height = max(self.scrollbar_canvas.winfo_height(), 1)
        thumb_top = getattr(self, "_thumb_top", 0)
        thumb_bottom = getattr(self, "_thumb_bottom", height)
        if thumb_top <= event.y <= thumb_bottom:
            self._scrollbar_dragging = True
            self._scrollbar_drag_offset = event.y - thumb_top
        else:
            # Klick in die Spur: sofort zur Position springen.
            first, last = self._last_scroll
            page = last - first
            target = max(0.0, min(1.0 - page, event.y / height - page / 2))
            self.canvas.yview_moveto(target)
        self._draw_scrollbar(*self._last_scroll, active=True)

    def _on_scrollbar_drag(self, event):
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

    def _on_scrollbar_release(self, event):
        self._scrollbar_dragging = False
        self._draw_scrollbar(*self._last_scroll)

    def _on_scrollbar_enter(self, event=None):
        self._draw_scrollbar(*self._last_scroll, active=True)

    def _on_scrollbar_leave(self, event=None):
        if not self._scrollbar_dragging:
            self._draw_scrollbar(*self._last_scroll, active=False)

    def _on_mousewheel(self, event):
        bbox = self.canvas.bbox("all")
        if bbox and bbox[3] > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# =============================================================================
# TOOLTIP
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
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg=self.bg, fg=self.fg, font=("Segoe UI", 9), padx=10, pady=5, relief="flat", bd=0).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# =============================================================================
# HAUPTANWENDUNG
# =============================================================================
class DevPulsePlanner(tk.Tk):
    STATUSES = ("offen", "in_bearbeitung", "erledigt")

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

        # Performance-Caches
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

    def _setup_styles(self):
        self.FONT_DISPLAY = ("Segoe UI Black", 22, "bold")
        self.FONT_TITLE = ("Segoe UI Semibold", 14)
        self.FONT_HEAD = ("Segoe UI Bold", 11)
        self.FONT_BODY = ("Segoe UI", 10)
        self.FONT_SMALL = ("Segoe UI", 9)
        self.FONT_MICRO = ("Segoe UI", 8)
        self.FONT_MONO = ("Consolas", 9)
        self.FONT_NAV = ("Segoe UI Semibold", 10)
        self.FONT_BADGE = ("Segoe UI Bold", 8)

    def _build_layout(self):
        colors = self.themes[self.current_theme]
        self.config(bg=colors["bg"])
        self.sidebar = tk.Frame(self, width=240, bg=colors["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.main_area = tk.Frame(self, bg=colors["bg"])
        self.main_area.pack(side="left", fill="both", expand=True)
        self.ui_elements["sidebar"] = self.sidebar
        self.ui_elements["main_area"] = self.main_area

    def _populate_layout(self):
        colors = self.themes[self.current_theme]

        brand_frame = tk.Frame(self.sidebar, bg=colors["sidebar_top"], height=72)
        brand_frame.pack(fill="x")
        brand_frame.pack_propagate(False)
        self.ui_elements["brand_frame"] = brand_frame
        self._draw_logo(brand_frame)

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
        
        def on_focus_in(event=None):
            if self.search_var.get() == "Suchen…":
                self.search_var.set("")
                search_entry.config(fg=colors["text_main"])
        
        def on_focus_out(event=None):
            current_text = self.search_var.get().strip()
            if not current_text:
                self.search_var.set("Suchen…")
                search_entry.config(fg=colors["text_sub"])
        
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        
        def global_focus_handler(event=None):
            if event and event.widget != search_entry and not self._is_child_of(event.widget, search_entry):
                search_entry.master.focus()
        
        self.bind("<Button-1>", global_focus_handler, add="+")
        
        self.search_var.trace_add("write", self._on_search)
        self.ui_elements["search_entry"] = search_entry

        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)
        nav_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        nav_container.pack(fill="x", pady=(8, 0))
        self.ui_elements["nav_container"] = nav_container
        self._build_nav(nav_container)

        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12, pady=(8, 0))
        stats_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=10)
        stats_frame.pack(fill="x")
        self.ui_elements["stats_frame"] = stats_frame
        self._build_stats_once(stats_frame)

        tk.Frame(self.sidebar, bg=colors["border"], height=1).pack(fill="x", padx=12)
        btn_frame = tk.Frame(self.sidebar, bg=colors["sidebar"], padx=12, pady=12)
        btn_frame.pack(fill="x", side="bottom")
        self.ui_elements["btn_frame"] = btn_frame
        self._build_sidebar_buttons(btn_frame)

        topbar = tk.Frame(self.main_area, bg=colors["topbar"], height=72)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.ui_elements["topbar"] = topbar
        self._build_topbar(topbar)

        board_outer = tk.Frame(self.main_area, bg=colors["bg"])
        board_outer.pack(fill="both", expand=True)
        self.ui_elements["board_outer"] = board_outer

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

        cols_frame = tk.Frame(board_outer, bg=colors["bg"])
        cols_frame.pack(fill="both", expand=True, padx=board_padding, pady=16)
        cols_frame.columnconfigure((0, 1, 2), weight=1, uniform="col")
        cols_frame.rowconfigure(0, weight=1)
        self.ui_elements["cols_frame"] = cols_frame
        self._build_board_columns_once(cols_frame)

        if getattr(self, "current_view", "Board") != "Board":
            self._switch_view(self.current_view)

    def _is_child_of(self, widget, parent):
        current = widget
        while current:
            if current == parent:
                return True
            current = current.master if hasattr(current, 'master') else None
        return False

    def _draw_logo(self, parent):
        colors = self.themes[self.current_theme]
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
        self._nav_items = {} 
        for icon, label in [("📋", "Board"), ("📈", "Analysen"), ("🗓️", "Kalender"), ("⚙️", "Einstellungen")]:
            active = (label == getattr(self, "current_view", "Board"))
            self._make_nav_item(parent, icon, label, active)

    def _make_nav_item(self, parent, icon, label, active):
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

        for widget in (row, bar, lbl):
            widget.bind("<Button-1>", lambda e, l=label: self._switch_view(l))

        self._nav_items[label] = {"row": row, "bar": bar, "lbl": lbl, "icon": icon}

    def _switch_view(self, view_name):
        self.current_view = view_name
        colors = self.themes[self.current_theme]

        # 1. Sidebar visuell aktualisieren
        for name, widgets in self._nav_items.items():
            active = (name == view_name)
            bg = colors["col_open"] if active else colors["sidebar"]
            fg = colors["accent"] if active else colors["text_sub"]
            bar_color = colors["accent"] if active else colors["sidebar"]

            widgets["row"].config(bg=bg)
            widgets["bar"].config(bg=bar_color)
            widgets["lbl"].config(bg=bg, fg=fg)

        # 2. Hauptbereich umschalten
        board_outer = self.ui_elements.get("board_outer")
        
        if view_name == "Board":
            if hasattr(self, "placeholder_outer") and self.placeholder_outer.winfo_exists():
                self.placeholder_outer.pack_forget()
            if board_outer:
                board_outer.pack(fill="both", expand=True)
        else:
            if board_outer:
                board_outer.pack_forget()

            if hasattr(self, "placeholder_outer") and self.placeholder_outer.winfo_exists():
                self.placeholder_outer.destroy()

            self.placeholder_outer = tk.Frame(self.main_area, bg=colors["bg"])
            self.placeholder_outer.pack(fill="both", expand=True)

            board_padding = 16
            header_outer = tk.Frame(self.placeholder_outer, bg=colors["bg"])
            header_outer.pack(fill="x", padx=board_padding, pady=(20, 0))
            tk.Label(header_outer, text=view_name, font=("Segoe UI Black", 20), bg=colors["bg"], fg=colors["text_main"]).pack(side="left")
            tk.Frame(self.placeholder_outer, bg=colors["border"], height=1).pack(fill="x", padx=board_padding, pady=(8, 10))

            content = tk.Frame(self.placeholder_outer, bg=colors["bg"])
            content.pack(fill="both", expand=True)
            tk.Label(content, text="Coming Soon", font=("Segoe UI Black", 36), bg=colors["bg"], fg=colors["text_sub"]).pack(expand=True)

    def _build_stats_once(self, parent):
        colors = self.themes[self.current_theme]
        self._stat_value_labels = {}
        self._overdue_label = None
        for child in parent.winfo_children():
            child.destroy()
        
        tk.Label(parent, text="ÜBERSICHT", font=self.FONT_BADGE, bg=colors["sidebar"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 8))
        
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
        
        tk.Label(parent, text="ÜBERFÄLLIG", font=self.FONT_BADGE, bg=colors["sidebar"], fg=colors["text_sub"]).pack(anchor="w", pady=(12, 8))
        
        overdue_cell = tk.Frame(parent, bg=colors["card"], highlightbackground=colors["border"], highlightthickness=1)
        overdue_cell.pack(fill="x")
        self._overdue_label = tk.Label(overdue_cell, text="0", font=("Segoe UI Black", 18), bg=colors["card"], fg=colors["text_sub"])
        self._overdue_label.pack(pady=(8, 6))

    def _update_stats_only(self):
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

    def _count_overdue_tasks(self):
        overdue = 0
        today = datetime.now().date()
        
        for status in ["offen", "in_bearbeitung"]:
            tasks = self.controller.get_tasks_by_status(status)
            for task in tasks:
                if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
                    task_date = task.get_faelligkeitsdatum().date()
                    if task_date < today:
                        overdue += 1
        
        return overdue

    def _build_sidebar_buttons(self, parent):
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

    def _build_topbar(self, topbar):
        colors = self.themes[self.current_theme]
        tk.Label(topbar, font=("Segoe UI Semibold", 12), bg=colors["topbar"], fg="#FFFFFF").pack(side="left", padx=16, pady=18)
        right = tk.Frame(topbar, bg=colors["topbar"])
        right.pack(side="right", padx=16)
        
        def remove_search_focus(event=None):
            search_entry = self.ui_elements.get("search_entry")
            if search_entry and search_entry.focus_get() == search_entry:
                topbar.focus()
        
        topbar.bind("<Button-1>", remove_search_focus, add="+")

    def _build_board_columns_once(self, cols_frame):
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
            header = tk.Frame(wrapper, bg=col_bg, padx=14, pady=12)
            header.pack(fill="x")
            tk.Label(header, text=title, font=self.FONT_HEAD, bg=col_bg, fg=colors["text_main"]).pack(side="left")
            badge = tk.Label(header, text="0", font=self.FONT_BADGE, bg=badge_color, fg="#FFFFFF", padx=7, pady=2)
            badge.pack(side="right")
            self._column_count_labels[status_key] = badge
            tk.Frame(wrapper, bg=colors["border"], height=1).pack(fill="x", padx=10)
            scroll = ScrollableFrame(wrapper, bg=col_bg, scrollbar_bg=colors["scrollbar_thumb"], scrollbar_trough=colors["scrollbar_trough"], scrollbar_active=colors["scrollbar_active"])
            scroll.pack(fill="both", expand=True)
            self._column_scrolls[status_key] = scroll

    # =========================================================================
    # DATEN & BOARD - PERFORMANCEOPTIMIERT
    # =========================================================================
    def load_initial_data(self):
        self.controller.load_demo_data()
        self.refresh_board()

    def _clear_search_placeholder(self, event=None):
        if self.search_var.get() == "Suchen…":
            self.search_var.set("")

    def _restore_search_placeholder(self, event=None):
        if not self.search_var.get():
            self.search_var.set("Suchen…")

    def _on_search(self, *args):
        if "cols_frame" not in self.ui_elements:
            return
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(180, self.refresh_board)

    def refresh_board(self):
        if not self._column_scrolls:
            return
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        if query == "suchen…":
            query = ""

        def task_matches(task):
            if not query:
                return True
            return query in task.get_titel().lower() or query in (task.get_beschreibung() or "").lower()

        all_existing_ids = set()
        visible_ids = set()
        tasks_by_status = {}
        for status in self.STATUSES:
            tasks = list(self.controller.get_tasks_by_status(status))
            tasks_by_status[status] = tasks
            self._task_count[status] = len([task for task in tasks if task_matches(task)]) if query else len(tasks)
            for task in tasks:
                all_existing_ids.add(task.get_id())

        for task_id in list(self._card_widgets.keys()):
            if task_id not in all_existing_ids:
                self._destroy_card_widget(task_id)

        for status in self.STATUSES:
            col_bg = self._get_column_bg(status)
            for task in tasks_by_status[status]:
                task_id = task.get_id()
                if not task_matches(task):
                    self._hide_card(task_id)
                    continue
                visible_ids.add(task_id)
                card_state = self._card_widgets.get(task_id)
                if card_state is None:
                    self._create_card_from_task(task, status, col_bg)
                elif card_state.get("status") != status:
                    self._destroy_card_widget(task_id)
                    self._create_card_from_task(task, status, col_bg)
                else:
                    self._update_card_content(task_id, task)
                self._show_card_in_order(task_id)

        for task_id in list(self._card_widgets.keys()):
            if task_id not in visible_ids:
                self._hide_card(task_id)

        self._visible_task_ids = visible_ids
        self._update_counts_only()

    def _get_column_bg(self, status):
        colors = self.themes[self.current_theme]
        return {"offen": colors["col_open"], "in_bearbeitung": colors["col_wip"], "erledigt": colors["col_done"]}[status]

    def _update_counts_only(self):
        for status, count in self._task_count.items():
            badge = self._column_count_labels.get(status)
            if badge and badge.winfo_exists():
                badge.config(text=str(count))
        self._update_stats_only()

    def _task_view_data(self, task):
        prio_map = {1: "Low", 3: "Medium", 5: "High"}
        task_prio = task.get_prio() if hasattr(task, "get_prio") else 3
        prio = prio_map.get(task_prio, "Medium")
        date = "–"
        if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
            date = task.get_faelligkeitsdatum().strftime("%d.%m.%Y")
        return {"title": task.get_titel(), "desc": task.get_beschreibung() or "", "prio": prio, "date": date, "task_id": task.get_id()}

    def _create_card_from_task(self, task, status, col_bg):
        data = self._task_view_data(task)
        parent = self._column_scrolls[status].inner
        self._create_card(parent, data, status, col_bg)

    def _create_card(self, parent, data, current_status, col_bg):
        colors = self.themes[self.current_theme]
        task_id = data["task_id"]
        outer = tk.Frame(parent, bg=col_bg, padx=10, pady=4)
        card = tk.Frame(outer, bg=colors["card"], highlightbackground=colors["border"], highlightthickness=1, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x")

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
        header = tk.Frame(card, bg=colors["card"])
        header.pack(fill="x")
        prio_colors = {"High": colors["tag_high"], "Medium": colors["tag_med"], "Low": colors["tag_low"]}
        prio_label = tk.Label(header, text=f"● {data['prio']}", font=("Segoe UI Bold", 7), bg=colors["card"], fg=prio_colors.get(data["prio"], colors["tag_low"]))
        prio_label.pack(side="left")
        tk.Button(header, text="✕", font=("Segoe UI Bold", 8), bg=colors["card"], fg=colors["text_sub"], relief="flat", bd=0, cursor="hand2", activeforeground="#FF4D6D", activebackground=colors["card"], command=lambda tid=task_id: self._delete_task(tid)).pack(side="right")
        title_label = tk.Label(card, text=data["title"], font=("Segoe UI Semibold", 10), bg=colors["card"], fg=colors["text_main"], anchor="w", wraplength=240, justify="left")
        title_label.pack(fill="x", pady=(6, 2))
        desc_label = None
        if data["desc"]:
            desc_label = tk.Label(card, text=data["desc"], font=self.FONT_MICRO, bg=colors["card"], fg=colors["text_sub"], anchor="w", wraplength=240, justify="left")
            desc_label.pack(fill="x", pady=(0, 8))
        tk.Frame(card, bg=colors["border"], height=1).pack(fill="x", pady=(4, 6))
        footer = tk.Frame(card, bg=colors["card"])
        footer.pack(fill="x")
        
        date_bg = self._get_date_display_bg(data["task_id"], data["date"])
        date_fg = self._get_date_display_color(data["task_id"], data["date"])
        date_label = tk.Label(footer, text=f"📅 {data['date']}", font=self.FONT_MICRO, bg=date_bg, fg=date_fg, relief="solid" if date_bg != colors["card"] else "flat", bd=1 if date_bg != colors["card"] else 0, padx=4, pady=2)
        date_label.pack(side="left")
        
        tk.Button(footer, text="✓ Erledigt", font=("Segoe UI Bold", 7), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", bd=0, padx=7, pady=2, cursor="hand2", command=lambda tid=task_id: self._complete_task(tid)).pack(side="right", padx=(4, 0))
        tk.Button(footer, text="✎ Bearbeiten", font=("Segoe UI Bold", 7), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", bd=0, padx=7, pady=2, cursor="hand2", command=lambda tid=task_id: self._bearbeitung_task(tid)).pack(side="right", padx=(0, 4))

        self._card_widgets[task_id] = {"outer": outer, "card": card, "status": current_status, "data": data.copy(), "labels": {"prio": prio_label, "title": title_label, "desc": desc_label, "date": date_label}}
        self._bind_card_drag(card, task_id, data["title"], current_status, root_card=card, card_info=data.copy())

    def _update_card_content(self, task_id, task):
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

    def _show_card_in_order(self, task_id):
        state = self._card_widgets.get(task_id)
        if state and state["outer"].winfo_exists():
            state["outer"].pack_forget()
            state["outer"].pack(fill="x")

    def _hide_card(self, task_id):
        state = self._card_widgets.get(task_id)
        if state and state["outer"].winfo_exists():
            state["outer"].pack_forget()

    def _destroy_card_widget(self, task_id):
        state = self._card_widgets.pop(task_id, None)
        if state and state["outer"].winfo_exists():
            state["outer"].destroy()

    def _delete_task(self, task_id):
        self.controller.delete_task(task_id)
        self.refresh_board()

    def _complete_task(self, task_id):
        self.controller.complete_task(task_id)
        self.refresh_board()

    def _bearbeitung_task(self, task_id):
        self.controller.bearbeitung_task(task_id)
        self.refresh_board()

    def _bind_card_drag(self, widget, task_id, title, current_status, root_card=None, card_info=None):
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

    def _start_drag(self, event, task_id, title, current_status, root_card, card_info):
        cached = self._card_widgets.get(task_id, {})
        current_status = cached.get("status", current_status)
        self._drag_data = {"task_id": task_id, "title": title, "source_status": current_status, "start_x": event.x_root, "start_y": event.y_root, "offset_x": event.x_root - root_card.winfo_rootx(), "offset_y": event.y_root - root_card.winfo_rooty(), "dragging": False, "root_card": root_card, "card_info": card_info}
        self._last_drop_status = None

    def _drag_motion(self, event):
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

    def _drop_task(self, event):
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

    def _create_drag_preview(self, event):
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

    def _schedule_drag_preview_move(self, event, immediate=False):
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

    def _apply_drag_preview_move(self):
        self._drag_preview_after_id = None
        if self._drag_preview and self._drag_preview_pending_xy:
            x, y = self._drag_preview_pending_xy
            self._drag_preview.geometry(f"+{x}+{y}")

    def _destroy_drag_preview(self):
        if self._drag_preview_after_id:
            self.after_cancel(self._drag_preview_after_id)
            self._drag_preview_after_id = None
        if self._drag_preview:
            self._drag_preview.destroy()
            self._drag_preview = None
        self._drag_preview_pending_xy = None

    def _set_original_card_drag_state(self, active):
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

    def _get_drop_status_at(self, x_root, y_root):
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

    def _highlight_drop_zone(self, target_status):
        colors = self.themes[self.current_theme]
        for status, zone in self._drop_zones.items():
            if not zone.winfo_exists():
                continue
            if status == target_status:
                zone.config(highlightbackground=colors["accent"], highlightthickness=2)
            else:
                zone.config(highlightbackground=colors["border"], highlightthickness=1)

    def _reset_drop_zone_highlights(self):
        colors = self.themes[self.current_theme]
        for zone in self._drop_zones.values():
            if zone.winfo_exists():
                zone.config(highlightbackground=colors["border"], highlightthickness=1)

    def _move_task_to_status(self, task_id, target_status):
        moved = False
        if self._call_existing_controller_move_method(task_id, target_status):
            moved = True
        else:
            task = self._find_task_by_id(task_id)
            if task and self._set_task_status_direct(task, target_status):
                moved = True
            elif target_status == "erledigt" and hasattr(self.controller, "complete_task"):
                self.controller.complete_task(task_id)
                moved = True
        if moved:
            self._notify_controller_after_status_change()
            self.refresh_board()
        else:
            print("Drag & Drop: Status konnte nicht geändert werden. Bitte Controller/Task prüfen.")

    def _call_existing_controller_move_method(self, task_id, target_status):
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

    def _find_task_by_id(self, task_id):
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

    def _find_task_in_container(self, container, task_id):
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

    def _looks_like_task(self, obj):
        return hasattr(obj, "get_id") or any(hasattr(obj, name) for name in ("id", "_id", "task_id", "_task_id"))

    def _task_has_id(self, task, task_id):
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

    def _set_task_status_direct(self, task, target_status):
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

    def _notify_controller_after_status_change(self):
        for method_name in ("save", "save_tasks", "speichern", "persist", "refresh", "notify_change"):
            method = getattr(self.controller, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass

    def _update_child_backgrounds(self, parent, old_bg, new_bg):
        for child in parent.winfo_children():
            try:
                if child.cget("bg") == old_bg:
                    child.config(bg=new_bg)
            except tk.TclError:
                pass
            self._update_child_backgrounds(child, old_bg, new_bg)

    def _add_task_dialog(self):
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
                title_entry.config(highlightbackground=colors["tag_high"])
                return

            desc = desc_text.get("1.0", "end").strip()

            date_input = date_var.get().strip()

            if not date_input:
                date_obj = None
            else:
                try:
                    date_obj = datetime.strptime(date_input, "%d.%m.%Y")
                except ValueError:
                    date_entry.config(highlightbackground=colors["tag_high"])
                    return

            self.controller.add_task(title, desc, prio=prio_var.get(), faellig=date_obj)
            win.destroy()
            self.refresh_board()


        tk.Frame(win, bg=colors["border"], height=1).pack(fill="x", padx=24, pady=(10, 0))
        btn_row = tk.Frame(win, bg=colors["card"])
        btn_row.pack(fill="x", padx=24, pady=10)
        tk.Button(btn_row, text="Abbrechen", command=win.destroy, font=self.FONT_SMALL, bg=colors["btn_theme"], fg="#FFFFFF", relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="➕ Hinzufügen", command=submit, font=("Segoe UI Bold", 9), bg=colors["btn_add"], fg="#FFFFFF", relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right")

    def _add_demo_task(self):
        self.controller.add_task("Demo-Aufgabe", "Diese Demo-Karte dient zum Testen der Scrollfunktion.", prio=3)
        self.refresh_board()

    def _load_demo(self):
        all_task_ids = list(self.controller.manager.aufgaben.keys())
        for task_id in all_task_ids:
            self.controller.manager.aufgabe_entfernen(task_id)
        
        self.controller.manager.geloescht.clear()
        self.controller.manager.speichere_daten()
        
        self.controller.load_demo_data()
        self.refresh_board()

    def _get_date_display_color(self, task_id, date_str):
        colors = self.themes[self.current_theme]
        
        task = self._find_task_by_id(task_id)
        if task and task.get_status() == "erledigt":
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

    def _get_date_display_bg(self, task_id, date_str):
        colors = self.themes[self.current_theme]
        
        task = self._find_task_by_id(task_id)
        if task and task.get_status() == "erledigt":
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

    def toggle_theme(self):
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

    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)


if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()