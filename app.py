import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    
    /* Cartão de Recibo (PAGO) */
    .recibo-card { 
        background-color: #d1f2eb; 
        border: 1px solid #2ecc71; 
        padding: 15px; 
        border-radius: 8px; 
        color: #117864;
        margin-bottom: 10px;
    }
    
    /* Cartão de Cobrança (PENDENTE) */
    .cobranca-card { 
        background-color: #fadbd8; 
        border: 1px solid #e74c3c; 
        padding: 15px; 
        border-radius: 8px; 
        color: #943126;
        margin-bottom: 10px;
    }
    
    /* Notificação de Hoje */
    .alerta-hoje {
        background-color: #fff3cd;
        border-left: 6px solid #ffc107;
        padding: 20px;
        font-size: 18px;
        color: #856404;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO INTELIGENTE
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']
    
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        # Carrega Alunos
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        df_alunos.columns = df_alunos.columns.str.strip() # Limpa espaços
        df_alunos = df_alunos.dropna(subset=['Aluno'])
        
        # --- DEFINIÇÃO DOS MESES (NOMES LIMPOS) ---
        # 2025 (Histórico)
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        # 2026 (Ano Atual - Limpo)
        meses_display_2026 = [
            "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
        ]
        
        financas = {}
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names
        
        # Carrega 2025
        for m in meses_2025:
            if m in sheet_names:
                financas[m] = pd.read_excel(xls, sheet_name=m, skiprows=1)
            else:
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])

        # Carrega 2026 (Com inteligência para achar abas antigas)
        for m_limpo in meses_display_2026:
            # Tenta achar o nome limpo OU o nome com .2026
            nome_encontrado = None
            if m_limpo in sheet_names:
                nome_encontrado = m_limpo
            elif f"{m_limpo}.2026" in sheet_names:
                nome_encontrado = f"{m_limpo}.2026"
            elif m_limpo.capitalize() in sheet_names: # Tenta 'Janeiro'
                nome_encontrado = m_limpo.capitalize()
            
            if nome_encontrado:
                df = pd.read_excel(xls, sheet_name=nome_encontrado, skiprows=1)
                # Garante colunas
                for c in ['Data', 'Lançamento', 'Valor', 'FORMA']:
                    if c not in df.columns: df[c] = None
                financas[m_limpo] = df
            else:
                # Cria aba vazia se não existir
                financas[m_limpo] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])

        return df_alunos, financas, meses_2025, meses_display_2026

    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
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
    st.title("Menu Principal")
    
    pagina = st.radio("Navegar:", ["🔔 Início (Notificações)", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    # BOTÃO SALVAR
    if st.button("💾 BAIXAR PLANILHA ATUALIZADA"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            for m, df in st.session_state.db_fin.items():
                # Salva com o nome limpo (Ex: JANEIRO)
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
        st.download_button(label="⬇️ Salvar Arquivo no PC", data=output.getvalue(), file_name="Financeiro_2026_Atualizado.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: NOTIFICAÇÕES ---
if pagina == "🔔 Início (Notificações)":
    hoje = datetime.now()
    st.header(f"📅 Painel do Dia: {hoje.strftime('%d/%m/%Y')}")
    
    dia_atual = hoje.day
    st.subheader("🔔 Alertas de Pagamento")
    
    tem_alerta = False
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            # Pega só o número do dia (Ex: "DIA 15" -> 15)
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            
            # Alerta de HOJE
            if dia_venc == dia_atual:
                st.markdown(f"""
                <div class="alerta-hoje">
                    🔴 <b>VENCE HOJE!</b><br>
                    👤 Aluno: <b>{aluno['Aluno']}</b><br>
                    📞 Contato: {aluno['Contato']}<br>
                    💰 Valor: R$ {aluno['Mensalidade']}
                </div>
                """, unsafe_allow_html=True)
                tem_alerta = True
                
            # Alerta de AMANHÃ
            elif dia_venc == dia_atual + 1:
                st.info(f"⚠️ Vence Amanhã: {aluno['Aluno']} (Dia {dia_venc})")
                tem_alerta = True
        except: continue
            
    if not tem_alerta:
        st.success("✅ Nenhuma conta vencendo hoje!")

# --- PÁGINA 2: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Aluno")
    with st.form("cad_novo"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome Completo")
        z = c2.text_input("WhatsApp")
        
        c3, c4 = st.columns(2)
        v = c3.selectbox("Escolha o Dia de Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c4.number_input("Valor Mensalidade (R$)", value=200.0)
        
        if st.form_submit_button("Salvar Cadastro"):
            novo = {
                'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m,
                'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'), 'Penden. Docum': 'NÃO'
            }
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno cadastrado com sucesso!")

# --- PÁGINA 3: LISTA E FICHA ---
elif pagina == "👥 Lista de Alunos":
    
    # MODO LISTA
    if st.session_state.aluno_selecionado is None:
        st.header("Gerenciar Alunos")
        busca = st.text_input("🔍 Buscar aluno...").upper()
        
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

    # MODO PASTA (FICHA DO ALUNO)
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        idx_aluno = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx_aluno]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        # --- DADOS EDITÁVEIS ---
        with st.expander(f"📝 Dados Cadastrais (Clique para Editar)"):
            with st.form("edit_aluno"):
                ec1, ec2 = st.columns(2)
                nv_nome = ec1.text_input("Nome", value=dados['Aluno'])
                nv_zap = ec2.text_input("Zap", value=dados['Contato'])
                ec3, ec4 = st.columns(2)
                
                opcoes = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                v_atual = dados['Vencimento'] if dados['Vencimento'] in opcoes else "DIA 15"
                nv_venc = ec3.selectbox("Vencimento", opcoes, index=opcoes.index(v_atual))
                
                try: val_padrao = float(dados['Mensalidade'])
                except: val_padrao = 200.0
                nv_valor = ec4.number_input("Valor Mensalidade", value=val_padrao)
                
                if st.form_submit_button("Salvar Dados"):
                    st.session_state.db_alunos.at[idx_aluno, 'Aluno'] = nv_nome
                    st.session_state.db_alunos.at[idx_aluno, 'Vencimento'] = nv_venc
                    st.session_state.db_alunos.at[idx_aluno, 'Mensalidade'] = nv_valor
                    st.session_state.aluno_selecionado = nv_nome
                    st.success("Atualizado!")
                    st.rerun()

        st.markdown("---")
        st.subheader("💳 Calendário de Pagamentos")
        
        tab25, tab26 = st.tabs(["Histórico 2025", "ANO 2026 (Atual)"])

        # FUNÇÃO DE RECIBO E COBRANÇA
        def mostrar_meses(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                nome_busca = str(st.session_state.aluno_selecionado).split()[0]
                
                # Procura pagamento
                pagamento = df_mes[df_mes['Lançamento'].astype(str).str.contains(nome_busca, case=False, na=False)]
                
                # Layout do Mês
                c_mes, c_detalhe = st.columns([1, 4])
                c_mes.markdown(f"### {mes}")
                
                with c_detalhe:
                    if not pagamento.empty:
                        # --- RECIBO VERDE (PAGO) ---
                        info = pagamento.iloc[0]
                        st.markdown(f"""
                        <div class="recibo-card">
                            ✅ <b>PAGAMENTO REALIZADO</b><br>
                            📅 Data: <b>{info.get('Data', '-')}</b> | 
                            💰 Valor: <b>R$ {info.get('Valor', 0)}</b> | 
                            💳 Forma: <b>{info.get('FORMA', '-')}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️ Excluir Lançamento", key=f"del_{mes}"):
                            st.session_state.db_fin[mes] = df_mes.drop(pagamento.index)
                            st.rerun()
                    else:
                        # --- ALERTA VERMELHO (PENDENTE) ---
                        st.markdown(f"""
                        <div class="cobranca-card">
                            ❌ <b>EM ABERTO</b><br>
                            Vencimento: {dados['Vencimento']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botão de Pagar
                        with st.popover("💸 Dar Baixa (Pagar)"):
                            st.write(f"Recebendo: **{mes}**")
                            val = st.number_input("Valor (R$)", value=float(val_padrao), key=f"v_{mes}")
                            dt = st.date_input("Data Pagamento", datetime.now(), key=f"d_{mes}")
                            fm = st.selectbox("Forma", ["PIX", "Dinheiro", "Cartão", "Bolsa"], key=f"f_{mes}")
                            
                            if st.button("Confirmar Recebimento", key=f"ok_{mes}"):
                                novo_pag = {
                                    'Data': dt.strftime('%d/%m/%Y'),
                                    'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}",
                                    'Valor': val,
                                    'FORMA': fm
                                }
                                st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo_pag])], ignore_index=True)
                                st.rerun()
                st.divider()

        with tab25: mostrar_meses(st.session_state.m25)
        with tab26: mostrar_meses(st.session_state.m26)
