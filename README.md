# Gordic Asistent – AI Účetní Automatizace

Inteligentní asistent pro automatizaci zpracování účetních dokladů, párování bankovních výpisů a analýzu smluv, primárně navržený pro obecní úřady, příspěvkové organizace a účetní pracující se systémem **GORDIC** (s možností rozšíření pro systém **POHODA**).

---

## 🎯 Hlavní účel a funkce projektu

Aplikace výrazně šetří čas účetním tím, že eliminuje manuální přepisování faktur do účetního softwaru, usnadňuje párování plateb z banky a poskytuje okamžitý přehled nad dokumenty:

1. **Automatické vytěžování PDF faktur pomocí AI:**
   - Využívá superrychlé LLM modely přes **Groq API** (`llama-3.3-70b-versatile`).
   - Z textu faktury spolehlivě extrahuje: číslo faktury, variabilní symbol, bankovní účet dodavatele, datum vystavení, název a IČO dodavatele, základ daně, DPH a celkovou částku.
   - **Matematická kontrola:** Systém ověřuje, zda základ + DPH = celková částka. Pokud AI udělá chybu v počtech, doklad je označen k prověření.
   - **Predikce rozpočtových paragrafů (pro obce):** Modul analyzuje předmět nákupu a automaticky navrhuje správný kód rozpočtové skladby obce (např. *6171 Místní správa*, *3631 Veřejné osvětlení*, *3722 Odpady*, *2212 Komunikace*, *3113 Školy*, *5512 Hasiči*).

2. **Generování elektronických dokladů ISDOC (v6.0.1):**
   - Vytěžená data transformuje do standardního formátu **ISDOC**, který lze přímo importovat do **Gordicu** (a dalších českých ERP).
   - Generuje též JSON metadata do lokálního indexu pro okamžité vyhledávání a párování s bankou.

3. **Stahování faktur přímo z e-mailu (IMAP):**
   - Automatické připojení na poštovní schránku (např. Gmail přes aplikační heslo).
   - Filtrování zpráv s předmětem „Faktura“ za zvolené časové období (den, týden, měsíc, rok).
   - Prevence duplicitního stahování již zpracovaných faktur.

4. **Banka & Automatické generování Účetní košilky (GPC / ABO):**
   - Načítání bankovních výpisů ve formátu **GPC / ABO** (standard českých bank).
   - Inteligentní párovací algoritmus propojující bankovní pohyby s vytěženými fakturami podle variabilního symbolu, částky a bankovního účtu.
   - **Tisk účetní košilky:** Generuje formátovaný protokol s rekapitulací spárovaných i nespárovaných plateb a s **oficiálními schvalovacími rámečky pro obecní finanční kontrolu** (Příkazce operace / starosta, Správce rozpočtu, Hlavní účetní).

5. **AI Právník (Rychlý výtah ze smluv):**
   - Načtení PDF smlouvy a okamžité vygenerování strukturovaného výtahu: smluvní strany, předmět smlouvy, finanční plnění a datum uzavření.

6. **Lokální fulltextové vyhledávání:**
   - Každé zpracované PDF se ukládá do textového indexu v `.index`.
   - Účetní může bleskově vyhledat jakýkoliv výraz napříč všemi archivovanými fakturami bez externí databáze.

7. **Moderní asynchronní desktopové UI:**
   - Vytvořeno v `customtkinter` (podpora tmavého/světlého režimu).
   - Asynchronní architektura (threading) – operace s AI a e-mailem nezasekávají okno.
   - Vestavěný logovací panel a testovací tlačítka pro ověření spojení s e-mailem a Groq API.

---

## 📂 Struktura projektu po úklidu

Projekt byl zorganizován do přehledné a čisté struktury:

| Složka / Soubor | Popis |
|---|---|
| **[`gordick/`](file:///c:/Users/retar/Documents/02_Programovani/projekty/ucetni_automatizace/gordick)** | **Hlavní aktivní projekt** (nejnovější verze s moderním CustomTkinter UI, threadingem, testy připojení, predikcí rozpočtových paragrafů obce a ISDOC exportem). |
| **[`vzory_a_historie/`](file:///c:/Users/retar/Documents/02_Programovani/projekty/ucetni_automatizace/vzory_a_historie)** | **Bezpečně oddělený archiv vzorů a programů:** původní kód pro export do systému **POHODA** (`ucetnictvi.py`, `gui_profi.py`), vzorové XML pro Pohodu a zkompilovaný `Gordic_Asistent.exe`. |
| **[`README.md`](file:///c:/Users/retar/Documents/02_Programovani/projekty/ucetni_automatizace/README.md)** | Tato dokumentace celého projektu a návod k obsluze. |

---

## 🚀 Jak aplikaci spustit

### Požadavky
- Python 3.10+
- Nainstalované knihovny:
  ```bash
  pip install customtkinter groq pypdf pypdf2 pillow
  ```

### Nastavení konfigurace (`config.json`)
Soubor `config.json` obsahuje základní parametry:
```json
{
    "uzivatel": "Jméno Účetní",
    "system_vystup": "gordic",
    "groq_api_key": "VÁŠ_GROQ_API_KLÍČ",
    "ai_model": "llama-3.3-70b-versatile",
    "email_nastaveni": {
        "imap_server": "imap.gmail.com",
        "email_adresa": "ucetni@obec.cz",
        "heslo_aplikace": "xxxx xxxx xxxx xxxx"
    },
    "moje_ic_organizace": "12345678",
    "zpracovano_faktur_celkem": 0
}
```

### Spuštění
```bash
cd "gordick/python"
python front_gordick.py
```

---

## 🛠️ Vize a doporučený plán dalšího rozvoje

1. **Sjednocení repozitáře a Git:**
   - Inicializovat `git` repozitář.
   - Přesunout unikátní vzory ze složky `gordick/python/z_hotove programy_a_vzory` do nové složky např. `reference/` nebo `legacy_pohoda/`.
   - Přejmenovat `gordick - claude` na hlavní pracovní kořen `src/` a starou složku `gordick` archivovat.

2. **Multi-ERP podpora (Gordic + Pohoda + Abra):**
   - V kódu již existují základy jak pro Gordic (ISDOC), tak pro Pohodu (XML). Vytvořit v nastavení přepínač cílového účetnictví.

3. **OCR pro skenované / obrázkové faktury:**
   - Dnes `PyPDF2` čte pouze textové vrstvy PDF. Pokud účetní dostane naskenovaný papír (bitmapové PDF), text se nenačte. Doporučeno doplnit lokální OCR (např. Tesseract nebo `pytesseract`) nebo multimodální AI (Groq / Llama Vision).

4. **Lepší správa citlivých údajů:**
   - Přesunout API klíče a hesla z otevřeného `config.json` do šifrovaného úložiště (např. Windows Credential Manager / `keyring`) nebo `.env`.

5. **Distribuce:**
   - Sestavit finální `.exe` instalátor pomocí PyInstalleru (`Gordic_Asistent.spec`), aby účetní nemusela mít na počítači instalovaný Python.
