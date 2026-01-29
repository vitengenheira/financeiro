import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

# 2. ESTILO BRANCO E AZUL (CSS)
st.markdown("""
    <style>
    /* Fundo do site e títulos */
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    
    /* Botões principais */
    .stButton>button {
        background-color: #004a99;
        color: white;
        border-radius: 5px;
        border: none;
    }
    .stButton>button:hover { background-color: #003366; color: white; }
    
    /* Badges de Status */
    .pago { 
        color: white; background-color: #2ecc71; 
        padding: 4px 10px; border-radius: 15px; font-weight: bold; 
    }
    .pendente { 
        color: white; background-color: #e74c3c; 
        padding: 4px 10px; border-radius: 15px; font-weight: bold; 
    }
    
    /* Sidebar azul */
    [data-testid="stSidebar"] { background-color: #f0f5ff; border-right: 2px solid #004a99; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNÇÃO DE DADOS
@st.cache_data
def carregar_dados_iniciais():
    df_alunos = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    meses = ["JANEIRO.2026", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    
    financeiro = {}
    for m in meses:
        try:
            financeiro[m] = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name=m, skiprows=1)
        except:
            financeiro[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'FORMA', 'Valor', 'Saldo'])
    return df_alunos, financeiro

# 4. GERENCIAMENTO DE ESTADO
if 'dados_alunos' not in st.session_state:
    al, fin = carregar_dados_iniciais()
    st.session_state.dados_alunos = al
    st.session_state.dados_financeiros = fin

if 'aluno_foco' not in st.session_state:
    st.session_state.aluno_foco = None

# --- SIDEBAR COM FOTO NO TOPO ---
with st.sidebar:
    if os.path.exists('logo.png'):
        st.image('logo.png', use_container_width=True)
    st.title("Menu Financeiro")
    if st.button("🏠 Ir para Início"):
        st.session_state.aluno_foco = None
        st.rerun()
    
    menu = st.radio("Seções:", ["📋 Lista de Alunos", "➕ Novo Cadastro", "📊 Relatório Mensal"])

# --- TELA: FICHA DO ALUNO (VIDA DO ALUNO) ---
if st.session_state.aluno_foco:
    aluno_nome = st.session_state.aluno_foco
    st.header(f"👤 Ficha do Aluno: {aluno_nome}")
    
    idx = st.session_state.dados_alunos[st.session_state.dados_alunos['Aluno'] == aluno_nome].index[0]
    info = st.session_state.dados_alunos.loc[idx]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 Dados Cadastrais")
        with st.container(border=True):
            novo_nome = st.text_input("Nome", value=info['Aluno'])
            novo_zap = st.text_input("WhatsApp", value=info['Contato'])
            if st.button("Salvar Alterações"):
                st.session_state.dados_alunos.at[idx, 'Aluno'] = novo_nome
                st.session_state.dados_alunos.at[idx, 'Contato'] = novo_zap
                st.success("Cadastro atualizado!")

    with col2:
        st.subheader("💰 Controle de Meses")
        for mes in st.session_state.dados_financeiros.keys():
            df_mes = st.session_state.dados_financeiros[mes]
            pago = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(aluno_nome.split()[0].upper(), na=False)]
            
            c_m, c_s, c_a = st.columns([2, 2, 2])
            c_m.write(f"**{mes}**")
            
            if not pago.empty:
                c_s.markdown('<span class="pago">PAGO</span>', unsafe_allow_html=True)
                if c_a.button("Estornar", key=f"del_{mes}"):
                    st.session_state.dados_financeiros[mes] = df_mes[~df_mes['Lançamento'].astype(str).str.upper().str.contains(aluno_nome.split()[0].upper())]
                    st.rerun()
            else:
                c_s.markdown('<span class="pendente">ABERTO</span>', unsafe_allow_html=True)
                if c_a.button("Dar Baixa", key=f"baixa_{mes}"):
                    nova_baixa = pd.DataFrame({
                        'Data': [pd.Timestamp.now().strftime('%d/%m/%Y')],
                        'Lançamento': [f"Mensalidade {aluno_nome}"],
                        'FORMA': ['SISTEMA'],
                        'Valor': [200.0],
                        'Saldo': [0.0]
                    })
                    st.session_state.dados_financeiros[mes] = pd.concat([df_mes, nova_baixa], ignore_index=True)
                    st.rerun()

# --- TELA: LISTA PRINCIPAL ---
elif menu == "📋 Lista de Alunos":
    st.header("Lista de Alunos")
    busca = st.text_input("🔍 Buscar aluno...").upper()
    
    df_lista = st.session_state.dados_alunos
    if busca:
        df_lista = df_lista[df_lista['Aluno'].str.upper().str.contains(busca)]

    # Cabeçalho da Lista
    st.markdown("---")
    c_n, c_z, c_a = st.columns([3, 2, 1])
    c_n.write("**ALUNO**")
    c_z.write("**CONTATO**")
    c_a.write("**HISTÓRICO**")

    for i, row in df_lista.iterrows():
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(row['Aluno'])
        col2.write(row['Contato'])
        if col3.button("Ver Vida", key=f"f_{i}"):
            st.session_state.aluno_foco = row['Aluno']
            st.rerun()

# --- TELA: NOVO CADASTRO ---
elif menu == "➕ Novo Cadastro":
    st.header("Cadastrar Aluno no Sistema")
    with st.form("novo_form"):
        n = st.text_input("Nome")
        z = st.text_input("WhatsApp")
        if st.form_submit_button("Confirmar Cadastro"):
            novo_aluno = pd.DataFrame({'Aluno': [n], 'Contato': [z]})
            st.session_state.dados_alunos = pd.concat([st.session_state.dados_alunos, novo_aluno], ignore_index=True)
            st.success("Aluno adicionado com sucesso!")
