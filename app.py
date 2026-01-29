import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(page_title="Financeiro Star Tec Ubatã", layout="wide", page_icon="💰")

# Nome do seu arquivo Excel no GitHub
NOME_ARQUIVO = "planilha atualizada 2026.xlsx"

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data
def carregar_dados():
    # Carregar Alunos (Aba 'Alunos')
    df_alunos = pd.read_excel(NOME_ARQUIVO, sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos[['Aluno', 'Contato', 'Mensalidade', 'Vencimento']].dropna(subset=['Aluno'])
    
    # Mapeamento das abas de meses
    abas_meses = [
        "JANEIRO.2026", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
    ]
    
    dados_mensais = {}
    for aba in abas_meses:
        try:
            df = pd.read_excel(NOME_ARQUIVO, sheet_name=aba, skiprows=1)
            # Limpar coluna de Valor (remover R$, converter para número)
            if 'Valor' in df.columns:
                df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').fillna(0)
            dados_mensais[aba] = df
        except:
            continue # Se a aba não existir ainda, ele pula
            
    return df_alunos, dados_mensais

# Inicialização do App
if not os.path.exists(NOME_ARQUIVO):
    st.error(f"Arquivo '{NOME_ARQUIVO}' não encontrado no GitHub. Verifique o nome!")
    st.stop()

df_alunos, dic_meses = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.title("💎 Star Tec Financeiro")
menu = st.sidebar.radio("Navegar para:", [
    "🏠 Início / Cadastro", 
    "📅 Lançamentos Mensais", 
    "📜 Histórico por Aluno", 
    "⚠️ Central de Pendências"
])

# --- ABA 1: INÍCIO E CADASTRO ---
if menu == "🏠 Início / Cadastro":
    st.header("Gestão de Alunos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Alunos Ativos")
        st.dataframe(df_alunos, use_container_width=True)
    
    with col2:
        st.subheader("➕ Novo Aluno")
        with st.form("novo_aluno"):
            nome = st.text_input("Nome Completo")
            zap = st.text_input("WhatsApp")
            mensal = st.text_input("Valor Mensalidade (ex: 200)")
            venc = st.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
            if st.form_submit_button("Pré-Cadastrar"):
                st.success(f"Aluno {nome} pronto para ser adicionado à planilha!")
                st.info("Dica: Adicione-o na aba 'Alunos' do seu Excel e suba o arquivo novamente.")

# --- ABA 2: LANÇAMENTOS MENSAIS ---
elif menu == "📅 Lançamentos Mensais":
    st.header("Consulta de Pagamentos por Mês")
    mes_sel = st.selectbox("Selecione o Mês:", list(dic_meses.keys()))
    
    df_mes = dic_meses[mes_sel]
    if not df_mes.empty:
        st.dataframe(df_mes[['Data', 'Lançamento', 'FORMA', 'Valor', 'Saldo']].dropna(subset=['Lançamento']), use_container_width=True)
        receita = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
        st.metric(f"Total Recebido em {mes_sel}", f"R$ {receita:,.2f}")
    else:
        st.warning("Sem dados para este mês.")

# --- ABA 3: HISTÓRICO POR ALUNO ---
elif menu == "📜 Histórico por Aluno":
    st.header("Busca de Histórico Individual")
    aluno_h = st.selectbox("Escolha o Aluno:", df_alunos['Aluno'].unique())
    
    historico_total = []
    # Busca o aluno em todas as abas de meses
    for mes, df in dic_meses.items():
        # Busca aproximada pelo primeiro nome para evitar erros de digitação
        primeiro_nome = aluno_h.split()[0].upper()
        match = df[df['Lançamento'].astype(str).str.upper().str.contains(primeiro_nome, na=False)]
        
        for _, row in match.iterrows():
            historico_total.append({
                "Mês": mes,
                "Data": row['Data'],
                "Descrição": row['Lançamento'],
                "Valor": row['Valor'],
                "Forma": row.get('FORMA', '-')
            })
            
    if historico_total:
        df_h = pd.DataFrame(historico_total)
        st.table(df_h)
        st.metric("Total Pago pelo Aluno", f"R$ {df_h['Valor'].sum():,.2f}")
    else:
        st.error("Nenhum pagamento registrado para este aluno.")

# --- ABA 4: CENTRAL DE PENDÊNCIAS ---
elif menu == "⚠️ Central de Pendências":
    st.header("Alunos Inadimplentes")
    mes_analise = st.selectbox("Verificar quem não pagou em:", list(dic_meses.keys()))
    
    df_mes = dic_meses[mes_analise]
    devedores = []
    
    for _, aluno in df_alunos.iterrows():
        nome_curto = aluno['Aluno'].split()[0].upper()
        # Se o nome não aparece nos lançamentos do mês, está devendo
        pagou = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(nome_curto, na=False)]
        
        if pagou.empty:
            devedores.append({
                "Aluno": aluno['Aluno'],
                "WhatsApp": aluno['Contato'],
                "Vencimento": aluno['Vencimento'],
                "Valor": aluno['Mensalidade']
            })
            
    if devedores:
        df_dev = pd.DataFrame(devedores)
        st.error(f"Encontrados {len(devedores)} alunos pendentes em {mes_analise}")
        st.dataframe(df_dev, use_container_width=True)
    else:
        st.success("Todos os alunos pagaram este mês!")
st.sidebar.markdown("---")
st.sidebar.caption("Star Tec Polo Ubatã v1.0")
