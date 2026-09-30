import imaplib
import email
import os
import json

# Načtení údajů z config.json
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ Chyba: Soubor config.json nebyl nalezen. Vytvoř ho ve stejné složce.")
    exit()

EMAIL_USER = config["email_nastaveni"]["email_adresa"]
EMAIL_PASS = config["email_nastaveni"]["heslo_aplikace"]
IMAP_SERVER = config["email_nastaveni"]["imap_server"]

def stahni_faktury_z_mailu():
    print(f"🚀 Připojuji se k e-mailu: {EMAIL_USER}...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
    except Exception as e:
        print(f"❌ Připojení selhalo. Zkontroluj heslo v config.json! Chyba: {e}")
        return

    status, data = mail.search(None, '(SUBJECT "Faktura")')
    mail_ids = data[0].split()
    print(f"📩 Nalezeno {len(mail_ids)} mailů se slovem 'Faktura' v předmětu.")

    for m_id in mail_ids:
        status, data = mail.fetch(m_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        for part in msg.walk():
            if part.get_content_maintype() == "multipart" or part.get("Content-Disposition") is None:
                continue
                
            jmeno_souboru = part.get_filename()
            if jmeno_souboru and jmeno_souboru.lower().endswith('.pdf'):
                cesta_ulozeni = os.path.join("faktury_vstup", jmeno_souboru)
                if not os.path.exists(cesta_ulozeni):
                    with open(cesta_ulozeni, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"✅ Staženo: {jmeno_souboru}")
                else:
                    print(f"⏩ Přeskočeno (už existuje): {jmeno_souboru}")
                    
    mail.logout()
    print("✅ Hotovo. Odpojeno od serveru.")

if __name__ == "__main__":
    os.makedirs("faktury_vstup", exist_ok=True)
    stahni_faktury_z_mailu()