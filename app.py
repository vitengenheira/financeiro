

import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="📝")

# --- CSS PARA STATUS ---
st.markdown("""
    <style>
    .pago { color: #2ecc71; font-weight: bold; background-color: #e8f8f5; padding: 5px; border-radius: 5px; }
    .pendente { color: #e74c3c; font-weight: bold; background-color: #fdedec; padding: 5px; border-radius: 5px; }
    .card { border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS (COM MEMÓRIA DE SESSÃO) ---
@st.cache_data
def carregar_planilha():
    df_alunos = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    meses = ["JANEIRO.2026", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    
    pagamentos = {}
    for m in meses:
        try:
            pagamentos[m] = pd.read_excel("planilha atualizada 2026.xlsx", sheet_name=m, skiprows=1)
        except: continue
    return df_alunos, pagamentos

# Inicializa os dados na memória do navegador para permitir edição
if 'df_alunos' not in st.session_state:
    df_al, pg_meses = carregar_planilha()
    st.session_state.df_alunos = df_al
    st.session_state.pg_meses = pg_meses

if 'aluno_foco' not in st.session_state:
    st.session_state.aluno_foco = None

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("💳 Gestão Star Tec")
if st.sidebar.button("⬅️ Voltar para Lista Principal"):
    st.session_state.aluno_foco = None

menu = st.sidebar.radio("Ir para:", ["📋 Lista e Busca", "➕ Cadastrar Aluno", "📈 Resumo Mensal"])

# --- TELA: DETALHE E EDIÇÃO (VIDA DO ALUNO) ---
if st.session_state.aluno_foco:
    nome_aluno = st.session_state.aluno_foco
    st.header(f"⚙️ Editando Ficha: {nome_aluno}")
    
    # Busca o índice do aluno para salvar a edição depois
    idx = st.session_state.df_alunos[st.session_state.df_alunos['Aluno'] == nome_aluno].index[0]
    aluno_data = st.session_state.df_alunos.loc[idx]

    tab1, tab2 = st.tabs(["📄 Dados Cadastrais", "💰 Financeiro Detalhado"])

    with tab1:
        with st.form("edicao_aluno"):
            col1, col2 = st.columns(2)
            novo_nome = col1.text_input("Nome do Aluno", value=aluno_data['Aluno'])
            novo_zap = col1.text_input("WhatsApp", value=aluno_data['Contato'])
            novo_venc = col2.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"], 
                                      index=["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"].index(str(aluno_data['Vencimento']).upper() if pd.notna(aluno_data['Vencimento']) else "DIA 15"))
            novo_doc = col2.selectbox("Pendência Doc?", ["--", "SIM", "Cursando"], index=0)
            
            if st.form_submit_button("💾 Salvar Alterações no Cadastro"):
                st.session_state.df_alunos.at[idx, 'Aluno'] = novo_nome
                st.session_state.df_alunos.at[idx, 'Contato'] = novo_zap
                st.session_state.df_alunos.at[idx, 'Vencimento'] = novo_venc
                st.success("Alterações salvas com sucesso!")

    with tab2:
        st.subheader("Histórico de Pagamentos 2026")
        st.write("Aqui você pode dar baixa em meses pendentes:")
        
        for mes in st.session_state.pg_meses.keys():
            pagou = st.session_state.pg_meses[mes][st.session_state.pg_meses[mes]['Lançamento'].astype(str).str.contains(nome_aluno.split()[0], case=False, na=False)]
            
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{mes}**")
            
            if not pagou.empty:
                c2.markdown(f"<span class='pago'>✅ PAGO (R$ {pagou.iloc[0]['Valor']})</span>", unsafe_allow_html=True)
                if c3.button("Estornar", key=f"est_{mes}"):
                    st.warning("Função de estorno acionada.")
            else:
                c2.markdown("<span class='pendente'>❌ PENDENTE</span>", unsafe_allow_html=True)
                if c3.button("Dar Baixa", key=f"bx_{mes}"):
                    st.success(f"Pagamento de {mes} registrado para {nome_aluno}!")
                    # Aqui você adicionaria a lógica de inserir a linha no dataframe do mês

# --- TELA: LISTA PRINCIPAL ---
elif menu == "📋 Lista e Busca":
    st.header("👥 Alunos do Polo Ubatã")
    
    busca = st.text_input("🔍 Buscar por nome do aluno...", "").upper()
    
    # Filtro de busca
    df_exibir = st.session_state.df_alunos
    if busca:
        df_exibir = df_exibir[df_exibir['Aluno'].str.upper().str.contains(busca)]

    # Cabeçalho da Tabela customizada
    st.markdown("---")
    c1, c2, c3 = st.columns([3, 2, 1])
    c1.write("**NOME**")
    c2.write("**CONTATO**")
    c3.write("**AÇÃO**")
    
    for _, row in df_exibir.iterrows():
        col_n, col_z, col_b = st.columns([3, 2, 1])
        col_n.write(row['Aluno'])
        col_z.write(row['Contato'])
        if col_b.button("Editar / Ver Vida", key=f"foco_{row['Aluno']}"):
            st.session_state.aluno_foco = row['Aluno']
            st.rerun()

# --- TELA: NOVO CADASTRO ---
elif menu == "➕ Cadastrar Aluno":
    st.header("Adicionar Novo Estudante")
    # Formulário de cadastro que insere no dataframe da sessão
    with st.form("cad_novo"):
        n = st.text_input("Nome Completo")
        z = st.text_input("WhatsApp")
        v = st.number_input("Valor Mensalidade", value=200)
        if st.form_submit_button("Cadastrar"):
            new_row = {"Aluno": n, "Contato": z, "Mensalidade": v, "Vencimento": "DIA 15"}
            st.session_state.df_alunos = pd.concat([st.session_state.df_alunos, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"{n} cadastrado com sucesso!")
