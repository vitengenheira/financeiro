import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; }
    .status-ok { color: white; background-color: #2ecc71; padding: 10px; border-radius: 10px; font-weight: bold; text-align: center; }
    .status-alerta { color: white; background-color: #e74c3c; padding: 10px; border-radius: 10px; font-weight: bold; text-align: center; }
    .info-card { background-color: #f8f9fa; border: 1px solid #004a99; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DE DADOS (Consolidado)
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    # Carrega todos os dados dos alunos
    df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    # Lista de meses 2025 e 2026
    meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    meses_2026 = ["JANEIRO.2026"] # Adicionar novos meses conforme surgirem
    
    financas = {}
    for m in meses_2025 + meses_2026:
        try:
            financas[m] = pd.read_excel(file, sheet_name=m, skiprows=1)
        except: financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor'])
            
    return df_alunos, financas, meses_2025, meses_2026

if 'db_alunos' not in st.session_state:
    a, f, m25, m26 = carregar_tudo()
    st.session_state.db_alunos = a
    st.session_state.db_fin = f
    st.session_state.m25 = m25
    st.session_state.m26 = m26

if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- SIDEBAR COM LOGO ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Star Tec Ubatã")
    if st.button("🏠 Voltar à Lista"):
        st.session_state.aluno_selecionado = None
        st.rerun()
    menu = st.radio("Navegação:", ["📋 Alunos", "📊 Resumo Geral"])

# --- TELA: PASTA DO ALUNO (DETALHADA) ---
if st.session_state.aluno_selecionado:
    nome = st.session_state.aluno_selecionado
    st.header(f"📂 Pasta do Aluno: {nome}")
    
    idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome].index[0]
    al = st.session_state.db_alunos.loc[idx]

    # SEÇÃO 1: DADOS CADASTRAIS COMPLETOS
    st.subheader("📝 Informações de Matrícula e Contato")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Contato:** {al['Contato']}")
            st.write(f"**Data da Matrícula:** {al['Data da Matricula ']}")
            st.write(f"**Vencimento:** {al['Vencimento']}")
        with c2:
            st.write(f"**Mensalidade Atual:** {al['Mensalidade']}")
            st.write(f"**Valor da Matrícula:** {al['Valor Matricula']}")
            st.write(f"**Bolsista:** {al['Bolsita']}")
        with c3:
            st.write(f"**Pendência Doc:** {al['Penden. Docum']}")
            st.write(f"**Qual Documento:** {al['Qual Documento?']}")
            st.write(f"**Último Pagamento:** {al['Data do U. Pag']}")

    # SEÇÃO 2: STATUS FINANCEIRO IMEDIATO
    st.divider()
    st.subheader("💰 Situação Financeira Atual")
    
    # Calcular pendências reais
    meses_devendo = []
    for mes in st.session_state.m25 + st.session_state.m26:
        df_mes = st.session_state.db_fin[mes]
        pagou = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(nome.split()[0].upper(), na=False)]
        if pagou.empty:
            meses_devendo.append(mes)

    if not meses_devendo:
        st.markdown('<div class="status-ok">✅ ALUNO EM DIA COM TODAS AS MENSALIDADES</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-alerta">⚠️ PENDÊNCIA ENCONTRADA EM {len(meses_devendo)} MÊS(ES)</div>', unsafe_allow_html=True)
        
        with st.expander("🔍 Ver meses com pendência"):
            for m in meses_devendo:
                c_m, c_b = st.columns([3, 1])
                c_m.write(f"🔴 Mês: **{m}**")
                if c_b.button("Dar Baixa", key=f"bx_{m}"):
                    # Lógica de baixa rápida
                    nova_baixa = pd.DataFrame({'Data': [pd.Timestamp.now().strftime('%d/%m/%Y')], 'Lançamento': [f"Mensalidade {nome}"], 'Valor': [200]})
                    st.session_state.db_fin[m] = pd.concat([st.session_state.db_fin[m], nova_baixa], ignore_index=True)
                    st.rerun()

    # SEÇÃO 3: HISTÓRICO COMPLETO (VIDA FINANCEIRA)
    st.divider()
    st.subheader("📜 Histórico Detalhado")
    
    col25, col26 = st.columns(2)
    
    with col25:
        if st.button("📅 Ver Vida Financeira 2025"):
            st.write("### Extrato 2025")
            for m in st.session_state.m25:
                df_m = st.session_state.db_fin[m]
                p = df_m[df_m['Lançamento'].astype(str).str.upper().str.contains(nome.split()[0].upper(), na=False)]
                if not p.empty:
                    st.success(f"{m}: Pago em {p.iloc[0]['Data']} - Valor: {p.iloc[0]['Valor']}")
                else:
                    st.error(f"{m}: Não consta pagamento no sistema")

    with col26:
        if st.button("📅 Ver Vida Financeira 2026"):
            st.write("### Extrato 2026")
            for m in st.session_state.m26:
                df_m = st.session_state.db_fin[m]
                p = df_m[df_m['Lançamento'].astype(str).str.upper().str.contains(nome.split()[0].upper(), na=False)]
                if not p.empty:
                    st.success(f"{m}: Pago em {p.iloc[0]['Data']} - Valor: {p.iloc[0]['Valor']}")
                else:
                    st.error(f"{m}: Pendente")

# --- TELA: LISTA PRINCIPAL ---
elif menu == "📋 Alunos":
    st.header("Lista de Alunos - Polo Ubatã")
    busca = st.text_input("Buscar por nome...").upper()
    df_lista = st.session_state.db_alunos
    if busca:
        df_lista = df_lista[df_lista['Aluno'].str.upper().str.contains(busca)]

    for i, row in df_lista.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{row['Aluno']}**")
            c2.write(row['Contato'])
            if c3.button("Abrir Pasta", key=f"ver_{i}"):
                st.session_state.aluno_selecionado = row['Aluno']
                st.rerun()
        st.divider()
