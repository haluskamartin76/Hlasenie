import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- PRIPOJENIE (CEZ SECRETS) ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # Načítanie zo Secrets a oprava zalomení riadkov v kľúči
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    # ID tvojej tabuľky
    sh = client.open_by_key("11mgxqbYWXZ97HA7Fz2Sihqaz9o4TDzK2Ac9iKShd4PQ").sheet1
except Exception as e:
    st.error(f"Chyba pripojenia: {e}")
    st.stop()

# --- FUNKCIA NA MAIL ---
def poslat_email(text, prijemca):
    # --- TU DOPLŇ SVOJ GMAIL A APP PASSWORD ---
    MOJ_MAIL = "tvoj-email@gmail.com" 
    MOJE_HESLO = "tvoj-app-password"

    msg = MIMEMultipart()
    msg['From'] = MOJ_MAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denný sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text, 'plain'))

    server = smtplib.SMTP("://gmail.com", 587)
    server.starttls()
    server.login(MOJ_MAIL, MOJE_HESLO)
    server.send_message(msg)
    server.quit()

# --- INTERFACE ---
st.title("📋 Systém hlásení")
tab1, tab2 = st.tabs(["🏗️ Pracovisko", "👑 Veliteľ"])

with tab1:
    with st.form("form_prac", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        txt = st.text_area("Detail hlásenia")
        if st.form_submit_button("Odoslať"):
            sh.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), prac, stav, txt, "Nie"])
            st.success("Uložené v Google tabuľke!")

with tab2:
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        vsetky = sh.get_all_records()
        if vsetky:
            df = pd.DataFrame(vsetky)
            if 'Odoslane' in df.columns:
                neodoslane = df[df['Odoslane'] == 'Nie']
                if not neodoslane.empty:
                    st.dataframe(neodoslane)
                    mail_sefa = st.text_input("Poslať na email", "nadriadeny@firma.sk")
                    if st.button("Odoslať sumár mailom"):
                        poslat_email(neodoslane.to_string(index=False), mail_sefa)
                        # Označenie v tabuľke (5. stĺpec je 'Odoslane')
                        for i, r in enumerate(vsetky, start=2):
                            if r.get('Odoslane') == 'Nie':
                                sh.update_cell(i, 5, 'Ano')
                        st.success("Odoslané!")
                        st.rerun()
