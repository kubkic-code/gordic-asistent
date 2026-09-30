# Gordic Asistent – AI Účetní Automatizace (v2.1)

Inteligentní desktopová aplikace pro automatizaci zpracování účetních dokladů, párování bankovních výpisů a analýzu smluv. Primárně navrženo pro obecní úřady, příspěvkové organizace a účetní pracující se systémem **GORDIC** (s architekturou připravenou pro rozšíření o systém **POHODA**).

---

## 🎯 Hlavní funkce aplikace

Aplikace výrazně šetří čas účetním tím, že eliminuje manuální přepisování faktur do účetního softwaru, usnadňuje párování plateb z banky a poskytuje okamžitý přehled nad dokumenty:

1. **Automatické vytěžování PDF faktur pomocí AI:**
   - Využívá rychlé LLM modely přes **Groq API** (`openai/gpt-oss-120b` s garantovaným strukturovaným JSON výstupem).
   - Z textu faktury spolehlivě extrahuje: číslo faktury, variabilní symbol, bankovní účet dodavatele, datum vystavení, název a IČO dodavatele, základ daně, DPH a celkovou částku.
   - **Matematická kontrola:** Systém ověřuje, zda `Základ + DPH == Celkem`. Pokud AI udělá početní chybu, doklad je označen k prověření.
   - **Predikce rozpočtových paragrafů (pro obce):** Modul analyzuje předmět nákupu a automaticky navrhuje správný kód rozpočtové skladby obce (např. *6171 Místní správa*, *3631 Veřejné osvětlení*, *3722 Odpady*, *2212 Komunikace*, *3113 Školy*, *5512 Hasiči*).

2. **Generování elektronických dokladů ISDOC (v6.0.1):**
   - Vytěžená data transformuje do standardního formátu **ISDOC**, který lze přímo importovat do systému **Gordic** (a dalších českých ERP).
   - Generuje též JSON metadata do lokálního indexu pro okamžité vyhledávání a párování s bankou.

3. **Stahování faktur z e-mailu (IMAP) s automatickou detekcí:**
   - **Chytrá detekce serveru:** Automaticky rozpozná a nakonfiguruje IMAP server podle domény (`@gmail.com` -> `imap.gmail.com`, `@seznam.cz` -> `imap.seznam.cz`, `@outlook.com` -> `outlook.office365.com` atd.).
   - Filtrování zpráv s předmětem „Faktura“ za zvolené časové období (den, týden, měsíc, rok, celá doba).
   - Prevence duplicitního stahování již zpracovaných faktur.

4. **Interaktivní průvodce pro účetní (Návod v aplikaci):**
   - Integrovaný rozklikávací návod krok za krokem v sekci **⚙️ Nastavení**.
   - Vysvětlení běžnou lidskou řečí, jak získat heslo aplikace pro **Gmail**, **Seznam.cz** i **Outlook**.
   - **Tlačítka na 1 kliknutí:** Otevření oficiální stránky Google pro vygenerování hesla aplikace a kontrolu IMAP přímo ve webovém prohlížeči.

5. **Banka & Automatické generování Účetní košilky (GPC / ABO):**
   - Načítání bankovních výpisů ve formátu **GPC / ABO** (standard českých bank).
   - Inteligentní párovací algoritmus propojující bankovní pohyby s vytěženými fakturami podle variabilního symbolu, částky a bankovního účtu.
   - **Tisk účetní košilky:** Generuje formátovaný protokol s rekapitulací spárovaných i nespárovaných plateb a s **oficiálními schvalovacími rámečky pro obecní finanční kontrolu** (Příkazce operace / starosta, Správce rozpočtu, Hlavní účetní dle zák. 320/2001 Sb.).

6. **AI Právník (Rychlý výtah ze smluv):**
   - Načtení PDF smlouvy a okamžité vygenerování strukturovaného výtahu: smluvní strany, předmět smlouvy, finanční plnění a datum uzavření.

7. **Lokální fulltextové vyhledávání:**
   - Každé zpracované PDF se ukládá do textového indexu v `.index`.
   - Bleskové vyhledání jakéhokoliv výrazu napříč všemi archivovanými fakturami bez nutnosti externí databáze.

8. **Moderní asynchronní desktopové UI (v2.1):**
   - Vytvořeno v `customtkinter` (podpora tmavého/světlého režimu).
   - Notion/Linear indigo sidebar, stavové karty, přehledný archiv s akcemi *Otevřít* a *Kopírovat*.
   - Asynchronní threading – AI ani e-mail nezasekávají grafické rozhraní.
   - Dynamické znovunačtení konfigurace za běhu (`reload_config`) při uložení v nastavení.

---

## 📂 Struktura projektu

```
.
├── python/
│   ├── front_gordick.py        # Hlavní GUI aplikace (CustomTkinter, asynchronní threading)
│   ├── back_gordick.py         # Backend logika (Groq AI, ISDOC XML, GPC parser, predikce paragrafů)
│   ├── config.json             # Lokální konfigurace s klíči (chráněno v .gitignore)
│   ├── config.example.json     # Veřejná šablona konfigurace
│   ├── Gordic_Asistent.spec    # PyInstaller specifikace pro sestavení .exe
│   ├── ikona.ico               # Aplikační ikona
│   ├── faktury_vstup/          # Vstupní složka pro PDF faktury
│   ├── archiv_pdf/             # Archiv zpracovaných faktur (včetně vzorové faktury)
│   └── isdoc_vystup/           # Výstupní složka vygenerovaných ISDOC souborů
├── requirements.txt            # Python závislosti
├── .gitignore                  # Ochrana citlivých dat, buildů a PDF
├── KONTEXT_PROJEKTU.txt        # Kontextový soubor pro AI asistenty
└── README.md                   # Tato dokumentace
```

---

## 🚀 Jak aplikaci spustit

### Možnost A: Samostatný `.exe` balíček (pro uživatele bez Pythonu)
Pro běžné uživatele a účetní je k dispozici samostatně spustitelný balíček:
1. Zkompilovaný soubor: `python/dist/Gordic_Asistent.exe` (nebo distribuční balíček `Gordic_Asistent_pro_mamku.zip`).
2. Stačí rozbalit a dvakrát kliknout na `Gordic_Asistent.exe`. Není potřeba instalovat Python ani knihovny.

### Možnost B: Spuštění ze zdrojového kódu (Python)
1. **Požadavky:** Python 3.10+
2. **Instalace závislostí:**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller   # volitelné, pouze pro sestavení .exe
   ```
3. **Konfigurace:**
   Zkopírujte `python/config.example.json` do `python/config.json` a zadejte svůj Groq API klíč.
4. **Spuštění:**
   ```bash
   cd python
   python front_gordick.py
   ```

---

## ⚙️ Ukázka konfigurace (`config.json`)

```json
{
    "uzivatel": "Ucetni",
    "system_vystup": "gordic",
    "groq_api_key": "gsk_...",
    "ai_model": "openai/gpt-oss-120b",
    "email_nastaveni": {
        "imap_server": "imap.gmail.com",
        "email_adresa": "ucetni@obec.cz",
        "heslo_aplikace": "xxxx xxxx xxxx xxxx"
    },
    "moje_ic_organizace": "12345678",
    "zpracovano_faktur_celkem": 0
}
```

---

## 🛠️ Vize a další doporučený rozvoj

1. **Feedback z reálného testování:**
   - Ověření práce s fakturami různých dodavatelů a otestování importu vytvořených ISDOC souborů přímo do ostrého Gordicu.
2. **OCR pro skenované / bitmapové faktury:**
   - Současný modul čte textovou vrstvu PDF. Pro skenované papírové faktury doplnit fallback přes lokální OCR (Tesseract / pytesseract) nebo multimodální AI vizi.
3. **Multi-ERP přepínač (Gordic vs. Pohoda):**
   - Vytvořit v nastavení přepínač výstupního formátu dokladů (ISDOC pro Gordic vs. Pohoda XML).
4. **Bezpečnost klíčů:**
   - Možnost ukládat API klíč a heslo schránky do šifrovaného systémového trezoru (Windows Credential Manager / `keyring`).
