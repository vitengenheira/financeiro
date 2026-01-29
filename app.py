import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

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
    # Definição das colunas padrão
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']
    
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
    # Garante que todas as colunas existem
    for col in cols_alunos:
        if col not in df_alunos.columns:
            df_alunos[col] = None
    df_alunos = df_alunos.dropna(subset=['Aluno'])
    
    meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    meses_2026 = ["JANEIRO.2026", "Fevereiro_26", "Março_26", "Abril_26", "Maio_26", "Junho_26"] 
    
    financas = {}
    all_months = meses_2025 + meses_2026
    for m in all_months:
        try:
            financas[m] = pd.read_excel(file, sheet_name=m, skiprows=1)
        except: 
            financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])
            
    return df_alunos, financas, meses_2025, meses_2026

# Inicialização da Memória
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
    
    pagina = st.radio("Ir para:", ["🔔 Início e Lembretes", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    st.write("📥 **Salvar Alterações**")
    
    # Botão para baixar Excel atualizado (Salvar Trabalho)
    if st.button("Gerar Planilha para Download"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
        st.download_button(label="⬇️ Baixar Arquivo Atualizado", data=output.getvalue(), file_name="Financeiro_StarTec_Atualizado.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: INÍCIO ---
if pagina == "🔔 Início e Lembretes":
    st.header(f"Bom dia! Hoje é dia {datetime.now().day}/{datetime.now().month}")
    
    dia_hoje = datetime.now().day
    alertas = []
    
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            dia_venc = int(str(aluno['Vencimento']).upper().replace('DIA', '').strip())
            if dia_venc == dia_hoje:
                alertas.append(f"🔴 HOJE: {aluno['Aluno']} (Vencimento dia {dia_venc})")
            elif dia_venc == dia_hoje + 1:
                alertas.append(f"⚠️ AMANHÃ: {aluno['Aluno']} (Vencimento dia {dia_venc})")
        except: continue

    if alertas:
        st.markdown('<div class="lembrete-card"><h4>📅 Alertas de Vencimento</h4></div>', unsafe_allow_html=True)
        for a in alertas: st.write(a)
    else:
        st.success("Nenhum vencimento previsto para hoje!")

# --- PÁGINA 2: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Estudante")
    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome Completo")
        contato = c2.text_input("WhatsApp")
        c3, c4 = st.columns(2)
        venc = c3.selectbox("Dia Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        mensalidade = c4.number_input("Valor Mensalidade", value=200.0)
        
        if st.form_submit_button("✅ Salvar Novo Aluno"):
            novo = {'Aluno': nome, 'Contato': contato, 'Vencimento': venc, 'Mensalidade': mensalidade, 'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'), 'Penden. Docum': 'NÃO'}
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Cadastrado com sucesso!")

# --- PÁGINA 3: LISTA E FICHA (COM EDIÇÃO) ---
elif pagina == "👥 Lista de Alunos":
    
    if st.session_state.aluno_selecionado is None:
        st.header("Gerenciar Alunos")
        busca = st.text_input("🔍 Buscar aluno...").upper()
        lista = st.session_state.db_alunos
        if busca: lista = lista[lista['Aluno'].astype(str).str.upper().str.contains(busca)]
            
        for idx, row in lista.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['Aluno']}**")
                c2.text(f"📞 {row['Contato']}")
                if c3.button("📂 Abrir Pasta", key=f"btn_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()
    
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar para Lista"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        # Pega o índice do aluno para edição
        idx_aluno = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx_aluno]
        
        st.header(f"Pasta do Aluno: {dados['Aluno']}")

        # --- SEÇÃO DE DADOS (VISUALIZAÇÃO + EDIÇÃO) ---
        with st.expander("📝 Dados Pessoais e Matrícula (Clique para Editar)", expanded=False):
            with st.form("editar_dados"):
                ec1, ec2 = st.columns(2)
                novo_nome = ec1.text_input("Nome", value=dados['Aluno'])
                novo_contato = ec2.text_input("WhatsApp", value=dados['Contato'])
                
                ec3, ec4 = st.columns(2)
                # Tenta encontrar o index do vencimento atual, se não, usa padrão
                opcoes_venc = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                venc_atual = dados['Vencimento'] if dados['Vencimento'] in opcoes_venc else "DIA 15"
                novo_venc = ec3.selectbox("Vencimento", opcoes_venc, index=opcoes_venc.index(venc_atual))
                
                nova_mensalidade = ec4.number_input("Mensalidade (R$)", value=float(dados['Mensalidade']) if pd.notnull(dados['Mensalidade']) else 200.0)
                
                ec5, ec6 = st.columns(2)
                novo_bolsista = ec5.selectbox("Bolsista?", ["NÃO", "SIM"], index=0 if str(dados.get('Bolsita','')).upper() != 'SIM' else 1)
                
                obs_doc = ec6.text_input("Documento Pendente?", value=dados.get('Qual Documento?', ''))
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    st.session_state.db_alunos.at[idx_aluno, 'Aluno'] = novo_nome
                    st.session_state.db_alunos.at[idx_aluno, 'Contato'] = novo_contato
                    st.session_state.db_alunos.at[idx_aluno, 'Vencimento'] = novo_venc
                    st.session_state.db_alunos.at[idx_aluno, 'Mensalidade'] = nova_mensalidade
                    st.session_state.db_alunos.at[idx_aluno, 'Bolsita'] = novo_bolsista
                    st.session_state.db_alunos.at[idx_aluno, 'Qual Documento?'] = obs_doc
                    st.session_state.db_alunos.at[idx_aluno, 'Penden. Docum'] = "SIM" if obs_doc else "NÃO"
                    
                    # Se mudou o nome, atualiza a variável de seleção para não quebrar a tela
                    st.session_state.aluno_selecionado = novo_nome
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()

        # Exibição Rápida dos Dados (Para leitura sem abrir o form)
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Vencimento:** {dados['Vencimento']}")
        c2.write(f"**Mensalidade:** R$ {dados['Mensalidade']}")
        c3.warning(f"**Doc:** {dados['Qual Documento?']}") if dados.get('Qual Documento?') else c3.success("**Doc:** OK")

        st.markdown("---")
        st.subheader("💳 Histórico Financeiro")

        tab25, tab26 = st.tabs(["📅 2025", "📅 2026"])

        def renderizar_financeiro(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                # Busca flexível pelo primeiro nome para não falhar
                nome_busca = st.session_state.aluno_selecionado.split()[0]
                pagamento = df_mes[df_mes['Lançamento'].astype(str).str.upper().str.contains(nome_busca.upper(), na=False)]
                
                col_mes, col_status, col_acao = st.columns([1, 2, 1])
                col_mes.markdown(f"### {mes}")
                
                if not pagamento.empty:
                    info = pagamento.iloc[0]
                    col_status.markdown(f"""<div class="pago-card">✅ <b>PAGO</b> | R$ {info.get('Valor', 0)}</div>""", unsafe_allow_html=True)
                    if col_acao.button("Desfazer", key=f"del_{mes}"):
                        st.session_state.db_fin[mes] = df_mes[~df_mes['Lançamento'].astype(str).str.upper().str.contains(nome_busca.upper())]
                        st.rerun()
                else:
                    col_status.markdown(f"""<div class="devendo-card">❌ <b>PENDENTE</b></div>""", unsafe_allow_html=True)
                    with col_acao.popover("💰 Pagar"):
                        val = st.number_input("Valor", value=float(dados['Mensalidade']), key=f"v_{mes}")
                        dt = st.date_input("Data", key=f"d_{mes}")
                        fm = st.selectbox("Forma", ["PIX", "Dinheiro"], key=f"f_{mes}")
                        if st.button("Confirmar", key=f"c_{mes}"):
                            nova = {'Data': dt.strftime('%Y-%m-%d'), 'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}", 'Valor': val, 'FORMA': fm}
                            st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([nova])], ignore_index=True)
                            st.rerun()
                st.divider()

        with tab25: renderizar_financeiro(st.session_state.m25)
        with tab26: renderizar_financeiro(st.session_state.m26)
