import tkinter as tk
from tkinter import messagebox, simpledialog
import ctypes
from PIL import Image, ImageTk, ImageDraw
from Controller import PlannerController
from datetime import datetime

# =============================================================================
# KONZEPT: HIGH-DPI SCALING & RENDERING
# =============================================================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class DevPulsePlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # ===== FENSTER-KONFIGURATION =====
        self.title("DevPulse Planner Professional")
        self.geometry("1400x900")
        self.minsize(900, 600)
        self.resizable(True, True)
        
        # ===== TASTENBINDUNGEN =====
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self.is_fullscreen = False
        
        # ===== CONTROLLER INITIALISIEREN =====
        self.controller = PlannerController(view=self)
        
        self.themes = {
            "light": {
                "bg": "#F8F9FA", "sidebar": "#FFFFFF", "text_main": "#1A1A1A",
                "text_sub": "#646464", "accent": "#005A9E", "card": "#FFFFFF",
                "logo_bg": "#005A9E", "logo_pulse": "#FFFFFF", "border": "#E1E1E1"
            },
            "dark": {
                "bg": "#0B0B0B", "sidebar": "#161616", "text_main": "#FFFFFF",
                "text_sub": "#A0A0A0", "accent": "#2899F5", "card": "#1E1E1E",
                "logo_bg": "#2899F5", "logo_pulse": "#FFFFFF", "border": "#333333"
            }
        }
        self.current_theme = "light"
        
        # ===== STATE VERWALTUNG =====
        self.ui_elements = {}
        self.card_images = []
        
        self.setup_layout()
        self.render_ui()
        self.load_initial_data()

    def _toggle_fullscreen(self, event=None):
        """Wechselt zwischen Fullscreen und Fenster-Modus (F11)"""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes('-fullscreen', self.is_fullscreen)
        print(f"\n📺 Fullscreen: {'AN' if self.is_fullscreen else 'AUS'}\n")

    def _exit_fullscreen(self, event=None):
        """Beendet Fullscreen-Modus"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes('-fullscreen', False)
            print(f"\n📺 Fullscreen: AUS\n")

    def setup_layout(self):
        """Erstellt die Grundstruktur: Sidebar + Main Area"""
        self.sidebar = tk.Frame(self, width=300)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.ui_elements["sidebar"] = self.sidebar
        
        self.main_area = tk.Frame(self)
        self.main_area.pack(side="left", fill="both", expand=True)
        self.ui_elements["main_area"] = self.main_area

    def render_ui(self):
        """Rendert die UI mit aktuellem Theme"""
        colors = self.themes[self.current_theme]
        
        self.config(bg=colors["bg"])
        self.sidebar.config(bg=colors["sidebar"], highlightbackground=colors["border"], highlightthickness=1)
        self.main_area.config(bg=colors["bg"])
        
        if not self.ui_elements.get("brand_container"):
            self._build_ui()
        
        self._update_theme_colors()

    def _build_ui(self):
        """Baut die UI nur einmal auf"""
        colors = self.themes[self.current_theme]
        
        # --- BRANDING SECTION ---
        brand_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        brand_container.pack(pady=(30, 30), padx=20, anchor="w")
        self.ui_elements["brand_container"] = brand_container

        self.draw_vector_logo(brand_container)

        name_frame = tk.Frame(brand_container, bg=colors["sidebar"])
        name_frame.pack(side="left", padx=(12, 0))
        
        tk.Label(name_frame, text="DEV", font=("Segoe UI Black", 20),
                 bg=colors["sidebar"], fg=colors["accent"]).pack(side="left")
        tk.Label(name_frame, text="Pulse", font=("Segoe UI Semibold", 20),
                 bg=colors["sidebar"], fg=colors["text_main"]).pack(side="left")

        # --- NAVIGATION ---
        nav_data = [("📋", "Aufgaben", True), ("📊", "Analysen", False), ("⚙️", "Settings", False)]
        nav_frame = tk.Frame(self.sidebar, bg=colors["sidebar"])
        nav_frame.pack(fill="x", padx=10)
        self.ui_elements["nav_frame"] = nav_frame
        
        for icon, txt, active in nav_data:
            bg_c = colors["bg"] if active else colors["sidebar"]
            fg_c = colors["accent"] if active else colors["text_main"]
            
            f = tk.Frame(nav_frame, bg=bg_c)
            f.pack(fill="x", padx=10, pady=4)
            
            l = tk.Label(f, text=f"   {icon}   {txt}", font=("Segoe UI Semibold", 11),
                         bg=bg_c, fg=fg_c, anchor="w")
            l.pack(side="left", ipady=12, fill="x", expand=True)

        # --- BUTTONS CONTAINER ---
        button_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        button_container.pack(side="bottom", fill="x", padx=15, pady=20)
        self.ui_elements["button_container"] = button_container
        
        tk.Button(button_container, text="🌙 MODE", command=self.toggle_theme,
                  font=("Segoe UI Bold", 9), bg=colors["accent"], fg="white",
                  relief="flat", pady=10, cursor="hand2").pack(fill="x", pady=(0, 8))
        
        tk.Button(button_container, text="➕ NEUE TASK", command=self._add_task_dialog,
                  font=("Segoe UI Bold", 9), bg="#107C10", fg="white",
                  relief="flat", pady=10, cursor="hand2").pack(fill="x", pady=(0, 8))
        
        tk.Button(button_container, text="📊 DEMO", command=self._load_demo,
                  font=("Segoe UI Bold", 9), bg="#0078D4", fg="white",
                  relief="flat", pady=10, cursor="hand2").pack(fill="x")
        
        tk.Label(button_container, text="F11: Fullscreen\nESC: Beenden", 
                 font=("Segoe UI", 7), bg=colors["sidebar"], fg=colors["text_sub"],
                 justify="left").pack(fill="x", pady=(15, 0), padx=5)

        # --- TOP BAR ---
        top_bar = tk.Frame(self.main_area, bg=colors["accent"], height=50)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        top_label = tk.Label(top_bar, text="DevPulse Planner - Press F11 for Fullscreen", 
                             font=("Segoe UI Semibold", 11), bg=colors["accent"], fg="white")
        top_label.pack(side="left", padx=20, pady=15)
        self.ui_elements["top_label"] = top_label

        # --- KANBAN BOARD AREA ---
        content = tk.Frame(self.main_area, bg=colors["bg"])
        content.pack(fill="both", expand=True, padx=40, pady=30)
        self.ui_elements["content"] = content

        title_label = tk.Label(content, text="Daily Board", font=("Segoe UI Bold", 26),
                 bg=colors["bg"], fg=colors["text_main"])
        title_label.pack(anchor="w", pady=(0, 25))
        self.ui_elements["title_label"] = title_label

        board = tk.Frame(content, bg=colors["bg"])
        board.pack(fill="both", expand=True)
        board.columnconfigure((0, 1), weight=1)
        board.rowconfigure(0, weight=1)
        
        self.ui_elements["board"] = board

    def load_initial_data(self):
        """Lädt Demo-Daten beim Start"""
        self.controller.load_demo_data()

    def _add_task_dialog(self):
        """Dialog zum Hinzufügen einer neuen Task"""
        titel = simpledialog.askstring("Neue Task", "Titel:")
        if not titel:
            return
        
        beschreibung = simpledialog.askstring("Neue Task", "Beschreibung (optional):")
        
        try:
            prio_input = simpledialog.askstring("Neue Task", "Priorität (1=Low, 3=Medium, 5=High):")
            prio = int(prio_input) if prio_input else 3
            if prio not in [1, 3, 5]:
                prio = 3
        except (ValueError, TypeError):
            prio = 3
        
        self.controller.add_task(titel, beschreibung or "", prio=prio)
        messagebox.showinfo("✅ Erfolg", f"Task '{titel}' hinzugefügt!")

    def _load_demo(self):
        """Lädt Demo-Daten"""
        self.controller.load_demo_data()
        messagebox.showinfo("✅ Demo geladen", "Demo-Aufgaben wurden hinzugefügt!")

    def refresh_board(self):
        """Aktualisiert das Board mit aktuellen Daten"""
        colors = self.themes[self.current_theme]
        board = self.ui_elements["board"]
        
        for widget in board.winfo_children():
            widget.destroy()
        
        in_progress = self.controller.get_tasks_by_status("offen")
        in_bearbeitung = self.controller.get_tasks_by_status("in_bearbeitung")
        completed = self.controller.get_tasks_by_status("erledigt")
        
        all_active = in_progress + in_bearbeitung
        
        self.create_column_with_tasks(board, "In Bearbeitung", 0, all_active)
        self.create_column_with_tasks(board, "Abgeschlossen", 1, completed)

    def create_column_with_tasks(self, parent, title, col, tasks):
        """Erstellt eine Spalte mit Task-Objekten"""
        colors = self.themes[self.current_theme]
        frame = tk.Frame(parent, bg=colors["bg"])
        frame.grid(row=0, column=col, sticky="nsew", padx=15, pady=10)
        
        tk.Label(frame, text=title.upper(), font=("Segoe UI Bold", 10),
                 bg=colors["bg"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 15))
        
        for task in tasks:
            prio_map = {1: "Low", 3: "Medium", 5: "High"}
            prio_text = prio_map.get(task.get_prio() if hasattr(task, "get_prio") else 1, "Medium")
            
            datum_text = "Kein Datum"
            if hasattr(task, "get_faelligkeitsdatum") and task.get_faelligkeitsdatum():
                datum_text = task.get_faelligkeitsdatum().strftime("%d.%m.%Y")
            
            self.create_modern_card(
                frame,
                task.get_titel(),
                task.get_beschreibung(),
                prio_text,
                datum_text,
                task_id=task.get_id()
            )

    def create_modern_card(self, parent, title, desc, prio, date, task_id=None):
        """Erstellt eine moderne Card"""
        colors = self.themes[self.current_theme]
        
        card = tk.Frame(parent, bg=colors["card"], padx=20, pady=20,
                        highlightbackground=colors["border"], highlightthickness=1)
        card.pack(fill="x", pady=10)
        
        # Header
        header = tk.Frame(card, bg=colors["card"])
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text=title, font=("Segoe UI Bold", 12),
                 bg=colors["card"], fg=colors["text_main"]).pack(side="left", fill="x", expand=True)
        
        if task_id:
            tk.Button(header, text="✕", font=("Segoe UI Bold", 10),
                      bg=colors["card"], fg="#D83B01", relief="flat", bd=0,
                      command=lambda: self.controller.delete_task(task_id),
                      cursor="hand2").pack(side="right")
        
        # Description
        tk.Label(card, text=desc, font=("Segoe UI", 9),
                 wraplength=350, justify="left",
                 bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 15), fill="x")
        
        # Footer
        footer = tk.Frame(card, bg=colors["card"])
        footer.pack(fill="x")
        
        p_color = "#D83B01" if prio == "High" else ("#FF8C00" if prio == "Medium" else colors["accent"])
        tk.Label(footer, text=prio, font=("Segoe UI Bold", 7),
                 bg=p_color, fg="white", padx=8, pady=2).pack(side="left")
        
        tk.Label(footer, text=f"📅 {date}", font=("Segoe UI", 7),
                 bg=colors["card"], fg=colors["text_sub"]).pack(side="right")
        
        if task_id:
            tk.Button(footer, text="✓ Erledigt", font=("Segoe UI Bold", 7),
                      bg="#107C10", fg="white", relief="flat", bd=0,
                      command=lambda: self.controller.complete_task(task_id),
                      cursor="hand2", padx=5, pady=1).pack(side="left", padx=(8, 0))

    def _update_theme_colors(self):
        """Aktualisiert nur die Farben ALLER Widgets rekursiv"""
        colors = self.themes[self.current_theme]
        self._apply_colors_recursive(self, colors)

    def _apply_colors_recursive(self, widget, colors):
        """Recursiv alle Widgets mit neuen Farben aktualisieren"""
        try:
            if isinstance(widget, tk.Label):
                if widget.cget("bg") in ["#F8F9FA", "#0B0B0B"]:
                    widget.config(bg=colors["bg"])
                elif widget.cget("bg") in ["#FFFFFF", "#161616"]:
                    widget.config(bg=colors["sidebar"])
                elif widget.cget("bg") in ["#1E1E1E"]:
                    widget.config(bg=colors["card"])
                    
                if widget.cget("fg") in ["#1A1A1A", "#FFFFFF"]:
                    widget.config(fg=colors["text_main"])
                elif widget.cget("fg") in ["#646464", "#A0A0A0"]:
                    widget.config(fg=colors["text_sub"])
                elif widget.cget("fg") in ["#005A9E", "#2899F5"]:
                    widget.config(fg=colors["accent"])
                    
            elif isinstance(widget, tk.Frame):
                if widget.cget("bg") in ["#F8F9FA", "#0B0B0B"]:
                    widget.config(bg=colors["bg"])
                elif widget.cget("bg") in ["#FFFFFF", "#161616"]:
                    widget.config(bg=colors["sidebar"])
                elif widget.cget("bg") in ["#1E1E1E"]:
                    widget.config(bg=colors["card"])
                    
                if widget.cget("highlightbackground") in ["#E1E1E1", "#333333"]:
                    widget.config(highlightbackground=colors["border"])
                    
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self._apply_colors_recursive(child, colors)

    def draw_vector_logo(self, parent):
        """Zeichnet das Logo"""
        colors = self.themes[self.current_theme]
        
        try:
            raw_img = Image.open("Logo.png")
            render_size = (48, 48)
            smooth_img = raw_img.resize(render_size, Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(smooth_img)
            
            logo_label = tk.Label(parent, image=self.logo_tk, bg=colors["sidebar"], bd=0)
            logo_label.pack(side="left")
            
        except Exception as e:
            print(f"⚠️ Logo konnte nicht geladen werden: {e}")
            cv = tk.Canvas(parent, width=48, height=48, bg=colors["sidebar"], highlightthickness=0)
            cv.pack(side="left")
            cv.create_oval(5, 5, 43, 43, fill=colors["accent"], outline="")

    def toggle_theme(self):
        """Theme wechseln"""
        print(f"\n🌙 Theme wird gewechselt: {self.current_theme} → ", end="")
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        print(f"{self.current_theme}\n")
        
        self.card_images = []
        self._update_theme_colors()
        self.refresh_board()


if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()