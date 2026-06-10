import streamlit as st
import pandas as pd
import os
import base64
import sqlite3
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Maxsuel Contabilidade - Gestão e Estratégia", layout="wide")

# ==============================================================================
# 1. ATUALIZAÇÃO: INICIALIZAÇÃO DO BANCO DE DADOS (SQLITE)
# ==============================================================================
DB_NOME = "maxsuel_contabilidade.db"

def conectar_db():
    return sqlite3.connect(DB_NOME)

def inicializar_banco():
    conn = conectar_db()
    cursor = conn.cursor()
    # Tabela de Empresas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT UNIQUE NOT NULL
        )
    """)
    # Tabela de Lançamentos Contábeis (amarrada à Empresa)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            debito TEXT NOT NULL,
            credito TEXT NOT NULL,
            valor REAL NOT NULL,
            historico TEXT,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    """)
    conn.commit()
    conn.close()

# Executa a criação das tabelas se não existirem
inicializar_banco()

# ==============================================================================
# 2. ATUALIZAÇÃO: PLANO DE CONTAS EXPANDIDO (INCLUSÃO DE DIVIDENDOS)
# ==============================================================================
plano_de_contas = {
    "1.01": "Caixa/Banco", 
    "1.02": "Estoque", 
    "1.03": "Clientes a Receber", 
    "1.04": "Imobilizado",
    "2.01": "Fornecedores", 
    "2.02": "Provisões", 
    "2.03": "Empréstimos", 
    "2.04": "Capital Social", 
    "2.05": "Lucros Acumulados",
    "2.06": "Dividendos a Pagar (Passivo)", # <-- Nova Conta de Histórico/Obrigação
    "4.01": "Receita de Vendas", 
    "5.01": "Despesas Operacionais", 
    "5.02": "Antecipação/Distribuição de Dividendos", # <-- Nova Conta de Resultado/Dedução
    "6.01": "Impostos", 
    "7.01": "ARE"
}

# --- FUNÇÃO DE FORMATAÇÃO DE MOEDA PT-BR ---
def formatar_br(valor):
    try:
        val_formatado = "{:,.2f}".format(valor)
        return "R$ " + val_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# --- FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64 ---
def obter_logo_base64(caminho_img):
    if os.path.exists(caminho_img):
        with open(caminho_img, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return None

# ==============================================================================
# 3. ATUALIZAÇÃO: FUNÇÕES DE CARGA E SALVAMENTO ADAPTADAS PARA O BANCO DE DADOS
# ==============================================================================
def carregar_lancamentos_db(empresa_id):
    conn = conectar_db()
    query = "SELECT id AS [Nº Lançamento], data AS Data, debito AS Debito, credito AS Credito, valor AS Valor, historico AS Historico FROM lancamentos WHERE empresa_id = ?"
    df = pd.read_sql_query(query, conn, params=(int(empresa_id),))
    conn.close()
    return df.to_dict(orient="records")

def salvar_lancamento_db(empresa_id, data, debito, credito, valor, historico):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lancamentos (empresa_id, data, debito, credito, valor, historico)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (int(empresa_id), str(data), debito, credito, float(valor), historico))
    conn.commit()
    conn.close()

def carregar_empresas():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM empresas ORDER BY nome ASC", conn)
    conn.close()
    return df

# ==============================================================================
# 4. ATUALIZAÇÃO: BUSCA DE EMPRESAS PARA A BARRA LATERAL
# ==============================================================================
df_empresas = carregar_empresas()

# --- BARRA LATERAL ---
nome_logo = "Logo - Empresa Max contabil_2.png"
logo_base64 = obter_logo_base64(nome_logo)

if logo_base64:
    st.sidebar.image(nome_logo, use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #0f2a4a;'>MAXSUEL</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center; margin-top: -15px; font-weight: bold;'>CONTABILIDADE</p>", unsafe_allow_html=True)

st.sidebar.divider()

# SELETOR DE EMPRESA ATIVA
st.sidebar.subheader("🏢 Empresa em Operação")
if not df_empresas.empty:
    lista_empresas = df_empresas["nome"].tolist()
    empresa_selecionada = st.sidebar.selectbox("Escolha a Empresa:", lista_empresas)
    empresa_id_atual = df_empresas[df_empresas["nome"] == empresa_selecionada]["id"].values[0]
    cnpj_empresa_atual = df_empresas[df_empresas["nome"] == empresa_selecionada]["cnpj"].values[0]
else:
    st.sidebar.warning("Nenhuma empresa cadastrada no sistema.")
    empresa_id_atual = None
    cnpj_empresa_atual = ""

st.sidebar.divider()

# CONTROLADOR DE NAVEGAÇÃO INTERNA
opcoes_menu = [
    "🏠 Menu Principal", 
    "💻 Módulo Contábil", 
    "🧮 Simulador Simples Nacional",
    "📋 Módulo de Folha & Fator R"
]

if 'pagina_selecionada' not in st.session_state:
    st.session_state.pagina_selecionada = "🏠 Menu Principal"

try:
    idx_atual = opcoes_menu.index(st.session_state.pagina_selecionada)
except ValueError:
    idx_atual = 0

opcao_menu = st.sidebar.radio("Navegação do Sistema", opcoes_menu, index=idx_atual, key="nav_radio")

if opcao_menu != st.session_state.pagina_selecionada:
    st.session_state.pagina_selecionada = opcao_menu
    st.rerun()

# Atualiza a memória de lançamentos com base na empresa ativa da barra lateral
if empresa_id_atual:
    st.session_state.livro_diario = carregar_lancamentos_db(empresa_id_atual)
else:
    st.session_state.livro_diario = []

# TABELAS OFICIAIS DO SIMPLES NACIONAL
TABELAS_PADRAO = {
    "Anexo I - Comércio": [(180000.0, 0.040, 0.0), (360000.0, 0.073, 5940.0), (720000.0, 0.095, 13860.0), (1800000.0, 0.107, 22500.0), (3600000.0, 0.143, 87300.0), (4800000.0, 0.190, 378000.0)],
    "Anexo II - Indústria": [(180000.0, 0.045, 0.0), (360000.0, 0.078, 5940.0), (720000.0, 0.100, 13860.0), (1800000.0, 0.112, 22500.0), (3600000.0, 0.147, 85500.0), (4800000.0, 0.300, 720000.0)],
    "Anexo III - Serviços": [(180000.0, 0.060, 0.0), (360000.0, 0.112, 9360.0), (720000.0, 0.135, 17640.0), (1800000.0, 0.160, 35640.0), (3600000.0, 0.210, 125640.0), (4800000.0, 0.330, 848000.0)],
    "Anexo IV - Serviços": [(180000.0, 0.045, 0.0), (360000.0, 0.090, 8100.0), (720000.0, 0.102, 12420.0), (1800000.0, 0.140, 39780.0), (3600000.0, 0.220, 183780.0), (4800000.0, 0.330, 828000.0)],
    "Anexo V - Serviços": [(180000.0, 0.155, 0.0), (360000.0, 0.180, 4500.0), (720000.0, 0.195, 9900.0), (1800000.0, 0.205, 17100.0), (3600000.0, 0.230, 62100.0), (4800000.0, 0.305, 540000.0)]
}

REPARTICAO_IMPOSTOS = {
    "Anexo I - Comércio":   {"IRPJ": 0.055, "CSLL": 0.035, "COFINS": 0.1274, "PIS": 0.0276, "CPP": 0.415, "ICMS": 0.34, "IPI": 0.0, "ISS": 0.0},
    "Anexo II - Indústria": {"IRPJ": 0.055, "CSLL": 0.035, "COFINS": 0.1151, "PIS": 0.0249, "CPP": 0.375, "ICMS": 0.32, "IPI": 0.075, "ISS": 0.0},
    "Anexo III - Serviços": {"IRPJ": 0.040, "CSLL": 0.035, "COFINS": 0.1282, "PIS": 0.0278, "CPP": 0.434, "ICMS": 0.0, "IPI": 0.0, "ISS": 0.335},
    "Anexo IV - Serviços":  {"IRPJ": 0.188, "CSLL": 0.152, "COFINS": 0.1767, "PIS": 0.0383, "CPP": 0.0, "ICMS": 0.0, "IPI": 0.0, "ISS": 0.445},
    "Anexo V - Serviços":   {"IRPJ": 0.250, "CSLL": 0.150, "COFINS": 0.1410, "PIS": 0.0305, "CPP": 0.2885, "ICMS": 0.0, "IPI": 0.0, "ISS": 0.140}
}

def calcular_saldos():
    saldos = {c: 0.0 for c in plano_de_contas}
    for l in st.session_state.livro_diario:
        try:
            d = str(l.get("Debito", ""))
            c = str(l.get("Credito", ""))
            v = float(l.get("Valor", 0.0))
            if d in saldos:
                if d.startswith(('1', '5', '6')): saldos[d] += v
                else: saldos[d] -= v
            if c in saldos:
                if c.startswith(('2', '4')): saldos[c] += v
                else: saldos[c] -= v
        except:
            continue
    return saldos

saldos = calcular_saldos()
# Ajuste do Lucro considerando a nova conta de distribuição 5.02
lucro = (saldos.get("4.01", 0.0)) - (saldos.get("5.01", 0.0) + saldos.get("5.02", 0.0) + saldos.get("6.01", 0.0))

# ==============================================================================
# 5. ATUALIZAÇÃO: INJEÇÃO DE INSTRUÇÕES DE IMPRESSÃO VIA CSS DO NAVEGADOR
# ==============================================================================
st.markdown("""
<style>
    .custom-card-btn button {
        border-radius: 0px 0px 10px 10px !important;
        border: 1px solid #ddd !important;
        border-top: none !important;
        padding: 10px !important;
        height: 45px !important;
        background-color: #ffffff !important;
        transition: all 0.3s ease;
    }
    .custom-card-btn button:hover {
        background-color: #f1f5f9 !important;
        color: #0f2a4a !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Configuração de Impressão Limpa */
    @media print {
        header, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, .no-print {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] {
            width: 100% !important;
            padding: 0 !important;
            background-color: white !important;
        }
        .printable-report {
            border: 2px solid #333 !important;
            padding: 20px !important;
            margin-top: 20px !important;
            color: black !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# TELA 1: MENU PRINCIPAL
# ==============================================================================
if st.session_state.pagina_selecionada == "🏠 Menu Principal":
    st.title("🏛️ Hub de Soluções Contábeis Maxsuel")
    st.markdown("Seja bem-vindo ao seu painel estratégico. Selecione abaixo a ferramenta que deseja operar:")
    st.write("")
    
    col_card1, col_card2, col_card3 = st.columns(3)
    
    with col_card1:
        st.markdown("""
        <div style="background-color: #f0f4f8; padding: 25px; border-radius: 10px 10px 0px 0px; border-left: 5px solid #0f2a4a; min-height: 180px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
            <h3 style="color: #0f2a4a; margin-top:0;">💻 Módulo Contábil Comercial</h3>
            <p style="color: #333; font-size: 14px;">Realize partidas dobradas do livro diário, gere relatórios de DRE e acompanhe o fechamento do seu Balanço Patrimonial em tempo real.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="custom-card-btn">', unsafe_allow_html=True)
        if st.button("Acessar Contabilidade ➡️", use_container_width=True, key="btn_contabil"):
            st.session_state.pagina_selecionada = "💻 Módulo Contábil"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
    with col_card2:
        st.markdown("""
        <div style="background-color: #fffde6; padding: 25px; border-radius: 10px 10px 0px 0px; border-left: 5px solid #d4af37; min-height: 180px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
            <h3 style="color: #6b5300; margin-top:0;">🧮 Inteligência do Simples Nacional</h3>
            <p style="color: #333; font-size: 14px;">Simule e compare simultaneamente a carga tributária dos Anexos I, II, III, IV e V. Faça simulações e descubra o rateio exato por imposto.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="custom-card-btn">', unsafe_allow_html=True)
        if st.button("Acessar Simulador Tributário ➡️", use_container_width=True, key="btn_simulador"):
            st.session_state.pagina_selecionada = "🧮 Simulador Simples Nacional"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_card3:
        st.markdown("""
        <div style="background-color: #f3fcf2; padding: 25px; border-radius: 10px 10px 0px 0px; border-left: 5px solid #2e7d32; min-height: 180px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
            <h3 style="color: #1b5e20; margin-top:0;">📋 Folha de Pagamento & Fator R</h3>
            <p style="color: #333; font-size: 14px;">Calcule o salário líquido de funcionários para 2026 com regras de INSS/IRRF e monitore o enquadramento estratégico do Fator R.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="custom-card-btn">', unsafe_allow_html=True)
        if st.button("Acessar Módulo de Folha ➡️", use_container_width=True, key="btn_folha_v"):
            st.session_state.pagina_selecionada = "📋 Módulo de Folha & Fator R"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# TELA 2: MÓDULO CONTÁBIL (REESTRUTURADO)
# ==============================================================================
elif st.session_state.pagina_selecionada == "💻 Módulo Contábil":
    
    # Menu interno estendido com as novas abas solicitadas
    sub_menu = st.radio("Seções Contábeis:", [
        "🏢 Cadastro de Empresas", "📝 Lançamentos", "⚖️ Balancete", "📊 DRE", "⚖️ Balanço Patrimonial"
    ], horizontal=True)

    # --- ABA NOVA: CADASTRO DE EMPRESAS ---
    if sub_menu == "🏢 Cadastro de Empresas":
        st.title("🏢 Painel de Cadastro Corporativo")
        
        with st.form("form_cadastro_empresa", clear_on_submit=True):
            st.subheader("Inserir Nova Empresa no Banco Local")
            nome_empresa = st.text_input("Razão Social / Nome Fantasia")
            cnpj_empresa = st.text_input("CNPJ (Apenas números ou formatado)")
            
            if st.form_submit_button("Salvar Empresa Definitivamente"):
                if nome_empresa and cnpj_empresa:
                    try:
                        conn = conectar_db()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO empresas (nome, cnpj) VALUES (?, ?)", (nome_empresa, cnpj_empresa))
                        conn.commit()
                        conn.close()
                        st.success(f"Empresa '{nome_empresa}' salva com sucesso no banco relacional!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Erro: Já existe uma empresa cadastrada com este CNPJ.")
                else:
                    st.error("Por favor, preencha todos os campos do cadastro.")
                    
        st.divider()
        st.subheader("Empresas Ativas no Sistema")
        if not df_empresas.empty:
            st.dataframe(df_empresas, use_container_width=True)
        else:
            st.info("Nenhuma empresa listada no banco local.")

    # Se o usuário tentar acessar os relatórios sem selecionar/cadastrar empresa
    elif empresa_id_atual is None:
        st.warning("⚠️ Atenção: Acesse primeiro a aba '🏢 Cadastro de Empresas' para registrar uma empresa antes de ver lançamentos ou gerar relatórios.")

    # --- ABA: LANÇAMENTOS ---
    elif sub_menu == "📝 Lançamentos":
        st.title(f"📝 Livro Diário de Lançamentos")
        st.info(f"Gravando dados na empresa: **{empresa_selecionada}** (CNPJ: {cnpj_empresa_atual})")
        
        st.subheader("📥 Importar Lançamentos via CSV")
        arquivo_upload = st.file_uploader("Selecione seu arquivo CSV exportado do Excel (Separado por ponto e vírgula)", type=["csv"])
        
        if arquivo_upload is not None:
            try:
                df_importado = pd.read_csv(arquivo_upload, sep=";", encoding="utf-8-sig")
                df_importado.columns = [col.replace("é", "e").replace("ó", "o").title() for col in df_importado.columns]
                colunas_obrigatorias = ["Data", "Debito", "Credito", "Valor", "Historico"]
                
                if all(col in df_importado.columns for col in colunas_obrigatorias):
                    if st.button("Confirmar Importação de Dados"):
                        dados_novos = df_importado[colunas_obrigatorias].to_dict(orient="records")
                        
                        # Salva item por item vinculando a empresa ativa
                        for item in dados_novos:
                            salvar_lancamento_db(empresa_id_atual, item["Data"], item["Debito"], item["Credito"], item["Valor"], item["Historico"])
                            
                        st.success(f"{len(dados_novos)} lançamentos importados e vinculados à empresa '{empresa_selecionada}'!")
                        st.rerun()
                else:
                    st.error("Erro: O arquivo precisa conter as colunas: Data, Debito, Credito, Valor, Historico.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                
        st.divider()

        with st.form("form_lancamento", clear_on_submit=True):
            col1, col2 = st.columns(2)
            data = col1.date_input("Data do Lançamento")
            valor = col2.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            
            c_debito = st.selectbox("Conta Débito (Entrada)", list(plano_de_contas.keys()), format_func=lambda x: f"{x} - {plano_de_contas[x]}")
            c_credito = st.selectbox("Conta Crédito (Origem)", list(plano_de_contas.keys()), format_func=lambda x: f"{x} - {plano_de_contas[x]}")
            historico = st.text_input("Histórico / Descrição da Operação")
            
            if st.form_submit_button("Confirmar e Salvar Lançamento"):
                salvar_lancamento_db(empresa_id_atual, data, c_debito, c_credito, valor, historico)
                st.success("Lançamento gravado com sucesso no banco relacional definitivo!")
                st.rerun()

        st.divider()
        st.subheader("📋 Registros Efetuados")
        if len(st.session_state.livro_diario) > 0:
            df_diario = pd.DataFrame(st.session_state.livro_diario)
            df_exibicao = df_diario.copy()
            df_exibicao.columns = ["Nº Lançamento", "Data", "Débito", "Crédito", "Valor", "Histórico"]
            
            if "Valor" in df_exibicao.columns:
                df_exibicao["Valor"] = df_exibicao["Valor"].apply(formatar_br)
            st.dataframe(df_exibicao, use_container_width=True)
            
            csv = df_diario.to_csv(index=False, sep=";", encoding="utf-8-sig").encode('utf-8-sig')
            st.download_button("📤 Exportar Lançamentos para Excel/CSV", data=csv, file_name=f"lancamentos_{empresa_selecionada}.csv", mime="text/csv")
        else:
            st.info("Nenhum lançamento armazenado na nuvem/banco para esta empresa.")

    # --- ABA NOVA: BALANCETE DE VERIFICAÇÃO ---
    elif sub_menu == "⚖️ Balancete":
        st.title("⚖️ Balancete de Verificação")
        st.write(f"Empresa: **{empresa_selecionada}** | CNPJ: {cnpj_empresa_atual}")
        
        # No lugar do botão antigo, cole este componente:
        components.html("""
        <button onclick="window.parent.print()" style="
            padding: 10px 20px; 
            background-color: #0f2a4a; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer;
            font-weight: bold;
            font-family: sans-serif;
        ">🖨️ Imprimir Relatório Profissional</button>
        """, height=50,)

        # Início do Bloco Estrutural Printable (Alvo do Print do Navegador)
        st.markdown(f"""
        <div class="printable-report">
        <div class="printable-report">
            <h2 style='text-align: center; margin-bottom: 5px;'>MAXSUEL CONTABILIDADE</h2>
            <h4 style='text-align: center; margin-top: 0; color:#555;'>BALANCETE DE VERIFICAÇÃO INTEGRAL</h4>
            <hr>
            <p><b>Empresa Emissora:</b> {empresa_selecionada} &nbsp;&nbsp;&nbsp;&nbsp; <b>CNPJ:</b> {cnpj_empresa_atual}</p>
            <p><b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)

        balancete_dados = []
        tot_deb = 0
        tot_cred = 0
        
        conn = conectar_db()
        df_l = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id = ?", conn, params=(int(empresa_id_atual),))
        conn.close()

        for cod, nome in plano_de_contas.items():
            debito_acumulado = df_l[df_l['debito'] == cod]['valor'].sum()
            credito_acumulado = df_l[df_l['credito'] == cod]['valor'].sum()
            
            # Natureza das Contas Contábeis (Ativo/Despesa = Devedora | Passivo/PL/Receita = Credora)
            if cod.startswith(('1', '5', '6')):
                saldo_final = debito_acumulado - credito_acumulado
            else:
                saldo_final = credito_acumulado - debito_acumulado
                
            if debito_acumulado > 0 or credito_acumulado > 0:
                tot_deb += debito_acumulado
                tot_cred += credito_acumulado
                balancete_dados.append({
                    "Código": cod,
                    "Conta Contábil": nome,
                    "Débito (R$)": formatar_br(debito_acumulado),
                    "Crédito (R$)": formatar_br(credito_acumulado),
                    "Saldo Final (R$)": formatar_br(saldo_final)
                })
        
        if balancete_dados:
            st.table(pd.DataFrame(balancete_dados))
            col_b1, col_b2 = st.columns(2)
            col_b1.metric("Total Débitos Movimentados", formatar_br(tot_deb))
            col_b2.metric("Total Créditos Movimentados", formatar_br(tot_cred))
        else:
            st.info("Sem movimentações financeiras para gerar o Balancete.")

    # --- ABA: DRE ---
    elif sub_menu == "📊 DRE":
        st.title("📊 Demonstrativo de Resultado do Exercício (DRE)")
        
        st.markdown('<button onclick="window.print()" style="padding:10px 20px; background-color:#0f2a4a; color:white; border:none; border-radius:5px; cursor:pointer;" class="no-print">🖨️ Imprimir DRE Profissional</button>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="printable-report">
            <h2 style='text-align: center; margin-bottom: 5px;'>MAXSUEL CONTABILIDADE</h2>
            <h4 style='text-align: center; margin-top: 0; color:#555;'>DEMONSTRATIVO DE RESULTADO DO EXERCÍCIO</h4>
            <hr>
            <p><b>Empresa Emissora:</b> {empresa_selecionada} &nbsp;&nbsp;&nbsp;&nbsp; <b>CNPJ:</b> {cnpj_empresa_atual}</p>
        </div>
        """, unsafe_allow_html=True)

        st.metric("LUCRO LÍQUIDO DO PERÍODO", formatar_br(lucro))
        df_dre = pd.DataFrame([
            {"Estrutura Contábil": "Receita Bruta de Vendas (4.x)", "Valor": formatar_br(saldos.get("4.01", 0.0))},
            {"Estrutura Contábil": "(-) Despesas Operacionais (5.01)", "Valor": formatar_br(-saldos.get("5.01", 0.0))},
            {"Estrutura Contábil": "(-) Distribuição de Dividendos (5.02)", "Valor": formatar_br(-saldos.get("5.02", 0.0))},
            {"Estrutura Contábil": "(-) Impostos Incidentes (6.x)", "Valor": formatar_br(-saldos.get("6.01", 0.0))},
            {"Estrutura Contábil": "(=) RESULTADO LÍQUIDO (ARE)", "Valor": formatar_br(lucro)}
        ])
        st.table(df_dre)

    # --- ABA: BALANÇO PATRIMONIAL ---
    elif sub_menu == "⚖️ Balanço Patrimonial":
        st.title("⚖️ Balanço Patrimonial Consolidado")
        
        st.markdown('<button onclick="window.print()" style="padding:10px 20px; background-color:#0f2a4a; color:white; border:none; border-radius:5px; cursor:pointer;" class="no-print">🖨️ Imprimir Balanço Profissional</button>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="printable-report">
            <h2 style='text-align: center; margin-bottom: 5px;'>MAXSUEL CONTABILIDADE</h2>
            <h4 style='text-align: center; margin-top: 0; color:#555;'>BALANÇO PATRIMONIAL CONSOLIDADO</h4>
            <hr>
            <p><b>Empresa Emissora:</b> {empresa_selecionada} &nbsp;&nbsp;&nbsp;&nbsp; <b>CNPJ:</b> {cnpj_empresa_atual}</p>
        </div>
        """, unsafe_allow_html=True)

        saldos_bp = saldos.copy()
        saldos_bp["2.05"] = saldos_bp.get("2.05", 0.0) + lucro  
        col_a, col_p = st.columns(2)
        with col_a:
            st.subheader("🔵 ATIVO")
            ativo_data = [{"Conta": n, "Valor": formatar_br(saldos_bp.get(c, 0.0))} for c, n in plano_de_contas.items() if c.startswith('1')]
            st.table(pd.DataFrame(ativo_data))
            total_ativo = sum(saldos_bp.get(c, 0.0) for c in plano_de_contas if c.startswith('1'))
            st.info(f"**Total do Ativo:** {formatar_br(total_ativo)}")
        with col_p:
            st.subheader("🟡 PASSIVO + PL")
            passivo_data = [{"Conta": n, "Valor": formatar_br(saldos_bp.get(c, 0.0))} for c, n in plano_de_contas.items() if c.startswith('2')]
            st.table(pd.DataFrame(passivo_data))
            total_passivo = sum(saldos_bp.get(c, 0.0) for c in plano_de_contas if c.startswith('2'))
            st.info(f"**Total do Passivo + PL:** {formatar_br(total_passivo)}")

# As outras abas estruturais do seu código ("🧮 Simulador Simples Nacional" e "📋 Módulo de Folha & Fator R") continuam logo abaixo intocadas, mantendo o funcionamento idêntico ao original.

# ==============================================================================
# TELA 3: SIMULADOR DO SIMPLES NACIONAL
# ==============================================================================
elif st.session_state.pagina_selecionada == "🧮 Simulador Simples Nacional":
    st.title("🧮 Super Simulador Comparativo do Simples Nacional")
    
    col_in1, col_in2 = st.columns(2)
    rbt12 = col_in1.number_input("Receita Acumulada nos últimos 12 meses (RBT12):", min_value=0.00, value=250000.00, format="%.2f")
    faturamento_mes = col_in2.number_input("Faturamento Estimado para o Mês Atual:", min_value=0.00, value=20000.00, format="%.2f")
    
    tabelas_calculo = {k: list(v) for k, v in TABELAS_PADRAO.items()}
    resultados = []
    detalhes_impostos = {}

    for nome_anexo, faixas in tabelas_calculo.items():
        rbt12_calculo = rbt12 if rbt12 > 0 else (faturamento_mes if faturamento_mes > 0 else 1.0)
        aliquota_nominal, deducao, encontrou = 0.0, 0.0, False
        
        for limite, aliq, ded in faixas:
            if rbt12_calculo <= limite:
                aliquota_nominal = aliq
                deducao = ded
                encontrou = True
                break
        
        if encontrou:
            if rbt12 == 0: aliquota_efetiva = aliquota_nominal
            else: aliquota_efetiva = ((rbt12 * aliquota_nominal) - deducao) / rbt12
            
            aliquota_efetiva = max(0.0, aliquota_efetiva)
            imposto_total = faturamento_mes * aliquota_efetiva
            
            resultados.append({
                "Anexo": nome_anexo,
                "Alíquota Nominal": f"{aliquota_nominal*100:.2f}%",
                "Alíquota Efetiva Real": f"{aliquota_efetiva*100:.2f}%",
                "Imposto Mensal": imposto_total
            })
            
            rateio = REPARTICAO_IMPOSTOS[nome_anexo]
            detalhes_impostos[nome_anexo] = {imp: imposto_total * pct for imp, pct in rateio.items()}
        else:
            resultados.append({"Anexo": nome_anexo, "Alíquota Nominal": "Excedido", "Alíquota Efetiva Real": "Excedido", "Imposto Mensal": 0.0})

    st.subheader("📊 Painel Comparativo de Cenários")
    df_res = pd.DataFrame(resultados)
    df_res_exibir = df_res.copy()
    df_res_exibir["Imposto Mensal"] = df_res_exibir["Imposto Mensal"].apply(formatar_br)
    st.table(df_res_exibir)
    
    st.divider()
    st.subheader("🔀 Detalhamento e Rateio Interno dos Impostos")
    anexo_detalhe = st.selectbox("Escolha um Anexo para enxergar a divisão da guia do imposto:", list(TABELAS_PADRAO.keys()))
    
    df_rateio_impressao = pd.DataFrame()
    if anexo_detalhe in detalhes_impostos:
        dict_impostos = detalhes_impostos[anexo_detalhe]
        df_rateio = pd.DataFrame([{"Imposto": k, "Valor Destinado": v} for k, v in dict_impostos.items() if v > 0])
        df_rateio_impressao = df_rateio.copy()
        
        col_graf1, col_graf2 = st.columns([1, 1])
        with col_graf1:
            df_rateio_exibir = df_rateio.copy()
            df_rateio_exibir["Valor Destinado"] = df_rateio_exibir["Valor Destinado"].apply(formatar_br)
            st.table(df_rateio_exibir)
        with col_graf2:
            st.bar_chart(df_rateio.set_index("Imposto"))

    # ==============================================================================
    # EXPORTAÇÃO E IMPRESSÃO COM LOGO (HTML IMPRIMÍVEL AUTOMÁTICO)
    # ==============================================================================
    st.divider()
    st.subheader("🖨️ Imprimir Simulação")
    
    # Construção do documento HTML customizado para impressão
    html_linhas_tabela = ""
    for r in resultados:
        imp_v = formatar_br(r["Imposto Mensal"]) if isinstance(r["Imposto Mensal"], (int, float)) else r["Imposto Mensal"]
        html_linhas_tabela += f"<tr><td>{r['Anexo']}</td><td>{r['Alíquota Nominal']}</td><td>{r['Alíquota Efetiva Real']}</td><td><b>{imp_v}</b></td></tr>"
        
    html_linhas_rateio = ""
    if not df_rateio_impressao.empty:
        for idx, row in df_rateio_impressao.iterrows():
            html_linhas_rateio += f"<tr><td>{row['Imposto']}</td><td>{formatar_br(row['Valor Destinado'])}</td></tr>"

    logo_tag = f'<img class="logo" src="data:image/png;base64,{logo_base64}">' if logo_base64 else '<h2 style="color: #0f2a4a; margin:0;">MAXSUEL CONTABILIDADE</h2>'
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Simulação Simples Nacional - Maxsuel Contabilidade</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #333; line-height: 1.5; }}
            .header {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #0f2a4a; padding-bottom: 15px; margin-bottom: 30px; }}
            .logo {{ max-height: 75px; max-width: 220px; object-fit: contain; }}
            .header-info {{ text-align: right; font-size: 13px; color: #666; }}
            .title {{ color: #0f2a4a; font-size: 24px; font-weight: bold; margin: 0 0 5px 0; }}
            .subtitle {{ color: #555; font-size: 15px; margin: 0; }}
            .section-title {{ color: #0f2a4a; font-size: 16px; font-weight: bold; margin-top: 30px; margin-bottom: 12px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            .grid-params {{ display: flex; gap: 40px; background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 25px; border: 1px solid #e2e8f0; }}
            .param-item {{ font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: left; }}
            th {{ background-color: #0f2a4a; color: white; font-weight: 600; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            .footer {{ margin-top: 50px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
            @media print {{
                .btn-print {{ display: none; }}
                body {{ margin: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1 class="title">Maxsuel Contabilidade</h1>
                <p class="subtitle">Relatório Estratégico de Planejamento Tributário</p>
            </div>
            <div>{logo_tag}</div>
        </div>
        
        <div class="header-info">
            Emitido em: {data_atual} | Competência Fiscal: 2026
        </div>

        <div class="section-title">Parâmetros de Entrada Aplicados</div>
        <div class="grid-params">
            <div class="param-item"><b>Receita Acumulada (RBT12):</b> {formatar_br(rbt12)}</div>
            <div class="param-item"><b>Faturamento Projetado para o Mês:</b> {formatar_br(faturamento_mes)}</div>
        </div>

        <div class="section-title">Painel Comparativo de Cenários (Simples Nacional)</div>
        <table>
            <thead>
                <tr>
                    <th>Anexo Fiscal</th>
                    <th>Alíquota Nominal</th>
                    <th>Alíquota Efetiva Real</th>
                    <th>Imposto Mensal Apurado</th>
                </tr>
            </thead>
            <tbody>
                {html_linhas_tabela}
            </tbody>
        </table>

        <div class="section-title">Detalhamento de Rateio Interno da Guia - {anexo_detalhe}</div>
        <table style="max-width: 500px;">
            <thead>
                <tr>
                    <th>Imposto / Ente Federativo</th>
                    <th>Valor Destinado</th>
                </tr>
            </thead>
            <tbody>
                {html_linhas_rateio}
            </tbody>
        </table>

        <div class="footer">
            Hub de Soluções Contábeis Maxsuel © 2026 - Documento gerado eletronicamente para suporte decisório estratégico.
        </div>
        
        <script>
            // Aciona automaticamente a janela de impressão ao abrir o arquivo externo
            window.onload = function() {{ window.print(); }}
        </script>
    </body>
    </html>
    """

    st.info("Clique no botão abaixo para gerar o arquivo de impressão. O relatório virá com a sua logomarca oficial e abrirá a tela de impressão do seu computador automaticamente.")
    st.download_button(
        label="🖨️ Baixar e Imprimir Relatório Fiscal",
        data=html_template,
        file_name=f"Simulacao_Simples_Nacional_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True
    )

# ==============================================================================
# TELA 4: MÓDULO DE FOLHA & FATOR R
# ==============================================================================
elif st.session_state.pagina_selecionada == "📋 Módulo de Folha & Fator R":
    st.title("📋 Painel Estratégico de DP: Folha & Fator R")
    
    sub_aba_dp = st.radio("Escolha a Operação:", ["🔍 Análise do Fator R", "🧮 Simulador Prático de Salário Líquido (2026)"], horizontal=True)
    st.divider()
    
    if sub_aba_dp == "🔍 Análise do Fator R":
        st.subheader("Análise Preventiva do Fator R (Anexos III e V)")
        st.markdown("Insira o histórico acumulado dos últimos 12 meses da empresa para projetar o enquadramento tributário.")
        
        col_f1, col_f2 = st.columns(2)
        faturamento_acumulado = col_f1.number_input("Faturamento Bruto Acumulado (Últimos 12 meses):", min_value=0.00, value=100000.00, step=1000.00, format="%.2f")
        folha_acumulada = col_f2.number_input("Massa Salarial / CPP / Pró-Labore (Últimos 12 meses):", min_value=0.00, value=30000.00, step=500.00, format="%.2f")
        
        if faturamento_acumulado > 0:
            fator_r_calculado = (folha_acumulada / faturamento_acumulado) * 100
            st.metric("Fator R Apurado", f"{fator_r_calculado:.2f}%")
            
            if fator_r_calculado >= 28.0:
                st.success("🟢 **Empresa Enquadrada no Anexo III!** Devido à proporção da folha ser maior ou igual a 28%, a tributação da prestação de serviços iniciará em **6%** em vez de 15,5%.")
            else:
                st.warning("🔴 **Empresa Enquadrada no Anexo V!** Como a proporção da folha está abaixo de 28%, a tributação iniciará na alíquota padrão de **15,50%**.")
                
            progresso = min(1.0, float(fator_r_calculado / 28.0))
            st.progress(progresso, text=f"Proporção da meta legal (Mínimo 28%): {fator_r_calculado:.2f}% / 28,00%")
        else:
            st.info("Insira um valor de faturamento acumulado válido para calcular o Fator R.")
            
    elif sub_aba_dp == "🧮 Simulador Prático de Salário Líquido (2026)":
        st.subheader("Simulador de Folha de Pagamento & Férias - Competência 2026")
        st.markdown("Cálculo integrado com os novos tetos de INSS, deduções legais e regras de férias.")
        
        st.sidebar.header("⚙️ Parâmetros do Trabalhador")
        salario_bruto = st.sidebar.number_input("Salário Bruto / Pró-Labore (R$):", min_value=0.00, value=6500.00, step=100.00, format="%.2f")
        num_dependentes = st.sidebar.number_input("Número de Dependentes:", min_value=0, value=0, step=1)
        
        st.sidebar.subheader("❌ Descontos Legais (Mensais)")
        valor_faltas = st.sidebar.number_input("Valor de Faltas (R$):", min_value=0.00, value=0.00, step=50.00, format="%.2f")
        valor_atrasos = st.sidebar.number_input("Valor de Atrasos/DSR (R$):", min_value=0.00, value=0.00, step=10.00, format="%.2f")
        
        st.sidebar.subheader("🏖️ Opções de Férias")
        calcular_ferias = st.sidebar.checkbox("Simular Recibo de Férias?")
        
        dias_gozo = 30
        abono_pecuniario = False
        adianta_13 = False
        liquido_ferias = 0.0
        
        if calcular_ferias:
            dias_gozo = st.sidebar.slider("Dias de Férias a Gozar:", min_value=10, max_value=30, value=30)
            abono_pecuniario = st.sidebar.checkbox("Vender 1/3 das Férias (Abono Pecuniário)?")
            adianta_13 = st.sidebar.checkbox("Adiantar 1ª Parcela do 13º?")
        
        total_descontos_legais = valor_faltas + valor_atrasos
        salario_sujeito_encargos = max(0.0, salario_bruto - total_descontos_legais)
        
        def calcular_inss_2026(valor_base):
            teto_inss = 8475.55
            salario_calculo_inss = min(valor_base, teto_inss)
            if salario_calculo_inss <= 1621.00: return salario_calculo_inss * 0.075
            elif salario_calculo_inss <= 2902.84: return (salario_calculo_inss * 0.090) - 24.32
            elif salario_calculo_inss <= 4354.27: return (salario_calculo_inss * 0.120) - 111.40
            else: return (salario_calculo_inss * 0.140) - 198.49

        def calcular_irrf_2026(valor_base, inss_retido, dependentes):
            deducao_dependentes = dependentes * 189.59
            base_irrf = max(0.0, valor_base - inss_retido - deducao_dependentes)
            
            if base_irrf <= 2259.20: irrf_bruto = 0.0
            elif base_irrf <= 2826.65: irrf_bruto = (base_irrf * 0.075) - 169.44
            elif base_irrf <= 3751.05: irrf_bruto = (base_irrf * 0.150) - 381.44
            elif base_irrf <= 4664.68: irrf_bruto = (base_irrf * 0.225) - 662.77
            else: irrf_bruto = (base_irrf * 0.275) - 896.00
                
            if base_irrf <= 5000.00: reducao = min(irrf_bruto, 312.89)
            elif base_irrf <= 7350.00: reducao = max(0.0, 978.62 - (0.133145 * base_irrf))
            else: reducao = 0.0
                
            return max(0.0, irrf_bruto - reducao), base_irrf, reducao

        if calcular_ferias:
            st.subheader("🏖️ Demonstrativo de Recibo de Férias")
            dias_faturamento_ferias = 20 if abono_pecuniario else dias_gozo
            
            valor_ferias_gozadas = (salario_bruto / 30) * dias_faturamento_ferias
            terco_constitucional = valor_ferias_gozadas / 3
            
            valor_abono = (salario_bruto / 30) * 10 if abono_pecuniario else 0.0
            terco_abono = valor_abono / 3 if abono_pecuniario else 0.0
            adiantamento_13o_valor = (salario_bruto / 2) if adianta_13 else 0.0
            
            base_tributavel_ferias = valor_ferias_gozadas + terco_constitucional
            inss_ferias = calcular_inss_2026(base_tributavel_ferias)
            irrf_ferias, base_irrf_fer, red_irrf_fer = calcular_irrf_2026(base_tributavel_ferias, inss_ferias, num_dependentes)
            
            total_proventos_ferias = valor_ferias_gozadas + terco_constitucional + valor_abono + terco_abono + adiantamento_13o_valor
            total_descontos_ferias = inss_ferias + irrf_ferias
            liquido_ferias = total_proventos_ferias - total_descontos_ferias
            
            df_ferias = pd.DataFrame([
                {"Evento / Rubrica": f"🟢 Férias Gozadas ({dias_faturamento_ferias} dias)", "Tipo": "Provento", "Valor": formatar_br(valor_ferias_gozadas)},
                {"Evento / Rubrica": "🟢 1/3 Constitucional de Férias", "Tipo": "Provento", "Valor": formatar_br(terco_constitucional)},
                {"Evento / Rubrica": "🟢 Abono Pecuniário (10 dias vendidos)", "Tipo": "Indenização", "Valor": formatar_br(valor_abono)},
                {"Evento / Rubrica": "🟢 1/3 Constitucional sobre Abono", "Tipo": "Indenização", "Valor": formatar_br(terco_abono)},
                {"Evento / Rubrica": "🟢 Adiantamento da 1ª Parcela do 13º", "Tipo": "Adiantamento", "Valor": formatar_br(adiantamento_13o_valor)},
                {"Evento / Rubrica": "🔴 Desconto INSS sobre Férias", "Tipo": "Desconto", "Valor": formatar_br(-inss_ferias)},
                {"Evento / Rubrica": "🔴 Desconto IRRF sobre Férias", "Tipo": "Desconto", "Valor": formatar_br(-irrf_ferias)},
                {"Evento / Rubrica": "💰 VALOR LÍQUIDO DE FÉRIAS A RECEBER", "Tipo": "Totalizador", "Valor": formatar_br(liquido_ferias)},
            ])
            df_ferias = df_ferias[df_ferias["Valor"] != formatar_br(0.0)]
            st.table(df_ferias)

        inss_desconto = calcular_inss_2026(salario_sujeito_encargos)
        irrf_final, base_irrf, reducao_imposto = calcular_irrf_2026(salario_sujeito_encargos, inss_desconto, num_dependentes)
        salario_liquido = salario_sujeito_encargos - inss_desconto - irrf_final
        
        st.subheader("📋 Demonstrativo de Pagamento Mensal Emitido")
        linhas_holerite = [{"Evento / Rubrica": "🟢 Salário Base / Bruto", "Tipo": "Provento", "Valor": formatar_br(salario_bruto)}]
        
        if valor_faltas > 0: linhas_holerite.append({"Evento / Rubrica": "🔴 Desconto de Faltas", "Tipo": "Desconto", "Valor": formatar_br(-valor_faltas)})
        if valor_atrasos > 0: linhas_holerite.append({"Evento / Rubrica": "🔴 Desconto de Atrasos / DSR", "Tipo": "Desconto", "Valor": formatar_br(-valor_atrasos)})
            
        linhas_holerite.extend([
            {"Evento / Rubrica": "🔴 Desconto INSS Previdenciário", "Tipo": "Desconto", "Valor": formatar_br(-inss_desconto)},
            {"Evento / Rubrica": f"⚪ Base de Cálculo Líquida do IRRF ({num_dependentes} dep.)", "Tipo": "Informativo", "Valor": formatar_br(base_irrf)},
            {"Evento / Rubrica": "🟢 Redução de IRRF (Lei nº 15.270/2025)", "Tipo": "Benefício", "Valor": formatar_br(reducao_imposto)},
            {"Evento / Rubrica": "🔴 Desconto IRRF Efetivo Retido", "Tipo": "Desconto", "Valor": formatar_br(-irrf_final)},
            {"Evento / Rubrica": "💰 SALÁRIO LÍQUIDO MENSAL A RECEBER", "Tipo": "Totalizador", "Valor": formatar_br(salario_liquido)},
        ])
        
        df_holerite = pd.DataFrame(linhas_holerite)
        st.table(df_holerite)
        
        if calcular_ferias:
            st.divider()
            st.subheader("💰 Resumo Consolidado de Recebimentos")
            total_liquido_geral = salario_liquido + liquido_ferias
            
            col_g1, col_g2, col_g3 = st.columns(3)
            col_g1.metric("Salário Líquido Mensal", formatar_br(salario_liquido))
            col_g2.metric("Líquido de Férias", formatar_br(liquido_ferias))
            col_g3.metric("TOTAL LÍQUIDO CONSOLIDADO", formatar_br(total_liquido_geral), delta="Mês + Férias", delta_color="inverse")
            st.divider()
        else:
            col_c1, col_c2, col_c3 = st.columns(3)
            col_c1.metric("Total Descontado (Folha)", formatar_br(inss_desconto + irrf_final + total_descontos_legais))
            col_c2.metric("Alíquota Efetiva de INSS", f"{(inss_desconto / salario_sujeito_encargos * 100) if salario_sujeito_encargos > 0 else 0:.2f}%")
            col_c3.metric("IRRF Retido Final", formatar_br(irrf_final))
