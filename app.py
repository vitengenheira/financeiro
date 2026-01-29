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
    
    /* Cards */
    .card-receita { background-color: #d1f2eb; border: 1px solid #2ecc71; padding: 20px; border-radius: 10px; color: #145a32; text-align: center; }
    .card-despesa { background-color: #fadbd8; border: 1px solid #e74c3c; padding: 20px; border-radius: 10px; color: #7b241c; text-align: center; }
    .card-saldo { background-color: #d6eaf8; border: 1px solid #3498db; padding: 20px; border-radius: 10px; color: #154360; text-align: center; }
    
    .alerta-hoje { background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin-bottom: 10px; }
    .recibo-card { background-color: #d1f2eb; border: 1px solid #2ecc71; padding: 15px; border-radius: 8px; color: #117864; margin-bottom: 10px; }
    .cobranca-card { background-color: #fadbd8; border: 1px solid #e74c3c; padding: 15px; border-radius: 8px; color: #943126; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÃO DE CARREGAMENTO ---
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    
    # NOVAS COLUNAS ADICIONADAS AQUI
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
        
        # Garante que todas as colunas novas existam no DataFrame
        for col in cols_alunos:
            if col not in df_alunos.columns:
                df_alunos[col] = None
        
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        meses_2026 = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        financas = {}
        all_months = meses_2025 + meses_2026
        
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names
        
        for m in all_months:
            nome_aba = None
            possiveis = [m, m.upper(), m.capitalize(), f"{m}.2026", f"{m.upper()}.2026"]
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
    
    # Lista de Pendências
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
    else: st.warning(f"Mês {nome_mes_atual} não iniciado.")

# --- PÁGINA 2: FLUXO DE CAIXA ---
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
    with st.expander("🔴 LANÇAR DESPESA", expanded=True):
        with st.form("desp"):
            d1, d2 = st.columns(2)
            desc = d1.text_input("Descrição")
            val = d2.number_input("Valor R$", min_value=0.0)
            if st.form_submit_button("Lançar"):
                novo = {'Data': datetime.now().strftime('%d/%m/%Y'), 'Lançamento': f"DESPESA: {desc}", 'Valor': -val, 'FORMA': 'CAIXA'}
                st.session_state.db_fin[mes_atual] = pd.concat([df_caixa, pd.DataFrame([novo])], ignore_index=True)
                st.rerun()
    st.dataframe(df_caixa, use_container_width=True)

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
        dm = c4.text_input("Data Matrícula (DD/MM/AAAA)", value=datetime.now().strftime('%d/%m/%Y'))
        
        if st.form_submit_button("Salvar"):
            novo = {
                'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m, 
                'Data da Matricula ': dm, 'Valor Matricula': vm,
                'Pendente Doc': 'NÃO', 'Bolsista': 'NÃO'
            }
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Salvo!")

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
        # --- PASTA DO ALUNO ---
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        # --- FORMULÁRIO COMPLETO DE EDIÇÃO ---
        with st.expander("📝 Editar Dados do Aluno (Clique aqui)", expanded=True):
            with st.form("edit_completo"):
                st.subheader("Informações Pessoais e Financeiras")
                
                # Linha 1
                col_a, col_b = st.columns(2)
                novo_nome = col_a.text_input("Nome Completo", value=dados['Aluno'])
                novo_contato = col_b.text_input("Contato (WhatsApp)", value=dados['Contato'])
                
                # Linha 2
                col_c, col_d = st.columns(2)
                opcoes_venc = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                v_index = opcoes_venc.index(dados['Vencimento']) if dados['Vencimento'] in opcoes_venc else 2
                novo_venc = col_c.selectbox("Vencimento", opcoes_venc, index=v_index)
                
                try: val_m = float(dados['Mensalidade'])
                except: val_m = 200.0
                novo_mensal = col_d.number_input("Mensalidade Atual (R$)", value=val_m)
                
                # Linha 3 (Matrícula)
                col_e, col_f = st.columns(2)
                novo_data_mat = col_e.text_input("Data da Matrícula", value=dados.get('Data da Matricula ', ''))
                
                try: val_mat = float(dados.get('Valor Matricula', 0))
                except: val_mat = 0.0
                novo_valor_mat = col_f.number_input("Valor da Matrícula (R$)", value=val_mat)
                
                st.divider()
                st.subheader("Situação Acadêmica")
                
                # Linha 4 (Docs e Bolsa)
                col_g, col_h, col_i = st.columns(3)
                
                # Pendência Doc
                idx_doc = 0 if dados.get('Pendente Doc') != 'SIM' else 1
                novo_pend_doc = col_g.selectbox("Pendente de Documento?", ["NÃO", "SIM"], index=idx_doc)
                
                # Qual Doc
                novo_qual_doc = col_h.text_input("Qual Documento? (Se sim)", value=dados.get('Qual Documento?', ''))
                
                # Bolsista
                lista_bolsa = ["NÃO", "SIM", "MEIA BOLSISTA"]
                val_bolsa = dados.get('Bolsista', 'NÃO')
                idx_bolsa = lista_bolsa.index(val_bolsa) if val_bolsa in lista_bolsa else 0
                novo_bolsista = col_i.selectbox("É Bolsista?", lista_bolsa, index=idx_bolsa)
                
                # Linha 5 (Último Pagamento)
                st.divider()
                novo_ult_pag = st.text_input("Data do Último Pagamento (Registro)", value=dados.get('Data Ultimo Pagamento', ''))

                if st.form_submit_button("💾 Salvar Alterações"):
                    # Atualiza tudo no banco de dados da memória
                    st.session_state.db_alunos.at[idx, 'Aluno'] = novo_nome
                    st.session_state.db_alunos.at[idx, 'Contato'] = novo_contato
                    st.session_state.db_alunos.at[idx, 'Vencimento'] = novo_venc
                    st.session_state.db_alunos.at[idx, 'Mensalidade'] = novo_mensal
                    st.session_state.db_alunos.at[idx, 'Data da Matricula '] = novo_data_mat
                    st.session_state.db_alunos.at[idx, 'Valor Matricula'] = novo_valor_mat
                    st.session_state.db_alunos.at[idx, 'Pendente Doc'] = novo_pend_doc
                    st.session_state.db_alunos.at[idx, 'Qual Documento?'] = novo_qual_doc
                    st.session_state.db_alunos.at[idx, 'Bolsista'] = novo_bolsista
                    st.session_state.db_alunos.at[idx, 'Data Ultimo Pagamento'] = novo_ult_pag
                    
                    st.session_state.aluno_selecionado = novo_nome
                    st.success("Cadastro atualizado com sucesso!")
                    st.rerun()

        st.subheader("💳 Calendário 2026")
        tab25, tab26 = st.tabs(["2025", "2026"])

        def render_meses(lista):
            for mes in lista:
                df = st.session_state.db_fin[mes]
                p_nome = str(st.session_state.aluno_selecionado).split()[0]
                pg = df[df['Lançamento'].astype(str).str.contains(p_nome, case=False, na=False)]
                
                c1, c2 = st.columns([1, 4])
                c1.markdown(f"### {mes}")
                with c2:
                    if not pg.empty:
                        st.success(f"✅ PAGO: R$ {pg.iloc[0]['Valor']}")
                        if st.button("Desfazer", key=f"d_{mes}"):
                            st.session_state.db_fin[mes] = df.drop(pg.index)
                            st.rerun()
                    else:
                        st.error("❌ EM ABERTO")
                        with st.popover("Pagar"):
                            val = st.number_input("Valor", value=val_m, key=f"v{mes}")
                            if st.button("Confirmar", key=f"ok{mes}"):
                                novo = {'Data': datetime.now().strftime('%d/%m/%Y'), 'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}", 'Valor': val, 'FORMA': 'PIX'}
                                st.session_state.db_fin[mes] = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
                                st.rerun()
                st.divider()

        with tab25: render_meses(st.session_state.m25)
        with tab26: render_meses(st.session_state.m26)
