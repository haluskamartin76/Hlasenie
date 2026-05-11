import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Hlásenia Pracovísk", layout="centered")

# --- PRIPOJENIE KU GOOGLE SHEETS ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # Načítanie a oprava kľúča zo Secrets
    creds_info = st.secrets["gcp_service_account"]
    creds_dict = dict(creds_info)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Názov tabuľky - uisti sa, že sa v Google Drive volá presne takto:
    SHEET_NAME = "Hlasenia_Data" 
    sh = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"Chyba pripojenia (skontrolujte Secrets a názov tabuľky): {e}")
    st.stop()

# --- FUNKCIA NA ODOSLANIE MAILU ---
def poslat_email(text_sumaru, prijemca):
    # Sem vlož svoje overené údaje pre Gmail
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "zmenovehlasenie@gmail.com"  # <--- DOPLŇ SVOJ MAIL
    SENDER_PASSWORD = "qvib ewfm liku yfum"  # <--- DOPLŇ SVOJ APP PASSWORD

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denný sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text_sumaru, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.set_debuglevel(0)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

# --- ROZHRANIE APLIKÁCIE ---
st.title("📋 Systém pracovných hlásení")

tab1, tab2 = st.tabs(["✍️ Vytvoriť hlásenie", "🕵️ Rozhranie veliteľa"])

# --- TAB 1: PRACOVISKO ---
with tab1:
    st.subheader("Nové hlásenie zo zmeny")
    with st.form("form_pracovisko", clear_on_submit=True):
        pracovisko = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Linka C", "Sklad", "Expedícia"])
        stav = st.select_slider("Stav prevádzky", options=["OK", "Drobné zdržanie", "Kritický problém"])
        poznamka = st.text_area("Popis situácie / Hlásenie")
        
        if st.form_submit_button("Odovzdať hlásenie"):
            teraz = datetime.now().strftime("%d.%m.%Y %H:%M")
            # Zápis do Google tabuľky (stĺpce: Datum, Pracovisko, Stav, Poznamka, Odoslane)
            sh.append_row([teraz, pracovisko, stav, poznamka, "Nie"])
            st.success("Hlásenie bolo úspešne uložené do databázy.")

# --- TAB 2: VELITEĽ ZMENY ---
with tab2:
    st.subheader("Kontrola a odoslanie nadriadenému")
    vstup_heslo = st.text_input("Zadajte prístupový kód", type="password")
    
    if vstup_heslo == "admin123": # <--- TVOJE HESLO PRE VELITEĽA
        data = sh.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            # Zobraziť len tie, čo ešte neodišli mailom
            neodoslane = df[df['Odoslane'] == 'Nie']
            
            if not neodoslane.empty:
                st.write("Hlásenia čakajúce na odoslanie:")
                st.dataframe(neodoslane)
                
                mail_sefa = st.text_input("Email nadriadeného (príjemca)", "sef@firma.sk")
                
                if st.button("Schváliť a poslať mailom"):
                    with st.spinner("Odosielam e-mail..."):
                        try:
                            # Tvorba textu mailu
                            telo = "Dobrý deň,\n\npripájam sumár hlásení z aktuálnej zmeny:\n\n"
                            for _, r in neodoslane.iterrows():
                                telo += f"• {r['Pracovisko']} [{r['Datum']}]: {r['Stav']}\n  Poznámka: {r['Poznamka']}\n"
                                telo += "-"*20 + "\n"
                            
                            poslat_email(telo, mail_sefa)
                            
                            # Označenie riadkov v Google Sheets ako odoslané
                            # Prechádzame záznamy v tabuľke (začíname od 2. riadku kvôli hlavičke)
                            for i, row in enumerate(data, start=2):
                                if row['Odoslane'] == 'Nie':
                                    sh.update_cell(i, 5, 'Ano')
                            
                            st.success(f"Sumár bol úspešne odoslaný na {mail_sefa}!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Chyba pri odosielaní: {ex}")
            else:
                st.info("Žiadne nové hlásenia na spracovanie.")
        else:
            st.info("V tabuľke sa nenachádzajú žiadne dáta.")
