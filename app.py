import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- NASTAVENIA ---
st.set_page_config(page_title="Systém hlásení", layout="centered")

# Prepojenie na Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# POUŽÍVAME PRIAMO ID TABUĽKY (vyrieši chybu NoValidUrlKeyFound)
ID_TABULKY = "11mgxqbYWXZ97HA7Fz2Sihqaz9o4TDzK2Ac9iKShd4PQ"
NAZOV_LISTU = "Hlasenia_Data"

# --- FUNKCIA NA MAIL ---
def poslat_email(text, prijemca):
    MOJ_MAIL = "zmenovehlasenie@gmail.com" 
    MOJE_HESLO = "qvib ewfm liku yfum"

    msg = MIMEMultipart()
    msg['From'] = MOJ_MAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Denný sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text, 'plain', 'utf-8'))

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
        prac = st.selectbox("Pracovisko", ["GH - Garáž Hrad", "G - Poslanecká Garáž", "W - Viedenská brána", "M - Mikulášska brána"])
        stav = st.radio("Stav zmeny", ["V poriadku", "Závada", "Hlásenie"])
        txt = st.text_area("Hlásenie (popis)")
        
        if st.form_submit_button("Uložiť hlásenie"):
            try:
                # Načítanie cez ID tabuľky
                df_existing = conn.read(spreadsheet=ID_TABULKY, worksheet=NAZOV_LISTU)
                
                new_row = pd.DataFrame([{
                    "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "Pracovisko": prac,
                    "Stav": stav,
                    "Poznamka": txt,
                    "Odoslane": "Nie"
                }])
                
                updated_df = pd.concat([df_existing, new_row], ignore_index=True)
                # Update cez ID tabuľky
                conn.update(spreadsheet=ID_TABULKY, worksheet=NAZOV_LISTU, data=updated_df)
                st.success(f"Hlásenie úspešne uložené!")
            except Exception as e:
                st.error("Chyba pri zápise!")
                st.exception(e)

with t2:
    st.subheader("Sekcia pre veliteľa")
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        try:
            # Načítanie cez ID tabuľky
            df = conn.read(spreadsheet=ID_TABULKY, worksheet=NAZOV_LISTU)
            if df is not None and not df.empty:
                neodoslane = df[df['Odoslane'].astype(str).str.contains('Nie', case=False, na=False)]
                
                if not neodoslane.empty:
                    st.write("Nové hlásenia čakajúce na odoslanie:")
                    st.table(neodoslane)
                    
                    mail_sefa = st.text_input("Email nadriadeného", "nadriadeny@firma.sk")
                    if st.button("Odoslať sumár šéfovi"):
                        telo = "Dobrý deň,\n\npripájam dnešné hlásenia:\n\n"
                        for _, r in neodoslane.iterrows():
                            telo += f"📍 {r['Pracovisko']} | {r['Stav']}\n{r['Poznamka']}\n({r['Datum']})\n\n"
                        
                        if poslat_email(telo, mail_sefa):
                            df.loc[df['Odoslane'].astype(str).str.contains('Nie', case=False, na=False), 'Odoslane'] = 'Ano'
                            conn.update(spreadsheet=ID_TABULKY, worksheet=NAZOV_LISTU, data=df)
                            st.success("Odoslané!")
                            st.rerun()
                else:
                    st.info("Žiadne nové hlásenia.")
        except Exception as e:
            st.error(f"Chyba pri práci s dátami: {e}")
