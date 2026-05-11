import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- AUTOMATICKÉ PRIPOJENIE (S OPRAVOU CHÝB V SECRETS) ---
scope = ["https://googleapis.com", "https://googleapis.com"]

try:
    # Načítanie dát zo Secrets
    info = dict(st.secrets["gcp_service_account"])
    
    # OPRAVA NESPRÁVNYCH ADRES (Samoopravný mechanizmus)
    info["auth_uri"] = "https://google.com"
    info["token_uri"] = "https://googleapis.com"
    info["auth_provider_x509_cert_url"] = "https://googleapis.com"
    info["client_x509_cert_url"] = f"https://googleapis.com{info['client_email'].replace('@', '%40')}"
    
    # Oprava kľúča (zalomenie riadkov)
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    # Otvorenie tabuľky - uisti sa, že sa volá: Hlasenia_Data
    sh = client.open("Hlasenia_Data").sheet1
except Exception as e:
    st.error(f"Chyba pripojenia ku Google Sheets: {e}")
    st.stop()

# --- FUNKCIA NA ODOSIELANIE MAILU ---
def poslat_email(text_sumaru, prijemca):
    # !!! SEM DOPLŇ SVOJ MAIL A APP PASSWORD !!!
    MOJ_MAIL = "zmenovehlasenie@gmail.com" 
    MOJE_HESLO = "qvib ewfm liku yfum"

    msg = MIMEMultipart()
    msg['From'] = MOJ_MAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denný sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text_sumaru, 'plain'))

    server = smtplib.SMTP("://gmail.com", 587)
    server.starttls()
    server.login(MOJ_MAIL, MOJE_HESLO)
    server.send_message(msg)
    server.quit()

# --- GRAFICKÉ ROZHRANIE ---
st.title("📋 Systém hlásení")

tab1, tab2 = st.tabs(["🏗️ Pracovisko", "👑 Veliteľ"])

with tab1:
    with st.form("form_vstup", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad", "Expedícia"])
        stav = st.radio("Stav zmeny", ["V poriadku", "Zdržanie", "Problém"])
        txt = st.text_area("Hlásenie")
        if st.form_submit_button("Odoslať"):
            cas = datetime.now().strftime("%d.%m.%Y %H:%M")
            sh.append_row([cas, prac, stav, txt, "Nie"])
            st.success("Hlásenie bolo uložené.")

with tab2:
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        vsetky_data = sh.get_all_records()
        if vsetky_data:
            df = pd.DataFrame(vsetky_data)
            neodoslane = df[df['Odoslane'] == 'Nie']
            
            if not neodoslane.empty:
                st.write("Nové hlásenia:")
                st.table(neodoslane)
                
                mail_nadriadeneho = st.text_input("Email nadriadeného", "nadriadeny@firma.sk")
                if st.button("Odoslať sumár mailom"):
                    sumar = "Sumár hlásení:\n\n" + neodoslane.to_string(index=False)
                    try:
                        poslat_email(sumar, mail_nadriadeneho)
                        # Označenie v tabuľke ako "Ano"
                        for i, row in enumerate(vsetky_data, start=2):
                            if row['Odoslane'] == 'Nie':
                                sh.update_cell(i, 5, 'Ano')
                        st.success("Odoslané!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Chyba pri maili: {ex}")
            else:
                st.info("Žiadne nové hlásenia.")
