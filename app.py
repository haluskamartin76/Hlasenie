import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- NASTAVENIA ---
SMTP_SERVER = "://gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "zmenovehlasenie@gmail.com"  # Mail, z ktorého sa odosiela
SENDER_PASSWORD = "qvib ewfm liku yfum"  # Heslo aplikácie (nie bežné heslo)

st.set_page_config(page_title="Hlásenia pracovísk", page_icon="📝")

st.title("📝 Systém hlásení pracovísk")

# 1. ČASŤ: PRACOVISKO (Vypĺňanie hlásenia)
st.header("Vytvoriť hlásenie")
with st.form("form_pracovisko"):
    pracovisko = st.selectbox("Vyberte pracovisko", ["Linka A", "Linka B", "Sklad", "Expedícia"])
    stav = st.radio("Stav zmeny", ["Bez problémov", "Menšie komplikácie", "Zastavenie výroby"])
    poznamka = st.text_area("Detailný popis/Hlásenie")
    submit_report = st.form_submit_button("Uložiť hlásenie")

    if submit_report:
        # Tu by sa v reálnej aplikácii dáta uložili do databázy (napr. SQLite alebo Google Sheets)
        st.success(f"Hlásenie pre {pracovisko} bolo úspešne uložené!")
        st.session_state['posledne_hlasenie'] = f"Pracovisko: {pracovisko}\nStav: {stav}\nPoznámka: {poznamka}"

# 2. ČASŤ: VELITEĽ ZMENY (Odoslanie nadriadenému)
st.divider()
st.header("👑 Rozhranie pre veliteľa")

prijemca = st.text_input("Email nadriadeného", "nadriadeny@firma.sk")

if st.button("Odoslať sumárne hlásenie mailom"):
    if 'posledne_hlasenie' in st.session_state:
        try:
            # Príprava emailu
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = prijemca
            msg['Subject'] = "Denné hlásenie zmeny"
            
            body = f"Dobrý deň,\n\npripájam hlásenie zo zmeny:\n\n{st.session_state['posledne_hlasenie']}"
            msg.attach(MIMEText(body, 'plain'))

            # Odosielanie
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()

            st.success("Hlásenie bolo úspešne odoslané nadriadenému!")
        except Exception as e:
            st.error(f"Chyba pri odosielaní: {e}")
    else:
        st.warning("Nie je pripravené žiadne hlásenie na odoslanie.")
