import tkinter as tk
from tkinter import messagebox
import ctypes
from PIL import Image, ImageTk

# =============================================================================
# KONZEPT: HIGH-DPI SCALING & RENDERING
# In modernen GUIs ist die Schärfe entscheidend. Dieser Block kommuniziert mit 
# dem Betriebssystem, um Pixelskalierung bei 4K-Monitoren zu verhindern.
# =============================================================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per Monitor Awareness
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # System Awareness
    except Exception:
        pass

class DevPulsePlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("DevPulse Planner Professional")
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        
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
        
        # ===== NEUE STATE VERWALTUNG =====
        self.user_tasks = []  # Speichert vom Nutzer hinzugefügte Tasks
        self.ui_elements = {}  # Referenzen zu wichtigen Widgets
        
        self.setup_layout()
        self.render_ui()

    def setup_layout(self):
        self.sidebar = tk.Frame(self, width=340)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.main_area = tk.Frame(self)
        self.main_area.pack(side="left", fill="both", expand=True)

    def render_ui(self):
        """
        OPTIMIERT: Nur Styling wird aktualisiert, nicht die komplette UI!
        """
        colors = self.themes[self.current_theme]
        self.config(bg=colors["bg"])
        self.sidebar.config(bg=colors["sidebar"], highlightbackground=colors["border"], highlightthickness=1)
        self.main_area.config(bg=colors["bg"])
        
        # Nur bei ERSTER Initialisierung aufbauen
        if not self.ui_elements:
            self._build_ui()
        
        # Bei Theme-Wechsel: Nur Farben aktualisieren
        self._update_theme_colors()

    def _build_ui(self):
        """Baut die UI nur einmal auf"""
        colors = self.themes[self.current_theme]
        
        # --- BRANDING SECTION ---
        brand_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        brand_container.pack(pady=(70, 50), padx=40, anchor="w")
        self.ui_elements["brand_container"] = brand_container

        self.draw_vector_logo(brand_container)

        name_frame = tk.Frame(brand_container, bg=colors["sidebar"])
        name_frame.pack(side="left", padx=(18, 0))
        
        tk.Label(name_frame, text="DEV", font=("Segoe UI Black", 24),
                 bg=colors["sidebar"], fg=colors["accent"]).pack(side="left")
        tk.Label(name_frame, text="Pulse", font=("Segoe UI Semibold", 24),
                 bg=colors["sidebar"], fg=colors["text_main"]).pack(side="left")

        # --- NAVIGATION ---
        nav_data = [("📋", "Aufgaben", True), ("📊", "Analysen", False), ("⚙️", "Settings", False)]
        nav_frame = tk.Frame(self.sidebar, bg=colors["sidebar"])
        nav_frame.pack(fill="x")
        self.ui_elements["nav_frame"] = nav_frame
        
        for icon, txt, active in nav_data:
            bg_c = colors["bg"] if active else colors["sidebar"]
            fg_c = colors["accent"] if active else colors["text_main"]
            
            f = tk.Frame(nav_frame, bg=bg_c)
            f.pack(fill="x", padx=20, pady=6)
            
            l = tk.Label(f, text=f"   {icon}   {txt}", font=("Segoe UI Semibold", 12),
                         bg=bg_c, fg=fg_c, anchor="w")
            l.pack(side="left", ipady=14, fill="x", expand=True)
            l.bind("<Button-1>", lambda e, t=txt: messagebox.showinfo("Info", f"{t} gewählt"))

        # --- BUTTONS CONTAINER ---
        button_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        button_container.pack(side="bottom", fill="x", padx=40, pady=40)
        self.ui_elements["button_container"] = button_container
        
        tk.Button(button_container, text="MODE WECHSELN", command=self.toggle_theme,
                  font=("Segoe UI Bold", 9), bg=colors["accent"], fg="white",
                  relief="flat", pady=12, cursor="hand2").pack(fill="x", pady=(0, 10))
        
        # ===== TEST BUTTON: Task hinzufügen =====
        tk.Button(button_container, text="+ TEST TASK", command=self._add_test_task,
                  font=("Segoe UI Bold", 9), bg="#107C10", fg="white",
                  relief="flat", pady=12, cursor="hand2").pack(fill="x")

        # --- KANBAN BOARD AREA ---
        content = tk.Frame(self.main_area, bg=colors["bg"])
        content.pack(fill="both", expand=True, padx=60, pady=60)
        self.ui_elements["content"] = content

        tk.Label(content, text="Daily Board", font=("Segoe UI Bold", 28),
                 bg=colors["bg"], fg=colors["text_main"]).pack(anchor="w", pady=(0, 40))

        board = tk.Frame(content, bg=colors["bg"])
        board.pack(fill="both", expand=True)
        board.columnconfigure((0, 1), weight=1)
        self.ui_elements["board"] = board

        self.create_column(board, "In Bearbeitung", 0, [
            ("GUI Refinement", "Logo auf Vektor-Basis umgestellt", "High", "Sofort"),
            ("KI Fallstudie", "Integration der ToDoListeKlassen", "Medium", "29.05.2026")
        ])
        self.create_column(board, "Abgeschlossen", 1, [
            ("DPI Bugfix", "High-DPI Awareness für Windows 11", "Low", "Erledigt")
        ])

    def _update_theme_colors(self):
        """Aktualisiert nur die Farben ALLER Widgets rekursiv"""
        colors = self.themes[self.current_theme]
        self._apply_colors_recursive(self, colors)

    def _apply_colors_recursive(self, widget, colors):
        """Recursiv alle Widgets mit neuen Farben aktualisieren"""
        try:
            # Farben basierend auf Widget-Typ setzen
            if isinstance(widget, tk.Label):
                if widget.cget("bg") in ["#F8F9FA", "#0B0B0B"]:
                    widget.config(bg=colors["bg"])
                elif widget.cget("bg") in ["#FFFFFF", "#161616"]:
                    widget.config(bg=colors["sidebar"])
                elif widget.cget("bg") in ["#1E1E1E", "#FFFFFF"]:
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
                elif widget.cget("bg") in ["#1E1E1E", "#FFFFFF"]:
                    widget.config(bg=colors["card"])
                    
                if widget.cget("highlightbackground") in ["#E1E1E1", "#333333"]:
                    widget.config(highlightbackground=colors["border"])
                    
            elif isinstance(widget, tk.Button):
                if widget.cget("bg") in ["#005A9E", "#2899F5"]:
                    widget.config(bg=colors["accent"])
                    
        except tk.TclError:
            pass
        
        # Rekursiv auf alle Kinder anwenden
        for child in widget.winfo_children():
            self._apply_colors_recursive(child, colors)

    def _add_test_task(self):
        """Fügt eine Test-Task hinzu - OHNE UI neu zu rendern!"""
        colors = self.themes[self.current_theme]
        board = self.ui_elements["board"]
        
        # Neue Task in erster Spalte hinzufügen
        first_column = board.winfo_children()[0]
        
        self.create_modern_card(first_column, 
                               f"Test Task #{len(self.user_tasks)+1}", 
                               "Diese Task bleibt nach Theme-Wechsel bestehen! ✅",
                               "Medium", 
                               "Heute")
        
        self.user_tasks.append({"title": f"Test Task #{len(self.user_tasks)+1}"})
        messagebox.showinfo("✅ Test erfolgreich", f"Task hinzugefügt!\nFunktioniert der Theme-Wechsel jetzt korrekt?")

    def draw_vector_logo(self, parent):
        colors = self.themes[self.current_theme]
        
        try:
            raw_img = Image.open("Logo.png")
            render_size = (64, 64)
            smooth_img = raw_img.resize(render_size, Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(smooth_img)
            
            logo_label = tk.Label(parent, image=self.logo_tk, bg=colors["sidebar"], bd=0)
            logo_label.pack(side="left")
            
        except Exception as e:
            print(f"Logo konnte nicht geladen werden: {e}")
            cv = tk.Canvas(parent, width=64, height=64, bg=colors["sidebar"], highlightthickness=0)
            cv.pack(side="left")
            cv.create_oval(5, 5, 59, 59, fill=colors["accent"], outline="")

    def create_column(self, parent, title, col, tasks):
        colors = self.themes[self.current_theme]
        frame = tk.Frame(parent, bg=colors["bg"])
        frame.grid(row=0, column=col, sticky="nsew", padx=25)
        
        tk.Label(frame, text=title.upper(), font=("Segoe UI Bold", 10), 
                 bg=colors["bg"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 20))
        
        for t, d, p, dt in tasks:
            self.create_modern_card(frame, t, d, p, dt)

    def create_modern_card(self, parent, title, desc, prio, date):
        colors = self.themes[self.current_theme]
        
        card = tk.Frame(parent, bg=colors["card"], padx=25, pady=25, 
                        highlightbackground=colors["border"], highlightthickness=1)
        card.pack(fill="x", pady=12)
        
        tk.Label(card, text=title, font=("Segoe UI Bold", 14), 
                 bg=colors["card"], fg=colors["text_main"]).pack(anchor="w")
        
        tk.Label(card, text=desc, font=("Segoe UI", 10), wraplength=400, justify="left",
                 bg=colors["card"], fg=colors["text_sub"]).pack(anchor="w", pady=(8, 15))
        
        footer = tk.Frame(card, bg=colors["card"])
        footer.pack(fill="x")
        
        p_color = "#D83B01" if prio == "High" else colors["accent"]
        tk.Label(footer, text=prio, font=("Segoe UI Bold", 8), bg=p_color, fg="white", padx=10, pady=2).pack(side="left")
        
        tk.Label(footer, text=f"📅 {date}", font=("Segoe UI", 9), 
                 bg=colors["card"], fg=colors["text_sub"]).pack(side="right")

    def toggle_theme(self):
        """Theme wechseln - Daten bleiben erhalten!"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self._update_theme_colors()  # Nur Farben updaten, nicht render_ui()!

if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()