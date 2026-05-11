import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 1. TVOJE ÚDAJE PRE EMAIL (TU DOPLŇ SVOJE) ---
MOJ_GMAIL = "zmenovehlasenie@gmail.com"
MOJE_APP_HESLO = "qvib ewfm liku yfum"

# --- 2. KONFIGURÁCIA GOOGLE (OVERENÁ - OPRAVENÝ EMAIL AJ ADRESY) ---
GOOGLE_INFO = {
  "type": "service_account",
  "project_id": "hlasenia-app",
  "private_key_id": "9ee2d60b548a078036d897c26ab07e138520caf6",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCfvMUfykG8ETtk\nAiY4nWnaRn/MywGThXg4q3xC6Q+Mv+hY7eRAWswCBlrHtZglGIqTnM4o0uNfpWcf\n/I7cH6CQ4k/13HyM0F9ue01G18I1XYmzxYK+1tpIcvCbzrWIApnqeLvUg3shs1xj\nfpEBfKH9+BqWeTcxUfin/Lvk3QVzVxWidQpe8ayH5yRoOVz33F+YaoFJZsxl2Q2F\nt+pjxBm3e8FOOT7Je8E1GYXMNqMZIXqfvJTNkCTHEgE4mKcHZz8dCLIqFjJbZ6JU\nhWpqSkqC3wn5tfnwaU0xVKmnIOhcoGAg1zYxrif7hyknIpmDp6L/T1bCZOOxSSEB\n2lz+IDYjAgMBAAECggEABjsqY2GT696uNuoAjK/TS8D5RkdbAeKwfGFwIPoPcbmg\nuitZfossLx4JV4YFb9kDuttgjWYgmYANxEkpV3viWxSA8wHNV/7e4iPsMUnEWSmT\ncBBR19jwvefB7AoFuc8EKwnXpeQVHwzsmzL6PBkdBpexjdIfrYxZi1AIElbu2f9p\nX82qOLjHMTDA1bdKgsFGFHkV/WTjVWEWQ4Lp94WOdo+Pf9ex7fIC1Z/T+PmU29ET\nzEgGQytdbrA0PDRAK65o+vZK0FbkteYPiFgoYLgM/Kk4fcYqg/KWnjZw78pCosPZ\nPVtYFuwS+sFGDsX5Pn5+jqvKB2yaOAZLEMn6AGYMzQKBgQDPwRw06jFG+2R0aul0\nO/r1bWZ6epGpw2+Kz87rzhZ3ibFJ21nYS040hw7lbhWhPdukg4H5jN858p1Gr0g2\nxvA09hMNADc5whC9iLPWr5sgrhKaPiqLbsGOIqJMi+dETnXrOBWUpC6b8lHTHM8T\no9HUzfnla70zFKvxXABmsvAApQKBgQDE1ROJXQTmILf1L+sy4XQU7UPEeCBQuIAT\nv8F+HY/LUsoCjHArzHDdE4OVBZo9WRnqM63Cb9fCnp5krZ2BoePfTm+vNtFlxN8v\n27iruXCOpd0YEDHUiNrPP9unvDm/lyeaMIvQFvhFm1UyyZWpYEl1Ws5JtoXhHYoA\nOYyTxYAZJwKBgF/kuMpL1tb2rpV1y7AVB29FQeoCrT14sgGWjeIVzBT8/1Ih50SI\n7d4dAOkxeNZmIP28nb+8IEU1ERdRTLnL9Y/cjUqQ8Oy+ANAbSzcq8yWQc5GyZBzb\n0Id0wQkoAmVq+c7KoltrtP/SR6Z0Q7jDAtWBBXm50yjCv+K2HpFIwrLpAoGAKiDc\n9JqXMNYx6WWfNp2wpcX+qi934y8KIq/5LxAOtdr7Z749R/KS+Y5yrFOtppHKjSkQ\neLxNdtdSWYQbYSKQTjxQhTT7bofLqUei6AZhw/ZWMw9MSwwboR4u2mDcD1i/3i2j\nzx8LdoJ/osYopT75mgecfYR2dS9IWTH4F6y+9SMCgYEAmIp9Au+G830Tkw7l1U9r\nO0+bX5wppw/zPW6Uohm8eJCFIy3KdvkX3s4niGxtLuuTPnldOYgF0uGjamayflqe\ngc8VnEn/hInn1A0nqhbhtaW/mXQm07qOaEePCU0FgdkiazdltVWL1lxWaFW/pceI\ni5OeotBB5HicUjrqni1fND4=\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit-db@hlasenia-app.iam.gserviceaccount.com",
  "client_id": "113588806567780330946",
  "auth_uri": "https://google.com",
  "token_uri": "https://googleapis.com",
  "auth_provider_x509_cert_url": "https://googleapis.com",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-db%40://gserviceaccount.com"
}

SHEET_ID = "11mgxqbYWXZ97HA7Fz2Sihqaz9o4TDzK2Ac9iKShd4PQ"

# --- PRIPOJENIE ---
try:
    scope = ["https://googleapis.com", "https://googleapis.com"]
    creds = Credentials.from_service_account_info(GOOGLE_INFO, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Chyba pripojenia: {e}")
    st.stop()

# --- FUNKCIA NA MAIL ---
def poslat_email(text, prijemca):
    msg = MIMEMultipart()
    msg['From'] = MOJ_GMAIL
    msg['To'] = prijemca
    msg['Subject'] = f"Sumár hlásení - {datetime.now().strftime('%d.%m.%Y')}"
    msg.attach(MIMEText(text, 'plain'))
    server = smtplib.SMTP("://gmail.com", 587)
    server.starttls()
    server.login(MOJ_GMAIL, MOJE_APP_HESLO)
    server.send_message(msg)
    server.quit()

# --- INTERFACE ---
st.title("📋 Systém prevádzkových hlásení")
t1, t2 = st.tabs(["🏗️ Pracovisko", "👑 Vedúci zmeny"])

with t1:
    with st.form("f1", clear_on_submit=True):
        prac = st.selectbox("Pracovisko", ["Linka A", "Linka B", "Sklad"])
        stav = st.radio("Stav", ["OK", "Problém"])
        txt = st.text_area("Hlásenie")
        if st.form_submit_button("Odoslať"):
            cas = datetime.now().strftime("%d.%m.%Y %H:%M")
            sh.append_row([cas, prac, stav, txt, "Nie"])
            st.success("Hlásenie uložené!")

with t2:
    heslo = st.text_input("Vstupné heslo", type="password")
    if heslo == "admin123":
        vsetky = sh.get_all_records()
        if vsetky:
            df = pd.DataFrame(vsetky)
            if 'Odoslane' in df.columns:
                neodoslane = df[df['Odoslane'] == 'Nie']
                st.write("Čakajúce hlásenia:")
                st.dataframe(neodoslane)
                mail_boss = st.text_input("Poslať na email", "nadriadeny@firma.sk")
                if st.button("Poslať mailom"):
                    poslat_email(neodoslane.to_string(index=False), mail_boss)
                    for i, r in enumerate(vsetky, start=2):
                        if r.get('Odoslane') == 'Nie': sh.update_cell(i, 5, 'Ano')
                    st.success("Odoslané!")
                    st.rerun()
