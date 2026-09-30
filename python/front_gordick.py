import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import datetime
import threading
import json
import back_gordick

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# =============================================================
# DESIGN SYSTEM – centralizované barvy, radiusy, styly
# =============================================================
APP_VERSION = "2.0"

THEME = {
    # Pozadí & povrchy
    "bg":          ("#F0F2F5", "#0B1120"),
    "sidebar":     ("#FFFFFF", "#0F1729"),
    "card":        ("#FFFFFF", "#162032"),
    "card_brd":    ("#E2E8F0", "#1E3048"),
    "card_alt":    ("#F8FAFC", "#131D2E"),
    # Text
    "text":        ("#0F172A", "#E8EDF5"),
    "text_mute":   ("#64748B", "#8896AB"),
    "text_sub":    ("#94A3B8", "#5E6F84"),
    # Navigace
    "nav_active":  ("#EEF2FF", "#1A2744"),
    "nav_bar":     "#6366F1",
    "nav_hover":   ("#F1F5F9", "#141E33"),
    # Akcenty
    "primary":     "#6366F1",  "primary_hi":  "#4F46E5",
    "success":     "#10B981",  "success_hi":  "#059669",
    "warning":     "#F59E0B",  "warning_hi":  "#D97706",
    "danger":      "#EF4444",  "danger_hi":   "#DC2626",
    "violet":      "#8B5CF6",  "violet_hi":   "#7C3AED",
    "neutral":     ("#64748B", "#475569"),
    "neutral_hi":  ("#475569", "#334155"),
    # Speciální
    "logo_text":   ("#1E3A8A", "#818CF8"),
    "danger_bg":   ("#FEF2F2", "#1C0F0F"),
    "danger_brd":  ("#FECACA", "#5C1616"),
}

R = 14          # card corner radius
R_BTN = 8       # button corner radius
PAD_SECTION = 36  # hlavní odsazení obsahu

STAV_BARVY = {
    "pripraveno": THEME["primary"],
    "pracuji":    THEME["warning"],
    "hotovo":     THEME["success"],
    "chyba":      THEME["danger"],
}

# Tlačítkové styly: (fg, hover, text_color)
BTN_STYLES = {
    "primary": (THEME["primary"], THEME["primary_hi"], "white"),
    "success": (THEME["success"], THEME["success_hi"], "white"),
    "warning": (THEME["warning"], THEME["warning_hi"], "white"),
    "danger":  (THEME["danger"],  THEME["danger_hi"],  "white"),
    "violet":  (THEME["violet"],  THEME["violet_hi"],  "white"),
    "neutral": (THEME["neutral"], THEME["neutral_hi"], "white"),
}


class GordicAsistentUI(ctk.CTk):
    """Hlavní okno aplikace Gordic Asistent – prémiová verze 2.0."""

    def __init__(self):
        super().__init__()
        self.title("Gordic Import Asistent")
        self.geometry("1240x820")
        self.minsize(1020, 640)
        self.configure(fg_color=THEME["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Centralizovaná font škála
        self.fonts = {
            "title":       ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            "card_title":  ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            "body":        ctk.CTkFont(family="Segoe UI", size=14),
            "body_bold":   ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            "small":       ctk.CTkFont(family="Segoe UI", size=12),
            "small_bold":  ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            "small_it":    ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            "icon":        ctk.CTkFont(size=40),
            "dot":         ctk.CTkFont(size=18),
            "mono":        ctk.CTkFont(family="Consolas", size=12),
            "cta":         ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            "nav":         ctk.CTkFont(family="Segoe UI", size=14),
            "section_btn": ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            "stat_num":    ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            "logo":        ctk.CTkFont(family="Impact", size=24),
            "version":     ctk.CTkFont(family="Segoe UI", size=10),
        }

        # Stav aplikace
        self.vybrane_soubory_cesty = []
        self.cesta_gpc_souboru = None
        self.cesta_smlouvy_souboru = None
        self.log_otevreny = False
        self.sort_pdf_var = ctk.StringVar(value="Nejnovější")
        self.sort_isdoc_var = ctk.StringVar(value="Nejnovější")

        # Sestavení UI
        self._build_sidebar()
        self._build_main_area()
        self.nacti_historii()
        self.show_dashboard_event()

    # =============================================================
    # TOVÁRNY NA WIDGETY (znovupoužitelné)
    # =============================================================
    def btn(self, master, text, command=None, kind="primary", height=40,
            corner_radius=R_BTN, **kw):
        """Univerzální továrna na stylizovaná tlačítka."""
        fg, hov, txt = BTN_STYLES.get(kind, BTN_STYLES["primary"])
        kw.setdefault("font", self.fonts["body"])
        return ctk.CTkButton(master, text=text, command=command, height=height,
                             corner_radius=corner_radius, fg_color=fg,
                             hover_color=hov, text_color=txt, **kw)

    def card(self, master, **kw):
        """Vytvoří kartu se zaoblenými rohy a jemným ohraničením."""
        return ctk.CTkFrame(master, fg_color=THEME["card"], corner_radius=R,
                            border_width=1, border_color=THEME["card_brd"], **kw)

    # =============================================================
    # DRY HELPERS – eliminují duplicitní kód
    # =============================================================
    def _toggle_visibility(self, entry, button):
        """Generické přepnutí viditelnosti hesla v Entry poli."""
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="🙈")
        else:
            entry.configure(show="*")
            button.configure(text="👁️")

    def _run_async(self, worker_fn, worker_args=(),
                   on_success=None, on_error=None,
                   disable_btns=None,
                   progress=None, progress_pack=None):
        """Generický async worker – jedno místo pro vlákna, progress bary a cleanup.

        Eliminuje duplicitní vzor: disable → thread → done/error → enable,
        který se dříve opakoval pro e-maily, smlouvy i testování.
        """
        for b in (disable_btns or []):
            b.configure(state="disabled")
        if progress and progress_pack:
            progress.pack(**progress_pack)
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
        """Společný cleanup po dokončení async operace."""
        if progress:
            progress.stop()
            progress.pack_forget()
        for b in (disable_btns or []):
            b.configure(state="normal")
        if callback:
            callback(result)

    def _populate_file_list(self, scroll, folder, ext, sort, icon, verb):
        """Generický populátor seznamu souborů pro archivní pohledy."""
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
            self._list_item(scroll, f"{icon} {f}", f"{verb}: {ts}",
                            lambda p=path: os.startfile(p))

    def _sorted_files(self, folder, ext, sort="Nejnovější"):
        """Vrátí seřazený seznam souborů v dané složce."""
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
        """Zobrazí prázdný stav s ikonou a textem."""
        wrapper = ctk.CTkFrame(master, fg_color="transparent")
        wrapper.pack(expand=True, fill="both", pady=40)
        ctk.CTkLabel(wrapper, text=icon,
                     font=ctk.CTkFont(size=52)).pack(pady=(20, 8))
        ctk.CTkLabel(wrapper, text=title, font=self.fonts["body_bold"],
                     text_color=THEME["text_mute"]).pack()
        if subtitle:
            ctk.CTkLabel(wrapper, text=subtitle, font=self.fonts["small"],
                         text_color=THEME["text_sub"]).pack(pady=(4, 0))

    def _list_item(self, master, title, sub, command):
        """Jeden řádek seznamu s titulkem, podtitulkem a tlačítkem Otevřít."""
        item = ctk.CTkFrame(master, fg_color="transparent")
        item.pack(fill="x", padx=15, pady=10)
        item.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(item, text=title, font=self.fonts["body_bold"],
                     anchor="w", text_color=THEME["text"]).grid(
                         row=0, column=0, sticky="w")
        ctk.CTkLabel(item, text=sub, font=self.fonts["small_it"],
                     text_color=THEME["text_mute"], anchor="w", wraplength=450,
                     justify="left").grid(row=1, column=0, sticky="w")
        if command:
            self.btn(item, "Otevřít", command, kind="primary", width=90,
                     height=32, corner_radius=16).grid(
                         row=0, column=1, rowspan=2, padx=(10, 0))
        ctk.CTkFrame(master, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=10, pady=(5, 0))

    def _create_action_card(self, master, icon, title, desc, browse_text,
                            browse_cmd, run_text, run_cmd, run_kind="primary",
                            default_label="Není vybrán žádný soubor",
                            has_progress=False, progress_color=None):
        """Znovupoužitelná akční karta (Banka, Smlouvy)."""
        c = self.card(master)
        c.pack(fill="both", expand=True)
        ctk.CTkLabel(c, text=icon, font=self.fonts["icon"]).pack(pady=(30, 8))
        ctk.CTkLabel(c, text=title, font=self.fonts["card_title"],
                     text_color=THEME["text"]).pack(pady=4)
        ctk.CTkLabel(c, text=desc, font=self.fonts["body"],
                     text_color=THEME["text_mute"], justify="center").pack(
                         pady=(4, 18))
        browse_btn = self.btn(c, browse_text, browse_cmd, kind="neutral",
                              height=38)
        browse_btn.pack(pady=8)
        label = ctk.CTkLabel(c, text=default_label, text_color=THEME["text_mute"],
                             font=self.fonts["small_it"])
        label.pack(pady=(0, 16))
        progress = None
        if has_progress:
            progress = ctk.CTkProgressBar(
                c, mode="indeterminate", height=6, corner_radius=3,
                progress_color=progress_color or THEME["primary"])
        run_btn = self.btn(c, run_text, run_cmd, kind=run_kind, height=52,
                           font=self.fonts["section_btn"])
        run_btn.pack(pady=(8, 30), padx=36, fill="x")
        return c, browse_btn, label, run_btn, progress

    def _create_archive_frame(self, open_folder_cmd, sort_var, with_search=False):
        """Znovupoužitelný archivní rám s toolbarem a volitelným vyhledáváním."""
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(1, weight=1)
        self.btn(top, "📂 Otevřít složku", open_folder_cmd, kind="neutral",
                 height=38).grid(row=0, column=0)
        ctk.CTkOptionMenu(top, values=["Nejnovější", "Nejstarší", "A-Z", "Z-A"],
                          variable=sort_var, command=self.nacti_historii,
                          fg_color=THEME["neutral"],
                          button_color=THEME["neutral_hi"],
                          corner_radius=R_BTN).grid(row=0, column=3)

        search_entry = None
        next_row = 1
        if with_search:
            sb = ctk.CTkFrame(frame, fg_color="transparent")
            sb.grid(row=1, column=0, sticky="ew", pady=(0, 12))
            sb.grid_columnconfigure(0, weight=1)
            search_entry = ctk.CTkEntry(
                sb, placeholder_text="🔍 Hledat obsah uvnitř faktur...",
                height=40, font=self.fonts["body"], corner_radius=R_BTN)
            search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            search_entry.bind("<Return>", self.spustit_hledani)
            self.btn(sb, "Hledat", self.spustit_hledani, kind="primary",
                     height=40, width=90).grid(row=0, column=1)
            next_row = 2

        frame.grid_rowconfigure(next_row, weight=1)
        scroll = ctk.CTkScrollableFrame(frame, fg_color=THEME["card"],
                                        corner_radius=R, border_width=1,
                                        border_color=THEME["card_brd"])
        scroll.grid(row=next_row, column=0, sticky="nsew")
        return frame, scroll, search_entry

    def _file_count(self, folder, ext):
        """Vrátí počet souborů v dané složce."""
        if not os.path.exists(folder):
            return 0
        return len([f for f in os.listdir(folder) if f.lower().endswith(ext)])

    # =============================================================
    # SIDEBAR – navigace s accent pruhem
    # =============================================================
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=250, corner_radius=0,
                          fg_color=THEME["sidebar"])
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(8, weight=1)
        self.sidebar_frame = sb

        # Logo
        ctk.CTkLabel(sb, text="GORDIC\nASISTENT",
                     font=self.fonts["logo"],
                     text_color=THEME["logo_text"]).grid(
                         row=0, column=0, padx=20, pady=(28, 4))
        ctk.CTkLabel(sb, text="Automatizace účetnictví",
                     font=ctk.CTkFont(size=11),
                     text_color=THEME["text_mute"]).grid(
                         row=1, column=0, pady=(0, 14))

        # Oddělovač
        ctk.CTkFrame(sb, height=1, fg_color=THEME["card_brd"]).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Navigační položky
        self.nav_items = []
        nav_defs = [
            ("🏠   Nová Faktura",    self.show_dashboard_event),
            ("📄   Archiv PDF",      self.show_archiv_pdf_event),
            ("⚙️   Exporty ISDOC",   self.show_archiv_isdoc_event),
            ("🏦   Párování Banky",  self.show_banka_event),
            ("📜   Čtečka Smluv",    self.show_smlouvy_event),
        ]
        for i, (text, cmd) in enumerate(nav_defs):
            item = self._create_nav_item(sb, text, 3 + i, cmd)
            self.nav_items.append(item)

        # Statistiky
        stats = ctk.CTkFrame(sb, fg_color=THEME["card"], corner_radius=R,
                             border_width=1, border_color=THEME["card_brd"])
        stats.grid(row=9, column=0, padx=16, pady=(16, 8), sticky="ew")
        ctk.CTkLabel(stats, text="⏱️ Tvoje úspora:", font=self.fonts["small"],
                     text_color=THEME["text_mute"]).pack(pady=(12, 0))
        self.lbl_stats_time = ctk.CTkLabel(
            stats, text="0 min", font=self.fonts["stat_num"],
            text_color=THEME["success"])
        self.lbl_stats_time.pack(pady=4)
        self.lbl_stats_count = ctk.CTkLabel(
            stats, text="0 dokumentů", font=self.fonts["small"],
            text_color=THEME["text_mute"])
        self.lbl_stats_count.pack(pady=(0, 12))
        self.obnov_statistiky_ui()

        # Tlačítko nastavení
        self.btn(sb, "⚙️  Nastavení", self.show_nastaveni_event, kind="neutral",
                 height=40, corner_radius=R_BTN, width=200,
                 font=self.fonts["small_bold"]).grid(
                     row=10, column=0, padx=16, pady=(4, 6))

        # Verze aplikace
        ctk.CTkLabel(sb, text=f"v{APP_VERSION}",
                     font=self.fonts["version"],
                     text_color=THEME["text_sub"]).grid(
                         row=11, column=0, pady=(0, 12))

    def _create_nav_item(self, parent, text, row, command):
        """Navigační položka s accent pruhem vlevo."""
        container = ctk.CTkFrame(parent, fg_color="transparent", height=42)
        container.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
        container.grid_columnconfigure(1, weight=1)
        container.grid_propagate(False)

        bar = ctk.CTkFrame(container, width=3, corner_radius=2,
                           fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ns", padx=(0, 6), pady=4)

        btn = ctk.CTkButton(container, text=text, font=self.fonts["nav"],
                            height=38, fg_color="transparent",
                            text_color=THEME["text"],
                            hover_color=THEME["nav_hover"], anchor="w",
                            corner_radius=R_BTN, command=command)
        btn.grid(row=0, column=1, sticky="ew")
        return {"button": btn, "bar": bar}

    def _set_nav_active(self, active_item):
        """Zvýrazní aktivní navigační položku s accent pruhem."""
        for item in self.nav_items:
            item["button"].configure(fg_color="transparent",
                                     text_color=THEME["text"])
            item["bar"].configure(fg_color="transparent")
        if active_item:
            active_item["button"].configure(fg_color=THEME["nav_active"])
            active_item["bar"].configure(fg_color=THEME["nav_bar"])

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
        self.section_title_label.grid(row=0, column=0, pady=(0, 18), sticky="w")

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

        # Karta: Nahrát z PC
        card_up = self.card(frame)
        card_up.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        ctk.CTkLabel(card_up, text="💻", font=self.fonts["icon"]).pack(
            pady=(30, 8))
        ctk.CTkLabel(card_up, text="Nahrát z počítače",
                     font=self.fonts["card_title"],
                     text_color=THEME["text"]).pack(pady=4)
        ctk.CTkLabel(card_up, text="Vyber jednu nebo více PDF faktur z disku",
                     font=self.fonts["small"],
                     text_color=THEME["text_mute"]).pack(pady=(0, 10))
        self.btn_browse = self.btn(card_up, "📁 Procházet PC...",
                                   self.select_file_dialog, kind="neutral",
                                   height=38)
        self.btn_browse.pack(pady=8)
        self.lbl_soubor_cesta = ctk.CTkLabel(
            card_up, text="Není vybrán žádný soubor",
            font=self.fonts["small_it"],
            text_color=THEME["text_mute"])
        self.lbl_soubor_cesta.pack(pady=(0, 20), padx=18)

        # Karta: E-mail
        card_em = self.card(frame)
        card_em.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        ctk.CTkLabel(card_em, text="📥", font=self.fonts["icon"]).pack(
            pady=(30, 8))
        ctk.CTkLabel(card_em, text="Stáhnout z e-mailu",
                     font=self.fonts["card_title"],
                     text_color=THEME["text"]).pack(pady=4)
        ctk.CTkLabel(card_em, text="Automaticky stáhne PDF faktury ze schránky",
                     font=self.fonts["small"],
                     text_color=THEME["text_mute"]).pack(pady=(0, 10))
        self.option_obdobi = ctk.CTkOptionMenu(
            card_em, values=["Den", "Týden", "Měsíc", "Rok", "Celá doba"],
            fg_color=THEME["neutral"], button_color=THEME["neutral_hi"],
            corner_radius=R_BTN)
        self.option_obdobi.pack(pady=8)
        self.check_archivovane = ctk.CTkCheckBox(
            card_em, text="Stáhnout i archivované", font=self.fonts["small"],
            fg_color=THEME["primary"], hover_color=THEME["primary_hi"])
        self.check_archivovane.pack(pady=8)
        self.btn_email = self.btn(card_em, "📨 Připojit a stáhnout",
                                  self.stáhnout_z_emailu_ui, kind="primary",
                                  height=38)
        self.btn_email.pack(pady=(4, 22))

        # Karta: Stav + Akce + Log
        card_st = self.card(frame)
        card_st.grid(row=1, column=0, columnspan=2, pady=(24, 0), sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)

        stav_row = ctk.CTkFrame(card_st, fg_color="transparent")
        stav_row.pack(pady=(20, 6))
        self.lbl_stav_dot = ctk.CTkLabel(stav_row, text="●",
                                          font=self.fonts["dot"],
                                          text_color=THEME["primary"])
        self.lbl_stav_dot.pack(side="left", padx=(0, 8))
        self.lbl_status = ctk.CTkLabel(
            stav_row, text="Aplikace připravena k práci.",
            font=self.fonts["body_bold"],
            text_color=THEME["primary"])
        self.lbl_status.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(
            card_st, mode="determinate", height=8, corner_radius=4,
            progress_color=THEME["primary"])
        self.progress_bar.set(0)

        self.btn_run = self.btn(
            card_st, "⚙️   SPUSTIT AI A VYTVOŘIT ISDOC", self.spustit_prevod,
            kind="primary", height=58, corner_radius=29, font=self.fonts["cta"])
        self.btn_run.pack(pady=(10, 20), padx=50, fill="x")

        ctk.CTkFrame(card_st, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=16, pady=(0, 2))
        self.btn_log_toggle = ctk.CTkButton(
            card_st, text="▸  Průběh zpracování", font=self.fonts["body"],
            fg_color="transparent", text_color=THEME["text_mute"],
            hover_color=THEME["nav_hover"], anchor="w",
            corner_radius=R_BTN, height=32, command=self.toggle_log)
        self.btn_log_toggle.pack(fill="x", padx=10, pady=(2, 0))
        self.log_box = ctk.CTkTextbox(
            card_st, height=140, font=self.fonts["mono"],
            fg_color=THEME["bg"], corner_radius=R_BTN, border_width=1,
            border_color=THEME["card_brd"])
        self.log_box.configure(state="disabled")

        return frame

    # ---------- ARCHIV PDF ----------
    def _build_archiv_pdf(self):
        frame, scroll, search = self._create_archive_frame(
            lambda: os.startfile(back_gordick.SLOZKA_ARCHIV),
            self.sort_pdf_var, with_search=True)
        return frame, scroll, search

    # ---------- ARCHIV ISDOC ----------
    def _build_archiv_isdoc(self):
        frame, scroll, _ = self._create_archive_frame(
            lambda: os.startfile(back_gordick.SLOZKA_VYSTUP),
            self.sort_isdoc_var)
        return frame, scroll

    # ---------- BANKA ----------
    def _build_banka(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=4)
        frame.grid_columnconfigure(1, weight=5)
        frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        _, self.btn_gpc_browse, self.lbl_gpc_cesta, self.btn_gpc_run, _ = \
            self._create_action_card(
                left, "🏦", "Automatické Párování",
                "Nahraj soubor z bankovnictví (.gpc)\na vytvoř úřední podepsanou košilku.",
                "Vybrat bankovní výpis...", self.select_gpc_dialog,
                "🔍 SPUSTIT PÁROVÁNÍ", self.spustit_gpc_parovani,
                run_kind="warning", default_label="Není vybrán žádný výpis")

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        self.btn(right, "📂 Otevřít složku s košilkami",
                 lambda: os.startfile(back_gordick.SLOZKA_KOSILKY),
                 kind="neutral", height=38).grid(
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
        left.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
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
        right.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        self.btn(right, "📂 Otevřít archiv smluv",
                 lambda: os.startfile(back_gordick.SLOZKA_SMLOUVY),
                 kind="neutral", height=38).grid(
                     row=0, column=0, sticky="ew", pady=(0, 8))
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
        scroll.grid(row=0, column=0, sticky="nsew", padx=36, pady=8)

        ctk.CTkLabel(scroll, text="🔧", font=self.fonts["icon"]).pack(
            pady=(30, 8))
        ctk.CTkLabel(scroll, text="Konfigurace Systému",
                     font=self.fonts["card_title"],
                     text_color=THEME["text"]).pack(pady=4)
        self.lbl_config_status = ctk.CTkLabel(
            scroll, text="Vše aktuální a uloženo.",
            font=self.fonts["small_it"],
            text_color=THEME["text_mute"])
        self.lbl_config_status.pack(pady=(0, 8))

        # Přepínač vzhledu
        vzhled = ctk.CTkFrame(scroll, fg_color="transparent")
        vzhled.pack(pady=(0, 4))
        ctk.CTkLabel(vzhled, text="Vzhled aplikace:",
                     font=self.fonts["body_bold"],
                     text_color=THEME["text"]).pack(pady=(0, 5))
        self.seg_vzhled = ctk.CTkSegmentedButton(
            vzhled, values=["☀️ Světlý", "🌙 Tmavý"],
            command=self.change_appearance_mode_event,
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hi"], corner_radius=R_BTN)
        self.seg_vzhled.set("☀️ Světlý")
        self.seg_vzhled.pack()

        # Formulář – generický loop místo copy-paste
        form = ctk.CTkFrame(scroll, fg_color="transparent")
        form.pack(pady=8, padx=55, fill="x")

        fields = [
            ("Naše IČO (Organizace):", "ico", False),
            ("Přihlašovací e-mail:", "email", False),
            ("Heslo aplikace (E-mail):", "heslo", True),
            ("Groq API Klíč (Umělá inteligence):", "api", True),
        ]
        self._entries = {}
        self._eye_buttons = {}

        for label_text, name, is_secret in fields:
            ctk.CTkLabel(form, text=label_text, font=self.fonts["body_bold"],
                         anchor="w", text_color=THEME["text"]).pack(
                             fill="x", pady=(8, 0))
            if is_secret:
                row = ctk.CTkFrame(form, fg_color="transparent")
                row.pack(fill="x", pady=(0, 12))
                entry = ctk.CTkEntry(row, height=36, show="*",
                                     corner_radius=R_BTN)
                entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
                entry.bind("<KeyRelease>", self.oznacit_zmeny)
                eye = self.btn(
                    row, "👁️",
                    lambda _n=name: self._toggle_visibility(
                        self._entries[_n], self._eye_buttons[_n]),
                    kind="neutral", width=36, height=36)
                eye.pack(side="right")
                self._eye_buttons[name] = eye
            else:
                entry = ctk.CTkEntry(form, height=36, corner_radius=R_BTN)
                entry.pack(fill="x", pady=(0, 12))
                entry.bind("<KeyRelease>", self.oznacit_zmeny)
            self._entries[name] = entry

        # Aliasy pro zpětnou kompatibilitu
        self.entry_ico = self._entries["ico"]
        self.entry_email = self._entries["email"]
        self.entry_heslo = self._entries["heslo"]
        self.entry_api = self._entries["api"]

        # Test připojení
        test_section = ctk.CTkFrame(scroll, fg_color="transparent")
        test_section.pack(pady=(4, 8), padx=55, fill="x")
        ctk.CTkLabel(test_section, text="Ověření připojení:",
                     font=self.fonts["body_bold"],
                     text_color=THEME["text"]).pack(anchor="w", pady=(0, 6))

        # E-mail test
        test_email_row = ctk.CTkFrame(test_section, fg_color="transparent")
        test_email_row.pack(fill="x", pady=3)
        self.btn_test_email = self.btn(
            test_email_row, "🔌 Test E-mailu", self.test_pripojeni_email,
            kind="neutral", height=34, width=150, font=self.fonts["small_bold"])
        self.btn_test_email.pack(side="left")
        self.lbl_test_email = ctk.CTkLabel(
            test_email_row, text="", font=self.fonts["small"],
            text_color=THEME["text_mute"])
        self.lbl_test_email.pack(side="left", padx=12)

        # API test
        test_api_row = ctk.CTkFrame(test_section, fg_color="transparent")
        test_api_row.pack(fill="x", pady=3)
        self.btn_test_api = self.btn(
            test_api_row, "🤖 Test AI (API)", self.test_pripojeni_api,
            kind="neutral", height=34, width=150, font=self.fonts["small_bold"])
        self.btn_test_api.pack(side="left")
        self.lbl_test_api = ctk.CTkLabel(
            test_api_row, text="", font=self.fonts["small"],
            text_color=THEME["text_mute"])
        self.lbl_test_api.pack(side="left", padx=12)

        # Akční tlačítka
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(pady=(12, 24))
        self.btn_save_config = self.btn(
            btn_row, "💾 ULOŽIT NASTAVENÍ", self.potvrdit_ulozeni,
            kind="success", height=42, font=self.fonts["section_btn"])
        self.btn_save_config.grid(row=0, column=0, padx=8)
        self.btn_revert_config = self.btn(
            btn_row, "❌ Zahodit změny", self.nacti_data_nastaveni,
            kind="neutral", height=42, font=self.fonts["small_bold"])
        self.btn_revert_config.grid(row=0, column=1, padx=8)
        self.btn_revert_config.grid_remove()

        # Nebezpečná zóna – vizuálně oddělená
        ctk.CTkFrame(scroll, height=1, fg_color=THEME["card_brd"]).pack(
            fill="x", padx=36, pady=(8, 16))
        danger_card = ctk.CTkFrame(scroll, fg_color=THEME["danger_bg"],
                                   corner_radius=R, border_width=2,
                                   border_color=THEME["danger_brd"])
        danger_card.pack(fill="x", padx=36, pady=(0, 24))
        ctk.CTkLabel(danger_card, text="⚠️ NEBEZPEČNÁ ZÓNA",
                     font=self.fonts["body_bold"],
                     text_color=THEME["danger"]).pack(pady=(16, 4))
        ctk.CTkLabel(danger_card,
                     text="Vymaže všechny nahrané faktury, "
                     "vygenerované ISDOCy a historii.",
                     font=self.fonts["small"],
                     text_color=THEME["text_mute"]).pack(pady=(0, 12))
        self.btn(danger_card, "🗑️ TOVÁRNÍ RESET A SMAZÁNÍ DAT",
                 self.potvrdit_reset_dat, kind="danger", height=40,
                 font=self.fonts["body_bold"]).pack(pady=(0, 16), padx=24)

        return frame

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
        self.log_box.insert("end",
                            f"{cas}  {znaky.get(typ, '•')}  {zprava}\n", tag)
        try:
            self.log_box.tag_config(tag,
                                    foreground=barvy.get(typ, THEME["text_mute"]))
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
            self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.log_otevreny = True
            self.btn_log_toggle.configure(text="▾  Průběh zpracování")

    def obnov_statistiky_ui(self):
        celkem = back_gordick.ziskej_statistiky()
        minuty = celkem * 3
        h, m = minuty // 60, minuty % 60
        self.lbl_stats_time.configure(
            text=f"{h}h {m}m" if h > 0 else f"{m} min")
        self.lbl_stats_count.configure(text=f"{celkem} zprac. dokumentů")

    # =============================================================
    # NAVIGACE – přepínání sekcí
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
        self._set_nav_active(None)
        self.nacti_data_nastaveni()
        self._show_frame(self.frame_nastaveni)

    # =============================================================
    # DIALOGY PRO VÝBĚR SOUBORŮ
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
        self._list_item(self.pdf_scroll, f"🔍 Hledám výraz: '{dotaz}'",
                        "Prohledávám full-textový index...", None)
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
                        self._list_item(
                            self.pdf_scroll, f"📄 {v['pdf']}",
                            f"...{v['utrzek']}...",
                            lambda p=cesta: os.startfile(p))
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
            with open(back_gordick.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            config["moje_ic_organizace"] = self.entry_ico.get().strip()
            config["groq_api_key"] = self.entry_api.get().strip()
            if "email_nastaveni" not in config:
                config["email_nastaveni"] = {}
            config["email_nastaveni"]["email_adresa"] = \
                self.entry_email.get().strip()
            config["email_nastaveni"]["heslo_aplikace"] = \
                self.entry_heslo.get().strip()
            with open(back_gordick.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            back_gordick.MOJE_ICO = config["moje_ic_organizace"]
            self.nacti_data_nastaveni()
            self.lbl_config_status.configure(
                text="✅ Úspěšně uloženo! (Pro AI změny doporučuji restart)",
                text_color=THEME["success"])
        except Exception as e:
            self.lbl_config_status.configure(
                text=f"⚠️ Chyba při ukládání: {e}",
                text_color=THEME["danger"])

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
        ctk.set_appearance_mode("Dark" if "Tmavý" in volba else "Light")

    # =============================================================
    # TEST PŘIPOJENÍ (Nastavení)
    # =============================================================
    def test_pripojeni_email(self):
        self.lbl_test_email.configure(text="⏳ Testuji...",
                                      text_color=THEME["warning"])
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
        self.lbl_test_api.configure(text="⏳ Testuji...",
                                    text_color=THEME["warning"])
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
    # ASYNC WORKERS – vlákna pro AI a e-mail
    # =============================================================

    # --- GPC párování (synchronní – jednoduchá operace) ---
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

    # --- Smlouvy (async přes generický _run_async) ---
    def spustit_cteni_smlouvy(self):
        if not self.cesta_smlouvy_souboru:
            self.lbl_smlouva_cesta.configure(
                text="⚠️ Nejdřív vyber PDF smlouvu!",
                text_color=THEME["danger"])
            return
        self._run_async(
            back_gordick.vytvor_vytah_ze_smlouvy,
            (self.cesta_smlouvy_souboru,),
            on_success=self._smlouva_done,
            on_error=self._smlouva_error,
            disable_btns=[self.btn_smlouva_run],
            progress=self.progress_bar_smlouva,
            progress_pack=dict(before=self.btn_smlouva_run, pady=(0, 18),
                               padx=36, fill="x"))

    def _smlouva_done(self, cesta_txt):
        self.lbl_smlouva_cesta.configure(
            text="✅ Souhrn úspěšně vytvořen!", text_color=THEME["success"])
        self.cesta_smlouvy_souboru = None
        back_gordick.aktualizuj_statistiky(1)
        self.obnov_statistiky_ui()
        self.nacti_historii()
        os.startfile(cesta_txt)

    def _smlouva_error(self, msg):
        self.lbl_smlouva_cesta.configure(text="⚠️ Nelze přečíst",
                                          text_color=THEME["danger"])
        print(msg)

    # --- E-mail stahování (async přes generický _run_async) ---
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
            progress=self.progress_bar,
            progress_pack=dict(before=self.btn_run, pady=(0, 16), padx=40,
                               fill="x"))

    def _email_done(self, pocet):
        obsah = os.listdir(back_gordick.SLOZKA_VSTUP)
        cesty = [os.path.join(back_gordick.SLOZKA_VSTUP, f)
                 for f in obsah if f.lower().endswith('.pdf')]
        self.vybrane_soubory_cesty = cesty
        self.log(f"Staženo {pocet} faktur ze schránky.", "ok")
        self.set_stav("hotovo",
                      f"Staženo {pocet} faktur. Klikni na SPUSTIT AI.")

    def _email_error(self, msg=""):
        if msg:
            self.log(f"Chyba e-mailu: {msg}", "err")
        self.set_stav("chyba", "Chyba při stahování e-mailu!")

    # --- Převod faktur na ISDOC (async – vlastní loop s progress) ---
    def spustit_prevod(self):
        if not self.vybrane_soubory_cesty:
            self.set_stav("chyba",
                          "Nejdřív vyber soubor nebo stáhni faktury z e-mailu.")
            return
        self.log_vycisti()
        self.toggle_log(vynutit_otevrit=True)
        # Determinate progress (má vlastní loop, nepoužívá _run_async)
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.pack(before=self.btn_run, pady=(0, 16), padx=40,
                               fill="x")
        self.progress_bar.set(0)
        self.set_stav("pracuji", "Spouštím AI zpracování...")
        self.log(f"Zahajuji zpracování "
                 f"{len(self.vybrane_soubory_cesty)} souborů.", "work")
        for b in [self.btn_email, self.btn_run, self.btn_browse]:
            b.configure(state="disabled")
        threading.Thread(target=self._prevod_worker, daemon=True).start()

    def _prevod_worker(self):
        total = len(self.vybrane_soubory_cesty)
        ok_count = 0
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
                self.after(0, lambda jm=jmeno:
                           self.log(f"{jm} – ISDOC vytvořen.", "ok"))
            except Exception as e:
                self.after(0, lambda jm=jmeno, err=str(e):
                           self.log(f"{jm} – chyba: {err}", "err"))
        self.after(0, lambda: self._prevod_done(ok_count, total))

    def _prevod_progress(self, idx, total, jmeno):
        self.progress_bar.set(idx / total)
        self.set_stav("pracuji",
                      f"🤖 AI zpracovává {idx + 1}/{total}...")
        self.log(f"Zpracovávám {jmeno} ({idx + 1}/{total})...", "work")

    def _prevod_done(self, ok_count, total):
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
        chyby = total - ok_count
        if chyby == 0:
            self.set_stav("hotovo",
                          f"✅ Hotovo – převedeno všech {ok_count} faktur.")
            self.log(f"Hotovo. Úspěšně převedeno {ok_count} z {total}.", "ok")
        else:
            self.set_stav("chyba",
                          f"Převedeno {ok_count} z {total} – {chyby} selhalo.")
            self.log(f"Dokončeno s chybami: {ok_count} OK, "
                     f"{chyby} selhalo.", "err")


if __name__ == "__main__":
    app = GordicAsistentUI()
    app.mainloop()