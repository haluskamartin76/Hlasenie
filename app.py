import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- PRIPOJENIE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MAIL FUNKCIA ---
def poslat_email(text, prijemca):
    MOJ_MAIL = "zmenovehlasenie@gmail.com"  # <--- DOPLŇ
    MOJE_HESLO = "qvib ewfm liku yfum"    # <--- DOPLŇ (16 znakov)

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

# --- WEB ---
st.title("📋 Systém hlásení")
t1, t2 = st.tabs(["🏗️ Pracovisko", "👑 Veliteľ"])

# URL tvojej tabuľky (skopíruj z prehliadača)
URL_TABULKY = "https://docs.google.com/spreadsheets/d/11mgxqbYWXZ97HA7Fz2Sihqaz9o4TDzK2Ac9iKShd4PQ/edit?usp=sharing"

with t1:
    with st.form("f1", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        txt = st.text_area("Správa")
        if st.form_submit_button("Odoslať"):
            # Načítanie aktuálnych dát
            existing_data = conn.read(spreadsheet=URL_TABULKY)
            new_row = pd.DataFrame([{
                "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "Pracovisko": prac,
                "Stav": stav,
                "Poznamka": txt,
                "Odoslane": "Nie"
            }])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(spreadsheet=URL_TABULKY, data=updated_df)
            st.success("Hlásenie uložené!")

with t2:
    pwd = st.text_input("Heslo", type="password")
    if pwd == "admin123":
        df = conn.read(spreadsheet=URL_TABULKY)
        if not df.empty:
            neodoslane = df[df['Odoslane'] == 'Nie']
            st.dataframe(neodoslane)
            
            prijemca_mail = st.text_input("Email šéfa", "nadriadeny@firma.sk")
            if st.button("Odoslať sumár"):
                telo = "Sumár hlásení:\n\n" + neodoslane.to_string(index=False)
                poslat_email(telo, prijemca_mail)
                # Označenie ako odoslané
                df.loc[df['Odoslane'] == 'Nie', 'Odoslane'] = 'Ano'
                conn.update(spreadsheet=URL_TABULKY, data=df)
                st.success("Odoslané!")
                st.rerun()
