import streamlit as st
import pandas as pd
import os

# Configurações de Design
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

# CSS para deixar os botões mais bonitos
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #f0f2f6; }
    .status-pago { color: green; font-weight: bold; }
    .status-devendo { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    # Carrega Alunos
    df_alunos = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    # Lista de abas de meses
    meses = ["JANEIRO.2026", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    
    pagamentos_meses = {}
    for m in meses:
        try:
            df_m = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name=m, skiprows=1)
            pagamentos_meses[m] = df_m
        except: continue
            
    return df_alunos, pagamentos_meses

df_alunos, dic_meses = carregar_dados()

# --- LÓGICA DE NAVEGAÇÃO ---
if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- BARRA LATERAL ---
st.sidebar.title("⭐ Star Tec Ubatã")
if st.sidebar.button("🏠 Voltar para Início"):
    st.session_state.aluno_selecionado = None

menu = st.sidebar.radio("Navegar:", ["Lista de Alunos", "Novo Aluno", "Pendências Gerais"])

# --- TELA: FICHA INDIVIDUAL (VIDA DO ALUNO) ---
if st.session_state.aluno_selecionado:
    nome_aluno = st.session_state.aluno_selecionado
    st.header(f"👤 Vida do Aluno: {nome_aluno}")
    
    # Pega dados do aluno
    dados = df_alunos[df_alunos['Aluno'] == nome_aluno].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Informações Base")
        st.write(f"**Contato:** {dados['Contato']}")
        st.write(f"**Matrícula:** {dados['Data da Matricula ']}")
        st.write(f"**Vencimento:** {dados['Vencimento']}")
    
    with col2:
        st.subheader("Documentação")
        doc_status = st.selectbox("Status Doc:", ["OK", "Pendente", "Cursando"], 
                                  index=0 if "SIM" in str(dados['Penden. Docum']) else 1)
        st.text_input("Qual documento?", value=dados['Qual Documento?'])
        if st.button("Salvar Alterações"):
            st.success("Dados atualizados (apenas nesta sessão)")

    with col3:
        st.subheader("Resumo Financeiro")
        st.write(f"**Valor Mensalidade:** {dados['Mensalidade']}")
        st.write(f"**Último Pagamento:** {dados['Data do U. Pag']}")

    st.divider()
    st.subheader("🗓️ Histórico de Mensalidades 2026")
    
    # Gerar a grade de meses
    cols_meses = st.columns(4)
    for i, mes in enumerate(dic_meses.keys()):
        with cols_meses[i % 4]:
            # Busca o nome do aluno na aba do mês
            pagou = dic_meses[mes][dic_meses[mes]['Lançamento'].astype(str).str.contains(nome_aluno.split()[0], case=False, na=False)]
            
            if not pagou.empty:
                st.markdown(f"**{mes}**")
                st.markdown("<span class='status-pago'>✅ PAGO</span>", unsafe_allow_html=True)
                st.caption(f"Valor: {pagou.iloc[0]['Valor']}")
            else:
                st.markdown(f"**{mes}**")
                st.markdown("<span class='status-devendo'>❌ EM ABERTO</span>", unsafe_allow_html=True)

# --- TELA: LISTA DE ALUNOS ---
elif menu == "Lista de Alunos":
    st.header("👥 Todos os Alunos")
    st.write("Clique no nome para ver o histórico financeiro completo.")
    
    # Criar uma tabela com botão
    for index, row in df_alunos.iterrows():
        col_nome, col_zap, col_acao = st.columns([3, 2, 1])
        col_nome.write(f"**{row['Aluno']}**")
        col_zap.write(row['Contato'])
        if col_acao.button("Ver Ficha", key=f"btn_{index}"):
            st.session_state.aluno_selecionado = row['Aluno']
            st.rerun()
        st.divider()

# --- TELA: NOVO ALUNO ---
elif menu == "Novo Aluno":
    st.header("➕ Cadastrar Novo Aluno")
    with st.form("cadastro"):
        nome = st.text_input("Nome Completo")
        contato = st.text_input("WhatsApp")
        venc = st.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20"])
        valor = st.number_input("Valor Mensalidade", value=200)
        if st.form_submit_button("Finalizar Cadastro"):
            st.balloons()
            st.success("Aluno enviado para a fila de processamento!")

# --- TELA: PENDÊNCIAS ---
elif menu == "Pendências Gerais":
    st.header("⚠️ Relatório de Devedores")
    mes_ref = st.selectbox("Verificar mês:", list(dic_meses.keys()))
    
    lista_devedores = []
    for _, al in df_alunos.iterrows():
        pago = dic_meses[mes_ref][dic_meses[mes_ref]['Lançamento'].astype(str).str.contains(al['Aluno'].split()[0], case=False, na=False)]
        if pago.empty:
            lista_devedores.append({"Aluno": al['Aluno'], "Contato": al['Contato']})
    
    st.table(pd.DataFrame(lista_devedores))
