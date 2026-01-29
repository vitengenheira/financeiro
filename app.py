import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; }
    .lembrete-card { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
    .pago-card { background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; color: #155724; }
    .devendo-card { background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DE DADOS
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    if not os.path.exists(file):
        # Cria dataframes vazios se não existir arquivo ainda
        return pd.DataFrame(columns=['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']), {}, [], []

    df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    meses_2026 = ["JANEIRO.2026", "Fevereiro_26", "Março_26"] # Adicione meses futuros aqui
    
    financas = {}
    # Tenta carregar as abas, se não existir, cria vazia
    all_months = meses_2025 + meses_2026
    for m in all_months:
        try:
            financas[m] = pd.read_excel(file, sheet_name=m, skiprows=1)
        except: 
            financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])
            
    return df_alunos, financas, meses_2025, meses_2026

# Inicialização da Memória (Session State)
if 'db_alunos' not in st.session_state:
    a, f, m25, m26 = carregar_tudo()
    st.session_state.db_alunos = a
    st.session_state.db_fin = f
    st.session_state.m25 = m25
    st.session_state.m26 = m26

if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Menu Principal")
    
    # Navegação
    pagina = st.radio("Ir para:", ["🔔 Início e Lembretes", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    if st.button("💾 Exportar Dados (Salvar)"):
        # Lógica simulada de exportação
        st.success("Para salvar definitivo, lembre de baixar a planilha se estiver usando localmente!")

# --- PÁGINA 1: INÍCIO E LEMBRETES ---
if pagina == "🔔 Início e Lembretes":
    st.header(f"Bom dia! Hoje é dia {datetime.now().day}/{datetime.now().month}")
    
    # Lógica de Lembrete: Vencimento hoje ou próximo
    dia_hoje = datetime.now().day
    alertas = []
    
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            # Extrai o número do texto "DIA 15"
            dia_venc = int(str(aluno['Vencimento']).upper().replace('DIA', '').strip())
            
            # Se vence hoje ou amanhã
            if dia_venc == dia_hoje:
                alertas.append(f"🔴 HOJE: {aluno['Aluno']} (Vencimento dia {dia_venc})")
            elif dia_venc == dia_hoje + 1:
                alertas.append(f"⚠️ AMANHÃ: {aluno['Aluno']} (Vencimento dia {dia_venc})")
        except:
            continue

    if alertas:
        st.markdown('<div class="lembrete-card"><h4>📅 Alertas de Vencimento</h4></div>', unsafe_allow_html=True)
        for a in alertas:
            st.write(a)
            st.divider()
    else:
        st.success("Nenhum vencimento previsto para hoje!")

    # Resumo Rápido
    st.markdown("### Resumo do Polo")
    c1, c2 = st.columns(2)
    c1.metric("Total de Alunos", len(st.session_state.db_alunos))
    # Exemplo de cálculo simples de receita do mês atual (Janeiro 26)
    mes_atual = "JANEIRO.2026"
    if mes_atual in st.session_state.db_fin:
        total = st.session_state.db_fin[mes_atual]['Valor'].sum()
        c2.metric(f"Receita {mes_atual}", f"R$ {total:,.2f}")

# --- PÁGINA 2: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Estudante")
    
    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        contato = col2.text_input("WhatsApp")
        
        col3, col4 = st.columns(2)
        venc = col3.selectbox("Dia Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        mensalidade = col4.number_input("Valor Mensalidade", value=200.0)
        
        matricula_val = col1.number_input("Valor Matrícula", value=80.0)
        data_mat = col2.date_input("Data Matrícula", datetime.now())
        
        obs = st.text_area("Observações (Documentos pendentes, etc)")
        
        if st.form_submit_button("✅ Salvar Novo Aluno"):
            novo_aluno = {
                'Aluno': nome, 'Contato': contato, 'Vencimento': venc, 
                'Mensalidade': mensalidade, 'Valor Matricula': matricula_val,
                'Data da Matricula ': data_mat.strftime('%d/%m/%Y'),
                'Penden. Docum': 'SIM' if obs else 'NÃO',
                'Qual Documento?': obs
            }
            # Adiciona ao DataFrame
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo_aluno])], ignore_index=True)
            st.success(f"{nome} cadastrado com sucesso! Vá para a Lista de Alunos para ver a ficha.")

# --- PÁGINA 3: LISTA E FICHA DO ALUNO ---
elif pagina == "👥 Lista de Alunos":
    
    # Se nenhum aluno selecionado, mostra a lista
    if st.session_state.aluno_selecionado is None:
        st.header("Gerenciar Alunos")
        busca = st.text_input("🔍 Buscar aluno...").upper()
        
        lista = st.session_state.db_alunos
        if busca:
            lista = lista[lista['Aluno'].astype(str).str.upper().str.contains(busca)]
            
        for idx, row in lista.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['Aluno']}**")
                c2.text(f"📞 {row['Contato']}")
                if c3.button("📂 Abrir Pasta", key=f"btn_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()
    
    # Se aluno selecionado, mostra a PASTA COMPLETA
    else:
        nome_aluno = st.session_state.aluno_selecionado
        
        # Botão de voltar
        if st.button("⬅️ Voltar para Lista"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        st.header(f"Pasta do Aluno: {nome_aluno}")
        
        # Pega dados do aluno
        try:
            dados = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].iloc[0]
        except:
            st.error("Erro ao carregar dados. Volte para a lista.")
            st.stop()

        # --- DADOS CADASTRAIS ---
        with st.expander("📝 Dados Pessoais e Matrícula", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Matrícula:** {dados['Data da Matricula ']}")
            c1.write(f"**Vencimento:** {dados['Vencimento']}")
            c2.write(f"**Mensalidade:** R$ {dados['Mensalidade']}")
            c2.write(f"**Bolsista:** {dados.get('Bolsita', 'Não')}")
            c3.write(f"**Doc Pendente:** {dados['Penden. Docum']}")
            if str(dados['Penden. Docum']).upper() == 'SIM':
                st.warning(f"Falta: {dados['Qual Documento?']}")

        st.markdown("---")
        st.subheader("💳 Histórico e Controle Financeiro")

        tab25, tab26 = st.tabs(["📅 2025", "📅 2026"])

        # Lógica para exibir os meses (reutilizável)
        def renderizar_meses(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                # Verifica pagamento
                pagamento = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(nome_aluno.split()[0].upper(), na=False)]
                
                col_mes, col_status, col_acao = st.columns([1, 2, 1])
                col_mes.markdown(f"### {mes}")
                
                if not pagamento.empty:
                    # ESTÁ PAGO
                    info = pagamento.iloc[0]
                    col_status.markdown(f"""
                        <div class="pago-card">
                        ✅ <b>PAGO</b><br>
                        Data: {info.get('Data', '-')}<br>
                        Valor: R$ {info.get('Valor', 0)}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if col_acao.button("🗑️ Remover", key=f"del_{mes}_{nome_aluno}"):
                        # Remove a linha
                        st.session_state.db_fin[mes] = df_mes[~df_mes['Lançamento'].astype(str).str.upper().str.contains(nome_aluno.split()[0].upper())]
                        st.rerun()
                else:
                    # ESTÁ DEVENDO
                    col_status.markdown(f"""
                        <div class="devendo-card">
                        ❌ <b>PENDENTE</b><br>
                        Vencimento: {dados['Vencimento']}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_acao.popover("💰 Pagar"):
                        st.write(f"Baixa em {mes}")
                        val_pag = st.number_input("Valor", value=200.0, key=f"val_{mes}")
                        data_pag = st.date_input("Data Pagamento", key=f"dt_{mes}")
                        forma = st.selectbox("Forma", ["PIX", "Dinheiro", "Cartão"], key=f"fm_{mes}")
                        
                        if st.button("Confirmar", key=f"conf_{mes}"):
                            nova_linha = {
                                'Data': data_pag.strftime('%Y-%m-%d'),
                                'Lançamento': f"Mensalidade {nome_aluno}",
                                'Valor': val_pag,
                                'FORMA': forma
                            }
                            st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([nova_linha])], ignore_index=True)
                            st.rerun()
                st.divider()

        with tab25:
            renderizar_meses(st.session_state.m25)
            
        with tab26:
            renderizar_meses(st.session_state.m26)
