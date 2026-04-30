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
        
        # =====================================================================
        # KONZEPT: WINDOW MANAGEMENT
        # Fullscreen-Modus und Event-Binding (Escape) sorgen für eine 
        # "immersive" User Experience, wie man sie von modernen Apps kennt.
        # =====================================================================
        self.title("DevPulse Planner Professional")
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        
        # =====================================================================
        # KONZEPT: THEMING & STATE MANAGEMENT
        # Ein zentrales Dictionary für Farben ermöglicht einen sauberen Darkmode.
        # "current_theme" steuert als State den gesamten Look der App.
        # =====================================================================
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
        
        # Initialisierung der UI-Komponenten[cite: 1]
        self.setup_layout()
        self.render_ui()

    def setup_layout(self):
        """
        KONZEPT: LAYOUT SEGMENTATION
        Trennung der Hauptbereiche (Sidebar vs. Content) mittels Frames.
        'pack_propagate(False)' verhindert, dass die Sidebar durch Inhalt schrumpft.
        """
        self.sidebar = tk.Frame(self, width=340)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.main_area = tk.Frame(self)
        self.main_area.pack(side="left", fill="both", expand=True)

    def render_ui(self):
        """
        KONZEPT: DYNAMISCHES RENDERING
        Diese Methode fungiert als 'Engine'. Sie löscht alle Widgets (.destroy())
        und baut sie basierend auf dem aktuellen Theme-State neu auf.
        """
        colors = self.themes[self.current_theme]
        self.config(bg=colors["bg"])
        self.sidebar.config(bg=colors["sidebar"], highlightbackground=colors["border"], highlightthickness=1)
        self.main_area.config(bg=colors["bg"])
        
        for w in self.sidebar.winfo_children(): w.destroy()
        for w in self.main_area.winfo_children(): w.destroy()

        # --- BRANDING SECTION ---
        # Hier wird die Identität der App definiert (Logo + Name)
        brand_container = tk.Frame(self.sidebar, bg=colors["sidebar"])
        brand_container.pack(pady=(70, 50), padx=40, anchor="w")

        self.draw_vector_logo(brand_container)

        name_frame = tk.Frame(brand_container, bg=colors["sidebar"])
        name_frame.pack(side="left", padx=(18, 0))
        
        tk.Label(name_frame, text="DEV", font=("Segoe UI Black", 24),
                 bg=colors["sidebar"], fg=colors["accent"]).pack(side="left")
        tk.Label(name_frame, text="Pulse", font=("Segoe UI Semibold", 24),
                 bg=colors["sidebar"], fg=colors["text_main"]).pack(side="left")

        # --- NAVIGATION ---
        # KONZEPT: ABSTRAKTION DURCH LISTEN
        # Statt jeden Button einzeln zu schreiben, werden Navigationsdaten 
        # in einer Liste definiert und per Schleife generiert.
        nav_data = [("📋", "Aufgaben", True), ("📊", "Analysen", False), ("⚙️", "Settings", False)]
        for icon, txt, active in nav_data:
            bg_c = colors["bg"] if active else colors["sidebar"]
            fg_c = colors["accent"] if active else colors["text_main"]
            
            f = tk.Frame(self.sidebar, bg=bg_c)
            f.pack(fill="x", padx=20, pady=6)
            
            l = tk.Label(f, text=f"   {icon}   {txt}", font=("Segoe UI Semibold", 12),
                         bg=bg_c, fg=fg_c, anchor="w")
            l.pack(side="left", ipady=14, fill="x", expand=True)
            # Event Handling: Klick-Interaktion
            l.bind("<Button-1>", lambda e, t=txt: messagebox.showinfo("Info", f"{t} gewählt"))

        # Dark Mode Button (Trigger für den Theme-Switch)
        tk.Button(self.sidebar, text="MODE WECHSELN", command=self.toggle_theme,
                  font=("Segoe UI Bold", 9), bg=colors["accent"], fg="white",
                  relief="flat", pady=12, cursor="hand2").pack(side="bottom", fill="x", padx=40, pady=40)

        # --- KANBAN BOARD AREA ---
        content = tk.Frame(self.main_area, bg=colors["bg"])
        content.pack(fill="both", expand=True, padx=60, pady=60)

        tk.Label(content, text="Daily Board", font=("Segoe UI Bold", 28),
                 bg=colors["bg"], fg=colors["text_main"]).pack(anchor="w", pady=(0, 40))

        # Grid-Layout für Spalten (Kanban-Struktur)
        board = tk.Frame(content, bg=colors["bg"])
        board.pack(fill="both", expand=True)
        board.columnconfigure((0, 1), weight=1)

        # Hier erfolgt später die Datenübergabe aus der logic.py (Manager-Klasse)[cite: 5]
        self.create_column(board, "In Bearbeitung", 0, [
            ("GUI Refinement", "Logo auf Vektor-Basis umgestellt", "High", "Sofort"),
            ("KI Fallstudie", "Integration der ToDoListeKlassen", "Medium", "29.05.2026")
        ])
        self.create_column(board, "Abgeschlossen", 1, [
            ("DPI Bugfix", "High-DPI Awareness für Windows 11", "Low", "Erledigt")
        ])


    def draw_vector_logo(self, parent):

#   Lädt das generierte Logo-Bild und skaliert es mit Anti-Aliasing (LANCZOS),
#    um maximale Schärfe zu garantieren.

        colors = self.themes[self.current_theme]
        
        try:
            # 1. Bild öffnen
            raw_img = Image.open("Logo.png")
            
            # 2. Hochwertiges Resizing (LANCZOS sorgt für die Glättung)
            # 64x64 ist ein guter Standard für die Sidebar
            render_size = (64, 64)
            smooth_img = raw_img.resize(render_size, Image.Resampling.LANCZOS)
            
            # 3. Konvertierung für Tkinter
            self.logo_tk = ImageTk.PhotoImage(smooth_img)
            
            # 4. Anzeige in einem Label (ohne Rahmen)
            logo_label = tk.Label(parent, image=self.logo_tk, bg=colors["sidebar"], bd=0)
            logo_label.pack(side="left")
            
        except Exception as e:
            # Fallback: Falls die Datei fehlt, zeichne einen einfachen Platzhalter
            print(f"Logo konnte nicht geladen werden: {e}")
            cv = tk.Canvas(parent, width=64, height=64, bg=colors["sidebar"], highlightthickness=0)
            cv.pack(side="left")
            cv.create_oval(5, 5, 59, 59, fill=colors["accent"], outline="")

    def create_column(self, parent, title, col, tasks):
        """
        KONZEPT: COMPONENT REUSABILITY
        Erstellt eine Kanban-Spalte. Durch Parameter steuerbar für beliebig viele Spalten.
        """
        colors = self.themes[self.current_theme]
        frame = tk.Frame(parent, bg=colors["bg"])
        frame.grid(row=0, column=col, sticky="nsew", padx=25)
        
        tk.Label(frame, text=title.upper(), font=("Segoe UI Bold", 10), 
                 bg=colors["bg"], fg=colors["text_sub"]).pack(anchor="w", pady=(0, 20))
        
        for t, d, p, dt in tasks:
            self.create_modern_card(frame, t, d, p, dt)

    def create_modern_card(self, parent, title, desc, prio, date):
        """
        KONZEPT: COMPOUND WIDGETS (Cards)
        Kombiniert mehrere Labels und Frames zu einer visuellen Einheit.
        Simuliert modernes Karten-Design durch 'highlightthickness' als Rahmen.
        """
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
        """
        KONZEPT: UI REFRESH LOGIC
        Ändert den globalen Status und stößt den Render-Prozess neu an.
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.render_ui()

if __name__ == "__main__":
    app = DevPulsePlanner()
    app.mainloop()