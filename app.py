import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="💸")

# --- FUNÇÕES DE AUXÍLIO ---
def format_currency(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data
def carregar_dados():
    # 1. Carregar Alunos
    df_alunos = pd.read_csv('planilha atualizada 2026.xlsx - Alunos.csv', skiprows=3)
    df_alunos = df_alunos[['Aluno', 'Contato', 'Mensalidade', 'Vencimento']].dropna(subset=['Aluno'])
    
    # Mapeamento de arquivos (Ajustado para os seus nomes reais)
    meses_map = {
        "Janeiro": "JANEIRO.2026", "Fevereiro": "Fevereiro", "Março": "Março",
        "Abril": "Abril", "Maio": "Maio", "Junho": "Junho",
        "Julho": "Julho", "Agosto": "Agosto", "Setembro": "Setembro",
        "Outubro": "OUTUBRO", "Novembro": "NOVEMBRO", "Dezembro": "DEZEMBRO"
    }
    
    # 2. Consolidar todos os pagamentos
    todos_pagamentos = []
    for mes_nome, arq_nome in meses_map.items():
        file_path = f'planilha atualizada 2026.xlsx - {arq_nome}.csv'
        if os.path.exists(file_path):
            try:
                df_mes = pd.read_csv(file_path, skiprows=1)
                df_mes['Mes_Ref'] = mes_nome
                # Limpeza básica de valores
                df_mes['Valor'] = pd.to_numeric(df_mes['Valor'], errors='coerce').fillna(0)
                todos_pagamentos.append(df_mes)
            except:
                continue
    
    df_financeiro = pd.concat(todos_pagamentos, ignore_index=True) if todos_pagamentos else pd.DataFrame()
    return df_alunos, df_financeiro, meses_map

# --- CARREGAMENTO ---
try:
    alunos, financeiro, meses_dict = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar arquivos: {e}")
    st.stop()

# --- SIDEBAR / NAVEGAÇÃO ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2845/2845869.png", width=100)
st.sidebar.title("Menu Financeiro")
aba = st.sidebar.radio("Navegar para:", ["🏠 Início", "📅 Fluxo Mensal", "👥 Alunos & Histórico", "⚠️ Central de Pendências"])

# --- ABA 1: INÍCIO ---
if aba == "🏠 Início":
    st.header("Resumo Geral 2026")
    col1, col2, col3 = st.columns(3)
    
    total_recebido = financeiro[financeiro['Valor'] > 0]['Valor'].sum()
    total_alunos = len(alunos)
    
    col1.metric("Alunos Ativos", total_alunos)
    col2.metric("Total Arrecadado (Ano)", format_currency(total_recebido))
    col3.metric("Polo", "Ubatã - BA")

    st.subheader("➕ Adicionar Novo Aluno")
    with st.expander("Clique para abrir formulário de cadastro"):
        with st.form("novo_aluno"):
            n = st.text_input("Nome do Aluno")
            c = st.text_input("WhatsApp")
            v = st.number_input("Valor Mensalidade", value=200.0)
            ven = st.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
            if st.form_submit_button("Salvar Cadastro"):
                st.success("Aluno cadastrado com sucesso (Simulação)!")

# --- ABA 2: FLUXO MENSAL ---
elif aba == "📅 Fluxo Mensal":
    st.header("Visualização por Mês")
    mes_sel = st.selectbox("Selecione o Mês:", list(meses_dict.keys()))
    
    df_mes = financeiro[financeiro['Mes_Ref'] == mes_sel]
    
    if not df_mes.empty:
        st.dataframe(df_mes[['Data', 'Lançamento', 'FORMA', 'Valor', 'Saldo']], use_container_width=True)
        rec = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
        desp = df_mes[df_mes['Valor'] < 0]['Valor'].sum()
        st.info(f"**Resumo de {mes_sel}:** Receita {format_currency(rec)} | Despesas {format_currency(abs(desp))}")
    else:
        st.warning("Nenhum registro encontrado para este mês.")

# --- ABA 3: ALUNOS & HISTÓRICO ---
elif aba == "👥 Alunos & Histórico":
    st.header("Histórico Individual do Aluno")
    aluno_sel = st.selectbox("Escolha o Aluno:", alunos['Aluno'].unique())
    
    # Filtro de histórico
    primeiro_nome = aluno_sel.split()[0].upper()
    hist_aluno = financeiro[financeiro['Lançamento'].str.upper().str.contains(primeiro_nome, na=False)]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Dados Cadastrais")
        info = alunos[alunos['Aluno'] == aluno_sel].iloc[0]
        st.write(f"**WhatsApp:** {info['Contato']}")
        st.write(f"**Vencimento:** {info['Vencimento']}")
        st.write(f"**Valor base:** {info['Mensalidade']}")
    
    with col2:
        st.markdown("### Pagamentos Realizados")
        if not hist_aluno.empty:
            st.table(hist_aluno[['Data', 'Mes_Ref', 'Valor', 'FORMA']])
        else:
            st.error("Nenhum pagamento registrado no sistema para este aluno.")

# --- ABA 4: CENTRAL DE PENDÊNCIAS ---
elif aba == "⚠️ Central de Pendências":
    st.header("Alunos em Débito")
    
    # Lógica de Pendência
    devedores = []
    mes_atual = "JANEIRO.2026" # Você pode tornar isso dinâmico
    
    for _, row in alunos.iterrows():
        nome = row['Aluno']
        primeiro_n = nome.split()[0].upper()
        
        # Verifica se o nome aparece no financeiro do mês atual
        pago_mes = financeiro[(financeiro['Mes_Ref'] == 'Janeiro') & 
                             (financeiro['Lançamento'].str.upper().str.contains(primeiro_n, na=False))]
        
        if pago_mes.empty:
            # Tenta pegar valor da mensalidade (limpa o 'R$' se houver)
            val_mensal = str(row['Mensalidade']).replace('R$', '').replace(' ', '').replace(',', '.')
            try:
                val_mensal = float(val_mensal)
            except:
                val_mensal = 200.0
                
            devedores.append({"Aluno": nome, "Valor": val_mensal, "Vencimento": row['Vencimento']})

    if devedores:
        df_dev = pd.DataFrame(devedores)
        st.error(f"Total de Pendências: {format_currency(df_dev['Valor'].sum())}")
        
        st.markdown("Clique no aluno para ver o que ele deve:")
        for _, d in df_dev.iterrows():
            with st.expander(f"🔴 {d['Aluno']} - Deve {format_currency(d['Valor'])}"):
                st.write(f"**Vencimento:** {d['Vencimento']}")
                st.write("---")
                st.button(f"Enviar Cobrança WhatsApp para {d['Aluno']}", key=d['Aluno'])
    else:
        st.success("Parabéns! Todos os alunos estão em dia.")

st.sidebar.markdown("---")
st.sidebar.caption("Star Tec Polo Ubatã v1.0")
