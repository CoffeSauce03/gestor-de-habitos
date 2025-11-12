import streamlit as st
import os
import sys
import django
from datetime import date
import pandas as pd
import plotly.express as px
from django.db.models import Count
from django.core.management import execute_from_command_line
import time

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO DO DJANGO ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'config')
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Inicializa o Django
django.setup()

# Importa os modelos APÓS a inicialização
from dados.models import Usuario, Habito, Registro

@st.cache_resource
def inicializar_banco():
    """
    Executa as migrações do Django para criar o banco de dados.
    O cache do Streamlit impede que isto execute mais de uma vez por sessão.
    """
    print("--- INICIALIZANDO BANCO DE DADOS ---")
    try:
        manage_py_path = os.path.join(DJANGO_PROJECT_PATH, 'manage.py')
        
        # Como as migrações já estão no GitHub, apenas executamos 'migrate'.
        # Se precisar de recriar as migrações, descomente a linha abaixo.
        # execute_from_command_line([manage_py_path, 'makemigrations', 'dados'])
        
        execute_from_command_line([manage_py_path, 'migrate'])
        
        print("Banco de dados inicializado e migrado com sucesso.")
    except Exception as e:
        print(f"Aviso durante inicialização do banco: {e}")

# --- 2. FUNÇÕES DE LÓGICA (BACKEND) ---

def registrar_usuario_db(username, password):
    if Usuario.objects.filter(username=username).exists():
        st.error("Este nome de usuário já está em uso.")
        return None
    user = Usuario(username=username)
    user.set_password(password)
    user.save()
    return user

def autenticar_usuario_db(username, password):
    try:
        user = Usuario.objects.get(username=username)
        if user.check_password(password):
            return user
    except Usuario.DoesNotExist:
        return None
    return None

# Função para a Estória de Usuário 1 (EU1)
def adicionar_habito_db(nome, user):
    if nome: 
        Habito.objects.create(nome=nome, usuario=user)
        return True
    return False

def remover_habito_db(habito_id, user):
    try:
        habito = Habito.objects.get(id=habito_id, usuario=user)
        habito.delete()
        st.success(f"Hábito '{habito.nome}' removido!")
        return True
    except Habito.DoesNotExist:
        st.error("Erro ao remover hábito.")
        return False

def buscar_habitos_db(user): 
    return Habito.objects.filter(usuario=user).order_by('nome')

def marcar_habito_db(habito_id, marcar_como_concluido):
    habito = Habito.objects.get(id=habito_id)
    hoje = date.today()
    if marcar_como_concluido:
        # Cria o registro se não existir
        Registro.objects.get_or_create(habito=habito, data_registro=hoje)
    else:
        # Remove o registro se existir
        Registro.objects.filter(habito=habito, data_registro=hoje).delete()

# Função para a Estória de Usuário 2 (EU2)
def buscar_dados_grafico_db(user):
    dados = Registro.objects.filter(habito__usuario=user).values('habito__nome').annotate(total=Count('id')).order_by('-total')
    df = pd.DataFrame(list(dados))
    if not df.empty: 
        df.rename(columns={'habito__nome': 'Hábito', 'total': 'Dias Cumpridos'}, inplace=True)
    return df

# --- 3. INTERFACE GRÁFICA (STREAMLIT) ---

def pagina_login_cadastro():
    st.set_page_config(page_title="Gestor de Hábitos")
    st.title("Gestor de Hábitos")
    aba_login, aba_cadastro = st.tabs(["Login", "Cadastro"])
    with aba_login:
        st.subheader("Acesse sua Conta")
        with st.form("login_form"):
            login_usuario = st.text_input("Nome de Usuário", key="login_user")
            login_senha = st.text_input("Senha", type="password", key="login_pass")
            if st.form_submit_button("Entrar"):
                user = autenticar_usuario_db(login_usuario, login_senha)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.rerun()
                else: 
                    st.error("Usuário ou senha inválidos.")
    with aba_cadastro:
        st.subheader("Crie sua Conta")
        with st.form("cadastro_form"):
            cadastro_usuario = st.text_input("Escolha um Nome de Usuário", key="reg_user")
            cadastro_senha = st.text_input("Crie uma Senha", type="password", key="reg_pass")
            if st.form_submit_button("Cadastrar"):
                if not (cadastro_usuario and cadastro_senha):
                    st.error("Usuário e senha são obrigatórios.")
                else:
                    user = registrar_usuario_db(cadastro_usuario, cadastro_senha)
                    if user:
                        st.success("Usuário criado com sucesso! Faça o login na aba ao lado.")
                        time.sleep(2)
                        st.rerun()

def pagina_principal():
    st.set_page_config(page_title="Painel de Hábitos", layout="wide")
    user = Usuario.objects.get(id=st.session_state.user_id)
    
    st.sidebar.success(f"Bem-vindo(a), {st.session_state.username}!")
    if st.sidebar.button("Sair"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- Funcionalidade para Estória de Usuário 1 (EU1) ---
    with st.expander("➕ Adicionar Novo Hábito"):
        novo_habito = st.text_input("Qual hábito monitorar?", key="novo_habito", help="Ex: Estudar Python por 1 hora")
        if st.button("Adicionar Hábito"):
            if adicionar_habito_db(novo_habito, user): 
                st.success(f"Hábito '{novo_habito}' adicionado!")
                time.sleep(1) # Dá tempo para o usuário ler a mensagem
                st.rerun()
            else: 
                st.warning("Digite um nome para o hábito.")

    st.markdown("---")
    
    # --- CORREÇÃO DO LAYOUT (EU2) ---
    # Define as duas colunas principais
    col1, col2 = st.columns([1, 1]) # Divide a tela em duas colunas de tamanho igual

    with col1:
        st.subheader("Meus Hábitos de Hoje")
        habitos = buscar_habitos_db(user)
        if not habitos:
            st.info("Você ainda não adicionou nenhum hábito.")
        
        # Itera por cada hábito e cria sua linha de interação
        for habito in habitos:
            col_hab, col_del = st.columns([5, 1]) # Colunas internas para o nome e o lixo
            
            with col_hab:
                marcado_hoje = Registro.objects.filter(habito=habito, data_registro=date.today()).exists()
                
                # Captura a mudança de estado do checkbox
                foi_clicado = st.checkbox(
                    habito.nome, 
                    value=marcado_hoje, 
                    key=f"habito_{habito.id}"
                )
                
                # Lógica de atualização (agora verifica a mudança)
                if foi_clicado != marcado_hoje:
                    marcar_habito_db(habito.id, foi_clicado)
                    st.rerun() # Recarrega a página para atualizar o gráfico

            with col_del:
                # --- CORREÇÃO DO BUG DE EXCLUSÃO ---
                # O `st.rerun()` só é chamado SE o botão for clicado
                if st.button("🗑️", key=f"del_{habito.id}", help=f"Remover '{habito.nome}'"):
                    remover_habito_db(habito.id, user)
                    st.rerun() # Recarrega a página para remover o hábito da lista

    # --- Funcionalidade para Estória de Usuário 2 (EU2) ---
    with col2:
        st.subheader("Progresso Geral")
        df = buscar_dados_grafico_db(user)
        
        if df.empty: 
            st.info("Marque um hábito como concluído para ver o seu progresso aqui.")
        else: 
            # Cria o gráfico de barras
            fig = px.bar(
                df, 
                x='Hábito', 
                y='Dias Cumpridos', 
                color='Hábito', 
                title="Total de Dias Cumpridos por Hábito"
            )
            st.plotly_chart(fig, use_container_width=True)

# --- 4. LÓGICA PRINCIPAL DA APLICAÇÃO ---
def main():
    # Inicializa o banco de dados (só executa uma vez)
    inicializar_banco()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        pagina_login_cadastro()
    else:
        pagina_principal()

if __name__ == "__main__":
    main()