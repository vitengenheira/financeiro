import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; }
    .pago-card { background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; color: #155724; }
    .devendo-card { background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; color: #721c24; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÃO DE LIMPEZA DE DADOS (A PROTEÇÃO) ---
def limpar_colunas(df):
    """Remove espaços extras dos nomes das colunas"""
    df.columns = df.columns.str.strip()
    return df

@st.cache_data
def carregar_dados():
    arquivo = "planilha atualizada 2026.xlsx"
    
    # Se o arquivo não existe, cria estrutura vazia
    if not os.path.exists(arquivo):
        st.error(f"⚠️ O arquivo '{arquivo}' não foi encontrado no GitHub/Pasta!")
        return None, {}, [], []

    try:
        # 1. Carregar Alunos
        # skiprows=3 significa que o cabeçalho está na linha 4 do Excel
        df_alunos = pd.read_excel(arquivo, sheet_name='Alunos', skiprows=3)
        df_alunos = limpar_colunas(df_alunos)
        df_alunos = df_alunos.dropna(subset=['Aluno']) # Remove linhas vazias
        
        # 2. Definir Meses
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        meses_2026 = ["JANEIRO.2026", "Fevereiro_26", "Março_26"] # Ajuste conforme o nome exato das abas
        all_meses = meses_2025 + meses_2026
        
        # 3. Carregar Financeiro
        financas = {}
        xls = pd.ExcelFile(arquivo)
        
        for m in all_meses:
            if m in xls.sheet_names:
                df_m = pd.read_excel(xls, sheet_name=m, skiprows=1)
                df_m = limpar_colunas(df_m)
                # Garante que as colunas essenciais existem
                if 'Lançamento' not in df_m.columns: df_m['Lançamento'] = ""
                if 'Valor' not in df_m.columns: df_m['Valor'] = 0.0
                if 'Data' not in df_m.columns: df_m['Data'] = ""
                financas[m] = df_m
            else:
                # Cria aba vazia se não existir
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA', 'Saldo'])

        return df_alunos, financas, meses_2025, meses_2026

    except Exception as e:
        st.error(f"❌ Erro fatal ao ler planilha: {e}")
        return None, {}, [], []

# --- 3. INICIALIZAÇÃO DA MEMÓRIA ---
if 'dados_carregados' not in st.session_state:
    a, f, m25, m26 = carregar_dados()
    if a is not None:
        st.session_state.db_alunos = a
        st.session_state.db_fin = f
        st.session_state.m25 = m25
        st.session_state.m26 = m26
        st.session_state.dados_carregados = True
    else:
        st.stop()

if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- 4. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Menu Star Tec")
    
    pagina = st.radio("Navegar:", ["🔔 Início", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---")
    
    # BOTÃO DE DOWNLOAD (SALVAR)
    if st.button("💾 Baixar Planilha Atualizada"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Salva Alunos
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            # Salva Meses
            for nome_aba, df_aba in st.session_state.db_fin.items():
                df_aba.to_excel(writer, sheet_name=nome_aba, startrow=1, index=False)
                
        st.download_button(
            label="⬇️ Clique para Salvar no PC",
            data=buffer.getvalue(),
            file_name="Financeiro_StarTec_Editado.xlsx",
            mime="application/vnd.ms-excel"
        )

# --- PÁGINA: LISTA E FICHA (O CORAÇÃO DO APP) ---
if pagina == "👥 Lista de Alunos":
    
    # MODO LISTA (Se ninguém estiver selecionado)
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

    # MODO FICHA (Dentro do aluno)
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar para Lista"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        # Encontra o aluno na tabela
        # TRATAMENTO DE ERRO: Se não achar, avisa
        try:
            filtro = st.session_state.db_alunos['Aluno'] == nome_aluno
            idx_aluno = st.session_state.db_alunos[filtro].index[0]
            dados = st.session_state.db_alunos.loc[idx_aluno]
        except:
            st.error("Erro ao encontrar aluno. Tente recarregar a página.")
            st.stop()

        st.title(f"Pasta: {dados['Aluno']}")

        # --- ÁREA DE EDIÇÃO DE DADOS ---
        with st.expander("📝 Dados Pessoais (Clique para Editar)", expanded=False):
            with st.form("form_edicao"):
                c1, c2 = st.columns(2)
                # Usa .get para evitar erro se a coluna não existir
                novo_nome = c1.text_input("Nome", value=dados.get('Aluno', ''))
                novo_contato = c2.text_input("WhatsApp", value=dados.get('Contato', ''))
                
                c3, c4 = st.columns(2)
                # Tratamento seguro para valores numéricos
                try:
                    val_mensal = float(dados.get('Mensalidade', 200))
                except: val_mensal = 200.0
                
                nova_mensalidade = c3.number_input("Mensalidade R$", value=val_mensal)
                novo_venc = c4.text_input("Vencimento (Ex: DIA 15)", value=dados.get('Vencimento', 'DIA 15'))
                
                obs_doc = st.text_input("Documento Pendente?", value=dados.get('Qual Documento?', ''))
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    st.session_state.db_alunos.at[idx_aluno, 'Aluno'] = novo_nome
                    st.session_state.db_alunos.at[idx_aluno, 'Contato'] = novo_contato
                    st.session_state.db_alunos.at[idx_aluno, 'Mensalidade'] = nova_mensalidade
                    st.session_state.db_alunos.at[idx_aluno, 'Vencimento'] = novo_venc
                    st.session_state.db_alunos.at[idx_aluno, 'Qual Documento?'] = obs_doc
                    st.session_state.aluno_selecionado = novo_nome # Atualiza seleção
                    st.success("Dados Salvos!")
                    st.rerun()

        # Resumo Rápido
        st.info(f"Vencimento: {dados.get('Vencimento', '-')} | Valor: R$ {dados.get('Mensalidade', '-')}")

        st.markdown("---")
        st.subheader("💰 Histórico Financeiro")
        
        # Abas de Anos
        tab25, tab26 = st.tabs(["2025", "2026"])

        def mostrar_meses(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                
                # Busca Inteligente (Pelo primeiro nome)
                primeiro_nome = str(st.session_state.aluno_selecionado).split()[0]
                # Verifica se existe pagamento com esse nome
                match = df_mes[df_mes['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
                
                col_mes, col_status, col_btn = st.columns([1, 2, 1])
                col_mes.markdown(f"### {mes}")
                
                if not match.empty:
                    # ESTÁ PAGO
                    valor_pago = match.iloc[0].get('Valor', 0)
                    col_status.markdown(f'<div class="pago-card">✅ PAGO (R$ {valor_pago})</div>', unsafe_allow_html=True)
                    if col_btn.button("Desfazer", key=f"undo_{mes}"):
                        # Remove a linha
                        idx_remove = match.index
                        st.session_state.db_fin[mes] = df_mes.drop(idx_remove)
                        st.rerun()
                else:
                    # ESTÁ PENDENTE
                    col_status.markdown('<div class="devendo-card">❌ PENDENTE</div>', unsafe_allow_html=True)
                    with col_btn.popover("Pagar"):
                        val = st.number_input("Valor", value=200.0, key=f"val_{mes}")
                        forma = st.selectbox("Forma", ["PIX", "Dinheiro"], key=f"fm_{mes}")
                        if st.button("Confirmar Baixa", key=f"pay_{mes}"):
                            novo_pag = {
                                'Data': datetime.now().strftime("%Y-%m-%d"),
                                'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}",
                                'Valor': val,
                                'FORMA': forma
                            }
                            st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo_pag])], ignore_index=True)
                            st.rerun()
                st.divider()

        with tab25:
            mostrar_meses(st.session_state.m25)
        with tab26:
            mostrar_meses(st.session_state.m26)

# --- PÁGINA: INÍCIO (LEMBRETES) ---
elif pagina == "🔔 Início":
    st.header(f"Olá! Hoje é {datetime.now().strftime('%d/%m')}")
    st.write("Verifique os vencimentos do dia abaixo:")
    
    hoje = datetime.now().day
    
    count = 0
    for _, row in st.session_state.db_alunos.iterrows():
        try:
            # Tenta ler o dia do vencimento (Ex: "DIA 15" -> 15)
            dia_venc = int(str(row['Vencimento']).upper().replace("DIA", "").strip())
            if dia_venc == hoje:
                st.error(f"🔴 VENCE HOJE: {row['Aluno']}")
                count += 1
            elif dia_venc == hoje + 1:
                st.warning(f"⚠️ Vence Amanhã: {row['Aluno']}")
                count += 1
        except:
            pass # Se o vencimento estiver escrito errado, ignora
            
    if count == 0:
        st.success("Nenhum vencimento urgente para hoje.")

# --- PÁGINA: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Aluno")
    with st.form("novo_aluno"):
        n = st.text_input("Nome Completo")
        c = st.text_input("WhatsApp")
        v = st.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = st.number_input("Valor Mensalidade", value=200.0)
        
        if st.form_submit_button("Salvar Cadastro"):
            novo = {
                'Aluno': n,
                'Contato': c, 
                'Vencimento': v,
                'Mensalidade': m,
                'Data da Matricula ': datetime.now().strftime("%d/%m/%Y")
            }
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno cadastrado! Vá para a lista para ver.")

        with tab25: renderizar_financeiro(st.session_state.m25)
        with tab26: renderizar_financeiro(st.session_state.m26)
