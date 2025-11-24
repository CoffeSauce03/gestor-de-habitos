import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from datetime import date
import time

# --- CONFIGURAÇÃO DA BASE DE DADOS (SQLite Puro) ---

def get_connection():
    # Cria/Conecta ao ficheiro 'habitos.db' automaticamente
    conn = sqlite3.connect('habitos.db', check_same_thread=False)
    return conn

def init_db():
    """Cria as tabelas se elas não existirem (substitui o 'migrate' do Django)"""
    conn = get_connection()
    c = conn.cursor()
    
    # Tabela de Utilizadores
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabela de Hábitos
    c.execute('''
        CREATE TABLE IF NOT EXISTS habitos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nome TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Tabela de Registos (Dias concluídos)
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habito_id INTEGER,
            data_registro DATE,
            FOREIGN KEY(habito_id) REFERENCES habitos(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- FUNÇÕES DE LÓGICA (BACKEND) ---

def hash_senha(senha):
    """Criptografa a senha antes de guardar"""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(username, password):
    conn = get_connection()
    c = conn.cursor()
    senha_segura = hash_senha(password)
    try:
        c.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, senha_segura))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Utilizador já existe
    finally:
        conn.close()

def autenticar_usuario(username, password):
    conn = get_connection()
    c = conn.cursor()
    senha_segura = hash_senha(password)
    c.execute('SELECT id, username FROM usuarios WHERE username = ? AND password = ?', (username, senha_segura))
    user = c.fetchone() # Retorna (id, username) ou None
    conn.close()
    return user

def adicionar_habito(user_id, nome):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO habitos (user_id, nome) VALUES (?, ?)', (user_id, nome))
    conn.commit()
    conn.close()

def listar_habitos(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, nome FROM habitos WHERE user_id = ? ORDER BY nome', (user_id,))
    habitos = c.fetchall() # Lista de tuplas [(id, nome), ...]
    conn.close()
    return habitos

def remover_habito(habito_id):
    conn = get_connection()
    c = conn.cursor()
    # Remove registos associados primeiro para manter a integridade
    c.execute('DELETE FROM registros WHERE habito_id = ?', (habito_id,))
    c.execute('DELETE FROM habitos WHERE id = ?', (habito_id,))
    conn.commit()
    conn.close()

def verificar_habito_hoje(habito_id):
    conn = get_connection()
    c = conn.cursor()
    hoje = date.today()
    c.execute('SELECT id FROM registros WHERE habito_id = ? AND data_registro = ?', (habito_id, hoje))
    existe = c.fetchone()
    conn.close()
    return existe is not None

def alternar_habito_hoje(habito_id, marcar):
    conn = get_connection()
    c = conn.cursor()
    hoje = date.today()
    if marcar:
        # Tenta inserir, se já existir ignora (OR IGNORE)
        c.execute('INSERT OR IGNORE INTO registros (habito_id, data_registro) VALUES (?, ?)', (habito_id, hoje))
    else:
        c.execute('DELETE FROM registros WHERE habito_id = ? AND data_registro = ?', (habito_id, hoje))
    conn.commit()
    conn.close()

def obter_dados_grafico(user_id):
    conn = get_connection()
    # Query SQL para contar quantos dias cada hábito foi cumprido
    query = '''
        SELECT h.nome as Hábito, COUNT(r.id) as Dias_Cumpridos
        FROM habitos h
        LEFT JOIN registros r ON h.id = r.habito_id
        WHERE h.user_id = ?
        GROUP BY h.id
        ORDER BY Dias_Cumpridos DESC
    '''
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

# --- INTERFACE GRÁFICA (STREAMLIT) ---

def pagina_login_cadastro():
    st.title("Gestor de Hábitos")
    tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
    
    with tab1:
        l_user = st.text_input("Utilizador", key="l_user")
        l_pass = st.text_input("Senha", type="password", key="l_pass")
        if st.button("Entrar"):
            user = autenticar_usuario(l_user, l_pass)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.success(f"Bem-vindo, {user[1]}!")
                st.rerun()
            else:
                st.error("Utilizador ou senha incorretos.")

    with tab2:
        n_user = st.text_input("Novo Utilizador", key="n_user")
        n_pass = st.text_input("Nova Senha", type="password", key="n_pass")
        if st.button("Registar"):
            if n_user and n_pass:
                if criar_usuario(n_user, n_pass):
                    st.success("Conta criada! Faça login na aba 'Entrar'.")
                else:
                    st.error("Esse nome de utilizador já existe.")
            else:
                st.warning("Preencha todos os campos.")

def pagina_principal():
    st.sidebar.title(f"Olá, {st.session_state.username}!")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    # Adicionar Hábito
    with st.expander("➕ Adicionar Novo Hábito"):
        novo_habito = st.text_input("Nome do hábito")
        if st.button("Adicionar"):
            if novo_habito:
                adicionar_habito(st.session_state.user_id, novo_habito)
                st.success("Hábito adicionado!")
                time.sleep(0.5)
                st.rerun()

    st.divider()

    col1, col2 = st.columns([1, 1])

    # Coluna 1: Lista de Hábitos
    with col1:
        st.subheader("Hábitos de Hoje")
        habitos = listar_habitos(st.session_state.user_id)
        
        if not habitos:
            st.info("Ainda não tem hábitos registados.")
        
        for h_id, h_nome in habitos:
            c1, c2 = st.columns([4, 1])
            with c1:
                checked = verificar_habito_hoje(h_id)
                novo_check = st.checkbox(h_nome, value=checked, key=f"check_{h_id}")
                if novo_check != checked:
                    alternar_habito_hoje(h_id, novo_check)
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{h_id}"):
                    remover_habito(h_id)
                    st.rerun()

    # Coluna 2: Gráfico
    with col2:
        st.subheader("Progresso")
        df = obter_dados_grafico(st.session_state.user_id)
        if not df.empty and df['Dias_Cumpridos'].sum() > 0:
            fig = px.bar(df, x='Hábito', y='Dias_Cumpridos', title="Dias Cumpridos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Complete hábitos para ver o gráfico.")

def main():
    # Inicializa a DB ao arrancar o script
    init_db()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        pagina_login_cadastro()
    else:
        pagina_principal()

if __name__ == "__main__":
    main()