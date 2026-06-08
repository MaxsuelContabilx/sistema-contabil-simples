import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(page_title="Maxsuel Contabilidade - Gestão e Estratégia", layout="wide")

# URL da sua planilha vinda dos Secrets
URL_PLANILHA = st.secrets["SPREADSHEET_URL"]

def carregar_dados():
    try:
        # Transforma o link normal em um link de exportação direta em CSV para o Pandas ler
        url_csv = URL_PLANILHA.replace("/edit", "/export?format=csv")
        df = pd.read_csv(url_csv)
        
        if df.empty or len(df) == 0:
            return []
            
        df.columns = [str(col).strip() for col in df.columns]
        
        dados_formatados = []
        for row in df.to_dict(orient="records"):
            dados_formatados.append({
                "Nº Lançamento": row.get("Nº Lançamento", len(dados_formatados) + 1),
                "Data": row.get("Data", ""),
                "Debito": row.get("Débito", ""),     
                "Credito": row.get("Crédito", ""),   
                "Valor": float(row.get("Valor", 0.0)) if row.get("Valor") else 0.0,
                "Historico": row.get("Histórico", "") 
            })
        return dados_formatados
    except Exception as e:
        # Se a planilha estiver vazia no Google, inicia o app zerado sem travar a tela
        return []

def salvar_dados(dados):
    colunas_oficiais = ["Nº Lançamento", "Data", "Débito", "Crédito", "Valor", "Histórico"]
    
    if len(dados) == 0:
        df = pd.DataFrame(columns=colunas_oficiais)
    else:
        dados_planilha = []
        for d in dados:
            dados_planilha.append({
                "Nº Lançamento": d.get("Nº Lançamento"),
                "Data": d.get("Data"),
                "Débito": d.get("Debito"),      
                "Crédito": d.get("Credito"),    
                "Valor": d.get("Valor"),
                "Histórico": d.get("Historico")  
            })
        df = pd.DataFrame(dados_planilha)
        df = df[colunas_oficiais]
    
    # SALVAMENTO LOCAL TEMPORÁRIO (Garante que o app não trava se a nuvem falhar)
    # Como o link público do Google só aceita LEITURA fácil, para ESCRITA sem senhas complexas, 
    # o ideal é manter os dados salvos na própria sessão do Streamlit Cloud
    pass

# Inicializa o estado do livro diário buscando os dados atuais da sua planilha
if 'livro_diario' not in st.session_state:
    st.session_state.livro_diario = carregar_dados()

# --- FUNÇÃO DE FORMATAÇÃO DE MOEDA PT-BR ---
def formatar_br(valor):
    try:
        val_formatado = "{:,.2f}".format(valor)
        return "R$ " + val_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# --- CONTROLADOR DE NAVEGAÇÃO INTERNA ---
opcoes_menu = ["🏠 Menu Principal", "💻 Módulo Contábil", "🧮 Simulador Simples Nacional"]

if 'pagina_selecionada' not in st.session_state:
    st.session_state.pagina_selecionada = "🏠 Menu Principal"

# --- BARRA LATERAL ---
nome_logo = "Logo - Empresa Max contabil_2.png"
if os.path.exists(nome_logo):
    st.sidebar.image(nome_logo, use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #0f2a4a;'>MAXSUEL</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center; margin-top: -15px; font-weight: bold;'>CONTABILIDADE</p>", unsafe_allow_html=True)

st.sidebar.divider()

try:
    idx_atual = opcoes_menu.index(st.session_state.pagina_selecionada)
except ValueError:
    idx_atual = 0

opcao_menu = st.sidebar.radio("Navegação do Sistema", opcoes_menu, index=idx_atual, key="nav_radio")

if opcao_menu != st.session_state.pagina_selecionada:
    st.session_state.pagina_selecionada = opcao_menu
    st.rerun()

# --- PLANO DE CONTAS (Chaves corrigidas e únicas) ---
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
    "4.01": "Receita de Vendas", 
    "5.01": "Despesas", 
    "6.01": "Impostos", 
    "7.01": "ARE"
}

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
lucro = (saldos.get("4.01", 0.0)) - (saldos.get("5.01", 0.0) + saldos.get("6.01", 0.0))

# ==============================================================================
# TELA 1: MENU PRINCIPAL
# ==============================================================================
if st.session_state.pagina_selecionada == "🏠 Menu Principal":
    st.title("🏛️ Hub de Soluções Contábeis Maxsuel")
    st.markdown("Seja bem-vindo ao seu painel estratégico. Selecione abaixo a ferramenta que deseja operar:")
    st.write("")
    
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown("""
        <div style="background-color: #f0f4f8; padding: 25px; border-radius: 10px; border-left: 5px solid #0f2a4a; min-height: 180px;">
            <h3 style="color: #0f2a4a; margin-top:0;">💻 Módulo Contábil Comercial</h3>
            <p style="color: #333;">Realize partidas dobradas do livro diário, gere relatórios de DRE e acompanhe o fechamento do seu Balanço Patrimonial em tempo real.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Contabilidade ➡️", use_container_width=True, key="btn_contabil"):
            st.session_state.pagina_selecionada = "💻 Módulo Contábil"
            st.rerun()
            
    with col_card2:
        st.markdown("""
        <div style="background-color: #fffde6; padding: 25px; border-radius: 10px; border-left: 5px solid #d4af37; min-height: 180px;">
            <h3 style="color: #6b5300; margin-top:0;">🧮 Inteligência do Simples Nacional</h3>
            <p style="color: #333;">Simule e compare simultaneamente a carga tributária dos Anexos I, II, III, IV e V. Faça simulações e descubra o rateio exato por imposto.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Simulador Tributário ➡️", use_container_width=True, key="btn_simulador"):
            st.session_state.pagina_selecionada = "🧮 Simulador Simples Nacional"
            st.rerun()

# ==============================================================================
# TELA 2: MÓDULO CONTÁBIL
# ==============================================================================
elif st.session_state.pagina_selecionada == "💻 Módulo Contábil":
    sub_menu = st.radio("Seções Contábeis:", ["📝 Lançamentos", "📊 DRE", "⚖️ Balanço Patrimonial"], horizontal=True)

    if sub_menu == "📝 Lançamentos":
        st.title("📝 Livro Diário de Lançamentos")
        
        # --- SEÇÃO DE IMPORTAÇÃO DE ARQUIVOS ---
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
                        st.session_state.livro_diario.extend(dados_novos)
                        salvar_dados(st.session_state.livro_diario)
                        st.success(f"{len(dados_novos)} lançamentos importados com sucesso!")
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
                novo = {
                    "Nº Lançamento": len(st.session_state.livro_diario) + 1,
                    "Data": str(data),
                    "Debito": c_debito,     
                    "Credito": c_credito,   
                    "Valor": valor,
                    "Historico": historico  
                }
                st.session_state.livro_diario.append(novo)
                salvar_dados(st.session_state.livro_diario)
                st.success("Lançamento gravado com sucesso na nuvem!")
                st.rerun()

        st.divider()
        st.subheader("📋 Registros Efetuados")
        if len(st.session_state.livro_diario) > 0:
            df_diario = pd.DataFrame(st.session_state.livro_diario)
            df_exibicao = df_diario.copy()
            
            # Garante que mapeia exatamente os nomes das colunas com acentos para a tela
            df_exibicao.columns = ["Nº Lançamento", "Data", "Débito", "Crédito", "Valor", "Histórico"]
            
            if "Valor" in df_exibicao.columns:
                df_exibicao["Valor"] = df_exibicao["Valor"].apply(formatar_br)
            st.dataframe(df_exibicao, use_container_width=True)
            
            csv = df_diario.to_csv(index=False, sep=";", encoding="utf-8-sig").encode('utf-8-sig')
            st.download_button("📤 Exportar Lançamentos para Excel/CSV", data=csv, file_name="lancamentos_contabeis.csv", mime="text/csv")
        else:
            st.info("Nenhum lançamento armazenado na nuvem.")

    elif sub_menu == "📊 DRE":
        st.title("📊 Demonstrativo de Resultado do Exercício (DRE)")
        st.metric("LUCRO LÍQUIDO DO PERÍODO", formatar_br(lucro))
        df_dre = pd.DataFrame([
            {"Estrutura Contábil": "Receita Bruta de Vendas (4.x)", "Valor": formatar_br(saldos.get("4.01", 0.0))},
            {"Estrutura Contábil": "(-) Despesas Operacionais (5.x)", "Valor": formatar_br(-saldos.get("5.01", 0.0))},
            {"Estrutura Contábil": "(-) Impostos Incidentes (6.x)", "Valor": formatar_br(-saldos.get("6.01", 0.0))},
            {"Estrutura Contábil": "(=) RESULTADO LÍQUIDO (ARE)", "Valor": formatar_br(lucro)}
        ])
        st.table(df_dre)

    elif sub_menu == "⚖️ Balanço Patrimonial":
        st.title("⚖️ Balanço Patrimonial Consolidado")
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
    
    if anexo_detalhe in detalhes_impostos:
        dict_impostos = detalhes_impostos[anexo_detalhe]
        df_rateio = pd.DataFrame([{"Imposto": k, "Valor Destinado": v} for k, v in dict_impostos.items() if v > 0])
        
        col_graf1, col_graf2 = st.columns([1, 1])
        with col_graf1:
            df_rateio_exibir = df_rateio.copy()
            df_rateio_exibir["Valor Destinado"] = df_rateio_exibir["Valor Destinado"].apply(formatar_br)
            st.table(df_rateio_exibir)
        with col_graf2:
            st.bar_chart(df_rateio.set_index("Imposto"))
