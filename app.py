import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- NASTAVENIA ---
st.set_page_config(page_title="Systém hlásení", layout="centered")

# Prepojenie na Google Sheets (používa nastavenia zo Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# URL tvojej tabuľky
URL_TABULKY = "https://docs.google.com/spreadsheets/d/11mgxqbYWXZ97HA7Fz2Sihqaz9o4TDzK2Ac9iKShd4PQ/edit?usp=sharing"

# --- FUNKCIA NA MAIL ---
def poslat_email(text, prijemca):
    # !!! SEM DOPLŇ SVOJE OVERENÉ ÚDAJE !!!
    MOJ_MAIL = "tvoj-email@gmail.com" 
    MOJE_HESLO = "tvoj-app-password"

    msg = MIMEMultipart()
    msg['From'] = MOJ_MAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denný sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text, 'plain'))

    try:
        server = smtplib.SMTP("://gmail.com", 587)
        server.starttls()
        server.login(MOJ_MAIL, MOJE_HESLO)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Chyba pri odosielaní mailu: {e}")
        return False

# --- WEB ROZHRANIE ---
st.title("📋 Systém hlásení")
t1, t2 = st.tabs(["🏗️ Pracovisko", "👑 Veliteľ"])

with t1:
    st.subheader("Nové hlásenie")
    with st.form("form_vstup", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad", "Expedícia"])
        stav = st.radio("Stav zmeny", ["V poriadku", "Zdržanie", "Problém"])
        txt = st.text_area("Hlásenie (popis)")
        
        if st.form_submit_button("Uložiť hlásenie"):
            try:
                # Načítame aktuálne dáta z tabuľky
                df_existing = conn.read(spreadsheet=URL_TABULKY)
                
                # Vytvoríme nový riadok
                new_row = pd.DataFrame([{
                    "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "Pracovisko": prac,
                    "Stav": stav,
                    "Poznamka": txt,
                    "Odoslane": "Nie"
                }])
                
                # Spojíme staré dáta s novým riadkom
                updated_df = pd.concat([df_existing, new_row], ignore_index=True)
                
                # Zapíšeme späť do tabuľky
                conn.update(spreadsheet=URL_TABULKY, data=updated_df)
                st.success("Hlásenie bolo úspešne uložené v Google Sheets!")
            except Exception as e:
                st.error(f"Chyba pri zápise do tabuľky: {e}")

with t2:
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        try:
            df = conn.read(spreadsheet=URL_TABULKY)
            if not df.empty:
                neodoslane = df[df['Odoslane'] == 'Nie']
                
                if not neodoslane.empty:
                    st.write("Nové hlásenia čakajúce na odoslanie:")
                    st.table(neodoslane)
                    
                    mail_sefa = st.text_input("Email nadriadeného", "nadriadeny@firma.sk")
                    if st.button("Odoslať sumár šéfovi"):
                        telo = "Dobrý deň,\n\npripájam dnešné hlásenia:\n\n"
                        for _, r in neodoslane.iterrows():
                            telo += f"📍 {r['Pracovisko']} | {r['Stav']}\n{r['Poznamka']}\n({r['Datum']})\n\n"
                        
                        if poslat_email(telo, mail_sefa):
                            # Označíme ako odoslané v DataFrame
                            df.loc[df['Odoslane'] == 'Nie', 'Odoslane'] = 'Ano'
                            conn.update(spreadsheet=URL_TABULKY, data=df)
                            st.success("Odoslané a archivované!")
                            st.rerun()
                else:
                    st.info("Momentálne nie sú žiadne nové hlásenia.")
            else:
                st.info("Tabuľka je prázdna.")
        except Exception as e:
            st.error(f"Chyba pri načítaní dát: {e}")
