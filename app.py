import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO VISUAL (BRANCO E AZUL) ---
st.set_page_config(page_title="Financeiro Star Tec 2026", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    
    /* Cartão PAGO (Verde) */
    .recibo-card { 
        background-color: #d1f2eb; border: 1px solid #2ecc71; 
        padding: 15px; border-radius: 8px; color: #117864; margin-bottom: 10px;
    }
    
    /* Cartão PENDENTE (Vermelho) */
    .cobranca-card { 
        background-color: #fadbd8; border: 1px solid #e74c3c; 
        padding: 15px; border-radius: 8px; color: #943126; margin-bottom: 10px;
    }
    
    /* Alerta de Hoje */
    .alerta-hoje {
        background-color: #fff3cd; border-left: 6px solid #ffc107;
        padding: 20px; font-size: 18px; color: #856404; margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARREGAMENTO INTELIGENTE (GERADOR DE MESES) ---
@st.cache_data
def carregar_sistema():
    file = "planilha atualizada 2026.xlsx"
    
    # Colunas obrigatórias para não dar erro
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Penden. Docum', 'Qual Documento?', 'Valor Matricula']
    
    # Se não tiver arquivo, cria base zerada
    if not os.path.exists(file):
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        # 1. Carregar Alunos
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        df_alunos.columns = df_alunos.columns.str.strip() # Limpa espaços nos nomes das colunas
        df_alunos = df_alunos.dropna(subset=['Aluno']) # Remove linhas vazias
        
        # Garante que todas colunas existem
        for col in cols_alunos:
            if col not in df_alunos.columns: df_alunos[col] = None

        # 2. Definir o Calendário Completo
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
        
        # AQUI ESTÁ O SEGREDO: Definimos os nomes oficiais que queremos no site
        meses_2026_oficial = [
            "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
        ]
        
        financas = {}
        xls = pd.ExcelFile(file)
        abas_existentes = xls.sheet_names
        
        # Carrega 2025 (Do jeito que está)
        for m in meses_2025:
            if m in abas_existentes:
                financas[m] = pd.read_excel(xls, sheet_name=m, skiprows=1)
            else:
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])

        # Carrega 2026 (Com inteligência para criar o que falta)
        for mes_site in meses_2026_oficial:
            # Tenta encontrar a aba no Excel (pode estar como "JANEIRO" ou "JANEIRO.2026")
            aba_encontrada = None
            
            possibilidades = [mes_site, f"{mes_site}.2026", mes_site.capitalize()]
            
            for tentativa in possibilidades:
                if tentativa in abas_existentes:
                    aba_encontrada = tentativa
                    break
            
            if aba_encontrada:
                # Se a aba existe no Excel, carrega os dados
                df = pd.read_excel(xls, sheet_name=aba_encontrada, skiprows=1)
                # Garante as colunas padrão
                for c in ['Data', 'Lançamento', 'Valor', 'FORMA']:
                    if c not in df.columns: df[c] = None
                financas[mes_site] = df
            else:
                # SE NÃO EXISTE NO EXCEL, O PYTHON CRIA UMA VAZIA NA MEMÓRIA AGORA!
                financas[mes_site] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])

        return df_alunos, financas, meses_2025, meses_2026_oficial

    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return pd.DataFrame(), {}, [], []

# Inicializa Memória do Site
if 'db_alunos' not in st.session_state:
    a, f, m25, m26 = carregar_sistema()
    st.session_state.db_alunos = a
    st.session_state.db_fin = f
    st.session_state.m25 = m25
    st.session_state.m26 = m26

if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- BARRA LATERAL ---
with st.sidebar:
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    st.title("Menu Star Tec")
    
    pagina = st.radio("Navegar:", ["🔔 Painel do Dia", "👥 Lista de Alunos", "➕ Cadastrar Aluno"])
    
    st.markdown("---")
    st.info("⚠️ Importante: Como criamos meses novos, clique abaixo para salvar a nova estrutura no seu computador.")
    
    # BOTÃO SALVAR (ESSENCIAL PARA ATUALIZAR O EXCEL)
    if st.button("💾 BAIXAR EXCEL COMPLETO 2026"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Salva Alunos
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            
            # Salva TODOS os meses (Incluindo os vazios que criamos)
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
                
        st.download_button(label="⬇️ Download Planilha Pronta", data=output.getvalue(), file_name="Financeiro_2026_Completo.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: PAINEL DO DIA ---
if pagina == "🔔 Painel do Dia":
    hoje = datetime.now()
    st.header(f"📅 Visão Geral - {hoje.strftime('%d/%m/%Y')}")
    
    dia_atual = hoje.day
    st.subheader("🔔 Cobranças de Hoje")
    
    tem_alerta = False
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            # Limpa o "DIA 15" para pegar só o 15
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            
            if dia_venc == dia_atual:
                st.markdown(f"""
                <div class="alerta-hoje">
                    🔴 <b>VENCIMENTO HOJE!</b><br>
                    👤 {aluno['Aluno']}<br>
                    📞 {aluno['Contato']}<br>
                    💰 R$ {aluno['Mensalidade']}
                </div>
                """, unsafe_allow_html=True)
                tem_alerta = True
                
        except: continue
            
    if not tem_alerta:
        st.success("✅ Nenhuma mensalidade vence hoje.")

# --- PÁGINA 2: NOVO ALUNO ---
elif pagina == "➕ Cadastrar Aluno":
    st.header("Novo Aluno")
    with st.form("cad"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome")
        z = c2.text_input("WhatsApp")
        c3, c4 = st.columns(2)
        v = c3.selectbox("Dia Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c4.number_input("Valor R$", value=200.0)
        
        if st.form_submit_button("Salvar"):
            novo = {'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m, 'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'), 'Penden. Docum': 'NÃO'}
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno Salvo!")

# --- PÁGINA 3: LISTA E FINANCEIRO ---
elif pagina == "👥 Lista de Alunos":
    
    # LISTA GERAL
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
                if c3.button("📂 Abrir Pasta", key=f"btn_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()

    # DENTRO DA PASTA DO ALUNO
    else:
        nome_aluno = st.session_state.aluno_selecionado
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        # Pega dados
        idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        # --- DADOS ---
        with st.expander("📝 Dados Cadastrais (Clique para Editar)"):
            with st.form("edit"):
                ec1, ec2 = st.columns(2)
                nv_n = ec1.text_input("Nome", value=dados['Aluno'])
                nv_z = ec2.text_input("Zap", value=dados['Contato'])
                ec3, ec4 = st.columns(2)
                
                ops = ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"]
                idx_v = ops.index(dados['Vencimento']) if dados['Vencimento'] in ops else 2
                nv_v = ec3.selectbox("Vencimento", ops, index=idx_v)
                
                try: val_def = float(dados['Mensalidade'])
                except: val_def = 200.0
                nv_m = ec4.number_input("Valor", value=val_def)
                
                if st.form_submit_button("Atualizar"):
                    st.session_state.db_alunos.at[idx, 'Aluno'] = nv_n
                    st.session_state.db_alunos.at[idx, 'Contato'] = nv_z
                    st.session_state.db_alunos.at[idx, 'Vencimento'] = nv_v
                    st.session_state.db_alunos.at[idx, 'Mensalidade'] = nv_m
                    st.session_state.aluno_selecionado = nv_n
                    st.success("Atualizado!")
                    st.rerun()

        st.markdown("---")
        st.subheader("💳 Calendário 2026")
        
        # --- LOOP PELOS MESES ---
        # Aqui ele vai mostrar de JANEIRO a DEZEMBRO, existindo no Excel ou não
        for mes in st.session_state.m26:
            df_mes = st.session_state.db_fin[mes]
            primeiro_nome = str(st.session_state.aluno_selecionado).split()[0]
            
            # Busca Pagamento
            pg = df_mes[df_mes['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
            
            c_mes, c_card = st.columns([1, 4])
            c_mes.markdown(f"### {mes}") # Mostra JANEIRO, FEVEREIRO...
            
            with c_card:
                if not pg.empty:
                    # VERDE - PAGO
                    info = pg.iloc[0]
                    st.markdown(f"""
                    <div class="recibo-card">
                        ✅ <b>PAGO</b><br>
                        Data: {info.get('Data', '-')}<br>
                        Valor: R$ {info.get('Valor', 0)} ({info.get('FORMA', '-')})
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Desfazer Baixa", key=f"del_{mes}"):
                        st.session_state.db_fin[mes] = df_mes.drop(pg.index)
                        st.rerun()
                else:
                    # VERMELHO - PENDENTE
                    st.markdown(f"""
                    <div class="cobranca-card">
                        ❌ <b>EM ABERTO</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.popover("💸 Receber Pagamento"):
                        st.write(f"Baixa: {mes}")
                        v_pg = st.number_input("Valor R$", value=val_def, key=f"v{mes}")
                        d_pg = st.date_input("Data", datetime.now(), key=f"d{mes}")
                        f_pg = st.selectbox("Forma", ["PIX", "Dinheiro", "Cartão"], key=f"f{mes}")
                        
                        if st.button("Confirmar", key=f"ok{mes}"):
                            novo = {
                                'Data': d_pg.strftime('%d/%m/%Y'),
                                'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}",
                                'Valor': v_pg,
                                'FORMA': f_pg
                            }
                            st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo])], ignore_index=True)
                            st.rerun()
            st.divider()
