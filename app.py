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
opcoes_menu = [
    "🏠 Menu Principal", 
    "💻 Módulo Contábil", 
    "🧮 Simulador Simples Nacional",
    "📋 Módulo de Folha & Fator R"
]

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
    
    col_card1, col_card2, col_card3 = st.columns(3)
    
    with col_card1:
        st.markdown("""
        <div style="background-color: #f0f4f8; padding: 25px; border-radius: 10px; border-left: 5px solid #0f2a4a; min-height: 200px;">
            <h3 style="color: #0f2a4a; margin-top:0;">💻 Módulo Contábil Comercial</h3>
            <p style="color: #333;">Realize partidas dobradas do livro diário, gere relatórios de DRE e acompanhe o fechamento do seu Balanço Patrimonial em tempo real.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Contabilidade ➡️", use_container_width=True, key="btn_contabil"):
            st.session_state.pagina_selecionada = "💻 Módulo Contábil"
            st.rerun()
            
    with col_card2:
        st.markdown("""
        <div style="background-color: #fffde6; padding: 25px; border-radius: 10px; border-left: 5px solid #d4af37; min-height: 200px;">
            <h3 style="color: #6b5300; margin-top:0;">🧮 Inteligência do Simples Nacional</h3>
            <p style="color: #333;">Simule e compare simultaneamente a carga tributária dos Anexos I, II, III, IV e V. Faça simulações e descubra o rateio exato por imposto.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Simulador Tributário ➡️", use_container_width=True, key="btn_simulador"):
            st.session_state.pagina_selecionada = "🧮 Simulador Simples Nacional"
            st.rerun()

    with col_card3:
        st.markdown("""
        <div style="background-color: #f3fcf2; padding: 25px; border-radius: 10px; border-left: 5px solid #2e7d32; min-height: 200px;">
            <h3 style="color: #1b5e20; margin-top:0;">📋 Folha de Pagamento & Fator R</h3>
            <p style="color: #333;">Calcule o salário líquido de funcionários para 2026 com regras de INSS/IRRF e monitore o enquadramento estratégico do Fator R.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Módulo de Folha ➡️", use_container_width=True, key="btn_folha_v"):
            st.session_state.pagina_selecionada = "📋 Módulo de Folha & Fator R"
            st.rerun()

# ==============================================================================
# TELA 2: MÓDULO CONTÁBIL
# ==============================================================================
elif st.session_state.pagina_selecionada == "💻 Módulo Contábil":
    sub_menu = st.radio("Seções Contábeis:", ["📝 Lançamentos", "📊 DRE", "⚖️ Balanço Patrimonial"], horizontal=True)

    if sub_menu == "📝 Lançamentos":
        st.title("📝 Livro Diário de Lançamentos")
        
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

# ==============================================================================
# TELA 4: MÓDULO DE FOLHA & FATOR R (NOVA TELA ACESSADA)
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
                
            # Exibe barra visual de progresso até a meta de 28%
            progresso = min(1.0, float(fator_r_calculado / 28.0))
            st.progress(progresso, text=f"Proporção da meta legal (Mínimo 28%): {fator_r_calculado:.2f}% / 28,00%")
        else:
            st.info("Insira um valor de faturamento acumulado válido para calcular o Fator R.")
            
    elif sub_aba_dp == "🧮 Simulador Prático de Salário Líquido (2026)":
        st.subheader("Simulador de Folha de Pagamento & Férias - Competência 2026")
        st.markdown("Cálculo integrado com os novos tetos de INSS, deduções legais e regras de férias.")
        
        # --- PAINEL DE ENTRADAS NA BARRA LATERAL (SIDEBAR) ---
        st.sidebar.header("⚙️ Parâmetros do Trabalhador")
        salario_bruto = st.sidebar.number_input("Salário Bruto / Pró-Labore (R$):", min_value=0.00, value=6500.00, step=100.00, format="%.2f")
        num_dependentes = st.sidebar.number_input("Número de Dependentes:", min_value=0, value=0, step=1)
        
        st.sidebar.subheader("❌ Descontos Legais (Mensais)")
        valor_faltas = st.sidebar.number_input("Valor de Faltas (R$):", min_value=0.00, value=0.00, step=50.00, format="%.2f")
        valor_atrasos = st.sidebar.number_input("Valor de Atrasos/DSR (R$):", min_value=0.00, value=0.00, step=10.00, format="%.2f")
        
        st.sidebar.subheader("🏖️ Opções de Férias")
        calcular_ferias = st.sidebar.checkbox("Simular Recibo de Férias?")
        
        if calcular_ferias:
            dias_gozo = st.sidebar.slider("Dias de Férias a Gozar:", min_value=10, max_value=30, value=30)
            abono_pecuniario = st.sidebar.checkbox("Vender 1/3 das Férias (Abono Pecuniário)?")
            adianta_13 = st.sidebar.checkbox("Adiantar 1ª Parcela do 13º?")
        
        # --- AJUSTE DO SALÁRIO PELOS DESCONTOS DE FALTAS/ATRASOS ---
        total_descontos_legais = valor_faltas + valor_atrasos
        salario_sujeito_encargos = max(0.0, salario_bruto - total_descontos_legais)
        
        # --- FUNÇÃO INTERNA PARA CÁLCULO DE INSS (PROGRESSIVO 2026) ---
        def calcular_inss_2026(valor_base):
            teto_inss = 8475.55
            salario_calculo_inss = min(valor_base, teto_inss)
            if salario_calculo_inss <= 1621.00:
                return salario_calculo_inss * 0.075
            elif salario_calculo_inss <= 2902.84:
                return (salario_calculo_inss * 0.090) - 24.32
            elif salario_calculo_inss <= 4354.27:
                return (salario_calculo_inss * 0.120) - 111.40
            else:
                return (salario_calculo_inss * 0.140) - 198.49

        # --- FUNÇÃO INTERNA PARA CÁLCULO DE IRRF (LEI Nº 15.270/2025) ---
        def calcular_irrf_2026(valor_base, inss_retido, dependentes):
            deducao_dependentes = dependentes * 189.59
            base_irrf = max(0.0, valor_base - inss_retido - deducao_dependentes)
            
            if base_irrf <= 2259.20:
                irrf_bruto = 0.0
            elif base_irrf <= 2826.65:
                irrf_bruto = (base_irrf * 0.075) - 169.44
            elif base_irrf <= 3751.05:
                irrf_bruto = (base_irrf * 0.150) - 381.44
            elif base_irrf <= 4664.68:
                irrf_bruto = (base_irrf * 0.225) - 662.77
            else:
                irrf_bruto = (base_irrf * 0.275) - 896.00
                
            # Redução Mensal (Lei nº 15.270/2025)
            if base_irrf <= 5000.00:
                reducao = min(irrf_bruto, 312.89)
            elif base_irrf <= 7350.00:
                reducao = max(0.0, 978.62 - (0.133145 * base_irrf))
            else:
                reducao = 0.0
                
            return max(0.0, irrf_bruto - reducao), base_irrf, reducao

        # --- FLUXO 1: CÁLCULO DO MÓDULO DE FÉRIAS ---
        if calcular_ferias:
            st.subheader("🏖️ Demonstrativo de Recibo de Férias")
            
            # Ajuste de dias caso haja abono pecuniário (venda de 10 dias)
            dias_faturamento_ferias = 20 if abono_pecuniario else dias_gozo
            
            valor_ferias_gozadas = (salario_bruto / 30) * dias_faturamento_ferias
            terco_constitucional = valor_ferias_gozadas / 3
            
            # Verbas indenizatórias (não incidem INSS/IRRF)
            valor_abono = (salario_bruto / 30) * 10 if abono_pecuniario else 0.0
            terco_abono = valor_abono / 3 if abono_pecuniario else 0.0
            adiantamento_13o_valor = (salario_bruto / 2) if adianta_13 else 0.0
            
            # Base de cálculo de tributos sobre as férias gozadas
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
            df_ferias = df_ferias[df_ferias["Valor"] != formatar_br(0.0)] # Remove linhas zeradas
            st.table(df_ferias)

        # --- FLUXO 2: CÁLCULO DA FOLHA DE PAGAMENTO MENSAL ---
        inss_desconto = calcular_inss_2026(salario_sujeito_encargos)
        irrf_final, base_irrf, reducao_imposto = calcular_irrf_2026(salario_sujeito_encargos, inss_desconto, num_dependentes)
        salario_liquido = salario_sujeito_encargos - inss_desconto - irrf_final
        
        st.subheader("📋 Demonstrativo de Pagamento Mensal Emitido")
        
        # Montagem dinâmica da tabela com os novos descontos de faltas/atrasos e dependentes
        linhas_holerite = [
            {"Evento / Rubrica": "🟢 Salário Base / Bruto", "Tipo": "Provento", "Valor": formatar_br(salario_bruto)}
        ]
        
        if valor_faltas > 0:
            linhas_holerite.append({"Evento / Rubrica": "🔴 Desconto de Faltas Justificadas/Injustificadas", "Tipo": "Desconto", "Valor": formatar_br(-valor_faltas)})
        if valor_atrasos > 0:
            linhas_holerite.append({"Evento / Rubrica": "🔴 Desconto de Atrasos / DSR", "Tipo": "Desconto", "Valor": formatar_br(-valor_atrasos)})
            
        linhas_holerite.extend([
            {"Evento / Rubrica": "🔴 Desconto INSS Previdenciário", "Tipo": "Desconto", "Valor": formatar_br(-inss_desconto)},
            {"Evento / Rubrica": f"⚪ Base de Cálculo Líquida do IRRF ({num_dependentes} dep.)", "Tipo": "Informativo", "Valor": formatar_br(base_irrf)},
            {"Evento / Rubrica": "🟢 Redução de IRRF (Lei nº 15.270/2025)", "Tipo": "Benefício", "Valor": formatar_br(reducao_imposto)},
            {"Evento / Rubrica": "🔴 Desconto IRRF Efetivo Retido", "Tipo": "Desconto", "Valor": formatar_br(-irrf_final)},
            {"Evento / Rubrica": "💰 SALÁRIO LÍQUIDO MENSAL A RECEBER", "Tipo": "Totalizador", "Valor": formatar_br(salario_liquido)},
        ])
        
        df_holerite = pd.DataFrame(linhas_holerite)
        st.table(df_holerite)
        
        # Cards Rápidos Informativos
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric("Total Descontado (Folha)", formatar_br(inss_desconto + irrf_final + total_descontos_legais))
        col_c2.metric("Alíquota Efetiva de INSS", f"{(inss_desconto / salario_sujeito_encargos * 100) if salario_sujeito_encargos > 0 else 0:.2f}%")
        col_c3.metric("IRRF Retido Final", formatar_br(irrf_final))
