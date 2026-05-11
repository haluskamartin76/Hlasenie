import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- AUTOMATICKÉ PRIPOJENIE ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # Načítanie a oprava kľúča
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    # Otvorenie tabuľky
    sh = client.open("Hlasenia_Data").sheet1
except Exception as e:
    st.error(f"Chyba: {e}")
    st.stop()

# --- FUNKCIA NA MAIL ---
def poslat_email(text, prijemca):
    MOJ_MAIL = "zmenovehlasenie@gmail.com"  # <--- SEM DAJ SVOJ GMAIL
    MOJE_HESLO = "qvib ewfm liku yfum"    # <--- SEM DAJ TIE 16 PÍSMEN

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

# --- ROZHRANIE ---
st.title("📋 Systém prevádzkových hlásení")

t1, t2 = st.tabs(["🏗️ Pracovisko", "👑 Rozhranie veliteľa"])

with t1:
    st.subheader("Nové hlásenie")
    with st.form("form_vstup", clear_on_submit=True):
        prac = st.selectbox("Vyberte linku/pracovisko", ["Linka A", "Linka B", "Sklad", "Expedícia"])
        stav = st.radio("Stav", ["V poriadku", "Zdržanie", "Porucha/Problém"])
        popis = st.text_area("Hlásenie (čo sa deje?)")
        
        if st.form_submit_button("Odoslať veliteľovi"):
            cas = datetime.now().strftime("%d.%m.%Y %H:%M")
            # Zápis: Dátum, Pracovisko, Stav, Hlásenie, Odoslané?
            sh.append_row([cas, prac, stav, popis, "Nie"])
            st.success("Hlásenie bolo uložené.")

with t2:
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        vsetky_data = sh.get_all_records()
        if vsetky_data:
            df = pd.DataFrame(vsetky_data)
            neodoslane = df[df['Odoslane'] == 'Nie']
            
            if not neodoslane.empty:
                st.write("Neposlané hlásenia od pracovníkov:")
                st.table(neodoslane)
                
                sef_mail = st.text_input("Email nadriadeného", "nadriadeny@firma.sk")
                if st.button("Odoslať sumár šéfovi"):
                    telo = "Dobrý deň,\n\npripájam hlásenia z dnešnej zmeny:\n\n"
                    for _, r in neodoslane.iterrows():
                        telo += f"📍 {r['Pracovisko']} | {r['Stav']}\n{r['Poznamka']}\n(Čas: {r['Datum']})\n\n"
                    
                    poslat_email(telo, sef_mail)
                    
                    # Označíme ako poslané v tabuľke
                    for i, row in enumerate(vsetky_data, start=2):
                        if row['Odoslane'] == 'Nie':
                            sh.update_cell(i, 5, 'Ano')
                    
                    st.success("Mail bol úspešne odoslaný!")
                    st.rerun()
            else:
                st.info("Žiadne nové hlásenia.")
        else:
            st.info("Databáza je prázdna.")
