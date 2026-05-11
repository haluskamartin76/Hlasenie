import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- PRIPOJENIE KU GOOGLE SHEETS ---
scope = ["https://googleapis.com", "https://googleapis.com"]
# Načítanie údajov zo Streamlit Secrets
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Názov tvojej tabuľky (musí byť presne taký istý!)
SHEET_NAME = "Hlasenia_Data" 
sh = client.open(SHEET_NAME).sheet1

# --- FUNKCIA NA ODOSLANIE MAILU ---
def poslat_email(text_sumaru, prijemca):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "zmenovehlasenie@gmail.com"  # Mail, z ktorého sa odosiela
    SENDER_PASSWORD = "qvib ewfm liku yfum"  # Heslo aplikácie (nie bežné heslo)

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denné hlásenia - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text_sumaru, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

# --- APP ROZHRANIE ---
st.title("Systém hlásení s Google Sheets")

tab1, tab2 = st.tabs(["📝 Pracovisko", "👑 Vedúci zmeny"])

with tab1:
    st.header("Nové hlásenie")
    with st.form("form_pracovisko", clear_on_submit=True):
        pracovisko = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        poznamka = st.text_area("Hlásenie")
        
        if st.form_submit_button("Uložiť hlásenie"):
            teraz = datetime.now().strftime("%d.%m.%Y %H:%M")
            sh.append_row([teraz, pracovisko, stav, poznamka, "Nie"])
            st.success("Zapísané do Google tabuľky.")

with tab2:
    st.header("Administrácia")
    heslo = st.text_input("Vstupné heslo", type="password")
    
    if heslo == "admin123":
        data = sh.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Filtrujeme len tie, ktoré majú v stĺpci "Odoslane" hodnotu "Nie"
            neodoslane = df[df['Odoslane'] == 'Nie']
            
            if not neodoslane.empty:
                st.write("Čakajúce hlásenia:")
                st.table(neodoslane)
                
                email_nadriadeneho = st.text_input("Email nadriadeného", "boss@firma.sk")
                if st.button("Odoslať sumár"):
                    sumar_text = "Prehľad hlásení:\n\n"
                    for _, row in neodoslane.iterrows():
                        sumar_text += f"{row['Pracovisko']} ({row['Datum']}): {row['Stav']} - {row['Poznamka']}\n"
                    
                    poslat_email(sumar_text, email_nadriadeneho)
                    
                    # Aktualizácia v tabuľke (zmena "Nie" na "Ano")
                    # Toto je jednoduchší spôsob pre malú tabuľku:
                    for i, row in enumerate(data, start=2): # start=2 kvôli hlavičke
                        if row['Odoslane'] == 'Nie':
                            sh.update_cell(i, 5, 'Ano')
                    
                    st.success("Odoslané a aktualizované!")
                    st.rerun()
            else:
                st.info("Všetko je už odoslané.")
