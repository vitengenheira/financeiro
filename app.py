import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# 1. CONFIGURAÇÃO E ESTILO (BRANCO E AZUL)
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; font-weight: bold;}
    
    /* Cards de Status */
    .recibo-card { 
        background-color: #e8f8f5; 
        border: 1px solid #2ecc71; 
        padding: 15px; 
        border-radius: 8px; 
        color: #145a32;
        margin-bottom: 10px;
    }
    .cobranca-card { 
        background-color: #fdedec; 
        border: 1px solid #e74c3c; 
        padding: 15px; 
        border-radius: 8px; 
        color: #7b241c;
        margin-bottom: 10px;
    }
    .alerta-vencimento {
        background-color: #fff3cd;
        border-left: 6px solid #ffc107;
        padding: 20px;
        margin-bottom: 15px;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO E CRIAÇÃO DE MESES
@st.cache_data
def carregar_tudo():
    file = "planilha atualizada 2026.xlsx"
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']
    
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        # Limpa colunas
        df_alunos.columns = df_alunos.columns.str.strip()
        for col in cols_alunos:
            if col not in df_alunos.columns: df_alunos[col] = None
        df_alunos = df_alunos.dropna(subset=['Aluno'])
        
        # DEFINIÇÃO DE TODOS OS MESES DO ANO
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        # Aqui criamos o calendário completo de 2026
        meses_2026 = [
            "JANEIRO.2026", "FEVEREIRO.2026", "MARÇO.2026", "ABRIL.2026", 
            "MAIO.2026", "JUNHO.2026", "JULHO.2026", "AGOSTO.2026", 
            "SETEMBRO.2026", "OUTUBRO.2026", "NOVEMBRO.2026", "DEZEMBRO.2026"
        ]
        
        financas = {}
        all_months = meses_2025 + meses_2026
        
        xls = pd.ExcelFile(file)
        for m in all_months:
            if m in xls.sheet_names:
                financas[m] = pd.read_excel(xls, sheet_name=m, skiprows=1)
                # Garante colunas essenciais
                for req in ['Data', 'Lançamento', 'Valor', 'FORMA']:
                    if req not in financas[m].columns: financas[m][req] = None
            else:
                # Se a aba não existe no Excel, cria vazia na memória
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA', 'Saldo'])
                
        return df_alunos, financas, meses_2025, meses_2026

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
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

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Menu Star Tec")
    
    pagina = st.radio("Navegar:", ["🔔 Início (Notificações)", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    # BOTÃO PARA SALVAR TUDO
    if st.button("💾 BAIXAR PLANILHA ATUALIZADA"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
        st.download_button(label="⬇️ Clique para Salvar no PC", data=output.getvalue(), file_name="Financeiro_StarTec_Completo.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: INÍCIO E NOTIFICAÇÕES ---
if pagina == "🔔 Início (Notificações)":
    hoje = datetime.now()
    st.header(f"📅 Painel do Dia: {hoje.strftime('%d/%m/%Y')}")
    
    dia_atual = hoje.day
    
    st.subheader("🔔 Alertas de Vencimento")
    
    tem_alerta = False
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            # Limpa o texto "DIA 15" para pegar só o número 15
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            
            nome = aluno['Aluno']
            zap = aluno['Contato']
            val = aluno['Mensalidade']
            
            # Lógica da Notificação
            if dia_venc == dia_atual:
                st.markdown(f"""
                <div class="alerta-vencimento">
                    🔴 <b>HOJE VENCE:</b> {nome}<br>
                    Valor: R$ {val} | Contato: {zap}
                </div>
                """, unsafe_allow_html=True)
                tem_alerta = True
                
            elif dia_venc == dia_atual + 1:
                st.info(f"⚠️ Vence Amanhã: {nome} (Dia {dia_venc})")
                tem_alerta = True
                
        except:
            continue
            
    if not tem_alerta:
        st.success("✅ Nenhuma mensalidade vencendo hoje!")

# --- PÁGINA 2: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Aluno")
    with st.form("cad_novo"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome Completo")
        z = c2.text_input("WhatsApp")
        
        c3, c4 = st.columns(2)
        # Seleção de Vencimento Obrigatória
        v = c3.selectbox("Escolha o Dia de Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c4.number_input("Valor Mensalidade (R$)", value=200.0)
        
        if st.form_submit_button("Salvar Cadastro"):
            novo = {
                'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m,
                'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'),
                'Penden. Docum': 'NÃO'
            }
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno cadastrado! O sistema já vai calcular os vencimentos.")

# --- PÁGINA 3: LISTA E FICHA (CONTROLE TOTAL) ---
elif pagina == "👥 Lista de Alunos":
    
    # LISTAGEM
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

    # PASTA DO ALUNO
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        # Pega dados do aluno
        idx_aluno = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx_aluno]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        # --- ÁREA DE DADOS (EDITÁVEL) ---
        with st.expander(f"📝 Dados Cadastrais (Vencimento: {dados['Vencimento']}) - Clique para Editar"):
            with st.form("edit_aluno"):
                ec1, ec2 = st.columns(2)
                nv_nome = ec1.text_input("Nome", value=dados['Aluno'])
                nv_zap = ec2.text_input("Zap", value=dados['Contato'])
                ec3, ec4 = st.columns(2)
                
                # Garante que o vencimento atual esteja na lista
                opcoes = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                venc_atual = dados['Vencimento'] if dados['Vencimento'] in opcoes else "DIA 15"
                nv_venc = ec3.selectbox("Alterar Vencimento", opcoes, index=opcoes.index(venc_atual))
                
                nv_valor = ec4.number_input("Valor", value=float(dados['Mensalidade']) if pd.notnull(dados['Mensalidade']) and isinstance(dados['Mensalidade'], (int, float)) else 200.0)
                
                if st.form_submit_button("Salvar Dados"):
                    st.session_state.db_alunos.at[idx_aluno, 'Aluno'] = nv_nome
                    st.session_state.db_alunos.at[idx_aluno, 'Vencimento'] = nv_venc
                    st.session_state.db_alunos.at[idx_aluno, 'Mensalidade'] = nv_valor
                    st.session_state.aluno_selecionado = nv_nome
                    st.success("Atualizado!")
                    st.rerun()

        st.markdown("---")
        st.subheader("💳 Histórico Financeiro Completo")
        
        tab25, tab26 = st.tabs(["2025 (Histórico)", "2026 (Ano Atual)"])

        # FUNÇÃO QUE GERA OS CARDS DE PAGAMENTO
        def renderizar_ano(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                primeiro_nome = str(st.session_state.aluno_selecionado).split()[0]
                
                # Procura pagamento
                pagamento = df_mes[df_mes['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
                
                col_nome_mes, col_detalhes = st.columns([1, 3])
                col_nome_mes.markdown(f"### {mes.split('.')[0]}") # Exibe só JANEIRO
                
                if not pagamento.empty:
                    # --- ESTÁ PAGO ---
                    dado_pag = pagamento.iloc[0]
                    with col_detalhes:
                        st.markdown(f"""
                        <div class="recibo-card">
                            ✅ <b>PAGAMENTO CONFIRMADO</b><br>
                            📅 Data: {dado_pag.get('Data', '-')}<br>
                            💰 Valor: R$ {dado_pag.get('Valor', 0)}<br>
                            💳 Forma: {dado_pag.get('FORMA', '-')}
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️ Excluir Pagamento", key=f"del_{mes}"):
                            st.session_state.db_fin[mes] = df_mes.drop(pagamento.index)
                            st.rerun()
                else:
                    # --- ESTÁ PENDENTE ---
                    with col_detalhes:
                        st.markdown(f"""
                        <div class="cobranca-card">
                            ❌ <b>EM ABERTO</b> - Vencimento: {dados['Vencimento']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Formulário de Baixa
                        with st.popover("💸 Realizar Pagamento"):
                            st.write(f"Baixa de: {mes.split('.')[0]}")
                            val_pg = st.number_input("Valor Recebido R$", value=float(dados['Mensalidade']), key=f"v_{mes}")
                            dt_pg = st.date_input("Data do Pagamento", datetime.now(), key=f"d_{mes}")
                            forma_pg = st.selectbox("Forma de Pagamento", ["PIX", "Dinheiro", "Cartão", "Bolsa"], key=f"f_{mes}")
                            
                            if st.button("Confirmar Baixa", key=f"ok_{mes}"):
                                novo_reg = {
                                    'Data': dt_pg.strftime('%d/%m/%Y'),
                                    'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}",
                                    'Valor': val_pg,
                                    'FORMA': forma_pg
                                }
                                st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo_reg])], ignore_index=True)
                                st.rerun()
                st.write("---")

        with tab25: renderizar_ano(st.session_state.m25)
        with tab26: renderizar_ano(st.session_state.m26)
