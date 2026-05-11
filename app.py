import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- OPRAVA PRIPOJENIA (TOTO VYRIEŠI TVOJU CHYBU) ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # 1. Vezmeme dáta zo Secrets
    creds_info = dict(st.secrets["gcp_service_account"])
    
    # 2. Automatické čistenie kľúča (vynúti správny formát PEM)
    p_key = creds_info["private_key"]
    # Odstráni prebytočné úvodzovky a opraví zalomenia riadkov
    p_key = p_key.replace('\\n', '\n').replace('"', '').strip()
    creds_info["private_key"] = p_key

    # 3. Prihlásenie
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    # Názov tabuľky na Google Drive
    sh = client.open("Hlasenia_Data").sheet1
except Exception as e:
    st.error(f"Ešte stále je problém s kľúčom alebo názvom tabuľky: {e}")
    st.stop()

# --- FUNKCIA NA MAIL (TU DOPLŇ SVOJE ÚDAJE) ---
def poslat_email(text_sumaru, prijemca):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "zmenovehlasenie@gmail.com"  # <--- TVOJ MAIL
    SENDER_PASSWORD = "qvib ewfm liku yfum"  # <--- TVOJ 16-MIESTNY KÓD

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Hlásenie zmeny - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text_sumaru, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

# --- GRAFICKÉ ROZHRANIE ---
st.title("📋 Interné hlásenia")

tab1, tab2 = st.tabs(["📝 Pracovisko", "👑 Vedúci"])

with tab1:
    with st.form("form_pracovisko", clear_on_submit=True):
        pracovisko = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        poznamka = st.text_area("Správa")
        if st.form_submit_button("Uložiť"):
            teraz = datetime.now().strftime("%d.%m.%Y %H:%M")
            sh.append_row([teraz, pracovisko, stav, poznamka, "Nie"])
            st.success("Uložené!")

with tab2:
    heslo = st.text_input("Heslo", type="password")
    if heslo == "admin123":
        data = sh.get_all_records()
        if data:
            df = pd.DataFrame(data)
            neodoslane = df[df['Odoslane'] == 'Nie']
            if not neodoslane.empty:
                st.dataframe(neodoslane)
                prijemca = st.text_input("Poslať na email", "sef@firma.sk")
                if st.button("Odoslať mailom"):
                    text = "Sumár:\n\n" + neodoslane.to_string()
                    poslat_email(text, prijemca)
                    # Označíme ako odoslané (zjednodušene)
                    for i, r in enumerate(data, start=2):
                        if r['Odoslane'] == 'Nie': sh.update_cell(i, 5, 'Ano')
                    st.success("Odoslané!")
                    st.rerun()
