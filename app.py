import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import xlsxwriter

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    
    /* Cards Financeiros */
    .card-receita { background-color: #d1f2eb; border: 1px solid #2ecc71; padding: 20px; border-radius: 10px; color: #145a32; text-align: center; }
    .card-despesa { background-color: #fadbd8; border: 1px solid #e74c3c; padding: 20px; border-radius: 10px; color: #7b241c; text-align: center; }
    .card-saldo { background-color: #d6eaf8; border: 1px solid #3498db; padding: 20px; border-radius: 10px; color: #154360; text-align: center; }
    
    /* Notificações */
    .alerta-hoje { background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARREGAMENTO E ESTRUTURA ---
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']
    
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        # Carrega Alunos
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        df_alunos.columns = df_alunos.columns.str.strip()
        df_alunos = df_alunos.dropna(subset=['Aluno'])
        
        # --- DEFINIÇÃO DOS MESES ---
        # 2025 (Mantendo histórico)
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        # 2026 (Ano Completo Padronizado)
        meses_2026 = [
            "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
        ]
        
        financas = {}
        all_months = meses_2025 + meses_2026
        
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names
        
        for m in all_months:
            # Lógica inteligente para encontrar a aba (Ex: "JANEIRO" ou "JANEIRO.2026")
            nome_aba = None
            possiveis = [m, m.upper(), m.capitalize(), f"{m}.2026", f"{m.upper()}.2026"]
            
            for p in possiveis:
                if p in sheet_names:
                    nome_aba = p
                    break
            
            if nome_aba:
                df = pd.read_excel(xls, sheet_name=nome_aba, skiprows=1)
                # Garante colunas essenciais
                for c in ['Data', 'Lançamento', 'Valor', 'FORMA']:
                    if c not in df.columns: df[c] = None
                financas[m] = df
            else:
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])
                
        return df_alunos, financas, meses_2025, meses_2026

    except Exception as e:
        st.error(f"Erro ao carregar sistema: {e}")
        return pd.DataFrame(), {}, [], []

# Inicializa Memória
if 'db_alunos' not in st.session_state:
    a, f, m25, m26 = carregar_tudo()
    st.session_state.db_alunos = a
    st.session_state.db_fin = f
    st.session_state.m25 = m25
    st.session_state.m26 = m26

if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- MENU LATERAL ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Menu Gestão")
    
    pagina = st.radio("Navegar:", ["🔔 Painel do Dia", "💰 Fluxo de Caixa (Despesas)", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    # BOTÃO DE DOWNLOAD (RELATÓRIO PARA COORDENAÇÃO)
    if st.button("📥 BAIXAR RELATÓRIO MENSAL"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Salva Alunos
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            
            # Salva Meses com Totais Calculados
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
                
                # Adiciona Resumo no final da planilha
                workbook = writer.book
                worksheet = writer.sheets[m]
                format_bold = workbook.add_format({'bold': True})
                
                # Calcula totais
                total_entrada = df[df['Valor'] > 0]['Valor'].sum()
                total_saida = df[df['Valor'] < 0]['Valor'].sum()
                saldo = total_entrada + total_saida
                
                row = len(df) + 3
                worksheet.write(row, 1, "TOTAL ENTRADAS:", format_bold)
                worksheet.write(row, 2, total_entrada)
                worksheet.write(row+1, 1, "TOTAL SAÍDAS:", format_bold)
                worksheet.write(row+1, 2, total_saida)
                worksheet.write(row+2, 1, "SALDO FINAL:", format_bold)
                worksheet.write(row+2, 2, saldo)

        st.download_button(label="⬇️ Salvar Planilha Pronta", data=output.getvalue(), file_name="Relatorio_Financeiro_StarTec.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: NOTIFICAÇÕES ---
if pagina == "🔔 Painel do Dia":
    hoje = datetime.now()
    st.header(f"📅 Visão Geral - {hoje.strftime('%d/%m/%Y')}")
    
    dia_atual = hoje.day
    st.subheader("🔔 Cobranças de Hoje")
    
    tem_alerta = False
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            
            if dia_venc == dia_atual:
                st.markdown(f"""
                <div class="alerta-hoje">
                    🔴 <b>VENCE HOJE!</b> {aluno['Aluno']} - R$ {aluno['Mensalidade']}
                </div>""", unsafe_allow_html=True)
                tem_alerta = True
            elif dia_venc == dia_atual + 1:
                st.info(f"⚠️ Vence Amanhã: {aluno['Aluno']}")
                tem_alerta = True
        except: continue
            
    if not tem_alerta: st.success("✅ Tudo tranquilo hoje!")

# --- PÁGINA 2: FLUXO DE CAIXA (NOVA FUNCIONALIDADE) ---
elif pagina == "💰 Fluxo de Caixa (Despesas)":
    st.header("💰 Controle Financeiro do Mês")
    
    # Seletor de Mês
    mes_atual = st.selectbox("Selecione o Mês:", st.session_state.m26)
    
    df_caixa = st.session_state.db_fin[mes_atual]
    
    # CÁLCULOS
    entradas = df_caixa[df_caixa['Valor'] > 0]['Valor'].sum()
    saidas = df_caixa[df_caixa['Valor'] < 0]['Valor'].sum()
    saldo = entradas + saidas
    
    # EXIBIÇÃO DOS CARDS
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-receita"><h3>Entradas</h3>R$ {entradas:,.2f}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-despesa"><h3>Despesas</h3>R$ {saidas:,.2f}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-saldo"><h3>Saldo Final</h3>R$ {saldo:,.2f}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ADICIONAR DESPESA
    with st.expander("🔴 LANÇAR NOVA DESPESA (Gasto)", expanded=True):
        with st.form("form_despesa"):
            col1, col2 = st.columns(2)
            desc_despesa = col1.text_input("Descrição (Ex: Internet, Luz, Material)")
            valor_despesa = col2.number_input("Valor do Gasto R$", min_value=0.0, step=10.0)
            data_despesa = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Registrar Despesa"):
                nova_despesa = {
                    'Data': data_despesa.strftime('%d/%m/%Y'),
                    'Lançamento': f"DESPESA: {desc_despesa}",
                    'Valor': -valor_despesa, # Valor negativo para saída
                    'FORMA': 'CAIXA'
                }
                st.session_state.db_fin[mes_atual] = pd.concat([df_caixa, pd.DataFrame([nova_despesa])], ignore_index=True)
                st.success("Despesa lançada com sucesso!")
                st.rerun()

    # TABELA DE EXTRATO
    st.subheader(f"Extrato Detalhado: {mes_atual}")
    st.dataframe(df_caixa, use_container_width=True)

# --- PÁGINA 3: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Aluno")
    with st.form("cad_novo"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome Completo")
        z = c2.text_input("WhatsApp")
        c3, c4 = st.columns(2)
        v = c3.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c4.number_input("Valor Mensalidade", value=200.0)
        
        if st.form_submit_button("Salvar"):
            novo = {'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m, 'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'), 'Penden. Docum': 'NÃO'}
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno Salvo!")

# --- PÁGINA 4: LISTA DE ALUNOS ---
elif pagina == "👥 Lista de Alunos":
    
    if st.session_state.aluno_selecionado is None:
        st.header("Gerenciar Alunos")
        busca = st.text_input("🔍 Buscar...").upper()
        lista = st.session_state.db_alunos
        if busca: lista = lista[lista['Aluno'].astype(str).str.upper().str.contains(busca)]
            
        for idx, row in lista.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['Aluno']}**")
                c2.text(f"Vencimento: {row['Vencimento']}")
                if c3.button("📂 Abrir Pasta", key=f"b_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()
    else:
        # PASTA DO ALUNO (Igual ao anterior, mantendo a funcionalidade)
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        with st.expander("📝 Editar Dados"):
            with st.form("edit"):
                ec1, ec2 = st.columns(2)
                nv_n = ec1.text_input("Nome", value=dados['Aluno'])
                nv_z = ec2.text_input("Zap", value=dados['Contato'])
                if st.form_submit_button("Salvar"):
                    st.session_state.db_alunos.at[idx, 'Aluno'] = nv_n
                    st.session_state.db_alunos.at[idx, 'Contato'] = nv_z
                    st.session_state.aluno_selecionado = nv_n
                    st.rerun()

        st.subheader("💳 Calendário 2026")
        tab25, tab26 = st.tabs(["Histórico 2025", "ANO 2026"])

        def mostrar_meses(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                primeiro_nome = str(st.session_state.aluno_selecionado).split()[0]
                pg = df_mes[df_mes['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
                
                c_mes, c_card = st.columns([1, 4])
                c_mes.markdown(f"### {mes}")
                
                with c_card:
                    if not pg.empty:
                        st.success(f"✅ PAGO: R$ {pg.iloc[0]['Valor']}")
                        if st.button("Desfazer", key=f"d_{mes}"):
                            st.session_state.db_fin[mes] = df_mes.drop(pg.index)
                            st.rerun()
                    else:
                        st.error("❌ EM ABERTO")
                        with st.popover("Pagar"):
                            val = st.number_input("Valor", value=200.0, key=f"v{mes}")
                            if st.button("Confirmar", key=f"ok{mes}"):
                                novo = {'Data': datetime.now().strftime('%d/%m/%Y'), 'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}", 'Valor': val, 'FORMA': 'PIX'}
                                st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo])], ignore_index=True)
                                st.rerun()
                st.divider()

        with tab25: mostrar_meses(st.session_state.m25)
        with tab26: mostrar_meses(st.session_state.m26)
