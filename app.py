import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

# 2. LOGO NO TOPO
# Substitua 'logo.png' pelo nome do arquivo da imagem que você subiu no GitHub
if os.path.exists('logo.png'):
    st.image('logo.png', width=200)
else:
    st.title("🏫 Star Tec - Polo Ubatã")

# --- CSS PARA STATUS ---
st.markdown("""
    <style>
    .pago { color: white; background-color: #2ecc71; padding: 4px 8px; border-radius: 5px; font-weight: bold; }
    .pendente { color: white; background-color: #e74c3c; padding: 4px 8px; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE CARREGAMENTO ---
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

# --- GERENCIAMENTO DE ESTADO (MEMÓRIA) ---
if 'dados_alunos' not in st.session_state:
    al, fin = carregar_dados_iniciais()
    st.session_state.dados_alunos = al
    st.session_state.dados_financeiros = fin

if 'aluno_foco' not in st.session_state:
    st.session_state.aluno_foco = None

# --- NAVEGAÇÃO ---
st.sidebar.title("Menu de Gestão")
if st.sidebar.button("🏠 Início / Lista de Alunos"):
    st.session_state.aluno_foco = None

menu = st.sidebar.radio("Ir para:", ["📋 Painel de Controle", "➕ Adicionar Aluno"])

# --- TELA: VIDA DO ALUNO (EDIÇÃO COMPLETA) ---
if st.session_state.aluno_foco:
    aluno_nome = st.session_state.aluno_foco
    st.header(f"👤 Ficha Financeira: {aluno_nome}")
    
    # Busca dados atuais na memória
    idx = st.session_state.dados_alunos[st.session_state.dados_alunos['Aluno'] == aluno_nome].index[0]
    info = st.session_state.dados_alunos.loc[idx]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Dados do Cadastro")
        novo_nome = st.text_input("Nome", value=info['Aluno'])
        novo_contato = st.text_input("Contato", value=info['Contato'])
        if st.button("Salvar Dados Cadastrais"):
            st.session_state.dados_alunos.at[idx, 'Aluno'] = novo_nome
            st.session_state.dados_alunos.at[idx, 'Contato'] = novo_contato
            st.success("Cadastro atualizado!")

    with col2:
        st.subheader("Situação de Mensalidades")
        # Lista os meses e permite dar baixa
        for mes in st.session_state.dados_financeiros.keys():
            df_mes = st.session_state.dados_financeiros[mes]
            # Verifica se o aluno consta como pago no mês
            pago = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(aluno_nome.split()[0].upper(), na=False)]
            
            c_mes, c_status, c_acao = st.columns([2, 2, 2])
            c_mes.write(f"**{mes}**")
            
            if not pago.empty:
                c_status.markdown('<span class="pago">PAGO</span>', unsafe_allow_html=True)
                if c_acao.button("Remover Pagamento", key=f"del_{mes}"):
                    # Remove a linha de pagamento da memória
                    st.session_state.dados_financeiros[mes] = df_mes[~df_mes['Lançamento'].astype(str).str.upper().str.contains(aluno_nome.split()[0].upper())]
                    st.rerun()
            else:
                c_status.markdown('<span class="pendente">PENDENTE</span>', unsafe_allow_html=True)
                if c_acao.button("Dar Baixa ✅", key=f"baixa_{mes}"):
                    # Adiciona uma nova linha de pagamento na memória
                    nova_baixa = pd.DataFrame({
                        'Data': [pd.Timestamp.now().strftime('%d/%m/%Y')],
                        'Lançamento': [f"Mensalidade {aluno_nome}"],
                        'FORMA': ['SISTEMA'],
                        'Valor': [200.0], # Valor padrão
                        'Saldo': [0.0]
                    })
                    st.session_state.dados_financeiros[mes] = pd.concat([df_mes, nova_baixa], ignore_index=True)
                    st.success(f"Baixa dada em {mes}!")
                    st.rerun()

# --- TELA: LISTA PRINCIPAL ---
elif menu == "📋 Painel de Controle":
    st.header("Lista de Alunos e Contatos")
    
    busca = st.text_input("🔍 Pesquisar Aluno:").upper()
    df_lista = st.session_state.dados_alunos
    if busca:
        df_lista = df_lista[df_lista['Aluno'].str.upper().str.contains(busca)]

    st.write("---")
    for i, row in df_lista.iterrows():
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{row['Aluno']}**")
        c2.write(row['Contato'])
        if c3.button("Ver Vida / Editar", key=f"f_{i}"):
            st.session_state.aluno_foco = row['Aluno']
            st.rerun()
        st.write("---")

# --- TELA: ADICIONAR ALUNO ---
elif menu == "➕ Adicionar Aluno":
    st.header("Novo Cadastro")
    with st.form("novo"):
        n = st.text_input("Nome")
        c = st.text_input("WhatsApp")
        if st.form_submit_button("Salvar"):
            novo_df = pd.DataFrame({'Aluno': [n], 'Contato': [c]})
            st.session_state.dados_alunos = pd.concat([st.session_state.dados_alunos, novo_df], ignore_index=True)
            st.success("Aluno adicionado!")
