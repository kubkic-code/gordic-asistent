import os
import shutil
import sys
import datetime
import imaplib
import email
import json
import unicodedata  # Přidaný import pro čištění diakritiky!
from groq import Groq
import PyPDF2

# --- NAČTENÍ KONFIGURACE (SaaS & Distribuce) ---
DOKUMENTY_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Gordic_Asistent")
CONFIG_FILE = "config.json"

if getattr(sys, 'frozen', False):
    local_cfg = os.path.join(os.path.dirname(sys.executable), CONFIG_FILE)
    doc_cfg = os.path.join(DOKUMENTY_DIR, CONFIG_FILE)
    if os.path.exists(local_cfg) and not os.path.exists(doc_cfg):
        try:
            os.makedirs(DOKUMENTY_DIR, exist_ok=True)
            shutil.copy2(local_cfg, doc_cfg)
        except Exception:
            pass
    if os.path.exists(doc_cfg):
        CONFIG_PATH = doc_cfg
    elif os.path.exists(local_cfg):
        CONFIG_PATH = local_cfg
    else:
        CONFIG_PATH = doc_cfg
else:
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)

# --- NASTAVENÍ SLOŽEK PROFI ---
SLOZKA_VSTUP = os.path.join(DOKUMENTY_DIR, "faktury_vstup")
SLOZKA_VYSTUP = os.path.join(DOKUMENTY_DIR, "isdoc_vystup")
SLOZKA_ARCHIV = os.path.join(DOKUMENTY_DIR, "archiv_pdf")
SLOZKA_INDEX = os.path.join(DOKUMENTY_DIR, ".index")
SLOZKA_KOSILKY = os.path.join(DOKUMENTY_DIR, "archiv_kosilek")
SLOZKA_SMLOUVY = os.path.join(DOKUMENTY_DIR, "archiv_smluv")

for slozka in [SLOZKA_VSTUP, SLOZKA_VYSTUP, SLOZKA_ARCHIV, SLOZKA_INDEX, SLOZKA_KOSILKY, SLOZKA_SMLOUVY]:
    os.makedirs(slozka, exist_ok=True)

# Globální proměnné konfigurace
config = {}
client = None
AI_MODEL = "openai/gpt-oss-120b"
MOJE_ICO = ""
EMAIL_USER = ""
EMAIL_PASS = ""
IMAP_SERVER = "imap.gmail.com"

def detekuj_imap_server(email_adresa):
    """Automaticky určí IMAP server podle domény e-mailu."""
    if not email_adresa or "@" not in email_adresa:
        return "imap.gmail.com"
    domena = email_adresa.split("@")[-1].lower().strip()
    if domena in ["gmail.com", "googlemail.com"]:
        return "imap.gmail.com"
    elif domena in ["seznam.cz", "email.cz", "post.cz"]:
        return "imap.seznam.cz"
    elif domena in ["centrum.cz", "atlas.cz"]:
        return "imap.centrum.cz"
    elif domena in ["outlook.com", "hotmail.com", "office365.com"]:
        return "outlook.office365.com"
    elif domena in ["volny.cz"]:
        return "imap.volny.cz"
    else:
        return f"imap.{domena}"

def reload_config():
    """Znovu načte config.json a aktualizuje API klienta a e-mailové připojení za běhu."""
    global config, client, AI_MODEL, MOJE_ICO, EMAIL_USER, EMAIL_PASS, IMAP_SERVER
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {
            "groq_api_key": "", "ai_model": "openai/gpt-oss-120b",
            "moje_ic_organizace": "", "zpracovano_faktur_celkem": 0,
            "email_nastaveni": {"imap_server": "imap.gmail.com",
                                "email_adresa": "", "heslo_aplikace": ""}
        }

    AI_MODEL = config.get("ai_model", "openai/gpt-oss-120b")
    MOJE_ICO = config.get("moje_ic_organizace", "")
    groq_key = config.get("groq_api_key", "")
    os.environ["GROQ_API_KEY"] = groq_key
    try:
        client = Groq(api_key=groq_key) if groq_key else None
    except Exception:
        client = None

    email_cfg = config.get("email_nastaveni", {})
    EMAIL_USER = email_cfg.get("email_adresa", "")
    EMAIL_PASS = email_cfg.get("heslo_aplikace", "")
    IMAP_SERVER = email_cfg.get("imap_server") or detekuj_imap_server(EMAIL_USER)

reload_config()

# =========================================================
# CHYTRÝ MODUL PRO PARAGRAFY A DIAKRITIKU
# =========================================================
PARAGRAFY = {
    "6171": ("Činnost místní správy", ["kancelář", "toner", "telefon", "papír", "it ", "počítač", "software", "tiskárn", "správa"]),
    "3631": ("Veřejné osvětlení",     ["elektřin", "energie", "osvětlen", "lampa", "lamp", "čez", "eon", "e.on"]),
    "3722": ("Svoz komunálního odpadu", ["odpad", "popelnic", "kontejner", "svoz", "komunál"]),
    "2212": ("Silnice a komunikace",  ["oprav", "asfalt", "cesta", "cesty", "komunikac", "silnic", "zimní údržba", "posyp"]),
    "3113": ("Základní školy",        ["škola", "škol", "učebnic", "sešit", "třída", "žák", "družin"]),
    "5512": ("Požární ochrana",       ["hasič", "požárn", "hasičárn", "sdh", "stříkačk"]),
}

def _bez_diakritiky(s):
    """Sjednotí text na malá písmena bez diakritiky (kvůli OCR nekonzistenci)."""
    rozlozene = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(ch for ch in rozlozene if not unicodedata.combining(ch))

def predikuj_paragraf(text):
    """Z plného textu odhadne nejpravděpodobnější paragraf podle klíčových slov."""
    if not text:
        return ""
    text = _bez_diakritiky(text)
    skore = {}
    for kod, (_nazev, klice) in PARAGRAFY.items():
        zasahy = sum(1 for k in klice if _bez_diakritiky(k) in text)
        if zasahy:
            skore[kod] = zasahy
    if not skore:
        return ""
    return max(skore, key=skore.get)

# =========================================================
# HLAVNÍ FAKTURACE A AI
# =========================================================
def vytahni_text_z_pdf(cesta_k_pdf):
    text = ""
    try:
        with open(cesta_k_pdf, "rb") as soubor:
            ctenar = PyPDF2.PdfReader(soubor)
            for strana in ctenar.pages:
                text += strana.extract_text() + "\n"
                
        jmeno_souboru = os.path.basename(cesta_k_pdf)
        jmeno_bez_pdf = jmeno_souboru.replace(".pdf", ".txt").replace(".PDF", ".txt")
        cesta_index = os.path.join(SLOZKA_INDEX, jmeno_bez_pdf)
        
        with open(cesta_index, "w", encoding="utf-8") as f:
            f.write(text)

        if not text or len(text.strip()) < 15:
            raise Exception(
                "Toto PDF neobsahuje čitelnou textovou vrstvu (jedná se o naskenovaný papír nebo obrázek). "
                "Prozatím prosím použijte elektronické PDF (stažené z e-mailu nebo vystavené z fakturačního systému). "
                "Podpora skenovaných papírových faktur (OCR) je v přípravě."
            )

        return text
    except Exception as e:
        raise Exception(f"Nepodařilo se přečíst PDF: {e}")

def analyzuj_fakturu_mozkem(text_faktury):
    prompt = """
    Jsi špičkový účetní asistent pro obecní úřad. Tvým úkolem je najít v textu faktury tyto konkrétní údaje a vrátit je POUZE jako čistý JSON formát.
    Žádný jiný text okolo, jen JSON struktura.

    Požadovaná pole v JSONu:
    - "cislo_faktury": (String, číslo dokladu)
    - "variabilni_symbol": (String, variabilní symbol pro platbu. Velmi často je shodný s číslem faktury, hledej zkratky jako VS nebo Var. symbol)
    - "cislo_uctu": (String, číslo bankovního účtu dodavatele včetně kódu banky, např. 12345/0100)
    - "datum_vystaveni": (String, formát RRRR-MM-DD)
    - "dodavatel_nazev": (String, název firmy)
    - "dodavatel_ico": (String, jen čísla)
    - "castka_zaklad": (Number, částka bez DPH)
    - "castka_dph": (Number, částka DPH)
    - "castka_celkem": (Number, celková částka)
    - "odberatel_ico": (String, IČO příjemce)
    - "paragraf": (String, čtyřmístný kód rozpočtové skladby podle předmětu nákupu. Použij tento tahák:
        3113 = Základní školy (sešity, učebnice, vybavení do tříd)
        3631 = Veřejné osvětlení (elektřina pro lampy, opravy světel)
        3722 = Svoz komunálního odpadu (popelnice, kontejnery)
        2212 = Silnice a komunikace (opravy cest, asfaltování, zimní údržba)
        6171 = Činnost místní správy (kancelářské potřeby pro úřad, telefony, IT služby, tonery)
        5512 = Požární ochrana (vybavení pro hasiče, opravy hasičárny)
        Pokud si nejsi jistý, nebo faktura nespadá ani do jedné kategorie, vrať POUZE prázdný string "".)

    Text faktury:
    """ + text_faktury

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=AI_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    odpoved = chat_completion.choices[0].message.content
    try:
        cista_odpoved = odpoved.replace("```json", "").replace("```", "").strip()
        data = json.loads(cista_odpoved)
        
        zaklad = float(data.get("castka_zaklad", 0))
        dph = float(data.get("castka_dph", 0))
        celkem = float(data.get("castka_celkem", 0))
        rozdil = abs((zaklad + dph) - celkem)
        
        if rozdil > 1.0:
            raise Exception(f"Matematická chyba AI! Základ {zaklad} + DPH {dph} se nerovná Celkem {celkem}.")
            
        return data
        
    except json.JSONDecodeError:
        raise Exception("AI nevrátila správný formát dat (JSON).")

def vygeneruj_isdoc(data):
    cislo_faktury = data.get('cislo_faktury', 'NeznameCislo')
    nazev_souboru = f"FA_{cislo_faktury}.isdoc"
    cesta_k_souboru = os.path.join(SLOZKA_VYSTUP, nazev_souboru)

    cesta_json = os.path.join(SLOZKA_INDEX, f"FA_{cislo_faktury}.json")
    try:
        with open(cesta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Nepodařilo se uložit JSON pro banku: {e}")

    vs = data.get('variabilni_symbol', '')
    ucet = data.get('cislo_uctu', '')
    paragraf = data.get('paragraf', '')
    poznamka = f"Automaticky nacteny paragraf AI: {paragraf}" if paragraf else "Paragraf nedoplnen"

    isdoc_obsah = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="http://isdoc.cz/namespace/2013/10/Document" version="6.0.1">
    <DocumentType>1</DocumentType>
    <ID>{cislo_faktury}</ID>
    <UUID>00000000-0000-0000-0000-000000000000</UUID>
    <IssueDate>{data.get('datum_vystaveni', '2026-01-01')}</IssueDate>
    <TaxPointDate>{data.get('datum_vystaveni', '2026-01-01')}</TaxPointDate>
    <VATApplicable>true</VATApplicable>
    <Note>{poznamka}</Note>
    <CurrRate>1</CurrRate>
    <AccountingSupplierParty>
        <Party>
            <PartyIdentification><ID>{data.get('dodavatel_ico', '')}</ID></PartyIdentification>
            <PartyName><Name>{data.get('dodavatel_nazev', '')}</Name></PartyName>
        </Party>
    </AccountingSupplierParty>
    <AccountingCustomerParty>
        <Party>
            <PartyIdentification><ID>{MOJE_ICO}</ID></PartyIdentification>
        </Party>
    </AccountingCustomerParty>
    <PaymentMeans>
        <Payment>
            <Details>
                <PaymentMeansCode>42</PaymentMeansCode>
                <VariableSymbol>{vs}</VariableSymbol>
                <PayeeFinancialAccount>
                    <ID>{ucet}</ID>
                </PayeeFinancialAccount>
            </Details>
        </Payment>
    </PaymentMeans>
    <LegalMonetaryTotal>
        <TaxExclusiveAmount>{data.get('castka_zaklad', 0)}</TaxExclusiveAmount>
        <TaxInclusiveAmount>{data.get('castka_celkem', 0)}</TaxInclusiveAmount>
        <PayableAmount>{data.get('castka_celkem', 0)}</PayableAmount>
    </LegalMonetaryTotal>
</Invoice>
"""
    with open(cesta_k_souboru, "w", encoding="utf-8") as f:
        f.write(isdoc_obsah.strip())
    return nazev_souboru

def stahni_faktury_z_mailu(obdobi, stahovat_archivovane):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    hledaci_prikaz = '(SUBJECT "Faktura")'
    dnes = datetime.date.today()

    if obdobi == "Den":
        datum_od = (dnes - datetime.timedelta(days=1)).strftime("%d-%b-%Y")
        hledaci_prikaz = f'(SUBJECT "Faktura" SINCE "{datum_od}")'
    elif obdobi == "Týden":
        datum_od = (dnes - datetime.timedelta(days=7)).strftime("%d-%b-%Y")
        hledaci_prikaz = f'(SUBJECT "Faktura" SINCE "{datum_od}")'
    elif obdobi == "Měsíc":
        datum_od = (dnes - datetime.timedelta(days=30)).strftime("%d-%b-%Y")
        hledaci_prikaz = f'(SUBJECT "Faktura" SINCE "{datum_od}")'
    elif obdobi == "Rok":
        datum_od = (dnes - datetime.timedelta(days=365)).strftime("%d-%b-%Y")
        hledaci_prikaz = f'(SUBJECT "Faktura" SINCE "{datum_od}")'

    status, data = mail.search(None, hledaci_prikaz)
    if not data[0]:
        mail.logout()
        return 0
        
    mail_ids = data[0].split()
    stazeno_pocet = 0

    for m_id in mail_ids:
        status, data = mail.fetch(m_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        for part in msg.walk():
            if part.get_content_maintype() == "multipart" or part.get("Content-Disposition") is None:
                continue
                
            jmeno_souboru = part.get_filename()
            if jmeno_souboru and jmeno_souboru.lower().endswith('.pdf'):
                cesta_archiv = os.path.join(SLOZKA_ARCHIV, jmeno_souboru)
                cesta_vstup = os.path.join(SLOZKA_VSTUP, jmeno_souboru)
                
                if os.path.exists(cesta_archiv) and not stahovat_archivovane:
                    continue
                
                with open(cesta_vstup, "wb") as f:
                    f.write(part.get_payload(decode=True))
                stazeno_pocet += 1

    mail.logout()
    return stazeno_pocet

def vyhledej_ve_fakturach(hledany_vyraz):
    vysledky = []
    if not os.path.exists(SLOZKA_INDEX) or not hledany_vyraz.strip():
        return vysledky
        
    hledany_vyraz = hledany_vyraz.lower()

    for txt_soubor in os.listdir(SLOZKA_INDEX):
        if not txt_soubor.endswith(".txt"):
            continue
        cesta_k_textu = os.path.join(SLOZKA_INDEX, txt_soubor)
        try:
            with open(cesta_k_textu, "r", encoding="utf-8") as f:
                cely_text = f.read()
            cely_text_lower = cely_text.lower()
            if hledany_vyraz in cely_text_lower:
                index_nalez = cely_text_lower.find(hledany_vyraz)
                zacatek = max(0, index_nalez - 25)
                konec = min(len(cely_text), index_nalez + len(hledany_vyraz) + 25)
                utrzek = "..." + cely_text[zacatek:konec].replace("\n", " ") + "..."
                jmeno_puvodniho_pdf = txt_soubor.replace(".txt", ".pdf")
                vysledky.append({"pdf": jmeno_puvodniho_pdf, "utrzek": utrzek})
        except Exception as e:
            print(f"Chyba při prohledávání: {e}")
    return vysledky

def ziskej_statistiky():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("zpracovano_faktur_celkem", 0)
    except:
        return 0

def aktualizuj_statistiky(pocet_novych):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["zpracovano_faktur_celkem"] = data.get("zpracovano_faktur_celkem", 0) + pocet_novych
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return data["zpracovano_faktur_celkem"]
    except Exception as e:
        return 0
    
# =========================================================
# DATOVÁ VRSTVA: BANKA (PÁROVÁNÍ V BACKENDU)
# =========================================================
def _jen_cislice(s):
    return "".join(ch for ch in str(s) if ch.isdigit())

def norm_vs(vs):
    return _jen_cislice(vs).lstrip("0")

def norm_ucet(ucet):
    if not ucet: return ""
    hlavni = str(ucet).split("/")[0]
    return _jen_cislice(hlavni).lstrip("0")

def parsuj_gpc(cesta_gpc):
    platby = []
    try:
        with open(cesta_gpc, "r", encoding="windows-1250") as f: lines = f.readlines()
    except Exception:
        with open(cesta_gpc, "r", encoding="utf-8", errors="ignore") as f: lines = f.readlines()

    for line in lines:
        if not line.startswith("075"): continue
        try:
            platby.append({
                "vs": line[61:71].strip(),
                "castka": int(line[48:60]) / 100.0,
                "ucet": line[19:35].strip()
            })
        except Exception as e:
            print(f"Chyba čtení GPC řádku: {e}")
    return platby

def sparuj_platby(platby, faktury):
    pouzite = set()
    auto, rucni = [], []

    for platba in platby:
        nejlepsi, nejlepsi_skore = None, -1
        for i, fa in enumerate(faktury):
            if i in pouzite: continue
            
            vs_p = norm_vs(platba.get("vs"))
            vs_f = norm_vs(fa.get("variabilni_symbol"))
            vs_shoda = bool(vs_p) and vs_p == vs_f
            
            castka_shoda = abs(float(platba.get("castka", 0)) - float(fa.get("castka_celkem", 0))) <= 1.0
            
            ucet_p = norm_ucet(platba.get("ucet"))
            ucet_f = norm_ucet(fa.get("cislo_uctu"))
            ucet_shoda = bool(ucet_p) and bool(ucet_f) and (ucet_p == ucet_f or ucet_p.endswith(ucet_f) or ucet_f.endswith(ucet_p))

            skore = (3 if vs_shoda else 0) + (3 if castka_shoda else 0) + (2 if ucet_shoda else 0)
            
            if vs_shoda and castka_shoda and skore > nejlepsi_skore:
                nejlepsi = (i, fa)
                nejlepsi_skore = skore
                
        if nejlepsi:
            i, fa = nejlepsi
            pouzite.add(i)
            auto.append({"platba": platba, "faktura": fa})
        else:
            rucni.append(platba)

    return auto, rucni

def zpracuj_gpc_a_vytvor_kosilku(cesta_gpc):
    faktury = []
    if os.path.exists(SLOZKA_INDEX):
        for f in os.listdir(SLOZKA_INDEX):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(SLOZKA_INDEX, f), 'r', encoding='utf-8') as jf:
                        faktury.append(json.load(jf))
                except: pass

    platby = parsuj_gpc(cesta_gpc)
    auto_sparovane, nesparovane_platby = sparuj_platby(platby, faktury)

    sparovano_format = []
    for a in auto_sparovane:
        sparovano_format.append({
            "vs": a["platba"]["vs"],
            "castka": a["platba"]["castka"],
            "dodavatel": a["faktura"].get("dodavatel_nazev", "Neznámý"),
            "faktura": a["faktura"].get("cislo_faktury", "N/A")
        })

    return vytvor_kosilku_soubor(sparovano_format, nesparovane_platby)

def vytvor_kosilku_soubor(sparovano, nesparovano):
    dnesni_datum = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    jmeno_kosilky = f"KOSILKA_BANKA_{dnesni_datum}.txt"
    cesta_k_souboru = os.path.join(SLOZKA_KOSILKY, jmeno_kosilky)

    obsah = []
    obsah.append("="*70)
    obsah.append("          🏛️  ÚČETNÍ KOŠILKA - PÁROVÁNÍ BANKOVNÍHO VÝPISU ")
    obsah.append("="*70)
    obsah.append(f" Vygenerováno: {datetime.datetime.now().strftime('%d.%m.%Y v %H:%M')}\n")
    
    obsah.append(" ✅ SPÁROVÁNO S FAKTURAMI (Vše sedí):")
    obsah.append("-" * 70)
    celkem_sparovano_kc = 0
    if not sparovano:
        obsah.append("  Žádné platby se nepodařilo spárovat.")
    else:
        for p in sparovano:
            obsah.append(f"  Faktura: {p['faktura']:<12} | VS: {p['vs']:<10} | Firma: {p['dodavatel'][:15]:<15}... | {p['castka']:>10,.2f} Kč")
            celkem_sparovano_kc += p['castka']
            
    obsah.append(f"\n ⚠️ NESPÁROVÁNO (Nutná ruční kontrola):")
    obsah.append("-" * 70)
    celkem_nesparovano_kc = 0
    if not nesparovano:
        obsah.append("  Všechny platby z výpisu mají svou fakturu!")
    else:
        for p in nesparovano:
            obsah.append(f"  VS z banky: {p['vs']:<10} | Částka: {p['castka']:>10,.2f} Kč (Nenalezeno v systému)")
            celkem_nesparovano_kc += p['castka']
            
    obsah.append("\n" + "="*70)
    obsah.append(f"  CELKEM SPÁROVÁNO:   {celkem_sparovano_kc:>15,.2f} Kč")
    obsah.append(f"  CELKEM NESPÁROVÁNO: {celkem_nesparovano_kc:>15,.2f} Kč")
    obsah.append("="*70 + "\n\n")

    obsah.append(" ✍️  FINANČNÍ KONTROLA A SCHVÁLENÍ OPERACE:")
    obsah.append("-" * 70 + "\n")
    obsah.append("  A) Operaci připravil (Hlavní účetní):")
    obsah.append("     Datum: ....................      Podpis: .........................\n")
    obsah.append("  B) Příkazce operací (Starosta obce):")
    obsah.append("     Prohlašuji, že operace je prověřená a schvaluji její proplacení.")
    obsah.append("     Datum: ....................      Podpis: .........................\n")
    obsah.append("  C) Správce rozpočtu:")
    obsah.append("     Prohlašuji, že operace je v souladu se schváleným rozpočtem obce.")
    obsah.append("     Datum: ....................      Podpis: .........................\n")
    obsah.append("-" * 70)

    with open(cesta_k_souboru, "w", encoding="utf-8") as f:
        f.write("\n".join(obsah))
        
    return cesta_k_souboru

# =========================================================
# FÁZE 3: MODUL SMLOUVY (AI PRÁVNÍK)
# =========================================================
def analyzuj_smlouvu_mozkem(text_smlouvy):
    prompt = """
    Jsi špičkový právní asistent pro obecní úřad. Tvým úkolem je najít v textu smlouvy klíčové údaje a vrátit je POUZE jako čistý JSON formát.
    Žádný jiný text okolo, jen JSON struktura.

    Požadovaná pole:
    - "smluvni_strany": (String, Kdo s kým smlouvu uzavírá. Vypiš názvy firem/jména a případně IČO)
    - "predmet_smlouvy": (String, O co přesně ve smlouvě jde? Vypiš stručně a jasně, max 2-3 věty)
    - "datum_uzavreni": (String, Datum podpisu nebo uzavření smlouvy)
    - "castka": (String, Pokud je ve smlouvě uvedena nějaká celková finanční částka, vypiš ji. Pokud ne, napiš 'Není uvedena')

    Text smlouvy:
    """ + text_smlouvy

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=AI_MODEL,
            temperature=0.1
        )
        odpoved = chat_completion.choices[0].message.content
        cista_odpoved = odpoved.replace("```json", "").replace("```", "").strip()
        return json.loads(cista_odpoved)
    except Exception as e:
        raise Exception(f"AI nedokázala smlouvu zpracovat: {e}")

def vytvor_vytah_ze_smlouvy(cesta_k_pdf):
    jmeno_souboru = os.path.basename(cesta_k_pdf)
    text_smlouvy = vytahni_text_z_pdf(cesta_k_pdf)
    data = analyzuj_smlouvu_mozkem(text_smlouvy)
    
    jmeno_bez_pdf = jmeno_souboru.replace('.pdf', '').replace('.PDF', '')
    cesta_txt = os.path.join(SLOZKA_SMLOUVY, f"SOUHRN_{jmeno_bez_pdf}.txt")

    obsah = []
    obsah.append("="*60)
    obsah.append("              📜 AI SOUHRN SMLOUVY ")
    obsah.append("="*60)
    obsah.append(f" Zpracovaný dokument: {jmeno_souboru}\n")
    obsah.append(" 🤝 SMLUVNÍ STRANY:\n" + "-" * 60)
    obsah.append(f" {data.get('smluvni_strany', 'Nenalezeno')}\n")
    obsah.append(" 📝 PŘEDMĚT SMLOUVY:\n" + "-" * 60)
    obsah.append(f" {data.get('predmet_smlouvy', 'Nenalezeno')}\n")
    obsah.append(" 💰 FINANČNÍ ČÁSTKA:\n" + "-" * 60)
    obsah.append(f" {data.get('castka', 'Není uvedena')}\n")
    obsah.append(" 📅 DATUM UZAVŘENÍ:\n" + "-" * 60)
    obsah.append(f" {data.get('datum_uzavreni', 'Nenalezeno')}\n")
    obsah.append("="*60)

    with open(cesta_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(obsah))
        
    shutil.copy(cesta_k_pdf, os.path.join(SLOZKA_SMLOUVY, jmeno_souboru))
    return cesta_txt

# =========================================================
# TESTOVACÍ FUNKCE PRO UI NASTAVENÍ
# =========================================================
def test_email_connection(email_addr=None, password=None, server=None):
    """Otestuje IMAP připojení. Vrací (bool, zpráva)."""
    addr = email_addr or EMAIL_USER
    pwd = password or EMAIL_PASS
    srv = server or (detekuj_imap_server(addr) if addr else IMAP_SERVER)
    try:
        mail = imaplib.IMAP4_SSL(srv)
        mail.login(addr, pwd)
        mail.logout()
        return True, f"Připojení k {addr} ({srv}) úspěšné!"
    except Exception as e:
        return False, f"Selhalo ({srv}): {e}"

def test_api_connection(api_key=None):
    """Otestuje Groq API připojení. Vrací (bool, zpráva)."""
    try:
        test_client = Groq(api_key=api_key) if api_key else client
        resp = test_client.chat.completions.create(
            messages=[{"role": "user", "content": "Řekni jen: OK"}],
            model=AI_MODEL, max_tokens=3, temperature=0
        )
        return True, f"AI model {AI_MODEL} odpovídá!"
    except Exception as e:
        return False, f"Selhalo: {e}"