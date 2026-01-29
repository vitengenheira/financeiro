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
    
    /* Cards Financeiros Modernos */
    .card-receita { background-color: #d1f2eb; border: 1px solid #2ecc71; padding: 20px; border-radius: 10px; color: #145a32; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .card-despesa { background-color: #fadbd8; border: 1px solid #e74c3c; padding: 20px; border-radius: 10px; color: #7b241c; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .card-saldo { background-color: #d6eaf8; border: 1px solid #3498db; padding: 20px; border-radius: 10px; color: #154360; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    
    /* Status e Alertas */
    .pago-texto { color: #27ae60; font-weight: bold; background-color: #eafaf1; padding: 4px 8px; border-radius: 5px; border: 1px solid #27ae60; display: inline-block; }
    .pendente-texto { color: #c0392b; font-weight: bold; background-color: #fdedec; padding: 4px 8px; border-radius: 5px; border: 1px solid #c0392b; display: inline-block; }
    .alerta-hoje { background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÃO DE CARREGAMENTO ---
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    cols_alunos = [
        'Aluno', 'Contato', 'Vencimento', 'Mensalidade', 
        'Data da Matricula ', 'Valor Matricula',
        'Bolsista', 'Pendente Doc', 'Qual Documento?', 
        'Data Ultimo Pagamento'
    ]
    
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        df_alunos.columns = df_alunos.columns.str.strip()
        df_alunos = df_alunos.dropna(subset=['Aluno'])
        
        for col in cols_alunos:
            if col not in df_alunos.columns: df_alunos[col] = None
        
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        meses_2026 = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        financas = {}
        all_months = meses_2025 + meses_2026
        
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names
        
        for m in all_months:
            nome_aba = None
            possiveis = [m, m.upper(), m.capitalize(), f"{m}.2026", f"{m.upper()}.2026", f"{m}_26"]
            for p in possiveis:
                if p in sheet_names:
                    nome_aba = p
                    break
            
            if nome_aba:
                df = pd.read_excel(xls, sheet_name=nome_aba, skiprows=1)
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
    
    pagina = st.radio("Navegar:", 
                      ["🔔 Painel do Dia", "💰 Fluxo de Caixa (Despesas)", "👥 Lista de Alunos", "➕ Novo Aluno"],
                      key="navegacao")
    
    st.markdown("---")
    if st.button("📥 BAIXAR RELATÓRIO MENSAL"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
                
                workbook = writer.book
                worksheet = writer.sheets[m]
                fmt = workbook.add_format({'bold': True})
                
                total_in = df[df['Valor'] > 0]['Valor'].sum()
                total_out = df[df['Valor'] < 0]['Valor'].sum()
                
                row = len(df) + 3
                worksheet.write(row, 1, "TOTAL ENTRADAS:", fmt)
                worksheet.write(row, 2, total_in)
                worksheet.write(row+1, 1, "TOTAL SAÍDAS:", fmt)
                worksheet.write(row+1, 2, total_out)
                worksheet.write(row+2, 1, "SALDO FINAL:", fmt)
                worksheet.write(row+2, 2, total_in + total_out)

        st.download_button(label="⬇️ Salvar Planilha Pronta", data=output.getvalue(), file_name="Relatorio_StarTec_2026.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: PAINEL DO DIA ---
if pagina == "🔔 Painel do Dia":
    hoje = datetime.now()
    st.header(f"📅 Visão Geral - {hoje.strftime('%d/%m/%Y')}")
    
    st.subheader("🔔 Vencimentos de Hoje")
    dia_atual = hoje.day
    tem_alerta = False
    
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            if dia_venc == dia_atual:
                st.markdown(f'<div class="alerta-hoje">🔴 <b>VENCE HOJE!</b> {aluno["Aluno"]}</div>', unsafe_allow_html=True)
                tem_alerta = True
            elif dia_venc == dia_atual + 1:
                st.info(f"⚠️ Vence Amanhã: {aluno['Aluno']}")
                tem_alerta = True
        except: continue
    
    if not tem_alerta: st.success("✅ Nenhum vencimento urgente hoje.")

    st.markdown("---")
    
    idx_mes = hoje.month - 1
    meses_oficiais = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    nome_mes_atual = meses_oficiais[idx_mes]
    
    st.subheader(f"⚠️ Pendências em {nome_mes_atual}")
    
    if nome_mes_atual in st.session_state.db_fin:
        df_mes_atual = st.session_state.db_fin[nome_mes_atual]
        pendentes_count = 0
        
        for idx, row in st.session_state.db_alunos.iterrows():
            nome_aluno = row['Aluno']
            primeiro_nome = str(nome_aluno).split()[0]
            
            pagou = df_mes_atual[df_mes_atual['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
            
            if pagou.empty:
                pendentes_count += 1
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 2])
                    c1.markdown(f"🔴 **{nome_aluno}**")
                    c2.text(f"Dia: {row['Vencimento']}")
                    if c3.button("Cobrar / Abrir Pasta", key=f"cobrar_{idx}"):
                        st.session_state.aluno_selecionado = nome_aluno
                        st.session_state.navegacao = "👥 Lista de Alunos"
                        st.rerun()
        if pendentes_count == 0: st.success(f"Tudo pago em {nome_mes_atual}!")
    else: st.warning(f"Mês {nome_mes_atual} ainda não iniciado.")

# --- PÁGINA 2: FLUXO DE CAIXA (NOVA TABELA) ---
elif pagina == "💰 Fluxo de Caixa (Despesas)":
    st.header("💰 Controle Financeiro do Mês")
    mes_atual = st.selectbox("Selecione o Mês:", st.session_state.m26)
    df_caixa = st.session_state.db_fin[mes_atual]
    
    entradas = df_caixa[df_caixa['Valor'] > 0]['Valor'].sum()
    saidas = df_caixa[df_caixa['Valor'] < 0]['Valor'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-receita"><h3>Entradas</h3>R$ {entradas:,.2f}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-despesa"><h3>Despesas</h3>R$ {saidas:,.2f}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-saldo"><h3>Saldo</h3>R$ {entradas+saidas:,.2f}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- ÁREA DE LANÇAMENTO ---
    col_lancar, col_vazia = st.columns([1, 1])
    with col_lancar:
        with st.expander("➕ Adicionar Gasto / Despesa", expanded=False):
            with st.form("desp"):
                desc = st.text_input("Descrição (Ex: Luz, Internet, Material)")
                val = st.number_input("Valor do Gasto (R$)", min_value=0.0, step=10.0)
                dt_gasto = st.date_input("Data", datetime.now())
                
                if st.form_submit_button("🔴 Registrar Saída"):
                    novo = {
                        'Data': dt_gasto.strftime('%d/%m/%Y'), 
                        'Lançamento': f"DESPESA: {desc}", 
                        'Valor': -val, 
                        'FORMA': 'CAIXA'
                    }
                    st.session_state.db_fin[mes_atual] = pd.concat([df_caixa, pd.DataFrame([novo])], ignore_index=True)
                    st.success("Despesa registrada!")
                    st.rerun()

    # --- TABELA BONITA ---
    st.subheader(f"Extrato: {mes_atual}")
    
    # Preparar dados para ficar bonito
    df_exibir = df_caixa.copy()
    if not df_exibir.empty:
        # Cria coluna de Tipo para o ícone
        df_exibir['Tipo'] = df_exibir['Valor'].apply(lambda x: '🟢 Receita' if x > 0 else '🔴 Despesa')
        # Converte data para formato data real para ordenar
        df_exibir['Data'] = pd.to_datetime(df_exibir['Data'], dayfirst=True, errors='coerce')
        # Seleciona ordem
        df_exibir = df_exibir[['Data', 'Tipo', 'Lançamento', 'FORMA', 'Valor']]
        
        st.dataframe(
            df_exibir,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Tipo": st.column_config.TextColumn("Categoria", width="small"),
                "Lançamento": st.column_config.TextColumn("Descrição", width="large"),
                "FORMA": st.column_config.TextColumn("Forma", width="small"),
                "Valor": st.column_config.NumberColumn(
                    "Valor (R$)",
                    format="R$ %.2f"
                )
            }
        )
    else:
        st.info("Nenhum lançamento neste mês.")

# --- PÁGINA 3: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Novo Cadastro")
    with st.form("cad"):
        n = st.text_input("Nome")
        z = st.text_input("WhatsApp")
        
        c1, c2 = st.columns(2)
        v = c1.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c2.number_input("Valor Mensalidade", value=200.0)
        
        c3, c4 = st.columns(2)
        vm = c3.number_input("Valor Matrícula", value=50.0)
        dm = c4.text_input("Data Matrícula", value=datetime.now().strftime('%d/%m/%Y'))
        
        if st.form_submit_button("Salvar"):
            novo = {
                'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m, 
                'Data da Matricula ': dm, 'Valor Matricula': vm,
                'Pendente Doc': 'NÃO', 'Bolsista': 'NÃO'
            }
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
                c2.text(row['Vencimento'])
                if c3.button("📂 Abrir Pasta", key=f"b_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        with st.expander("📝 Editar Dados do Aluno", expanded=True):
            with st.form("edit_completo"):
                st.subheader("Dados Pessoais")
                c_a, c_b = st.columns(2)
                novo_nome = c_a.text_input("Nome", value=dados['Aluno'])
                novo_contato = c_b.text_input("Zap", value=dados['Contato'])
                
                c_c, c_d = st.columns(2)
                ops_venc = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                idx_v = ops_venc.index(dados['Vencimento']) if dados['Vencimento'] in ops_venc else 2
                novo_venc = c_c.selectbox("Vencimento", ops_venc, index=idx_v)
                
                try: val_men = float(dados['Mensalidade'])
                except: val_men = 200.0
                novo_mensal = c_d.number_input("Mensalidade", value=val_men)
                
                st.subheader("Acadêmico")
                c_e, c_f = st.columns(2)
                novo_data_mat = c_e.text_input("Data Matrícula", value=dados.get('Data da Matricula ', ''))
                novo_val_mat = c_f.number_input("Valor Matrícula", value=float(dados.get('Valor Matricula', 0) or 0))
                
                c_g, c_h, c_i = st.columns(3)
                idx_doc = 0 if dados.get('Pendente Doc') != 'SIM' else 1
                novo_pend = c_g.selectbox("Doc Pendente?", ["NÃO", "SIM"], index=idx_doc)
                novo_qual = c_h.text_input("Qual Doc?", value=dados.get('Qual Documento?', ''))
                
                ops_bolsa = ["NÃO", "SIM", "MEIA BOLSISTA"]
                idx_bolsa = ops_bolsa.index(dados.get('Bolsista', 'NÃO')) if dados.get('Bolsista', 'NÃO') in ops_bolsa else 0
                novo_bolsa = c_i.selectbox("Bolsista?", ops_bolsa, index=idx_bolsa)
                
                novo_pag = st.text_input("Último Pagamento (Data)", value=dados.get('Data Ultimo Pagamento', ''))

                if st.form_submit_button("💾 Salvar Alterações"):
                    st.session_state.db_alunos.at[idx, 'Aluno'] = novo_nome
                    st.session_state.db_alunos.at[idx, 'Contato'] = novo_contato
                    st.session_state.db_alunos.at[idx, 'Vencimento'] = novo_venc
                    st.session_state.db_alunos.at[idx, 'Mensalidade'] = novo_mensal
                    st.session_state.db_alunos.at[idx, 'Data da Matricula '] = novo_data_mat
                    st.session_state.db_alunos.at[idx, 'Valor Matricula'] = novo_val_mat
                    st.session_state.db_alunos.at[idx, 'Pendente Doc'] = novo_pend
                    st.session_state.db_alunos.at[idx, 'Qual Documento?'] = novo_qual
                    st.session_state.db_alunos.at[idx, 'Bolsista'] = novo_bolsa
                    st.session_state.db_alunos.at[idx, 'Data Ultimo Pagamento'] = novo_pag
                    
                    st.session_state.aluno_selecionado = novo_nome
                    st.success("Atualizado!")
                    st.rerun()

        st.subheader("💳 Calendário Financeiro")
        tab25, tab26 = st.tabs(["Histórico 2025", "ANO 2026"])

        # --- FUNÇÃO DE GRADE COM CORREÇÃO DE DUPLICIDADE ---
        def render_grade(lista_meses, ano_ref):
            cols = st.columns(4)
            for i, mes in enumerate(lista_meses):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"### {mes}")
                        df = st.session_state.db_fin[mes]
                        p_nome = str(st.session_state.aluno_selecionado).split()[0]
                        pg = df[df['Lançamento'].astype(str).str.contains(p_nome, case=False, na=False)]
                        
                        # SUFIXO ÚNICO PARA CADA BOTÃO
                        uid = f"{mes}_{ano_ref}"
                        
                        if not pg.empty:
                            v = pg.iloc[0]['Valor']
                            st.markdown(f'<div class="pago-texto">✅ PAGO<br>R$ {v}</div>', unsafe_allow_html=True)
                            if st.button("Desfazer", key=f"d_{uid}"):
                                st.session_state.db_fin[mes] = df.drop(pg.index)
                                st.rerun()
                        else:
                            st.markdown('<div class="pendente-texto">❌ ABERTO</div>', unsafe_allow_html=True)
                            st.caption(f"Vence: {dados['Vencimento']}")
                            with st.popover("Pagar"):
                                val = st.number_input("R$", value=val_men, key=f"v_{uid}")
                                if st.button("Confirmar", key=f"ok_{uid}"):
                                    novo = {'Data': datetime.now().strftime('%d/%m/%Y'), 'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}", 'Valor': val, 'FORMA': 'PIX'}
                                    st.session_state.db_fin[mes] = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
                                    st.rerun()
                        st.write("")

        with tab25: render_grade(st.session_state.m25, "25")
        with tab26: render_grade(st.session_state.m26, "26")
