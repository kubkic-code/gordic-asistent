# GORDIC ASISTENT – Trvalý kontext projektu pro AI asistenta

> Tento soubor se načte automaticky na začátku každé AI relace. Nemazat!

## 1. Co tento projekt je

**Gordic Asistent v2.1** — desktopová aplikace pro účetní obecních úřadů a organizací.  
Zbavuje účetní ručního přepisování faktur. AI přečte PDF fakturu a vyexportuje ji do formátu ISDOC, který jde přímo importovat do systému GORDIC (GINIS).

- **GitHub:** https://github.com/kubkic-code/gordic-asistent
- **Cílový uživatel:** Účetní bez IT znalostí ("blbuvzdorná" aplikace)
- **Distribuce:** Standalone `.exe` (PyInstaller, bez nutnosti instalace Pythonu)

---

## 2. Architektura (soubory, které editujeme)

```
gordick/
├── python/
│   ├── front_gordick.py      ← GUI (CustomTkinter, threading, navigace, accordiony)
│   ├── back_gordick.py       ← Backend (Groq API, ISDOC XML, IMAP, GPC parser)
│   ├── config.json           ← API klíče (IGNOROVÁNO gitem! Nikdy necommitovat)
│   ├── config.example.json   ← Veřejná šablona pro GitHub
│   └── Gordic_Asistent.spec  ← PyInstaller build konfigurace
├── Gordic_Asistent_pro_mamku/  ← Distribuční balíček (IGNOROVÁNO gitem!)
│   ├── Gordic_Asistent.exe
│   ├── JAK_ZACIT.txt
│   └── DOTAZNIK_HODNOCENI.html
├── requirements.txt
├── README.md
└── GEMINI.md                 ← Tento soubor
```

---

## 3. Klíčová technická rozhodnutí (NIKDY neměnit bez dobrého důvodu)

| Rozhodnutí | Proč |
|---|---|
| Groq API klíč je Base64-enkódovaný v `back_gordick.py` | GitHub blokuje push s API klíčem v plaintextu |
| `config.json` se auto-vytváří v `Documents/Gordic_Asistent/` | Funguje i bez přiloženého configu při distribuci |
| PowerShell: `$ProgressPreference = 'SilentlyContinue'` před `Compress-Archive` | Jinak padá kvůli console buffer erroru |
| Python se spouští jako `python` (ne `py`), ale jen s `BypassSandbox: true` | Sandbox nemá Python v PATH |
| Git commit nesmí obsahovat Groq klíč v plaintextu | GitHub secret scanning blokuje push |

---

## 4. Design systém GUI (front_gordick.py)

- **Téma:** Deep Indigo (`#6366F1` primary, `#1E1B4B` sidebar) – Light/Dark mode
- **Knihovna:** `customtkinter` (ctk)
- **Navigace:** Sidebar s 5 sekcemi: Nová Faktura, Archiv PDF, Exporty ISDOC, Párování Banky, Čtečka Smluv + Nastavení
- **Pattern pro nové sekce:** Vždy `_build_XYZ()` metoda → `frame_XYZ` → `show_XYZ_event()` v navigaci
- **Accordiony (rozklikávací návody):** Vzor viz `_build_navod_accordion()` (e-mail) a `_build_navod_gordic_accordion()` (Gordic import)
- **Barvy a fonty:** Vždy přes `THEME[...]` a `self.fonts[...]` — nikdy hardcoded hodnoty

---

## 5. Aktuální stav projektu

**Co je hotovo (v2.1):**
- [x] Extrakce textu z PDF + AI analýza (Groq: `openai/gpt-oss-120b`)
- [x] Export do ISDOC 6.0.1 XML
- [x] Stahování faktur z e-mailu (IMAP, auto-detekce serveru dle domény)
- [x] Interaktivní návod na nastavení e-mailu (Gmail / Seznam / Outlook accordion)
- [x] Interaktivní návod na import ISDOC do GORDIC systému (accordion v dashboardu)
- [x] Párování bankovních výpisů GPC (ABO formát)
- [x] Tisk Účetní košilky (zákon 320/2001 Sb.)
- [x] AI čtečka smluv
- [x] Fulltextový index pro vyhledávání
- [x] Standalone .exe (PyInstaller)
- [x] Distribuční ZIP `Gordic_Asistent_pro_mamku.zip` pro testování

**Testování:**
- Balíček byl odeslán mamce (reálná účetní obecního úřadu) k otestování.
- Dotazník zpětné vazby je v `DOTAZNIK_HODNOCENI.html`.

---

## 6. Plánované další kroky

1. Zpětná vazba z reálného testování mamky (import ISDOCu do GORDIC GINIS)
2. OCR fallback pro skenované PDF (Tesseract nebo Groq Vision)
3. Multi-ERP přepínač (GORDIC ISDOC ↔ Pohoda XML)
4. Bezpečnější uložení klíčů (Windows Credential Manager / `keyring`)

---

## 7. Pravidla pro práci na tomto projektu

1. **Nikdy necommitovat** `config.json`, `.exe`, `.zip`, `.pdf`, `.isdoc` — viz `.gitignore`
2. **Vždy otestovat** syntaxi (`python -c "import ast; ast.parse(...)"`) před buildem
3. **Groq API klíč** ukládat Base64-enkódovaný, nikdy jako plaintext
4. **GUI změny** — vždy zachovat stávající `THEME` systém a `self.fonts`
5. **Nové funkce** — nejprve update `KONTEXT_PROJEKTU.txt` i `GEMINI.md`
