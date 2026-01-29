import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import xlsxwriter

# --- 1. CONFIGURAÇÃO VISUAL ---
# Define o título da aba do navegador, o layout "wide" (tela cheia) e o ícone
st.set_page_config(page_title="Financeiro Star Tec", layout="wide", page_icon="🏫")

# Aqui começa o CSS (Estilo visual do site). Tudo dentro de <style> define cores e formatos.
st.markdown("""
    <style>
    /* Define o fundo branco para a área principal */
    .main { background-color: #ffffff; }
    
    /* Define a cor azul (#004a99) para todos os títulos (H1, H2, H3) */
    h1, h2, h3 { color: #004a99; }
    
    /* Estiliza todos os botões para serem azuis, com texto branco e bordas arredondadas */
    .stButton>button { background-color: #004a99; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    
    /* Cria o estilo do cartão de RECEITA (Verde) */
    .card-receita { background-color: #d1f2eb; border: 1px solid #2ecc71; padding: 20px; border-radius: 10px; color: #145a32; text-align: center; }
    
    /* Cria o estilo do cartão de DESPESA (Vermelho) */
    .card-despesa { background-color: #fadbd8; border: 1px solid #e74c3c; padding: 20px; border-radius: 10px; color: #7b241c; text-align: center; }
    
    /* Cria o estilo do cartão de SALDO (Azul) */
    .card-saldo { background-color: #d6eaf8; border: 1px solid #3498db; padding: 20px; border-radius: 10px; color: #154360; text-align: center; }
    
    /* Define o estilo do alerta amarelo de vencimento na tela inicial */
    .alerta-hoje { background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True) # unsafe_allow_html permite injetar esse CSS no site

# --- 2. FUNÇÃO DE CARREGAMENTO (O CÉREBRO) ---
# O @st.cache_data faz o Streamlit "lembrar" dos dados para não recarregar tudo a cada clique, deixando o site rápido.
@st.cache_data
def carregar_tudo():
    # Define o nome do arquivo Excel que o sistema vai procurar
    file = "planilha atualizada 2026.xlsx"
    
    # Define a lista de colunas que a tabela de Alunos OBRIGATORIAMENTE deve ter
    cols_alunos = ['Aluno', 'Contato', 'Vencimento', 'Mensalidade', 'Data da Matricula ', 'Bolsita', 'Pendente de Documento', 'Qual Documento?', 'Valor Matricula']
    
    # Verifica: Se o arquivo NÃO existe na pasta...
    if not os.path.exists(file):
        # ...retorna tabelas vazias para o site não quebrar com erro.
        return pd.DataFrame(columns=cols_alunos), {}, [], []

    try:
        # Se o arquivo existe, tenta ler a aba 'Alunos' do Excel
        # skiprows=3 pula as 3 primeiras linhas (cabeçalhos inúteis da sua planilha original)
        df_alunos = pd.read_excel(file, sheet_name='Alunos', skiprows=3)
        
        # Remove espaços extras dos nomes das colunas (Ex: "Aluno " vira "Aluno")
        df_alunos.columns = df_alunos.columns.str.strip()
        
        # Remove linhas que não tenham nome de aluno (linhas vazias no Excel)
        df_alunos = df_alunos.dropna(subset=['Aluno'])
        
        # --- DEFINIÇÃO DOS MESES ---
        # Lista manual dos meses de 2025 para manter o histórico
        meses_2025 = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        # Lista oficial dos meses de 2026 que queremos no sistema
        meses_2026 = ["Janeiro","Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",  "Outubro", "Novembro", "Dezembro"]
        
        # Cria um dicionário vazio para guardar as tabelas de cada mês
        financas = {}
        # Junta as duas listas de meses em uma só
        all_months = meses_2025 + meses_2026
        
        # Abre o arquivo Excel para ler os nomes de todas as abas existentes
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names # Lista com nomes das abas (ex: 'JANEIRO.2026', 'Alunos')
        
        # Loop: Para cada mês que definimos nas listas acima...
        for m in all_months:
            nome_aba = None
            
            # Testa cada variação
            for p in possiveis:
                if p in sheet_names: # Se achar uma aba com esse nome...
                    nome_aba = p # ...salva o nome certo
                    break
            
            if nome_aba:
                # Se achou a aba, lê os dados dela (pulando a primeira linha de título)
                df = pd.read_excel(xls, sheet_name=nome_aba, skiprows=1)
                
                # Garante que as colunas vitais existam, se não, cria elas vazias
                for c in ['Data', 'Lançamento', 'Valor', 'FORMA']:
                    if c not in df.columns: df[c] = None
                
                # Guarda a tabela processada no dicionário 'financas'
                financas[m] = df
            else:
                # Se a aba NÃO existe no Excel (ex: DEZEMBRO ainda não chegou), cria uma tabela vazia na memória
                financas[m] = pd.DataFrame(columns=['Data', 'Lançamento', 'Valor', 'FORMA'])
                
        # Retorna todos os dados processados para serem usados no app
        return df_alunos, financas, meses_2025, meses_2026

    except Exception as e:
        # Se der qualquer erro na leitura, mostra na tela e retorna vazio
        st.error(f"Erro ao carregar sistema: {e}")
        return pd.DataFrame(), {}, [], []

# --- 3. INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
# Verifica se os dados já estão carregados na memória do navegador
if 'db_alunos' not in st.session_state:
    # Se não estiverem, chama a função de carregar e salva na memória (session_state)
    a, f, m25, m26 = carregar_tudo()
    st.session_state.db_alunos = a
    st.session_state.db_fin = f
    st.session_state.m25 = m25
    st.session_state.m26 = m26

# Variável para controlar qual aluno está selecionado na tela "Lista de Alunos"
if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None

# --- 4. BARRA LATERAL (MENU) ---
with st.sidebar: # Tudo aqui dentro aparece na barra esquerda
    # Se existir uma imagem 'logo.png', mostra ela
    if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
    
    st.title("Menu Gestão") # Título do menu
    
    # Cria os botões de rádio para navegação entre as páginas
    pagina = st.radio("Navegar:", ["🔔 Painel do Dia", "💰 Fluxo de Caixa (Despesas)", "👥 Lista de Alunos", "➕ Novo Aluno"])
    
    st.markdown("---") # Linha divisória visual
    
    # --- BOTÃO DE DOWNLOAD (SALVAR) ---
    if st.button("📥 BAIXAR RELATÓRIO MENSAL"):
        # Cria um buffer de memória para montar o arquivo Excel
        output = io.BytesIO()
        
        # Inicia o escritor do Excel usando a biblioteca XlsxWriter
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Salva a aba de Alunos
            st.session_state.db_alunos.to_excel(writer, sheet_name='Alunos', startrow=3, index=False)
            
            # Loop para salvar cada mês (aba por aba)
            for m, df in st.session_state.db_fin.items():
                df.to_excel(writer, sheet_name=m, startrow=1, index=False)
                
                # --- LÓGICA DE SOMATÓRIO NO EXCEL ---
                workbook = writer.book
                worksheet = writer.sheets[m] # Pega a aba atual
                format_bold = workbook.add_format({'bold': True}) # Cria estilo negrito
                
                # Filtra entradas (valores positivos) e saídas (valores negativos)
                total_entrada = df[df['Valor'] > 0]['Valor'].sum()
                total_saida = df[df['Valor'] < 0]['Valor'].sum()
                saldo = total_entrada + total_saida
                
                # Escreve os totais no final da planilha (3 linhas abaixo do último dado)
                row = len(df) + 3
                worksheet.write(row, 1, "TOTAL ENTRADAS:", format_bold)
                worksheet.write(row, 2, total_entrada)
                worksheet.write(row+1, 1, "TOTAL SAÍDAS:", format_bold)
                worksheet.write(row+1, 2, total_saida)
                worksheet.write(row+2, 1, "SALDO FINAL:", format_bold)
                worksheet.write(row+2, 2, saldo)

        # Cria o botão de download real com o arquivo gerado
        st.download_button(label="⬇️ Salvar Planilha Pronta", data=output.getvalue(), file_name="Relatorio_Financeiro_StarTec.xlsx", mime="application/vnd.ms-excel")

# --- PÁGINA 1: PAINEL DO DIA (NOTIFICAÇÕES) ---
if pagina == "🔔 Painel do Dia":
    hoje = datetime.now() # Pega data e hora atual
    st.header(f"📅 Visão Geral - {hoje.strftime('%d/%m/%Y')}") # Mostra data formatada
    
    dia_atual = hoje.day
    st.subheader("🔔 Cobranças de Hoje")
    
    tem_alerta = False # Variável de controle (flag)
    
    # Varre a lista de alunos para ver quem vence hoje
    for _, aluno in st.session_state.db_alunos.iterrows():
        try:
            # Limpa o texto "DIA 15" para virar o número 15
            venc_str = str(aluno['Vencimento']).upper().replace("DIA", "").strip()
            dia_venc = int(venc_str)
            
            # Se o dia do vencimento for igual ao dia de hoje...
            if dia_venc == dia_atual:
                # ...mostra o alerta vermelho
                st.markdown(f"""
                <div class="alerta-hoje">
                    🔴 <b>VENCE HOJE!</b> {aluno['Aluno']} - R$ {aluno['Mensalidade']}
                </div>""", unsafe_allow_html=True)
                tem_alerta = True
            # Se vence amanhã...
            elif dia_venc == dia_atual + 1:
                st.info(f"⚠️ Vence Amanhã: {aluno['Aluno']}")
                tem_alerta = True
        except: continue # Se der erro na leitura (dado sujo), pula para o próximo
            
    if not tem_alerta: st.success("✅ Tudo tranquilo hoje!") # Mensagem se não houver ninguém

# --- PÁGINA 2: FLUXO DE CAIXA (DESPESAS) ---
elif pagina == "💰 Fluxo de Caixa (Despesas)":
    st.header("💰 Controle Financeiro do Mês")
    
    # Caixa de seleção para escolher o mês
    mes_atual = st.selectbox("Selecione o Mês:", st.session_state.m26)
    
    # Pega os dados financeiros daquele mês
    df_caixa = st.session_state.db_fin[mes_atual]
    
    # Calcula os totais somando a coluna 'Valor'
    entradas = df_caixa[df_caixa['Valor'] > 0]['Valor'].sum()
    saidas = df_caixa[df_caixa['Valor'] < 0]['Valor'].sum()
    saldo = entradas + saidas
    
    # Exibe os 3 cartões coloridos no topo (Receita, Despesa, Saldo)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-receita"><h3>Entradas</h3>R$ {entradas:,.2f}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-despesa"><h3>Despesas</h3>R$ {saidas:,.2f}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-saldo"><h3>Saldo Final</h3>R$ {saldo:,.2f}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Formulário para lançar uma despesa nova
    with st.expander("🔴 LANÇAR NOVA DESPESA (Gasto)", expanded=True):
        with st.form("form_despesa"):
            col1, col2 = st.columns(2)
            desc_despesa = col1.text_input("Descrição (Ex: Internet, Luz)")
            valor_despesa = col2.number_input("Valor do Gasto R$", min_value=0.0, step=10.0)
            data_despesa = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Registrar Despesa"):
                # Cria o objeto da nova despesa
                nova_despesa = {
                    'Data': data_despesa.strftime('%d/%m/%Y'),
                    'Lançamento': f"DESPESA: {desc_despesa}",
                    'Valor': -valor_despesa, # IMPORTANTE: Salva como negativo para a conta fechar
                    'FORMA': 'CAIXA'
                }
                # Adiciona na tabela do mês e salva na memória
                st.session_state.db_fin[mes_atual] = pd.concat([df_caixa, pd.DataFrame([nova_despesa])], ignore_index=True)
                st.success("Despesa lançada com sucesso!")
                st.rerun() # Recarrega a página para atualizar os saldos

    # Mostra a tabela completa do mês
    st.subheader(f"Extrato Detalhado: {mes_atual}")
    st.dataframe(df_caixa, use_container_width=True)

# --- PÁGINA 3: NOVO ALUNO ---
elif pagina == "➕ Novo Aluno":
    st.header("Cadastrar Novo Aluno")
    # Formulário simples de cadastro
    with st.form("cad_novo"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome Completo")
        z = c2.text_input("WhatsApp")
        c3, c4 = st.columns(2)
        v = c3.selectbox("Vencimento", ["DIA 05", "DIA 10", "DIA 15", "DIA 20", "DIA 30"])
        m = c4.number_input("Valor Mensalidade", value=200.0)
        
        if st.form_submit_button("Salvar"):
            # Cria o dicionário do novo aluno
            novo = {'Aluno': n, 'Contato': z, 'Vencimento': v, 'Mensalidade': m, 'Data da Matricula ': datetime.now().strftime('%d/%m/%Y'), 'Penden. Docum': 'NÃO'}
            # Adiciona na tabela de alunos
            st.session_state.db_alunos = pd.concat([st.session_state.db_alunos, pd.DataFrame([novo])], ignore_index=True)
            st.success("Aluno Salvo!")

# --- PÁGINA 4: LISTA DE ALUNOS (GERENCIAMENTO) ---
elif pagina == "👥 Lista de Alunos":
    
    # Se nenhum aluno foi selecionado, mostra a lista geral com busca
    if st.session_state.aluno_selecionado is None:
        st.header("Gerenciar Alunos")
        busca = st.text_input("🔍 Buscar...").upper()
        
        lista = st.session_state.db_alunos
        # Filtra a lista se tiver algo escrito na busca
        if busca: lista = lista[lista['Aluno'].astype(str).str.upper().str.contains(busca)]
            
        # Loop para criar um cartão para cada aluno
        for idx, row in lista.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['Aluno']}**")
                c2.text(f"Vencimento: {row['Vencimento']}")
                # Botão que, ao clicar, define este aluno como 'selecionado'
                if c3.button("📂 Abrir Pasta", key=f"b_{idx}"):
                    st.session_state.aluno_selecionado = row['Aluno']
                    st.rerun()
    
    # Se um aluno ESTIVER selecionado, mostra a pasta detalhada dele
    else:
        nome_aluno = st.session_state.aluno_selecionado
        # Botão para limpar a seleção e voltar
        if st.button("⬅️ Voltar"):
            st.session_state.aluno_selecionado = None
            st.rerun()
            
        # Encontra os dados do aluno selecionado
        idx = st.session_state.db_alunos[st.session_state.db_alunos['Aluno'] == nome_aluno].index[0]
        dados = st.session_state.db_alunos.loc[idx]
        
        st.title(f"Aluno: {dados['Aluno']}")
        
        # Área de Edição (Nome, Telefone, etc.)
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

        # Função interna para gerar os cartões de cada mês
        def mostrar_meses(lista_meses):
            for mes in lista_meses:
                df_mes = st.session_state.db_fin[mes]
                primeiro_nome = str(st.session_state.aluno_selecionado).split()[0]
                
                # Procura se existe pagamento para este aluno neste mês
                pg = df_mes[df_mes['Lançamento'].astype(str).str.contains(primeiro_nome, case=False, na=False)]
                
                c_mes, c_card = st.columns([1, 4])
                c_mes.markdown(f"### {mes}")
                
                with c_card:
                    if not pg.empty:
                        # Se achou pagamento, mostra VERDE
                        st.success(f"✅ PAGO: R$ {pg.iloc[0]['Valor']}")
                        # Botão para desfazer (remove a linha)
                        if st.button("Desfazer", key=f"d_{mes}"):
                            st.session_state.db_fin[mes] = df_mes.drop(pg.index)
                            st.rerun()
                    else:
                        # Se não achou, mostra VERMELHO
                        st.error("❌ EM ABERTO")
                        # Botão popover para pagar
                        with st.popover("Pagar"):
                            val = st.number_input("Valor", value=200.0, key=f"v{mes}")
                            if st.button("Confirmar", key=f"ok{mes}"):
                                # Adiciona o pagamento na memória
                                novo = {'Data': datetime.now().strftime('%d/%m/%Y'), 'Lançamento': f"Mensalidade {st.session_state.aluno_selecionado}", 'Valor': val, 'FORMA': 'PIX'}
                                st.session_state.db_fin[mes] = pd.concat([df_mes, pd.DataFrame([novo])], ignore_index=True)
                                st.rerun()
                st.divider()

        # Chama a função para renderizar as abas
        with tab25: mostrar_meses(st.session_state.m25)
        with tab26: mostrar_meses(st.session_state.m26)
