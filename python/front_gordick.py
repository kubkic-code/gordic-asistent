import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import datetime
import threading
import json
import webbrowser
import back_gordick

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# =============================================================
# DESIGN SYSTEM – centralizované barvy, radiusy, styly
# =============================================================
APP_VERSION = "2.1"

THEME = {
    # Pozadí & povrchy
    "bg":          ("#F0F2F5", "#0B1120"),
    "sidebar":     ("#1E1B4B", "#0F0C2E"),   # deep indigo sidebar
    "sidebar_hi":  ("#2D2A6E", "#1A164A"),
    "card":        ("#FFFFFF", "#162032"),
    "card_brd":    ("#E2E8F0", "#1E3048"),
    "card_alt":    ("#F8FAFC", "#131D2E"),
    # Text
    "text":        ("#0F172A", "#E8EDF5"),
    "text_mute":   ("#64748B", "#8896AB"),
    "text_sub":    ("#94A3B8", "#5E6F84"),
    "text_sidebar":("#CBD5E1", "#B8C4D4"),   # text v sidebaru
    "text_sidebar_active": ("#FFFFFF", "#FFFFFF"),
    # Navigace
    "nav_active":  ("#4338CA", "#312E81"),   # indigo active
    "nav_bar":     "#818CF8",               # accent pruh – světlý indigo
    "nav_hover":   ("#2D2A6E", "#231F5E"),
    # Akcenty
    "primary":     "#6366F1",  "primary_hi":  "#4F46E5",
    "success":     "#10B981",  "success_hi":  "#059669",
    "warning":     "#F59E0B",  "warning_hi":  "#D97706",
    "danger":      "#EF4444",  "danger_hi":   "#DC2626",
    "violet":      "#8B5CF6",  "violet_hi":   "#7C3AED",
    "neutral":     ("#64748B", "#475569"),
    "neutral_hi":  ("#475569", "#334155"),
    # Speciální
    "logo_text":   "#A5B4FC",
    "danger_bg":   ("#FEF2F2", "#1C0F0F"),
    "danger_brd":  ("#FECACA", "#5C1616"),
    "result_bg":   ("#EEF2FF", "#1A2744"),
    "result_brd":  ("#C7D2FE", "#2D3F6B"),
}

R = 12
R_BTN = 8
R_NAV = 8
PAD_SECTION = 28

STAV_BARVY = {
    "pripraveno": THEME["primary"],
    "pracuji":    THEME["warning"],
    "hotovo":     THEME["success"],
    "chyba":      THEME["danger"],
}

BTN_STYLES = {
    "primary": (THEME["primary"], THEME["primary_hi"], "white"),
    "success": (THEME["success"], THEME["success_hi"], "white"),
    "warning": (THEME["warning"], THEME["warning_hi"], "white"),
    "danger":  (THEME["danger"],  THEME["danger_hi"],  "white"),
    "violet":  (THEME["violet"],  THEME["violet_hi"],  "white"),
    "neutral": (THEME["neutral"], THEME["neutral_hi"], "white"),
}


class GordicAsistentUI(ctk.CTk):
    """Hlavní okno aplikace Gordic Asistent – prémiová verze 2.1."""

    def __init__(self):
        super().__init__()
        self.title("Gordic Import Asistent")
        self.geometry("1300x860")
        self.minsize(1050, 660)
        self.configure(fg_color=THEME["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Aplikační ikona okna
        ikona_cesta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ikona.ico")
        if os.path.exists(ikona_cesta):
            try:
                self.iconbitmap(ikona_cesta)
            except Exception:
                pass

        self.fonts = {
            "title":       ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            "card_title":  ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            "body":        ctk.CTkFont(family="Segoe UI", size=13),
            "body_bold":   ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            "small":       ctk.CTkFont(family="Segoe UI", size=11),
            "small_bold":  ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            "small_it":    ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            "icon":        ctk.CTkFont(size=36),
            "icon_sm":     ctk.CTkFont(size=22),
            "dot":         ctk.CTkFont(size=16),
            "mono":        ctk.CTkFont(family="Consolas", size=11),
            "cta":         ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            "nav":         ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            "section_btn": ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            "stat_num":    ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            "logo_big":    ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            "logo_sub":    ctk.CTkFont(family="Segoe UI", size=10),
            "version":     ctk.CTkFont(family="Segoe UI", size=9),
            "result_val":  ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            "result_lbl":  ctk.CTkFont(family="Segoe UI", size=10),
        }

        self.vybrane_soubory_cesty = []
        self.cesta_gpc_souboru = None
        self.cesta_smlouvy_souboru = None
        self.log_otevreny = False
        self.sort_pdf_var = ctk.StringVar(value="Nejnovější")
        self.sort_isdoc_var = ctk.StringVar(value="Nejnovější")
        self._current_mode = "Light"

        self._build_sidebar()
        self._build_main_area()
        self.nacti_historii()
        self.show_dashboard_event()

    # =============================================================
    # TOVÁRNY NA WIDGETY
    # =============================================================
    def btn(self, master, text, command=None, kind="primary", height=38,
            corner_radius=R_BTN, **kw):
        fg, hov, txt = BTN_STYLES.get(kind, BTN_STYLES["primary"])
        kw.setdefault("font", self.fonts["body"])
        return ctk.CTkButton(master, text=text, command=command, height=height,
                             corner_radius=corner_radius, fg_color=fg,
                             hover_color=hov, text_color=txt, **kw)

    def card(self, master, **kw):
        return ctk.CTkFrame(master, fg_color=THEME["card"], corner_radius=R,
                            border_width=1, border_color=THEME["card_brd"], **kw)

    def result_card(self, master, label, value, color=None):
        """Malá výsledková karta pro zobrazení extrahovaných dat."""
        c = ctk.CTkFrame(master, fg_color=THEME["result_bg"], corner_radius=8,
                         border_width=1, border_color=THEME["result_brd"])
        ctk.CTkLabel(c, text=label, font=self.fonts["result_lbl"],
                     text_color=THEME["text_mute"]).pack(padx=10, pady=(6, 0), anchor="w")
        ctk.CTkLabel(c, text=str(value) if value else "—", font=self.fonts["result_val"],
                     text_color=color or THEME["text"],
                     wraplength=160, justify="left").pack(padx=10, pady=(1, 8), anchor="w")
        return c

    # =============================================================
    # DRY HELPERS
    # =============================================================
    def _toggle_visibility(self, entry, button):
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="🙈")
        else:
            entry.configure(show="*")
            button.configure(text="👁️")

    def _run_async(self, worker_fn, worker_args=(),
                   on_success=None, on_error=None,
                   disable_btns=None, progress=None):
        """Generický async worker."""
        for b in (disable_btns or []):
            b.configure(state="disabled")
        if progress:
            progress.pack(pady=(0, 16), padx=40, fill="x")
            progress.configure(mode="indeterminate")
            progress.start()

        def _thread():
            try:
                result = worker_fn(*worker_args)
                self.after(0, lambda: self._async_done(
                    result, on_success, disable_btns, progress))
            except Exception as e:
                self.after(0, lambda: self._async_done(
                    str(e), on_error, disable_btns, progress))

        threading.Thread(target=_thread, daemon=True).start()

    def _async_done(self, result, callback, disable_btns, progress):
        if progress:
            progress.stop()
            progress.pack_forget()
        for b in (disable_btns or []):
            b.configure(state="normal")
        if callback:
            callback(result)

    def _populate_file_list(self, scroll, folder, ext, sort, icon, verb):
        for w in scroll.winfo_children():
            w.destroy()
        files = self._sorted_files(folder, ext, sort)
        if not files:
            self._empty_state(scroll, "📭", "Zatím tu nic není",
                              "Zpracované dokumenty se zobrazí zde.")
            return
        for f in files:
            path = os.path.join(folder, f)
            ts = datetime.datetime.fromtimestamp(
                os.path.getctime(path)).strftime('%d.%m.%Y %H:%M')
            self._list_item_with_actions(scroll, f"{icon} {f}", f"{verb}: {ts}", path)

    def _sorted_files(self, folder, ext, sort="Nejnovější"):
        if not os.path.exists(folder):
            return []
        files = [f for f in os.listdir(folder) if f.lower().endswith(ext)]
        key = lambda x: os.path.getctime(os.path.join(folder, x))
        if sort == "Nejnovější":   files.sort(key=key, reverse=True)
        elif sort == "Nejstarší":  files.sort(key=key)
        elif sort == "A-Z":        files.sort()
        elif sort == "Z-A":        files.sort(reverse=True)
        return files

    def _empty_state(self, master, icon, title, subtitle=""):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(expand=True, pady=40)
        ctk.CTkLabel(f, text=icon, font=self.fonts["icon"]).pack()
        ctk.CTkLabel(f, text=title, font=self.fonts["body_bold"],
                     text_color=THEME["text"]).pack(pady=(6, 2))
        if subtitle:
            ctk.CTkLabel(f, text=subtitle, font=self.fonts["small"],
                         text_color=THEME["text_mute"]).pack()

    def _list_item_with_actions(self, master, title, subtitle, path):
        """Řádek archivu s tlačítky Otevřít a Kopírovat cestu."""
        row = ctk.CTkFrame(master, fg_color=THEME["card_alt"], corner_radius=8,
                           border_width=1, border_color=THEME["card_brd"])
        row.pack(fill="x", padx=6, pady=3)
        row.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ctk.CTkLabel(info, text=title, font=self.fonts["small_bold"],
                     text_color=THEME["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=subtitle, font=self.fonts["small"],
                     text_color=THEME["text_mute"], anchor="w").pack(anchor="w")

        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.grid(row=0, column=1, padx=(0, 8), pady=6)
        ctk.CTkButton(btns, text="📂 Otevřít", width=80, height=26,
                      corner_radius=6, font=self.fonts["small"],
                      fg_color=THEME["primary"], hover_color=THEME["primary_hi"],
                      text_color="white",
                      command=lambda p=path: os.startfile(p) if os.path.exists(p) else None
                      ).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="📋 Kopírovat", width=88, height=26,
                      corner_radius=6, font=self.fonts["small"],
                      fg_color=THEME["neutral"], hover_color=THEME["neutral_hi"],
                      text_color="white",
                      command=lambda p=path: (self.clipboard_clear(), self.clipboard_append(p))
                      ).pack(side="left", padx=2)

    def _create_action_card(self, master, icon, title, desc,
                            browse_text, browse_cmd, run_text, run_cmd,
                            run_kind="primary",
                            default_label="Není vybrán žádný soubor",
                            has_progress=False, progress_color=None):
        c = self.card(master)
        c.pack(fill="both", expand=True)
        ctk.CTkLabel(c, text=icon, font=self.fonts["icon"]).pack(pady=(28, 6))
        ctk.CTkLabel(c, text=title, font=self.fonts["card_title"],
                     text_color=THEME["text"]).pack(pady=3)
        ctk.CTkLabel(c, text=desc, font=self.fonts["body"],
                     text_color=THEME["text_mute"], justify="center").pack(
                         pady=(3, 16))
        browse_btn = self.btn(c, browse_text, browse_cmd, kind="neutral", height=36)
        browse_btn.pack(pady=6)
        label = ctk.CTkLabel(c, text=default_label, text_color=THEME["text_mute"],
                             font=self.fonts["small_it"])
        label.pack(pady=(0, 14))
        progress = None
        if has_progress:
            progress = ctk.CTkProgressBar(
                c, mode="indeterminate", height=6, corner_radius=3,
                progress_color=progress_color or THEME["primary"])
        run_btn = self.btn(c, run_text, run_cmd, kind=run_kind, height=48,
                           font=self.fonts["section_btn"])
        run_btn.pack(pady=(6, 28), padx=28, fill="x")
        return c, browse_btn, label, run_btn, progress

    def _create_archive_frame(self, open_folder_cmd, sort_var, with_search=False):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(1, weight=1)
        self.btn(top, "📂 Otevřít složku", open_folder_cmd, kind="neutral",
                 height=36).grid(row=0, column=0)
        ctk.CTkOptionMenu(top, values=["Nejnovější", "Nejstarší", "A-Z", "Z-A"],
                          variable=sort_var, command=self.nacti_historii,
                          fg_color=THEME["neutral"],
                          button_color=THEME["neutral_hi"],
                          corner_radius=R_BTN).grid(row=0, column=3)

        search_entry = None
        next_row = 1
        if with_search:
            sb = ctk.CTkFrame(frame, fg_color="transparent")
            sb.grid(row=1, column=0, sticky="ew", pady=(0, 10))
            sb.grid_columnconfigure(0, weight=1)
            search_entry = ctk.CTkEntry(
                sb, placeholder_text="🔍 Hledat obsah uvnitř faktur...",
                height=38, font=self.fonts["body"], corner_radius=R_BTN)
            search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            search_entry.bind("<Return>", self.spustit_hledani)
            self.btn(sb, "Hledat", self.spustit_hledani, kind="primary",
                     height=38, width=90).grid(row=0, column=1)
            next_row = 2

        frame.grid_rowconfigure(next_row, weight=1)
        scroll = ctk.CTkScrollableFrame(frame, fg_color=THEME["card"],
                                        corner_radius=R, border_width=1,
                                        border_color=THEME["card_brd"])
        scroll.grid(row=next_row, column=0, sticky="nsew")
        return frame, scroll, search_entry

    def _file_count(self, folder, ext):
        if not os.path.exists(folder):
            return 0
        return len([f for f in os.listdir(folder) if f.lower().endswith(ext)])

    def _dnes_pocet(self):
        if not os.path.exists(back_gordick.SLOZKA_ARCHIV):
            return 0
        dnes = datetime.date.today()
        return sum(1 for f in os.listdir(back_gordick.SLOZKA_ARCHIV)
                   if f.lower().endswith(".pdf") and
                   datetime.date.fromtimestamp(
                       os.path.getctime(os.path.join(back_gordick.SLOZKA_ARCHIV, f))) == dnes)

    def _posledni_faktura(self):
        if not os.path.exists(back_gordick.SLOZKA_ARCHIV):
            return None
        pdfs = [f for f in os.listdir(back_gordick.SLOZKA_ARCHIV)
                if f.lower().endswith(".pdf")]
        if not pdfs:
            return None
        pdfs.sort(key=lambda x: os.path.getctime(
            os.path.join(back_gordick.SLOZKA_ARCHIV, x)), reverse=True)
        return pdfs[0]

    # =============================================================
    # SIDEBAR
    # =============================================================
    # Sidebar barvy (hardcoded hexu kvůli CTkButton transparency bugu v Light mode)
    SB_BG       = "#1E1B4B"   # sidebar pozadí
    SB_ACTIVE   = "#3730A3"   # aktivní položka
    SB_HOVER    = "#2D2A6E"   # hover
    SB_BAR      = "#818CF8"   # accent pruh
    SB_TEXT     = "#C7D2FE"   # text neaktivní
    SB_TEXT_ACT = "#FFFFFF"   # text aktivní

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0,
                          fg_color=self.SB_BG)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        self.sidebar_frame = sb

        # --- HORNÍ SEKCE: logo + nav ---
        top = ctk.CTkFrame(sb, fg_color="transparent")
        top.pack(fill="x", padx=0, pady=0)

        # Logo
        logo_frame = ctk.CTkFrame(top, fg_color="transparent")
        logo_frame.pack(fill="x", padx=18, pady=(24, 4))
        ctk.CTkLabel(logo_frame, text="⚖️  GORDIC", font=self.fonts["logo_big"],
                     text_color="#A5B4FC").pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="ASISTENT  v" + APP_VERSION,
                     font=self.fonts["logo_sub"],
                     text_color="#6366F1").pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Automatizace účetnictví",
                     font=self.fonts["version"],
                     text_color="#3D3878").pack(anchor="w", pady=(2, 0))

        # Oddělovač
        ctk.CTkFrame(top, height=1, fg_color="#2D2A6E").pack(
            fill="x", padx=14, pady=(10, 6))

        # Sekce label
        ctk.CTkLabel(top, text="NAVIGACE",
                     font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color="#3D3878").pack(anchor="w", padx=20, pady=(2, 4))

        # Navigační položky
        self.nav_items = []
        nav_defs = [
            ("🏠", "Nová Faktura",    self.show_dashboard_event),
            ("📄", "Archiv PDF",      self.show_archiv_pdf_event),
            ("⚙️", "Exporty ISDOC",   self.show_archiv_isdoc_event),
            ("🏦", "Párování Banky",  self.show_banka_event),
            ("📜", "Čtečka Smluv",    self.show_smlouvy_event),
        ]
        for icon, text, cmd in nav_defs:
            item = self._create_nav_item(top, icon, text, cmd)
            self.nav_items.append(item)

        # Oddělovač před Nastavením
        ctk.CTkFrame(top, height=1, fg_color="#2D2A6E").pack(
            fill="x", padx=14, pady=(6, 4))

        # Nastavení
        item_nav = self._create_nav_item(top, "⚙️", "Nastavení",
                                         self.show_nastaveni_event)
        self.nav_items_extra = [item_nav]

        # --- DOLNÍ SEKCE: statistiky ---
        stats = ctk.CTkFrame(sb, fg_color="#252260", corner_radius=10)
        stats.pack(side="bottom", fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(stats, text="⏱️ Celková úspora",
                     font=self.fonts["small"],
                     text_color="#A5B4FC").pack(pady=(10, 0))
        self.lbl_stats_time = ctk.CTkLabel(
            stats, text="0 min", font=self.fonts["stat_num"],
            text_color="#818CF8")
        self.lbl_stats_time.pack(pady=2)
        self.lbl_stats_count = ctk.CTkLabel(
            stats, text="0 dokumentů", font=self.fonts["small"],
            text_color="#6366F1")
        self.lbl_stats_count.pack(pady=(0, 10))
        self.obnov_statistiky_ui()

    def _create_nav_item(self, parent, icon, text, command):
        """Navigační položka – spolehlivý pack layout, explicitní barvy (žádný transparency bug)."""
        # Outer wrapper (highlight bar + button side by side)
        wrapper = ctk.CTkFrame(parent, fg_color="transparent", height=42)
        wrapper.pack(fill="x", padx=8, pady=2)
        wrapper.pack_propagate(False)

        # Accent bar vlevo (4 px wide indicator)
        bar = ctk.CTkFrame(wrapper, width=4, corner_radius=2,
                           fg_color="transparent")
        bar.pack(side="left", fill="y", padx=(2, 0), pady=6)

        # Tlačítko – EXPLICITNÍ barva pozadí sidebaru, nikdy transparent!
        btn = ctk.CTkButton(
            wrapper,
            text=f"  {icon}  {text}",
            font=self.fonts["nav"],
            height=36,
            fg_color=self.SB_BG,        # <-- klíčová oprava: explicitní hex
            hover_color=self.SB_HOVER,
            text_color=self.SB_TEXT,
            anchor="w",
            corner_radius=8,
            command=command
        )
        btn.pack(side="left", fill="both", expand=True, padx=(2, 4))
        return {"button": btn, "bar": bar}

    def _set_nav_active(self, active_item):
        """Zvýrazní aktivní navigační položku."""
        all_items = self.nav_items + getattr(self, "nav_items_extra", [])
        for item in all_items:
            item["button"].configure(
                fg_color=self.SB_BG,      # explicitní sidebar barva
                text_color=self.SB_TEXT)
            item["bar"].configure(fg_color="transparent")
        if active_item:
            active_item["button"].configure(
                fg_color=self.SB_ACTIVE,
                text_color=self.SB_TEXT_ACT)
            active_item["bar"].configure(fg_color=self.SB_BAR)

    # =============================================================
    # HLAVNÍ OBSAHOVÁ OBLAST
    # =============================================================
    def _build_main_area(self):
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew",
                                     padx=PAD_SECTION, pady=PAD_SECTION)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(1, weight=1)

        self.section_title_label = ctk.CTkLabel(
            self.main_content_frame, text="",
            font=self.fonts["title"], text_color=THEME["text"])
        self.section_title_label.grid(row=0, column=0, pady=(0, 16), sticky="w")

        self.active_frame = None
        self.frame_dashboard = self._build_dashboard()
        self.frame_archiv_pdf, self.pdf_scroll, self.search_entry = \
            self._build_archiv_pdf()
        self.frame_archiv_isdoc, self.isdoc_scroll = self._build_archiv_isdoc()
        self.frame_banka = self._build_banka()
        self.frame_smlouvy = self._build_smlouvy()
        self.frame_nastaveni = self._build_nastaveni()

    # ---------- DASHBOARD ----------
    def _build_dashboard(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Horní stat karty
        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        top_row.grid_columnconfigure(0, weight=1)
        top_row.grid_columnconfigure(1, weight=1)
        top_row.grid_columnconfigure(2, weight=1)

        self.card_dnes = self.card(top_row)
        self.card_dnes.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(self.card_dnes, text="📅", font=self.fonts["icon_sm"]).pack(pady=(12, 2))
        ctk.CTkLabel(self.card_dnes, text="Zpracováno dnes",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack()
        self.lbl_dnes = ctk.CTkLabel(self.card_dnes, text="0",
                                     font=self.fonts["stat_num"],
                                     text_color=THEME["primary"])
        self.lbl_dnes.pack(pady=(2, 12))

        self.card_posledni = self.card(top_row)
        self.card_posledni.grid(row=0, column=1, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(self.card_posledni, text="📄", font=self.fonts["icon_sm"]).pack(pady=(12, 2))
        ctk.CTkLabel(self.card_posledni, text="Poslední faktura",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack()
        self.lbl_posledni = ctk.CTkLabel(self.card_posledni, text="—",
                                          font=self.fonts["small_bold"],
                                          text_color=THEME["text"], wraplength=200)
        self.lbl_posledni.pack(pady=(2, 12))

        card_celkem = self.card(top_row)
        card_celkem.grid(row=0, column=2, sticky="ew")
        ctk.CTkLabel(card_celkem, text="✅", font=self.fonts["icon_sm"]).pack(pady=(12, 2))
        ctk.CTkLabel(card_celkem, text="Celkem faktur",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack()
        self.lbl_celkem_db = ctk.CTkLabel(card_celkem, text="0",
                                           font=self.fonts["stat_num"],
                                           text_color=THEME["success"])
        self.lbl_celkem_db.pack(pady=(2, 12))

        # Karta: Nahrát z PC
        card_up = self.card(frame)
        card_up.grid(row=1, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(card_up, text="💻", font=self.fonts["icon"]).pack(pady=(26, 6))
        ctk.CTkLabel(card_up, text="Nahrát z počítače",
                     font=self.fonts["card_title"], text_color=THEME["text"]).pack(pady=3)
        ctk.CTkLabel(card_up, text="Vyber jednu nebo více PDF faktur z disku",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack(pady=(0, 10))
        self.btn_browse = self.btn(card_up, "📁 Procházet PC...",
                                   self.select_file_dialog, kind="neutral", height=36)
        self.btn_browse.pack(pady=6)
        self.lbl_soubor_cesta = ctk.CTkLabel(
            card_up, text="Není vybrán žádný soubor",
            font=self.fonts["small_it"], text_color=THEME["text_mute"])
        self.lbl_soubor_cesta.pack(pady=(0, 16), padx=16)

        # Karta: E-mail
        card_em = self.card(frame)
        card_em.grid(row=1, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(card_em, text="📥", font=self.fonts["icon"]).pack(pady=(26, 6))
        ctk.CTkLabel(card_em, text="Stáhnout z e-mailu",
                     font=self.fonts["card_title"], text_color=THEME["text"]).pack(pady=3)
        ctk.CTkLabel(card_em, text="Automaticky stáhne PDF faktury ze schránky",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack(pady=(0, 10))
        self.option_obdobi = ctk.CTkOptionMenu(
            card_em, values=["Den", "Týden", "Měsíc", "Rok", "Celá doba"],
            fg_color=THEME["neutral"], button_color=THEME["neutral_hi"],
            corner_radius=R_BTN)
        self.option_obdobi.pack(pady=6)
        self.check_archivovane = ctk.CTkCheckBox(
            card_em, text="Stáhnout i archivované", font=self.fonts["small"],
            fg_color=THEME["primary"], hover_color=THEME["primary_hi"])
        self.check_archivovane.pack(pady=6)
        self.btn_email = self.btn(card_em, "📨 Připojit a stáhnout",
                                  self.stáhnout_z_emailu_ui, kind="primary", height=36)
        self.btn_email.pack(pady=(4, 6))

        self.btn_navod_hlavni = ctk.CTkButton(
            card_em, text="❓ Jak nastavit e-mail? (Návod pro účetní)",
            font=self.fonts["small_bold"], fg_color="transparent",
            text_color=THEME["primary"], hover_color=THEME["card_alt"],
            height=26, corner_radius=R_BTN,
            command=self.prejit_na_navod_email)
        self.btn_navod_hlavni.pack(pady=(0, 16))

        # Karta: Stav + Akce + Log + Výsledky
        card_st = self.card(frame)
        card_st.grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="nsew")

        stav_row = ctk.CTkFrame(card_st, fg_color="transparent")
        stav_row.pack(pady=(16, 4))
        self.lbl_stav_dot = ctk.CTkLabel(stav_row, text="●",
                                          font=self.fonts["dot"],
                                          text_color=THEME["primary"])
        self.lbl_stav_dot.pack(side="left", padx=(0, 6))
        self.lbl_status = ctk.CTkLabel(
            stav_row, text="Aplikace připravena k práci.",
            font=self.fonts["body_bold"], text_color=THEME["primary"])
        self.lbl_status.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(
            card_st, mode="determinate", height=7, corner_radius=4,
            progress_color=THEME["primary"])
        self.progress_bar.set(0)

        self.btn_run = self.btn(
            card_st, "⚙️   SPUSTIT AI A VYTVOŘIT ISDOC", self.spustit_prevod,
            kind="primary", height=54, corner_radius=27, font=self.fonts["cta"])
        self.btn_run.pack(pady=(8, 16), padx=40, fill="x")

        ctk.CTkFrame(card_st, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=14, pady=(0, 2))
        self.btn_log_toggle = ctk.CTkButton(
            card_st, text="▸  Průběh zpracování", font=self.fonts["body"],
            fg_color="transparent", text_color=THEME["text_mute"],
            hover_color=THEME["card_alt"], anchor="w",
            corner_radius=R_BTN, height=30, command=self.toggle_log)
        self.btn_log_toggle.pack(fill="x", padx=8, pady=(2, 0))
        self.log_box = ctk.CTkTextbox(
            card_st, height=110, font=self.fonts["mono"],
            fg_color=THEME["bg"], corner_radius=R_BTN, border_width=1,
            border_color=THEME["card_brd"])
        self.log_box.configure(state="disabled")

        ctk.CTkFrame(card_st, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=14, pady=(4, 2))
        self.lbl_vysledky_toggle = ctk.CTkButton(
            card_st, text="▸  Výsledky posledního zpracování",
            font=self.fonts["body"], fg_color="transparent",
            text_color=THEME["text_mute"], hover_color=THEME["card_alt"],
            anchor="w", corner_radius=R_BTN, height=30,
            command=self.toggle_vysledky)
        self.lbl_vysledky_toggle.pack(fill="x", padx=8, pady=(2, 0))
        self.vysledky_panel = ctk.CTkFrame(card_st, fg_color="transparent")
        self.vysledky_otevreny = False

        # Accordion: Jak importovat ISDOC do Gordicu
        ctk.CTkFrame(card_st, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=14, pady=(6, 2))
        self._build_navod_gordic_accordion(card_st)

        return frame

    # ---------- ARCHIV PDF ----------
    def _build_archiv_pdf(self):
        frame, scroll, search = self._create_archive_frame(
            lambda: os.startfile(back_gordick.SLOZKA_ARCHIV),
            self.sort_pdf_var, with_search=True)
        return frame, scroll, search

    # ---------- ARCHIV ISDOC ----------
    def _build_archiv_isdoc(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Info banner: Jak importovat do Gordicu
        banner = ctk.CTkFrame(frame, fg_color=THEME["result_bg"], corner_radius=R,
                              border_width=1, border_color=THEME["result_brd"])
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        banner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(banner, text="📌", font=self.fonts["icon_sm"]).grid(
            row=0, column=0, rowspan=4, padx=(14, 8), pady=14, sticky="nw")
        ctk.CTkLabel(
            banner,
            text="Jak importovat ISDOC soubor do systému GORDIC?",
            font=self.fonts["body_bold"], text_color=THEME["text"], anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(0, 14), pady=(14, 2))

        kroky_text = (
            "1. Otevřete složku s ISDOC soubory – klikněte na tlačítko 📂 vpravo nahoře.\n"
            "2. Zkopírujte nebo přesuňte soubor  FA_xxxxxxxxx.isdoc  na síťové úložiště obce.\n"
            "3. Přihlaste se do systému GORDIC (GINIS) a přejděte do modulu: Doklady → Import.\n"
            "4. V dialogu importu vyberte typ: ISDOC (elektronická faktura), potvrďte tlačítkem OK.\n"
            "5. Systém GORDIC automaticky načte dodavatele, částku a číslo faktury z ISDOC souboru.\n"
            "6. Zkontrolujte načtené údaje, doplňte analytický účet / paragraf a zaúčtujte doklad."
        )
        ctk.CTkLabel(
            banner, text=kroky_text,
            font=self.fonts["small"], text_color=THEME["text_mute"],
            justify="left", anchor="w", wraplength=780
        ).grid(row=1, column=1, sticky="w", padx=(0, 14), pady=(0, 12))

        # Archiv soubory (scrollable)
        scroll_outer = ctk.CTkFrame(frame, fg_color=THEME["card"], corner_radius=R,
                                    border_width=1, border_color=THEME["card_brd"])
        scroll_outer.grid(row=1, column=0, sticky="nsew")
        scroll_outer.grid_columnconfigure(0, weight=1)
        scroll_outer.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(scroll_outer, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        ctk.CTkLabel(top_bar, text="Připravené ISDOC soubory",
                     font=self.fonts["card_title"], text_color=THEME["text"]).pack(side="left")
        self.btn(
            top_bar, "📂 Otevřít složku",
            lambda: os.startfile(back_gordick.SLOZKA_VYSTUP),
            kind="neutral", height=28, font=self.fonts["small_bold"]
        ).pack(side="right")

        ctk.CTkFrame(scroll_outer, height=1, fg_color=THEME["card_brd"]).grid(
            row=0, column=0, sticky="ew", padx=0, pady=(40, 0))

        scroll = ctk.CTkScrollableFrame(
            scroll_outer, fg_color="transparent", corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        self.sort_isdoc_var.trace_add("write", self.nacti_historii)
        return frame, scroll

    # ---------- BANKA ----------
    def _build_banka(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=4)
        frame.grid_columnconfigure(1, weight=5)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        _, self.btn_gpc_browse, self.lbl_gpc_cesta, self.btn_gpc_run, _ = \
            self._create_action_card(
                left, "🏦", "Automatické Párování",
                "Nahraj soubor z bankovnictví (.gpc)\na vytvoř úřední podepsanou košilku.",
                "Vybrat bankovní výpis...", self.select_gpc_dialog,
                "🔍 SPUSTIT PÁROVÁNÍ", self.spustit_gpc_parovani,
                run_kind="warning", default_label="Není vybrán žádný výpis")

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        self.btn(right, "📂 Otevřít složku s košilkami",
                 lambda: os.startfile(back_gordick.SLOZKA_KOSILKY),
                 kind="neutral", height=36).grid(
                     row=0, column=0, sticky="ew", pady=(0, 8))
        self.banka_scroll = ctk.CTkScrollableFrame(
            right, fg_color=THEME["card"], corner_radius=R, border_width=1,
            border_color=THEME["card_brd"])
        self.banka_scroll.grid(row=1, column=0, sticky="nsew")
        return frame

    # ---------- SMLOUVY ----------
    def _build_smlouvy(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=4)
        frame.grid_columnconfigure(1, weight=5)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        _, self.btn_smlouva_browse, self.lbl_smlouva_cesta, \
            self.btn_smlouva_run, self.progress_bar_smlouva = \
            self._create_action_card(
                left, "📜", "AI Čtečka Smluv",
                "Nahraj smlouvu v PDF. AI ji celou přečte\na vytáhne ty nejdůležitější údaje.",
                "Vybrat smlouvu (PDF)...", self.select_smlouva_dialog,
                "🤖 VYTVOŘIT SOUHRN", self.spustit_cteni_smlouvy,
                run_kind="violet", default_label="Není vybrána žádná smlouva",
                has_progress=True, progress_color=THEME["violet"])

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.smlouva_result_frame = ctk.CTkFrame(
            right, fg_color=THEME["card"], corner_radius=R, border_width=1,
            border_color=THEME["card_brd"])
        self.smlouva_result_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.smlouva_result_frame.grid_columnconfigure(0, weight=1)
        self.smlouva_result_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.smlouva_result_frame, text="📋 Výsledek analýzy smlouvy",
                     font=self.fonts["card_title"],
                     text_color=THEME["text"]).grid(
                         row=0, column=0, columnspan=2, padx=14, pady=(14, 8), sticky="w")
        self._smlouva_placeholder = ctk.CTkLabel(
            self.smlouva_result_frame,
            text="Výsledky se zobrazí zde po analýze smlouvy.",
            font=self.fonts["small_it"], text_color=THEME["text_mute"])
        self._smlouva_placeholder.grid(row=1, column=0, columnspan=2,
                                        padx=14, pady=(0, 14), sticky="w")

        self.smlouvy_scroll = ctk.CTkScrollableFrame(
            right, fg_color=THEME["card"], corner_radius=R, border_width=1,
            border_color=THEME["card_brd"])
        self.smlouvy_scroll.grid(row=1, column=0, sticky="nsew")
        return frame

    # ---------- NASTAVENÍ ----------
    def _build_nastaveni(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(frame, fg_color=THEME["card"],
                                         corner_radius=R, border_width=1,
                                         border_color=THEME["card_brd"])
        scroll.grid(row=0, column=0, sticky="nsew", padx=30, pady=8)

        ctk.CTkLabel(scroll, text="🔧", font=self.fonts["icon"]).pack(pady=(28, 6))
        ctk.CTkLabel(scroll, text="Konfigurace Systému",
                     font=self.fonts["card_title"], text_color=THEME["text"]).pack(pady=3)
        self.lbl_config_status = ctk.CTkLabel(
            scroll, text="Vše aktuální a uloženo.",
            font=self.fonts["small_it"], text_color=THEME["text_mute"])
        self.lbl_config_status.pack(pady=(0, 6))

        # Přepínač vzhledu
        vzhled = ctk.CTkFrame(scroll, fg_color="transparent")
        vzhled.pack(pady=(0, 4))
        ctk.CTkLabel(vzhled, text="Vzhled aplikace:",
                     font=self.fonts["body_bold"], text_color=THEME["text"]).pack(pady=(0, 4))
        self.seg_vzhled = ctk.CTkSegmentedButton(
            vzhled, values=["☀️ Světlý", "🌙 Tmavý"],
            command=self.change_appearance_mode_event,
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hi"], corner_radius=R_BTN)
        self.seg_vzhled.set("☀️ Světlý")
        self.seg_vzhled.pack()

        # Interaktivní návod pro účetní
        self._build_navod_accordion(scroll)

        form = ctk.CTkFrame(scroll, fg_color="transparent")
        form.pack(pady=8, padx=50, fill="x")

        fields = [
            ("Naše IČO (Organizace):", "ico", False),
            ("Přihlašovací e-mail:", "email", False),
            ("Heslo aplikace (E-mail):", "heslo", True),
            ("Groq API Klíč (Umělá inteligence):", "api", True),
        ]
        self._entries = {}
        self._eye_buttons = {}

        for label_text, name, is_secret in fields:
            lbl_row = ctk.CTkFrame(form, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(8, 0))
            ctk.CTkLabel(lbl_row, text=label_text, font=self.fonts["body_bold"],
                         anchor="w", text_color=THEME["text"]).pack(side="left")
            if name == "heslo":
                ctk.CTkButton(
                    lbl_row, text="❓ Jak získat heslo? (Návod)",
                    font=self.fonts["small_bold"], fg_color="transparent",
                    text_color=THEME["primary"], hover_color=THEME["card_alt"],
                    height=20, corner_radius=R_BTN,
                    command=self.rozbalit_navod_email).pack(side="left", padx=8)
            if is_secret:
                row_f = ctk.CTkFrame(form, fg_color="transparent")
                row_f.pack(fill="x", pady=(0, 10))
                entry = ctk.CTkEntry(row_f, height=34, show="*", corner_radius=R_BTN)
                entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
                entry.bind("<KeyRelease>", self.oznacit_zmeny)
                eye = self.btn(
                    row_f, "👁️",
                    lambda _n=name: self._toggle_visibility(
                        self._entries[_n], self._eye_buttons[_n]),
                    kind="neutral", width=34, height=34)
                eye.pack(side="right")
                self._eye_buttons[name] = eye
            else:
                entry = ctk.CTkEntry(form, height=34, corner_radius=R_BTN)
                entry.pack(fill="x", pady=(0, 10))
                entry.bind("<KeyRelease>", self.oznacit_zmeny)
            self._entries[name] = entry

        self.entry_ico = self._entries["ico"]
        self.entry_email = self._entries["email"]
        self.entry_heslo = self._entries["heslo"]
        self.entry_api = self._entries["api"]

        test_section = ctk.CTkFrame(scroll, fg_color="transparent")
        test_section.pack(pady=(4, 8), padx=50, fill="x")
        ctk.CTkLabel(test_section, text="Ověření připojení:",
                     font=self.fonts["body_bold"], text_color=THEME["text"]).pack(anchor="w", pady=(0, 6))

        test_email_row = ctk.CTkFrame(test_section, fg_color="transparent")
        test_email_row.pack(fill="x", pady=3)
        self.btn_test_email = self.btn(
            test_email_row, "🔌 Test E-mailu", self.test_pripojeni_email,
            kind="neutral", height=32, width=150, font=self.fonts["small_bold"])
        self.btn_test_email.pack(side="left")
        self.lbl_test_email = ctk.CTkLabel(
            test_email_row, text="", font=self.fonts["small"],
            text_color=THEME["text_mute"])
        self.lbl_test_email.pack(side="left", padx=12)

        test_api_row = ctk.CTkFrame(test_section, fg_color="transparent")
        test_api_row.pack(fill="x", pady=3)
        self.btn_test_api = self.btn(
            test_api_row, "🤖 Test AI (API)", self.test_pripojeni_api,
            kind="neutral", height=32, width=150, font=self.fonts["small_bold"])
        self.btn_test_api.pack(side="left")
        self.lbl_test_api = ctk.CTkLabel(
            test_api_row, text="", font=self.fonts["small"],
            text_color=THEME["text_mute"])
        self.lbl_test_api.pack(side="left", padx=12)

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(pady=(12, 22))
        self.btn_save_config = self.btn(
            btn_row, "💾 ULOŽIT NASTAVENÍ", self.potvrdit_ulozeni,
            kind="success", height=40, font=self.fonts["section_btn"])
        self.btn_save_config.grid(row=0, column=0, padx=8)
        self.btn_revert_config = self.btn(
            btn_row, "❌ Zahodit změny", self.nacti_data_nastaveni,
            kind="neutral", height=40, font=self.fonts["small_bold"])
        self.btn_revert_config.grid(row=0, column=1, padx=8)
        self.btn_revert_config.grid_remove()

        ctk.CTkFrame(scroll, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=30, pady=(8, 14))
        danger_card = ctk.CTkFrame(scroll, fg_color=THEME["danger_bg"],
                                   corner_radius=R, border_width=2,
                                   border_color=THEME["danger_brd"])
        danger_card.pack(fill="x", padx=30, pady=(0, 24))
        ctk.CTkLabel(danger_card, text="⚠️ NEBEZPEČNÁ ZÓNA",
                     font=self.fonts["body_bold"], text_color=THEME["danger"]).pack(pady=(14, 3))
        ctk.CTkLabel(danger_card,
                     text="Vymaže všechny nahrané faktury, vygenerované ISDOCy a historii.",
                     font=self.fonts["small"], text_color=THEME["text_mute"]).pack(pady=(0, 10))
        self.btn(danger_card, "🗑️ TOVÁRNÍ RESET A SMAZÁNÍ DAT",
                 self.potvrdit_reset_dat, kind="danger", height=38,
                 font=self.fonts["body_bold"]).pack(pady=(0, 14), padx=22)

        return frame

    # =============================================================
    # INTERAKTIVNÍ NÁVOD NA PROPOJENÍ E-MAILU (PRO ÚČETNÍ)
    # =============================================================
    def _build_navod_accordion(self, parent):
        self.navod_otevren = False

        self.navod_card = ctk.CTkFrame(
            parent, fg_color=THEME["result_bg"], corner_radius=R,
            border_width=1, border_color=THEME["result_brd"])
        self.navod_card.pack(pady=(8, 10), padx=50, fill="x")

        # Hlavička (klikací lišta)
        hdr = ctk.CTkFrame(self.navod_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=12)
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="💡", font=self.fonts["icon_sm"]).grid(
            row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        lbl_title = ctk.CTkLabel(
            hdr, text="NÁVOD PRO ÚČETNÍ: Jak získat heslo a propojit e-mail",
            font=self.fonts["body_bold"], text_color=THEME["text"], anchor="w")
        lbl_title.grid(row=0, column=1, sticky="w")

        lbl_sub = ctk.CTkLabel(
            hdr, text="Gmail, Seznam i Outlook vyžadují speciální heslo pro stahování faktur – klikněte pro postup krok za krokem.",
            font=self.fonts["small"], text_color=THEME["text_mute"], anchor="w")
        lbl_sub.grid(row=1, column=1, sticky="w")

        self.btn_navod_toggle = ctk.CTkButton(
            hdr, text="📖 Rozbalit návod  ▼", font=self.fonts["small_bold"],
            height=32, corner_radius=R_BTN, fg_color=THEME["primary"],
            hover_color=THEME["primary_hi"], text_color="white",
            command=self.toggle_navod_email)
        self.btn_navod_toggle.grid(row=0, column=2, rowspan=2, padx=(10, 0), sticky="e")

        # Tělo návodu (skryté ve výchozím stavu)
        self.navod_body = ctk.CTkFrame(self.navod_card, fg_color="transparent")

        # Dělící linka
        ctk.CTkFrame(self.navod_body, height=1, fg_color=THEME["result_brd"]).pack(
            fill="x", padx=14, pady=(0, 10))

        # Přepínač poskytovatelů
        self.seg_navod_tab = ctk.CTkSegmentedButton(
            self.navod_body,
            values=["🔴 Gmail (Google)", "🟡 Seznam.cz / Email.cz", "🔵 Outlook / Ostatní"],
            command=self._zmenit_tab_navodu,
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hi"],
            corner_radius=R_BTN, height=32, font=self.fonts["small_bold"])
        self.seg_navod_tab.set("🔴 Gmail (Google)")
        self.seg_navod_tab.pack(padx=16, pady=(0, 12))

        # Kontejner pro jednotlivé záložky
        self.navod_panels_container = ctk.CTkFrame(self.navod_body, fg_color="transparent")
        self.navod_panels_container.pack(fill="x", padx=16, pady=(0, 10))

        # Panely pro jednotlivé poskytovatele
        self.panel_gmail = self._build_navod_gmail_panel(self.navod_panels_container)
        self.panel_seznam = self._build_navod_seznam_panel(self.navod_panels_container)
        self.panel_outlook = self._build_navod_outlook_panel(self.navod_panels_container)

        self.panel_gmail.pack(fill="x")

        # Spodní lišta se zavřením
        ctk.CTkButton(
            self.navod_body, text="▲ Skrýt návod", font=self.fonts["small_bold"],
            fg_color="transparent", text_color=THEME["text_mute"],
            hover_color=THEME["card_alt"], height=28, corner_radius=R_BTN,
            command=self.toggle_navod_email).pack(pady=(4, 10))

    def _build_navod_gmail_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        info_box = ctk.CTkFrame(panel, fg_color=THEME["card"], corner_radius=8,
                                border_width=1, border_color=THEME["card_brd"])
        info_box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info_box,
            text="ℹ️  PROČ TO NEJDE BĚŽNÝM HESLEM?\n"
                 "Google z bezpečnostních důvodů zakazuje programům přihlašovat se vaším běžným heslem ke Google účtu.\n"
                 "Místo toho vám Google zdarma vygeneruje bezpečné 16místné „Heslo aplikace“, které slouží výhradně pro stahování faktur.",
            font=self.fonts["small"], text_color=THEME["text"],
            justify="left", anchor="w").pack(padx=12, pady=10, fill="x")

        kroky = [
            ("1. Dvoufázové ověření na Google",
             "Na svém Google účtu musíte mít zapnuté Dvoufázové ověření (SMS kód nebo potvrzení na mobilu).\n"
             "Pokud ho ještě nemáte aktivní, Google vás při vstupu na odkaz níže vyzve k jeho zapnutí."),
            ("2. Otevřete oficiální generátor hesel Google",
             "Klikněte na modré tlačítko níže – stránka se vám ihned otevře přímo ve vašem webovém prohlížeči:"),
        ]
        for t, d in kroky:
            ctk.CTkLabel(panel, text=t, font=self.fonts["body_bold"],
                         text_color=THEME["text"], anchor="w").pack(fill="x", pady=(4, 1))
            ctk.CTkLabel(panel, text=d, font=self.fonts["small"],
                         text_color=THEME["text_mute"], justify="left", anchor="w").pack(fill="x", pady=(0, 6))

        btn_app_pwd = ctk.CTkButton(
            panel, text="🌐  1. OTEVŘÍT GOOGLE HESLA APLIKACÍ (v prohlížeči)",
            font=self.fonts["small_bold"], height=36, corner_radius=R_BTN,
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="white",
            command=lambda: webbrowser.open("https://myaccount.google.com/apppasswords"))
        btn_app_pwd.pack(fill="x", pady=(2, 10))

        kroky2 = [
            ("3. Vytvořte heslo pro aplikaci",
             "Do políčka „Název aplikace“ napište např. Gordic a klikněte na tlačítko Vytvořit."),
            ("4. Zkopírujte vygenerované 16místné heslo",
             "Google vám zobrazí žlutý rámeček se 16 písmeny (např. abcd efgh ijkl mnop).\n"
             "Označte ho myší a zkopírujte (klávesová zkratka Ctrl+C)."),
            ("5. Vložte heslo do formuláře níže",
             "Do pole „Heslo aplikace (E-mail)“ níže vložte toto zkopírované heslo a klikněte na 💾 ULOŽIT NASTAVENÍ."),
            ("6. DŮLEŽITÉ: Zkontrolujte povolení protokolu IMAP v Gmailu",
             "Aby mohl program faktury ze schránky stáhnout, musí mít Gmail povolený protokol IMAP.\n"
             "Klikněte na tlačítko níže, ověřte zaškrtnutí „Povolit protokol IMAP“ a dole klikněte na Uložit změny:")
        ]
        for t, d in kroky2:
            ctk.CTkLabel(panel, text=t, font=self.fonts["body_bold"],
                         text_color=THEME["text"], anchor="w").pack(fill="x", pady=(4, 1))
            ctk.CTkLabel(panel, text=d, font=self.fonts["small"],
                         text_color=THEME["text_mute"], justify="left", anchor="w").pack(fill="x", pady=(0, 6))

        btn_imap = ctk.CTkButton(
            panel, text="📬  2. ZKONTROLOVAT POVOLENÍ IMAP V GMAILU (v prohlížeči)",
            font=self.fonts["small_bold"], height=36, corner_radius=R_BTN,
            fg_color="#4F46E5", hover_color="#4338CA", text_color="white",
            command=lambda: webbrowser.open("https://mail.google.com/mail/u/0/#settings/fwdandpop"))
        btn_imap.pack(fill="x", pady=(2, 6))

        return panel

    def _build_navod_seznam_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        info_box = ctk.CTkFrame(panel, fg_color=THEME["card"], corner_radius=8,
                                border_width=1, border_color=THEME["card_brd"])
        info_box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info_box,
            text="ℹ️  PRO SCHRÁNKY @seznam.cz, @email.cz, @post.cz\n"
                 "Aplikace si automaticky nastaví správný server (imap.seznam.cz).\n"
                 "Stačí mít v nastavení schránky povolený protokol IMAP a zadat heslo.",
            font=self.fonts["small"], text_color=THEME["text"],
            justify="left", anchor="w").pack(padx=12, pady=10, fill="x")

        kroky = [
            ("1. Přihlaste se na Seznam.cz",
             "Otevřete web www.seznam.cz a přihlaste se ke své e-mailové schránce."),
            ("2. Otevřete nastavení zabezpečení",
             "Klikněte na tlačítko níže pro přímý přechod do nastavení zabezpečení Seznamu:"),
        ]
        for t, d in kroky:
            ctk.CTkLabel(panel, text=t, font=self.fonts["body_bold"],
                         text_color=THEME["text"], anchor="w").pack(fill="x", pady=(4, 1))
            ctk.CTkLabel(panel, text=d, font=self.fonts["small"],
                         text_color=THEME["text_mute"], justify="left", anchor="w").pack(fill="x", pady=(0, 6))

        btn_seznam = ctk.CTkButton(
            panel, text="🌐  OTEVŘÍT ZABEZPEČENÍ SEZNAMU (v prohlížeči)",
            font=self.fonts["small_bold"], height=36, corner_radius=R_BTN,
            fg_color="#CC0000", hover_color="#990000", text_color="white",
            command=lambda: webbrowser.open("https://ucet.seznam.cz/zabezpeceni"))
        btn_seznam.pack(fill="x", pady=(2, 10))

        kroky2 = [
            ("3. Povolte protokol IMAP",
             "V sekci Zabezpečení zkontrolujte, zda máte povolený přístup přes protokol IMAP\n"
             "(pokud máte zapnuté dvoufázové ověření Seznamu, klikněte na „Hesla pro aplikace“ a vytvořte si heslo)."),
            ("4. Zadejte údaje do formuláře níže",
             "Do pole „Přihlašovací e-mail“ zadejte celou adresu (např. ucetni@seznam.cz).\n"
             "Do pole „Heslo aplikace (E-mail)“ zadejte své heslo k Seznamu."),
            ("5. Vyzkoušejte spojení",
             "Klikněte na tlačítko „🔌 Test E-mailu“ níže. Až se objeví zelené potvrzení, klikněte na 💾 ULOŽIT NASTAVENÍ.")
        ]
        for t, d in kroky2:
            ctk.CTkLabel(panel, text=t, font=self.fonts["body_bold"],
                         text_color=THEME["text"], anchor="w").pack(fill="x", pady=(4, 1))
            ctk.CTkLabel(panel, text=d, font=self.fonts["small"],
                         text_color=THEME["text_mute"], justify="left", anchor="w").pack(fill="x", pady=(0, 6))

        return panel

    def _build_navod_outlook_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        info_box = ctk.CTkFrame(panel, fg_color=THEME["card"], corner_radius=8,
                                border_width=1, border_color=THEME["card_brd"])
        info_box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info_box,
            text="ℹ️  PRO PRACOVNÍ A OBECNÍ SCHRÁNKY\n"
                 "Podporuje @outlook.com, @hotmail.com, Microsoft 365 i vlastní domény obcí a úřadů.\n"
                 "Aplikace sama automaticky detekuje a nastaví správný poštovní server.",
            font=self.fonts["small"], text_color=THEME["text"],
            justify="left", anchor="w").pack(padx=12, pady=10, fill="x")

        kroky = [
            ("1. Zadejte e-mailovou adresu",
             "Do pole „Přihlašovací e-mail“ níže zadejte svou celou adresu (např. starosta@obec.cz nebo ucetni@outlook.cz)."),
            ("2. Zadejte přihlašovací heslo",
             "Do pole „Heslo aplikace (E-mail)“ zadejte své běžné heslo k této schránce."),
            ("3. Otestujte spojení",
             "Klikněte na tlačítko „🔌 Test E-mailu“ níže pro ověření připojení ke schránce."),
            ("💡 TIP PRO OBECNÍ ÚŘADY A IT SPRÁVCE:",
             "Pokud se spojení nezdaří s chybou ověření, může mít Microsoft 365 na vašem úřadě zakázaný protokol IMAP.\n"
             "V takovém případě stačí kontaktovat vašeho IT správce se zprávou:\n"
             "„Prosím o povolení protokolu IMAP pro schránku s fakturami kvůli automatickému stahování.“")
        ]
        for t, d in kroky:
            ctk.CTkLabel(panel, text=t, font=self.fonts["body_bold"],
                         text_color=THEME["text"], anchor="w").pack(fill="x", pady=(4, 1))
            ctk.CTkLabel(panel, text=d, font=self.fonts["small"],
                         text_color=THEME["text_mute"], justify="left", anchor="w").pack(fill="x", pady=(0, 6))

        return panel

    def toggle_navod_email(self):
        if getattr(self, "navod_otevren", False):
            self.navod_body.pack_forget()
            self.btn_navod_toggle.configure(text="📖 Rozbalit návod  ▼")
            self.navod_otevren = False
        else:
            self.navod_body.pack(fill="x", padx=4, pady=(0, 10))
            self.btn_navod_toggle.configure(text="▲ Skrýt návod")
            self.navod_otevren = True

    def rozbalit_navod_email(self, provider="🔴 Gmail (Google)"):
        if not getattr(self, "navod_otevren", False):
            self.navod_body.pack(fill="x", padx=4, pady=(0, 10))
            self.btn_navod_toggle.configure(text="▲ Skrýt návod")
            self.navod_otevren = True
        self.seg_navod_tab.set(provider)
        self._zmenit_tab_navodu(provider)

    def _zmenit_tab_navodu(self, val):
        self.panel_gmail.pack_forget()
        self.panel_seznam.pack_forget()
        self.panel_outlook.pack_forget()
        if "Gmail" in val:
            self.panel_gmail.pack(fill="x")
        elif "Seznam" in val:
            self.panel_seznam.pack(fill="x")
        else:
            self.panel_outlook.pack(fill="x")

    def prejit_na_navod_email(self):
        self.show_nastaveni_event()
        self.rozbalit_navod_email()

    # =============================================================
    # NÁVOD NA IMPORT ISDOC DO GORDICU (ACCORDION V DASHBOARDU)
    # =============================================================
    def _build_navod_gordic_accordion(self, parent):
        self.gordic_navod_otevren = False

        self.gordic_navod_card = ctk.CTkFrame(
            parent, fg_color=THEME["result_bg"], corner_radius=R,
            border_width=1, border_color=THEME["result_brd"])
        self.gordic_navod_card.pack(pady=(4, 10), padx=10, fill="x")

        # Hlavička (klikací lišta)
        hdr = ctk.CTkFrame(self.gordic_navod_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=10)
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="📌", font=self.fonts["icon_sm"]).grid(
            row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        ctk.CTkLabel(
            hdr, text="Jak naimportovat hotový ISDOC soubor do systému GORDIC?",
            font=self.fonts["body_bold"], text_color=THEME["text"], anchor="w"
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            hdr,
            text="Po vygenerování ISDOC souboru ho stačí nahrát do GORDIC systému – klikněte pro postup krok za krokem.",
            font=self.fonts["small"], text_color=THEME["text_mute"], anchor="w"
        ).grid(row=1, column=1, sticky="w")

        self.btn_gordic_navod_toggle = ctk.CTkButton(
            hdr, text="📖 Zobrazit postup  ▼", font=self.fonts["small_bold"],
            height=32, corner_radius=R_BTN, fg_color=THEME["success"],
            hover_color=THEME["success_hi"], text_color="white",
            command=self.toggle_navod_gordic)
        self.btn_gordic_navod_toggle.grid(row=0, column=2, rowspan=2, padx=(10, 0), sticky="e")

        # Tělo (skryté ve výchozím stavu)
        self.gordic_navod_body = ctk.CTkFrame(self.gordic_navod_card, fg_color="transparent")

        ctk.CTkFrame(self.gordic_navod_body, height=1,
                     fg_color=THEME["result_brd"]).pack(fill="x", padx=14, pady=(0, 10))

        kroky = [
            ("1️⃣  Otevřete složku s ISDOC soubory",
             "Klikněte na tlačítko  ⚙️ Exporty ISDOC  v levém menu a pak na  📂 Otevřít složku.\n"
             "Případně přejděte ručně do:  Dokumenty → Gordic_Asistent → isdoc_vystup"),
            ("2️⃣  Zkopírujte soubor na síťové úložiště obce",
             "Soubor má název  FA_xxxxxxxxx.isdoc  (místo x je číslo faktury).\n"
             "Přesuňte nebo zkopírujte ho na váš síťový disk (kde máte přístup z GORDIC systému)."),
            ("3️⃣  Přihlaste se do systému GORDIC (GINIS)",
             "Otevřete GORDIC aplikaci a přejděte do modulu:\n"
             "Doklady  →  Import dokladů  (nebo  Faktury přijaté  →  Import)"),
            ("4️⃣  Vyberte typ importu: ISDOC",
             "V dialogu importu zvolte typ souboru:  ISDOC – Elektronická faktura (ISO 16931)\n"
             "Pak vyberte soubor  FA_xxxxxxxxx.isdoc  ze síťového úložiště a klikněte  OK."),
            ("5️⃣  GORDIC automaticky načte údaje z faktury",
             "Systém sám vyplní: jméno dodavatele, IČO, číslo faktury, částku, DPH a datum splatnosti.\n"
             "Nemusíte nic přepisovat ručně – to za vás udělala AI."),
            ("6️⃣  Zkontrolujte a zaúčtujte doklad",
             "Doplňte analytický účet, paragraf a středisko (pokud vyžaduje váš úřad).\n"
             "Klikněte na  Zaúčtovat  nebo  Uložit  – faktura je zpracována! ✅"),
        ]

        for t, d in kroky:
            row_f = ctk.CTkFrame(self.gordic_navod_body, fg_color="transparent")
            row_f.pack(fill="x", padx=16, pady=(2, 4))
            ctk.CTkLabel(row_f, text=t,
                         font=self.fonts["body_bold"], text_color=THEME["text"],
                         anchor="w").pack(fill="x")
            ctk.CTkLabel(row_f, text=d,
                         font=self.fonts["small"], text_color=THEME["text_mute"],
                         justify="left", anchor="w", wraplength=700).pack(fill="x", padx=(20, 0))

        ctk.CTkButton(
            self.gordic_navod_body, text="▲ Skrýt postup",
            font=self.fonts["small_bold"],
            fg_color="transparent", text_color=THEME["text_mute"],
            hover_color=THEME["card_alt"], height=28, corner_radius=R_BTN,
            command=self.toggle_navod_gordic).pack(pady=(4, 10))

    def toggle_navod_gordic(self):
        if getattr(self, "gordic_navod_otevren", False):
            self.gordic_navod_body.pack_forget()
            self.btn_gordic_navod_toggle.configure(text="📖 Zobrazit postup  ▼")
            self.gordic_navod_otevren = False
        else:
            self.gordic_navod_body.pack(fill="x", padx=4, pady=(0, 10))
            self.btn_gordic_navod_toggle.configure(text="▲ Skrýt postup")
            self.gordic_navod_otevren = True

    # =============================================================
    # STAVOVÝ INDIKÁTOR A LOG
    # =============================================================
    def set_stav(self, stav, text):
        barva = STAV_BARVY.get(stav, THEME["text_mute"])
        self.lbl_stav_dot.configure(text_color=barva)
        self.lbl_status.configure(text=text, text_color=barva)

    def log(self, zprava, typ="info"):
        barvy = {"ok": THEME["success"], "err": THEME["danger"],
                 "work": THEME["warning"], "info": THEME["text_mute"]}
        znaky = {"ok": "✓", "err": "✗", "work": "⏳", "info": "•"}
        cas = datetime.datetime.now().strftime("%H:%M:%S")
        tag = f"t_{typ}"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{cas}  {znaky.get(typ, '•')}  {zprava}\n", tag)
        try:
            self.log_box.tag_config(tag, foreground=barvy.get(typ, THEME["text_mute"]))
        except Exception:
            pass
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def log_vycisti(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def toggle_log(self, vynutit_otevrit=False):
        if self.log_otevreny and not vynutit_otevrit:
            self.log_box.pack_forget()
            self.log_otevreny = False
            self.btn_log_toggle.configure(text="▸  Průběh zpracování")
        elif not self.log_otevreny:
            self.log_box.pack(fill="both", expand=False, padx=8, pady=(0, 8))
            self.log_otevreny = True
            self.btn_log_toggle.configure(text="▾  Průběh zpracování")

    def toggle_vysledky(self):
        if self.vysledky_otevreny:
            self.vysledky_panel.pack_forget()
            self.vysledky_otevreny = False
            self.lbl_vysledky_toggle.configure(text="▸  Výsledky posledního zpracování")
        else:
            self.vysledky_panel.pack(fill="x", padx=8, pady=(0, 10))
            self.vysledky_otevreny = True
            self.lbl_vysledky_toggle.configure(text="▾  Výsledky posledního zpracování")

    def zobraz_vysledky_faktury(self, data):
        """Zobrazí výsledková data faktury v kartičkách."""
        for w in self.vysledky_panel.winfo_children():
            w.destroy()

        grid = ctk.CTkFrame(self.vysledky_panel, fg_color="transparent")
        grid.pack(fill="x", pady=4)
        for col in range(4):
            grid.grid_columnconfigure(col, weight=1)

        fields = [
            ("Číslo faktury", data.get("cislo_faktury"), THEME["primary"]),
            ("Dodavatel", data.get("dodavatel_nazev"), THEME["text"]),
            ("Základ bez DPH", f"{float(data.get('castka_zaklad', 0)):,.2f} Kč", THEME["text"]),
            ("DPH", f"{float(data.get('castka_dph', 0)):,.2f} Kč", THEME["warning"]),
            ("Celkem", f"{float(data.get('castka_celkem', 0)):,.2f} Kč", THEME["success"]),
            ("Variabilní symbol", data.get("variabilni_symbol"), THEME["text"]),
            ("IČO dodavatele", data.get("dodavatel_ico"), THEME["text"]),
            ("Paragraf", data.get("paragraf") or "—", THEME["violet"]),
        ]
        for idx, (lbl, val, col) in enumerate(fields):
            rc = self.result_card(grid, lbl, val, color=col)
            rc.grid(row=idx // 4, column=idx % 4, padx=4, pady=4, sticky="ew")

        if not self.vysledky_otevreny:
            self.toggle_vysledky()

    def obnov_statistiky_ui(self):
        celkem = back_gordick.ziskej_statistiky()
        minuty = celkem * 3
        h, m = minuty // 60, minuty % 60
        self.lbl_stats_time.configure(
            text=f"{h}h {m}m" if h > 0 else f"{m} min")
        self.lbl_stats_count.configure(text=f"{celkem} zprac. dokumentů")
        try:
            self.lbl_celkem_db.configure(text=str(celkem))
            self.lbl_dnes.configure(text=str(self._dnes_pocet()))
            posledni = self._posledni_faktura()
            self.lbl_posledni.configure(text=posledni if posledni else "—")
        except Exception:
            pass

    # =============================================================
    # NAVIGACE
    # =============================================================
    def _show_frame(self, frame):
        if self.active_frame:
            self.active_frame.grid_forget()
        frame.grid(row=1, column=0, sticky="nsew")
        self.active_frame = frame

    def show_dashboard_event(self):
        self.section_title_label.configure(text="Příprava faktury pro Gordic")
        self._set_nav_active(self.nav_items[0])
        self._show_frame(self.frame_dashboard)
        self.obnov_statistiky_ui()

    def show_archiv_pdf_event(self):
        count = self._file_count(back_gordick.SLOZKA_ARCHIV, ".pdf")
        self.section_title_label.configure(
            text=f"Archiv Zpracovaných PDF  ·  {count} souborů")
        self._set_nav_active(self.nav_items[1])
        self._show_frame(self.frame_archiv_pdf)
        self.nacti_historii()

    def show_archiv_isdoc_event(self):
        count = self._file_count(back_gordick.SLOZKA_VYSTUP, ".isdoc")
        self.section_title_label.configure(
            text=f"Připravené ISDOC soubory  ·  {count} exportů")
        self._set_nav_active(self.nav_items[2])
        self._show_frame(self.frame_archiv_isdoc)
        self.nacti_historii()

    def show_banka_event(self):
        self.section_title_label.configure(text="Účetní Košilka a Párování")
        self._set_nav_active(self.nav_items[3])
        self._show_frame(self.frame_banka)
        self.nacti_historii()

    def show_smlouvy_event(self):
        self.section_title_label.configure(text="Inteligentní Čtečka Smluv")
        self._set_nav_active(self.nav_items[4])
        self._show_frame(self.frame_smlouvy)
        self.nacti_historii()

    def show_nastaveni_event(self):
        self.section_title_label.configure(text="Nastavení a Údržba")
        all_items = self.nav_items + getattr(self, "nav_items_extra", [])
        self._set_nav_active(all_items[-1] if all_items else None)
        self.nacti_data_nastaveni()
        self._show_frame(self.frame_nastaveni)

    # =============================================================
    # DIALOGY
    # =============================================================
    def select_file_dialog(self):
        cesty = filedialog.askopenfilenames(
            filetypes=(("PDF", "*.pdf"), ("Vše", "*.*")))
        if cesty:
            self.vybrane_soubory_cesty = list(cesty)
            txt = (f"Vybráno: {len(cesty)} souborů" if len(cesty) > 1
                   else f"Vybráno: {os.path.basename(cesty[0])}")
            self.lbl_soubor_cesta.configure(
                text=txt, text_color=THEME["primary"],
                font=self.fonts["small_bold"])
            self.set_stav("pripraveno",
                          f"Připraveno {len(cesty)} souborů – klikni na SPUSTIT AI.")

    def select_gpc_dialog(self):
        cesta = filedialog.askopenfilename(
            filetypes=(("GPC", "*.gpc *.abo"), ("Vše", "*.*")))
        if cesta:
            self.cesta_gpc_souboru = cesta
            self.lbl_gpc_cesta.configure(
                text=f"Vybráno: {os.path.basename(cesta)}",
                text_color=THEME["warning"])

    def select_smlouva_dialog(self):
        cesta = filedialog.askopenfilename(
            filetypes=(("PDF", "*.pdf"), ("Vše", "*.*")))
        if cesta:
            self.cesta_smlouvy_souboru = cesta
            self.lbl_smlouva_cesta.configure(
                text=f"Vybráno: {os.path.basename(cesta)}",
                text_color=THEME["violet"])

    # =============================================================
    # HISTORIE A VYHLEDÁVÁNÍ
    # =============================================================
    def nacti_historii(self, _=None):
        self._populate_file_list(
            self.pdf_scroll, back_gordick.SLOZKA_ARCHIV, ".pdf",
            self.sort_pdf_var.get(), "📄", "Zpracováno")
        self._populate_file_list(
            self.isdoc_scroll, back_gordick.SLOZKA_VYSTUP, ".isdoc",
            self.sort_isdoc_var.get(), "⚙️", "Vytvořeno")
        self._populate_file_list(
            self.banka_scroll, back_gordick.SLOZKA_KOSILKY, ".txt",
            "Nejnovější", "🏛️", "Spárováno")
        self._populate_file_list(
            self.smlouvy_scroll, back_gordick.SLOZKA_SMLOUVY, ".txt",
            "Nejnovější", "📜", "Analyzováno")

    def spustit_hledani(self, event=None):
        dotaz = self.search_entry.get().strip()
        if not dotaz:
            self.nacti_historii()
            return
        for w in self.pdf_scroll.winfo_children():
            w.destroy()
        self._list_item_with_actions(
            self.pdf_scroll, f"🔍 Hledám: '{dotaz}'",
            "Prohledávám full-textový index...", "")
        self.update()
        try:
            vysledky = back_gordick.vyhledej_ve_fakturach(dotaz)
            for w in self.pdf_scroll.winfo_children():
                w.destroy()
            if not vysledky:
                self._empty_state(self.pdf_scroll, "❌", "Nic nenalezeno",
                                  "Zkus jiné klíčové slovo.")
            else:
                for v in vysledky:
                    cesta = os.path.join(back_gordick.SLOZKA_ARCHIV, v["pdf"])
                    if os.path.exists(cesta):
                        self._list_item_with_actions(
                            self.pdf_scroll, f"📄 {v['pdf']}",
                            f"...{v['utrzek']}...", cesta)
        except Exception as e:
            print(e)

    # =============================================================
    # NASTAVENÍ – CRUD
    # =============================================================
    def nacti_data_nastaveni(self, _=None):
        try:
            with open(back_gordick.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
        mapping = [
            ("ico", config.get("moje_ic_organizace", "")),
            ("email", config.get("email_nastaveni", {}).get("email_adresa", "")),
            ("heslo", config.get("email_nastaveni", {}).get("heslo_aplikace", "")),
            ("api", config.get("groq_api_key", "")),
        ]
        for name, value in mapping:
            entry = self._entries[name]
            entry.delete(0, "end")
            entry.insert(0, value)
        self.lbl_config_status.configure(text="Vše aktuální a uloženo.",
                                          text_color=THEME["text_mute"])
        self.btn_save_config.configure(text="💾 ULOŽIT NASTAVENÍ",
                                        fg_color=THEME["success"],
                                        hover_color=THEME["success_hi"])
        self.btn_revert_config.grid_remove()

    def oznacit_zmeny(self, event=None):
        self.lbl_config_status.configure(
            text="⚠️ Máš neuložené změny, nezapomeň to uložit!",
            text_color=THEME["warning"])
        self.btn_save_config.configure(
            text="⚠️ ULOŽIT ZMĚNY", fg_color=THEME["warning"],
            hover_color=THEME["warning_hi"])
        self.btn_revert_config.grid()

    def potvrdit_ulozeni(self):
        if messagebox.askyesno("Uložit změny",
                               "Opravdu chceš přepsat aktuální nastavení?"):
            self.ulozit_nastaveni()

    def ulozit_nastaveni(self):
        try:
            try:
                with open(back_gordick.CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = back_gordick.DEFAULT_CONFIG.copy()
            config["moje_ic_organizace"] = self.entry_ico.get().strip()
            config["groq_api_key"] = self.entry_api.get().strip()
            email_adresa = self.entry_email.get().strip()
            if "email_nastaveni" not in config or not isinstance(config["email_nastaveni"], dict):
                config["email_nastaveni"] = {}
            config["email_nastaveni"]["email_adresa"] = email_adresa
            config["email_nastaveni"]["heslo_aplikace"] = self.entry_heslo.get().strip()
            config["email_nastaveni"]["imap_server"] = back_gordick.detekuj_imap_server(email_adresa)
            os.makedirs(os.path.dirname(back_gordick.CONFIG_PATH), exist_ok=True)
            with open(back_gordick.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            back_gordick.reload_config()
            self.nacti_data_nastaveni()
            self.lbl_config_status.configure(
                text="✅ Úspěšně uloženo a aktivováno!",
                text_color=THEME["success"])
        except Exception as e:
            self.lbl_config_status.configure(
                text=f"⚠️ Chyba při ukládání: {e}", text_color=THEME["danger"])

    def potvrdit_reset_dat(self):
        if messagebox.askyesno(
                "⚠️ KRITICKÉ VAROVÁNÍ",
                "Opravdu chceš TRVALE SMAZAT všechny zpracované faktury, "
                "košilky a historii?!\n\nTato akce je nevratná!"):
            self.vymazat_vsechna_data()

    def vymazat_vsechna_data(self):
        for slozka in [back_gordick.SLOZKA_VSTUP, back_gordick.SLOZKA_VYSTUP,
                       back_gordick.SLOZKA_ARCHIV, back_gordick.SLOZKA_INDEX,
                       back_gordick.SLOZKA_KOSILKY, back_gordick.SLOZKA_SMLOUVY]:
            if os.path.exists(slozka):
                shutil.rmtree(slozka)
            os.makedirs(slozka, exist_ok=True)
        try:
            with open(back_gordick.CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["zpracovano_faktur_celkem"] = 0
            with open(back_gordick.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        except Exception:
            pass
        self.obnov_statistiky_ui()
        self.nacti_historii()
        messagebox.showinfo("Hotovo",
                            "Všechna data byla smazána. Začínáš s čistým štítem!")

    def change_appearance_mode_event(self, volba):
        if "Tmavý" in volba:
            ctk.set_appearance_mode("Dark")
            self._current_mode = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self._current_mode = "Light"

    # =============================================================
    # TEST PŘIPOJENÍ
    # =============================================================
    def test_pripojeni_email(self):
        self.lbl_test_email.configure(text="⏳ Testuji...", text_color=THEME["warning"])
        self._run_async(
            back_gordick.test_email_connection,
            (self.entry_email.get().strip(), self.entry_heslo.get().strip()),
            on_success=self._on_test_email,
            on_error=lambda e: self.lbl_test_email.configure(
                text=f"❌ {e}", text_color=THEME["danger"]),
            disable_btns=[self.btn_test_email])

    def _on_test_email(self, result):
        ok, msg = result
        self.lbl_test_email.configure(
            text=f"{'✅' if ok else '❌'} {msg}",
            text_color=THEME["success"] if ok else THEME["danger"])

    def test_pripojeni_api(self):
        self.lbl_test_api.configure(text="⏳ Testuji...", text_color=THEME["warning"])
        self._run_async(
            back_gordick.test_api_connection,
            (self.entry_api.get().strip(),),
            on_success=self._on_test_api,
            on_error=lambda e: self.lbl_test_api.configure(
                text=f"❌ {e}", text_color=THEME["danger"]),
            disable_btns=[self.btn_test_api])

    def _on_test_api(self, result):
        ok, msg = result
        self.lbl_test_api.configure(
            text=f"{'✅' if ok else '❌'} {msg}",
            text_color=THEME["success"] if ok else THEME["danger"])

    # =============================================================
    # ASYNC WORKERS
    # =============================================================
    def spustit_gpc_parovani(self):
        if not self.cesta_gpc_souboru:
            return
        try:
            cesta_kosilky = back_gordick.zpracuj_gpc_a_vytvor_kosilku(
                self.cesta_gpc_souboru)
            os.startfile(cesta_kosilky)
            self.lbl_gpc_cesta.configure(text="✅ Košilka vytvořena!",
                                          text_color=THEME["success"])
            self.cesta_gpc_souboru = None
            self.nacti_historii()
        except Exception as e:
            self.lbl_gpc_cesta.configure(text=f"⚠️ Chyba: {e}",
                                          text_color=THEME["danger"])

    def spustit_cteni_smlouvy(self):
        if not self.cesta_smlouvy_souboru:
            self.lbl_smlouva_cesta.configure(
                text="⚠️ Nejdřív vyber PDF smlouvu!", text_color=THEME["danger"])
            return
        self._run_async(
            back_gordick.vytvor_vytah_ze_smlouvy,
            (self.cesta_smlouvy_souboru,),
            on_success=self._smlouva_done,
            on_error=self._smlouva_error,
            disable_btns=[self.btn_smlouva_run],
            progress=self.progress_bar_smlouva)

    def _smlouva_done(self, vysledek):
        self.lbl_smlouva_cesta.configure(
            text="✅ Souhrn úspěšně vytvořen!", text_color=THEME["success"])
        self.cesta_smlouvy_souboru = None
        back_gordick.aktualizuj_statistiky(1)
        self.obnov_statistiky_ui()
        self.nacti_historii()
        # Pokud backend vrátil tuple (cesta, data), zobraz karty
        if isinstance(vysledek, tuple) and len(vysledek) == 2:
            cesta_txt, data = vysledek
            self._zobraz_smlouva_karty(data)
            os.startfile(cesta_txt)
        elif vysledek and os.path.exists(str(vysledek)):
            os.startfile(str(vysledek))

    def _zobraz_smlouva_karty(self, data):
        """Zobrazí klíčové údaje smlouvy v kartičkách."""
        for w in list(self.smlouva_result_frame.winfo_children()):
            try:
                lbl_text = w.cget("text") if hasattr(w, "cget") else ""
                if "📋" not in str(lbl_text):
                    w.destroy()
            except Exception:
                pass

        fields = [
            ("Smluvní strany", data.get("smluvni_strany"), THEME["primary"]),
            ("Předmět smlouvy", data.get("predmet_smlouvy"), THEME["text"]),
            ("Finanční částka", data.get("castka"), THEME["success"]),
            ("Datum uzavření", data.get("datum_uzavreni"), THEME["violet"]),
        ]
        for idx, (lbl, val, col) in enumerate(fields):
            rc = self.result_card(self.smlouva_result_frame, lbl, val, color=col)
            rc.grid(row=(idx // 2) + 1, column=idx % 2, padx=8, pady=4, sticky="ew")

    def _smlouva_error(self, msg):
        self.lbl_smlouva_cesta.configure(text="⚠️ Nelze přečíst",
                                          text_color=THEME["danger"])
        print(msg)

    def stáhnout_z_emailu_ui(self):
        self.toggle_log(vynutit_otevrit=True)
        self.log("Připojuji se k e-mailové schránce...", "work")
        self.set_stav("pracuji", "Stahuji faktury z e-mailu...")
        self._run_async(
            back_gordick.stahni_faktury_z_mailu,
            (self.option_obdobi.get(), bool(self.check_archivovane.get())),
            on_success=self._email_done,
            on_error=self._email_error,
            disable_btns=[self.btn_email, self.btn_run],
            progress=self.progress_bar)

    def _email_done(self, pocet):
        obsah = os.listdir(back_gordick.SLOZKA_VSTUP)
        cesty = [os.path.join(back_gordick.SLOZKA_VSTUP, f)
                 for f in obsah if f.lower().endswith('.pdf')]
        self.vybrane_soubory_cesty = cesty
        self.log(f"Staženo {pocet} faktur ze schránky.", "ok")
        self.set_stav("hotovo", f"Staženo {pocet} faktur. Klikni na SPUSTIT AI.")

    def _email_error(self, msg=""):
        if msg:
            self.log(f"Chyba e-mailu: {msg}", "err")
        self.set_stav("chyba", "Chyba při stahování e-mailu!")

    def spustit_prevod(self):
        if not self.vybrane_soubory_cesty:
            self.set_stav("chyba",
                          "Nejdřív vyber soubor nebo stáhni faktury z e-mailu.")
            return
        self.log_vycisti()
        self.toggle_log(vynutit_otevrit=True)
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.pack(pady=(0, 16), padx=40, fill="x")
        self.progress_bar.set(0)
        self.set_stav("pracuji", "Spouštím AI zpracování...")
        self.log(f"Zahajuji zpracování {len(self.vybrane_soubory_cesty)} souborů.", "work")
        for b in [self.btn_email, self.btn_run, self.btn_browse]:
            b.configure(state="disabled")
        threading.Thread(target=self._prevod_worker, daemon=True).start()

    def _prevod_worker(self):
        total = len(self.vybrane_soubory_cesty)
        ok_count = 0
        last_data = None
        for i, cesta in enumerate(self.vybrane_soubory_cesty):
            jmeno = os.path.basename(cesta)
            self.after(0, lambda idx=i, jm=jmeno:
                       self._prevod_progress(idx, total, jm))
            cesta_vstup = os.path.join(back_gordick.SLOZKA_VSTUP, jmeno)
            if os.path.dirname(cesta) != back_gordick.SLOZKA_VSTUP:
                try:
                    shutil.copy(cesta, cesta_vstup)
                except Exception:
                    pass
            try:
                text = back_gordick.vytahni_text_z_pdf(cesta_vstup)
                data = back_gordick.analyzuj_fakturu_mozkem(text)
                back_gordick.vygeneruj_isdoc(data)
                shutil.move(cesta_vstup,
                            os.path.join(back_gordick.SLOZKA_ARCHIV, jmeno))
                ok_count += 1
                last_data = data
                self.after(0, lambda jm=jmeno:
                           self.log(f"{jm} – ISDOC vytvořen.", "ok"))
            except Exception as e:
                self.after(0, lambda jm=jmeno, err=str(e):
                           self.log(f"{jm} – chyba: {err}", "err"))
        self.after(0, lambda: self._prevod_done(ok_count, total, last_data))

    def _prevod_progress(self, idx, total, jmeno):
        self.progress_bar.set(idx / total)
        self.set_stav("pracuji", f"🤖 AI zpracovává {idx + 1}/{total}...")
        self.log(f"Zpracovávám {jmeno} ({idx + 1}/{total})...", "work")

    def _prevod_done(self, ok_count, total, last_data=None):
        if ok_count > 0:
            back_gordick.aktualizuj_statistiky(ok_count)
            self.obnov_statistiky_ui()
        self.progress_bar.set(1)
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        for b in [self.btn_email, self.btn_run, self.btn_browse]:
            b.configure(state="normal")
        self.nacti_historii()
        self.vybrane_soubory_cesty = []
        self.lbl_soubor_cesta.configure(
            text="Není vybrán žádný soubor",
            text_color=THEME["text_mute"],
            font=self.fonts["small_it"])
        if last_data:
            self.after(100, lambda: self.zobraz_vysledky_faktury(last_data))
        chyby = total - ok_count
        if chyby == 0:
            self.set_stav("hotovo", f"✅ Hotovo – převedeno všech {ok_count} faktur.")
            self.log(f"Hotovo. Úspěšně převedeno {ok_count} z {total}.", "ok")
        else:
            self.set_stav("chyba", f"Převedeno {ok_count} z {total} – {chyby} selhalo.")
            self.log(f"Dokončeno s chybami: {ok_count} OK, {chyby} selhalo.", "err")


if __name__ == "__main__":
    app = GordicAsistentUI()
    app.mainloop()
