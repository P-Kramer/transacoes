import streamlit as st
import requests
import pandas as pd
from datetime import date
import io
import sqlite3
from openpyxl.styles import Alignment, PatternFill, Font
from openpyxl.utils import get_column_letter

from transacoes import tela_transacoes
from carteira import tela_carteira

from PIL import Image
logo_longview = Image.open("longview.png")
# ========== CONFIGURAÇÕES ==========
st.set_page_config(layout="wide")
BASE_URL_API = "https://longview.bluedeck.com.br/api"
CLIENT_ID = "46745f1ee8a39550799966aeac655589.access"
CLIENT_SECRET = "7c8c1802b0f4c9ac4ebe57eee3eb84f4ed87a2eb6a25a5b3afe335474708ce11"
EXCEL_PATH = "Movimentações.xlsx"
DB_PATH = "transacoes.db"
CARTEIRAS = {
    257: "PEPENERO FIM",
    275: "FILIPINA FIM",
    307: "PARMIGIANO FIM",
    308: "HARPYJA FIM",
    1313: "SL_01_ON",
    1362: "TL_01_ON",
    1489: "MEDICI"
}

# LÓGICA FUTURA: Enviar e-mail de notificação a cada nova transação realizada
#
# def enviar_email_transacao(respostas, destinatarios):
#     import smtplib
#     from email.mime.text import MIMEText
#     from email.mime.multipart import MIMEMultipart
#
#     remetente = "SEU_EMAIL@gmail.com"
#     senha = "SUA_SENHA_DE_APP"
#
#     assunto = "Nova transação registrada"
#     corpo = "Uma nova transação foi registrada:\n\n"
#     for k, v in respostas.items():
#         corpo += f"{k}: {v}\n"
#
#     msg = MIMEMultipart()
#     msg['From'] = remetente
#     msg['To'] = ", ".join(destinatarios)
#     msg['Subject'] = assunto
#     msg.attach(MIMEText(corpo, 'plain'))
#
#     # Conectando ao servidor Gmail (pode ser outro, ex: SMTP corporativo)
#     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
#         server.login(remetente, senha)
#         server.sendmail(remetente, destinatarios, msg.as_string())
#
# # Exemplo de uso (quando quiser ativar, depois de salvar a transação):
# # destinatarios = ["pessoa1@email.com", "pessoa2@email.com"]
# # enviar_email_transacao(respostas, destinatarios)

def ir_para(tela):
    st.session_state.pagina_atual = tela
    st.rerun()

def highlight_negative(val):
    try:
        val_float = float(str(val).replace(",", "").replace(" ", ""))
        if val_float < 0:
            return "color: red;"
    except:
        pass
    return ""

def mostrar_header():
    st.image(logo_longview, use_container_width=False, width=320)

# ========== CONTROLE DE SESSÃO ==========
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"
if "token" not in st.session_state:
    st.session_state.token = None
if "headers" not in st.session_state:
    st.session_state.headers = None

# ========== LOGOUT SEMPRE VISÍVEL ==========
mostrar_header()

col1, col2, col3 = st.columns(3)
if st.session_state.token:
    with col3:
        if st.button("Logout", key="logout-btn"):
            st.session_state.clear()
            st.rerun()
    with col1:
        if st.session_state.pagina_atual != "menu":
            if st.button("Voltar ao menu"):
                ir_para("menu")

# ========== TELAS ==========
def tela_menu():
    st.title("Menu Principal")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Transações"):
            ir_para("transacoes")
            st.rerun()
    with col2:
        if st.button("Status Carteira"):
            ir_para("carteira")
            st.rerun()
    with col3:
        if st.button("Configurações"):
            ir_para("configuracoes")
            st.rerun()







def tela_configuracoes():
    st.title("Configurações")
    st.write("Aqui vão suas configurações (personalize esta tela!)")

# ========== LOGIN ==========
if st.session_state.pagina_atual == "login" and not st.session_state.token:
    st.title("🔐 Login")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", key="btn-entrar"):
        client_headers = {
            "CF-Access-Client-Id": CLIENT_ID,
            "CF-Access-Client-Secret": CLIENT_SECRET
        }
        data = {"username": email, "password": senha}
        try:
            resp = requests.post(f"{BASE_URL_API}/auth/token", data=data, headers=client_headers)
            resp.raise_for_status()
            json_data = resp.json()
            st.session_state.token = json_data["access_token"]
            st.session_state.headers = {
                **client_headers,
                "Authorization": f"Bearer {st.session_state.token}"
            }
            st.success("Login bem-sucedido!")
            ir_para("menu")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao autenticar: {e}")

# ========== NAVEGAÇÃO ENTRE TELAS ==========
elif st.session_state.token:
    if st.session_state.pagina_atual == "menu":
        tela_menu()
    elif st.session_state.pagina_atual == "transacoes":
        tela_transacoes()
    elif st.session_state.pagina_atual == "carteira":
        tela_carteira()
    elif st.session_state.pagina_atual == "configuracoes":
        tela_configuracoes()
