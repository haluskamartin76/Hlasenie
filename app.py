import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- FORCE OPRAVA PRIPOJENIA (IGNORUJE ZLÉ ADRESY ZO SECRETS) ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # Načítame to, čo je v Secrets
    s = st.secrets["gcp_service_account"]
    
    # Vytvoríme čistý slovník so SPRÁVNYMI adresami, ktoré Google vyžaduje
    info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"].replace("\\n", "\n"),
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": "https://google.com",
        "token_uri": "https://googleapis.com",
        "auth_provider_x509_cert_url": "https://googleapis.com",
        "client_x509_cert_url": f"https://googleapis.com{s['client_email'].replace('@', '%40')}",
        "universe_domain": "googleapis.com"
    }
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    # Otvorenie tabuľky - MUSÍ SA VOLAŤ: Hlasenia_Data
    sh = client.open("Hlasenia_Data").sheet1
except Exception as e:
    st.error(f"Chyba pripojenia ku Google Sheets: {e}")
    st.stop()

# --- MAIL FUNKCIA ---
def poslat_email(text, prijemca):
    MOJ_MAIL = "tvoj-email@gmail.com"  # <--- DOPLŇ
    MOJE_HESLO = "tvoj-app-password"    # <--- DOPLŇ (16 znakov)

    msg = MIMEMultipart()
    msg['From'] = MOJ_MAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text, 'plain'))

    server = smtplib.SMTP("://gmail.com", 587)
    server.starttls()
    server.login(MOJ_MAIL, MOJE_HESLO)
    server.send_message(msg)
    server.quit()

# --- WEB ROZHRANIE ---
st.title("📋 Systém hlásení")
t1, t2 = st.tabs(["🏗️ Pracovisko", "👑 Veliteľ"])

with t1:
    with st.form("f1", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        txt = st.text_area("Hlásenie")
        if st.form_submit_button("Uložiť"):
            sh.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), prac, stav, txt, "Nie"])
            st.success("Hlásenie uložené!")

with t2:
    pwd = st.text_input("Heslo", type="password")
    if pwd == "admin123":
        vsetky = sh.get_all_records()
        if vsetky:
            df = pd.DataFrame(vsetky)
            neodoslane = df[df['Odoslane'] == 'Nie']
            if not neodoslane.empty:
                st.table(neodoslane)
                mail_sefa = st.text_input("Poslať na email", "nadriadeny@firma.sk")
                if st.button("Odoslať sumár"):
                    telo = "Sumár:\n\n" + neodoslane.to_string(index=False)
                    poslat_email(telo, mail_sefa)
                    for i, row in enumerate(vsetky, start=2):
                        if row['Odoslane'] == 'Nie': sh.update_cell(i, 5, 'Ano')
                    st.success("Odoslané!")
                    st.rerun()
