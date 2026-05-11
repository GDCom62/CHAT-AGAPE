import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, base64, json

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Portal Ágape", layout="wide", page_icon="⛪")

# URL DO SEU CHAT NO RAILWAY
URL_CHAT_RAILWAY = "https://railway.app"

def aplicar_estilo_facebook():
    st.markdown(f"""
        <style>
        html, body, [class*="st-"] {{ font-family: Arial, sans-serif !important; }}
        .stApp {{ background-color: #f0f2f5; }}
        p, span, label {{ color: #000000 !important; font-size: 19px !important; }}
        [data-testid="stSidebar"] {{ background-color: #1c1e21 !important; }}
        [data-testid="stSidebar"] * {{ color: #ffffff !important; font-size: 18px !important; }}
        .card-post {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #ced0d4; min-height: 250px; }}
        .palavra-destaque {{ background: linear-gradient(135deg, #1877f2, #0054ca); color: white !important; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }}
        .chat-container {{ border: none; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
        </style>
    """, unsafe_allow_html=True)

# --- 2. BANCO DE DADOS ---
engine = create_engine("sqlite:///agape_v60.db", pool_pre_ping=True)

# CORREÇÃO: Usar params=None para evitar erro de 'unhashable type dict'
def executar_query(sql, params=None):
    if params is None: params = {}
    with engine.begin() as conn: 
        conn.execute(text(sql), params)

def consultar_db(sql, params=None):
    if params is None: params = {}
    with engine.connect() as conn: 
        return pd.read_sql_query(text(sql), conn, params=params)

def init_db():
    executar_query('CREATE TABLE IF NOT EXISTS membros (id INTEGER PRIMARY KEY, nome TEXT, email TEXT UNIQUE, codigo TEXT, senha TEXT, is_admin INTEGER)')
    executar_query('CREATE TABLE IF NOT EXISTS avisos (id INTEGER PRIMARY KEY, conteudo TEXT, img_data TEXT, data TEXT)')
    executar_query('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY, descricao TEXT, valor REAL, tipo TEXT, data TEXT, usuario TEXT)')
    executar_query('CREATE TABLE IF NOT EXISTS biblia (id INTEGER PRIMARY KEY, livro TEXT, cap INTEGER, ver INTEGER, texto TEXT)')
    executar_query('CREATE TABLE IF NOT EXISTS oracoes (id INTEGER PRIMARY KEY, nome TEXT, pedido TEXT, status TEXT, data TEXT)')
    executar_query('CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, titulo TEXT, dia_semana TEXT, hora TEXT)')
    
    # Cria admin padrão
    if consultar_db("SELECT id FROM membros WHERE email='admin@agape.com'").empty:
        pw = generate_password_hash('Agape2026')
        executar_query("INSERT INTO membros (nome, email, codigo, senha, is_admin) VALUES ('Admin', 'admin@agape.com', 'ADM-000', :pw, 1)", {"pw": pw})

init_db()

# --- 3. LOGIN ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    aplicar_estilo_facebook()
    _, col_l, _ = st.columns([1, 1.2, 1])
    with col_l:
        st.markdown("<h1 style='color:#1877f2; text-align:center;'>Portal Ágape</h1>", unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = consultar_db("SELECT * FROM membros WHERE email=:e", {"e":e})
                # CORREÇÃO: Acesso via iloc[0] para evitar erros de Series/DataFrame
                if not res.empty and check_password_hash(res.iloc[0]['senha'], s):
                    st.session_state.update({"logado": True, "user": res.iloc[0].to_dict()})
                    st.rerun()
                st.error("Credenciais incorretas.")
else:
    u = st.session_state.user
    aplicar_estilo_facebook()
    
    with st.sidebar:
        if os.path.exists("logo.png"):
            with open("logo.png", "rb") as f:
                data_img = base64.b64encode(f.read()).decode()
                st.markdown(f'<p align="center"><img src="data:image/png;base64,{data_img}" width="120"></p>', unsafe_allow_html=True)
        
        st.markdown(f"### 👤 {u['nome']}")
        
        label_or = "🙏 Orações"
        if u['is_admin']:
            res_or = consultar_db("SELECT COUNT(*) as total FROM oracoes WHERE status='Pendente'")
            if not res_or.empty:
                pendentes = res_or.iloc[0]['total']
                if pendentes > 0: label_or = f"🙏 Orações ({pendentes} 🔴)"

        menu = st.radio("Menu", ["🏠 Feed", "📅 Agenda", "📖 Bíblia", label_or, "🤝 Ofertas", "💰 Financeiro", "💬 Chat Online"])
        if st.button("Sair"): 
            st.session_state.clear()
            st.rerun()

    # --- NAVEGAÇÃO ---
    if menu == "🏠 Feed":
        st.title("Mural da Igreja")
        st.info("Bem-vindo de volta!")

    elif menu == "💬 Chat Online":
        st.title("💬 Chat Comunitário")
        # Login automático via URL
        link_final = f"{URL_CHAT_RAILWAY}?user={u['nome']}&room=Geral"
        
        st.markdown(f"""
            <div class="chat-container">
                <iframe src="{link_final}" width="100%" height="750px" allow="camera; microphone; display-capture; autoplay; clipboard-write" style="border:none;"></iframe>
            </div>
        """, unsafe_allow_html=True)
