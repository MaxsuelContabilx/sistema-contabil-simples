import base64
import os
import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from tax_engine import (
    ATIVIDADES_PRESUMIDO,
    CRONOGRAMA_TRANSICAO_IVA,
    REDUCOES_ALIQUOTA_LC214,
    TABELAS_SIMPLES_NACIONAL,
    ParametrosSimulacao,
    calcular_irrf_dividendos_2026,
    calcular_lucro_presumido,
    calcular_lucro_real,
    calcular_simples_nacional,
    executar_simulacao_completa,
    validar_premissas,
)

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL (MAXSUEL CONTABILIDADE)
# ==============================================================================
st.set_page_config(
    page_title="Maxsuel Gestão Contábil & Planejamento Tributário",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main { background-color: #f8fafc; }
        .stMetric {
            background-color: #ffffff;
            padding: 14px 16px;
            border-radius: 10px;
            border-left: 4px solid #0f2a4a;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .legal-badge {
            display: inline-block;
            background: #e2e8f0;
            color: #0f2a4a;
            padding: 3px 9px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def formatar_br(valor: float) -> str:
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def obter_logo_base64(caminho_img: str):
    if os.path.exists(caminho_img):
        with open(caminho_img, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    return None


# ==============================================================================
# BANCO DE DADOS RELACIONAL (SQLITE) - MÓDULO CONTÁBIL INTEGRADO
# ==============================================================================
DB_PATH = "maxsuel_contabilidade.db"


def conectar_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def inicializar_banco():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL UNIQUE
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()


inicializar_banco()


def carregar_empresas() -> pd.DataFrame:
    conn = conectar_db()
    df = pd.read_sql_query("SELECT id, nome, cnpj FROM empresas ORDER BY nome", conn)
    conn.close()
    return df


def carregar_lancamentos_db(empresa_id: int) -> list:
    conn = conectar_db()
    df = pd.read_sql_query(
        "SELECT id, data, debito, credito, valor, historico FROM lancamentos WHERE empresa_id = ? ORDER BY data DESC, id DESC",
        conn,
        params=(int(empresa_id),),
    )
    conn.close()
    return df.to_dict(orient="records")


def salvar_lancamento_db(empresa_id: int, data, debito: str, credito: str, valor: float, historico: str):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lancamentos (empresa_id, data, debito, credito, valor, historico) VALUES (?, ?, ?, ?, ?, ?)",
        (int(empresa_id), str(data), debito, credito, float(valor), historico),
    )
    conn.commit()
    conn.close()


PLANO_DE_CONTAS = {
    "1.01": "Caixa e Equivalentes de Caixa",
    "1.02": "Bancos Conta Movimento",
    "1.03": "Clientes / Duplicatas a Receber",
    "1.04": "Estoques de Mercadorias",
    "1.05": "Imobilizado",
    "2.01": "Fornecedores a Pagar",
    "2.02": "Obrigações Fiscais e Tributárias",
    "2.03": "Salários e Encargos a Pagar",
    "2.04": "Empréstimos e Financiamentos",
    "2.05": "Capital Social / Lucros Acumulados",
    "4.01": "Receita Bruta de Vendas e Serviços",
    "5.01": "Despesas Operacionais e Administrativas",
    "5.02": "Distribuição de Lucros e Dividendos",
    "6.01": "Impostos e Contribuições Incidentes",
}


def calcular_saldos(empresa_id: int) -> dict:
    conn = conectar_db()
    df_l = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id = ?", conn, params=(int(empresa_id),))
    conn.close()
    saldos = {}
    for cod in PLANO_DE_CONTAS:
        deb = df_l[df_l["debito"] == cod]["valor"].sum() if not df_l.empty else 0.0
        cred = df_l[df_l["credito"] == cod]["valor"].sum() if not df_l.empty else 0.0
        if cod.startswith(("1", "5", "6")):
            saldos[cod] = float(deb - cred)
        else:
            saldos[cod] = float(cred - deb)
    return saldos


# ==============================================================================
# GERADOR DE RELATÓRIO HTML EXECUTIVO PARA IMPRESSÃO / EXPORTAÇÃO
# ==============================================================================
def gerar_relatorio_html(
    titulo_modulo: str,
    parametros_dict: dict,
    colunas_tabela: list,
    dados_tabela: list,
    mem_presumido: dict,
    mem_real: dict,
    mem_simples: dict,
    recomendacao: str,
    observacao: str,
    alertas: list,
) -> str:
    linhas_params = "".join(
        f"<tr><td style='font-weight:600;color:#334155;'>{k}</td><td>{v}</td></tr>"
        for k, v in parametros_dict.items()
    )
    ths = "".join(f"<th>{c}</th>" for c in colunas_tabela)
    trs = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in dados_tabela
    )

    def _dict_rows(d):
        return "".join(f"<tr><td>{k}</td><td style='text-align:right;font-weight:600;'>{v}</td></tr>" for k, v in d.items())

    alertas_html = ""
    if alertas:
        items = "".join(f"<li><strong>{a['titulo']}:</strong> {a['mensagem']}</li>" for a in alertas)
        alertas_html = f"<div class='alert-box'><h4>⚠️ Alertas Legais e Premissas Sinalizadas</h4><ul>{items}</ul></div>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{titulo_modulo}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; margin: 32px; background: #fff; }}
  .header {{ border-bottom: 3px solid #0f2a4a; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }}
  .header h1 {{ margin: 0; color: #0f2a4a; font-size: 20px; }}
  .header .sub {{ color: #64748b; font-size: 12px; }}
  h3 {{ color: #0f2a4a; border-left: 4px solid #d4af37; padding-left: 8px; margin-top: 22px; font-size: 15px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
  th {{ background: #0f2a4a; color: #fff; text-align: left; padding: 8px; }}
  td {{ border: 1px solid #cbd5e1; padding: 7px 8px; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  .grid3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 10px; }}
  .card {{ border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; }}
  .rec-box {{ background: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; padding: 12px; margin-top: 16px; font-size: 13px; }}
  .alert-box {{ background: #fffbeb; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px; margin-top: 16px; font-size: 12px; }}
  .footer {{ margin-top: 28px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 8px; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>MAXSUEL GESTÃO CONTÁBIL & ESTRATÉGICA</h1>
      <div class="sub">{titulo_modulo}</div>
    </div>
    <div class="sub">Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
  </div>
  <h3>Parâmetros da Simulação</h3>
  <table><tbody>{linhas_params}</tbody></table>
  <h3>Quadro Comparativo dos Regimes Tributários</h3>
  <table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>
  <div class="grid3">
    <div class="card"><strong>Simples Nacional</strong><table>{_dict_rows(mem_simples)}</table></div>
    <div class="card"><strong>Lucro Presumido</strong><table>{_dict_rows(mem_presumido)}</table></div>
    <div class="card"><strong>Lucro Real</strong><table>{_dict_rows(mem_real)}</table></div>
  </div>
  <div class="rec-box"><strong>Conclusão Técnica:</strong> {recomendacao}<br><span style="font-size:12px;color:#334155;">{observacao}</span></div>
  {alertas_html}
  <div class="footer">Fundamentação: LC nº 123/2006, Res. CGSN nº 140/2018 e nº 190/2026, LC nº 214/2025, Dec. nº 12.955/2026, LC nº 224/2025, RIR/2018 e Lei nº 15.270/2025.</div>
</body>
</html>"""


# ==============================================================================
# NAVEGAÇÃO PRINCIPAL (SIDEBAR)
# ==============================================================================
opcoes_menu = [
    "🏠 Menu Principal",
    "📊 Planejamento Tributário Comparativo",
    "🧮 Simulador Simples Nacional",
    "📋 Módulo de Folha & Fator R",
    "💻 Módulo Contábil",
]

if "pagina_selecionada" not in st.session_state:
    st.session_state.pagina_selecionada = "🏠 Menu Principal"

with st.sidebar:
    st.markdown("## ⚖️ Maxsuel Contabilidade")
    st.caption("Plataforma Unificada de Planejamento Tributário & Contábil")
    idx_atual = opcoes_menu.index(st.session_state.pagina_selecionada)
    opcao_menu = st.radio("Navegação:", opcoes_menu, index=idx_atual)
    if opcao_menu != st.session_state.pagina_selecionada:
        st.session_state.pagina_selecionada = opcao_menu
        st.rerun()

    st.divider()
    df_empresas = carregar_empresas()
    empresa_id_atual = None
    empresa_selecionada = None
    cnpj_empresa_atual = None
    if not df_empresas.empty:
        nomes_emp = df_empresas["nome"].tolist()
        empresa_selecionada = st.selectbox("Empresa Ativa (Módulo Contábil):", nomes_emp)
        row_emp = df_empresas[df_empresas["nome"] == empresa_selecionada].iloc[0]
        empresa_id_atual = int(row_emp["id"])
        cnpj_empresa_atual = row_emp["cnpj"]
        st.session_state.livro_diario = carregar_lancamentos_db(empresa_id_atual)
    else:
        st.info("Nenhuma empresa cadastrada no banco local.")
        st.session_state.livro_diario = []


# ==============================================================================
# TELA 1: MENU PRINCIPAL
# ==============================================================================
if st.session_state.pagina_selecionada == "🏠 Menu Principal":
    st.title("🏛️ Hub de Soluções Contábeis & Planejamento Tributário")
    st.markdown(
        "Plataforma unificada com cálculos rigorosamente fundamentados na **LC nº 123/2006**, "
        "**Res. CGSN nº 140/2018 e nº 190/2026**, **LC nº 214/2025**, **Decreto nº 12.955/2026**, "
        "**LC nº 224/2025**, **RIR/2018** e **Lei nº 15.270/2025**."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.subheader("📊 Planejamento Tríplice")
        st.write("Comparativo completo Simples x Presumido x Real, DRE, B2B/B2C, Transição 2026–2033 e Dividendos 2026.")
        if st.button("Abrir Planejamento", use_container_width=True):
            st.session_state.pagina_selecionada = "📊 Planejamento Tributário Comparativo"
            st.rerun()
    with c2:
        st.subheader("🧮 Simples Nacional")
        st.write("Anexos I a V oficiais, Fator R, segregação de receitas (exportação, ST, ISS retido) e opção IBS/CBS 2027+.")
        if st.button("Abrir Simulador Simples", use_container_width=True):
            st.session_state.pagina_selecionada = "🧮 Simulador Simples Nacional"
            st.rerun()
    with c3:
        st.subheader("📋 Folha & Fator R")
        st.write("Diagnóstico de Fator R (28%), encargos patronais (CPP/RAT/Terceiros) e impacto Anexo III vs V.")
        if st.button("Abrir Folha & Fator R", use_container_width=True):
            st.session_state.pagina_selecionada = "📋 Módulo de Folha & Fator R"
            st.rerun()
    with c4:
        st.subheader("💻 Módulo Contábil")
        st.write("Cadastro de empresas, Livro Diário, importação CSV, Balancete, DRE e Balanço Patrimonial.")
        if st.button("Abrir Módulo Contábil", use_container_width=True):
            st.session_state.pagina_selecionada = "💻 Módulo Contábil"
            st.rerun()


# ==============================================================================
# TELA 2: PLANEJAMENTO TRIBUTÁRIO COMPARATIVO UNIFICADO
# ==============================================================================
elif st.session_state.pagina_selecionada == "📊 Planejamento Tributário Comparativo":
    st.title("📊 Planejamento Tributário Comparativo (Simples x Presumido x Real)")
    st.markdown(
        '<span class="legal-badge">LC 123/2006 • LC 214/2025 • Dec. 12.955/2026 • LC 224/2025 • RIR/2018 • Lei 15.270/2025</span>',
        unsafe_allow_html=True,
    )

    tab_sim, tab_dre, tab_b2b, tab_transicao, tab_memoria = st.tabs([
        "⚙️ Parâmetros & Comparativo",
        "📑 DRE Comparativa",
        "🏷️ Precificação & B2B",
        "📅 Transição 2026–2033",
        "⚖️ Memória de Cálculo & Base Legal",
    ])

    with tab_sim:
        st.subheader("1. Cenário Temporal e Reforma Tributária")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        ano_ref = col_t1.selectbox("Ano de Referência:", list(range(2026, 2034)), index=0)
        reducao_rotulo = col_t2.selectbox("Redução IBS/CBS (LC 214/2025):", list(REDUCOES_ALIQUOTA_LC214.keys()))
        cbs_ref = col_t3.number_input("CBS Referência (%):", min_value=0.0, max_value=25.0, value=8.80, step=0.1) / 100.0
        ibs_ref = col_t4.number_input("IBS Referência (%):", min_value=0.0, max_value=30.0, value=17.70, step=0.1) / 100.0

        st.subheader("2. Faturamento, Atividade e Segregação de Receitas")
        col_f1, col_f2, col_f3 = st.columns(3)
        fat_mes = col_f1.number_input("Faturamento Mensal (R$):", min_value=0.0, value=120000.0, step=5000.0)
        rbt12 = col_f2.number_input("RBT12 — Receita Bruta 12 Meses (R$):", min_value=0.0, value=1440000.0, step=10000.0)
        atividade_lp = col_f3.selectbox("Atividade (Lucro Presumido):", list(ATIVIDADES_PRESUMIDO.keys()), index=4)

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        anexo_sn = col_s1.selectbox("Anexo Base (Simples Nacional):", list(TABELAS_SIMPLES_NACIONAL.keys()), index=2)
        sujeito_fr = col_s2.checkbox("Atividade sujeita ao Fator R?", value=("Anexo III" in anexo_sn or "Anexo V" in anexo_sn))
        aliq_icms_iss = col_s3.number_input("Alíquota Efetiva ICMS/ISS (%):", min_value=0.0, max_value=25.0, value=5.0, step=0.5) / 100.0
        opcao_iva_sn = col_s4.checkbox(
            "Simples c/ IBS/CBS por fora (2027+)",
            value=False,
            disabled=(ano_ref < 2027),
            help="Opção semestral prevista no Art. 40-C e 40-D da Res. CGSN nº 190/2026 (vigência 01/01/2027).",
        )

        with st.expander("📦 Segregação de Receitas no Simples Nacional (Art. 25 Res. CGSN nº 140/2018)", expanded=False):
            c_seg1, c_seg2, c_seg3 = st.columns(3)
            rec_exp = c_seg1.number_input("Exportação para o Exterior (R$/mês):", min_value=0.0, value=0.0, step=1000.0)
            rec_st = c_seg2.number_input("Receita c/ ICMS-ST / PIS-COFINS Monofásico (R$/mês):", min_value=0.0, value=0.0, step=1000.0)
            rec_iss_ret = c_seg3.number_input("Serviços c/ ISS Retido na Fonte (R$/mês):", min_value=0.0, value=0.0, step=1000.0)

        st.subheader("3. Custos, Despesas, Folha e Insumos")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        cmv_csp = col_c1.number_input("CMV / Custo dos Serviços (R$/mês):", min_value=0.0, value=25000.0, step=1000.0)
        desp_op = col_c2.number_input("Despesas Operacionais Dedutíveis (R$/mês):", min_value=0.0, value=18000.0, step=1000.0)
        insumos_cred = col_c3.number_input("Compras/Insumos c/ Direito a Crédito (R$/mês):", min_value=0.0, value=25000.0, step=1000.0)
        folha_sal = col_c4.number_input("Folha de Salários (R$/mês):", min_value=0.0, value=20000.0, step=1000.0)

        col_c5, col_c6, col_c7, col_c8 = st.columns(4)
        pro_labore = col_c5.number_input("Pró-Labore (R$/mês):", min_value=0.0, value=10000.0, step=500.0)
        informar_folha_12m = col_c6.checkbox("Informar Folha+Encargos 12m real?", value=False)
        folha_12m_val = (
            col_c6.number_input("Folha+Encargos 12m (R$):", min_value=0.0, value=(folha_sal + pro_labore) * 12.0, step=5000.0)
            if informar_folha_12m
            else None
        )
        rat_fap = col_c7.number_input("RAT Ajustado pelo FAP (%):", min_value=0.5, max_value=6.0, value=2.0, step=0.5) / 100.0
        terceiros = col_c8.number_input("Terceiros / Sistema S (%):", min_value=0.0, max_value=10.0, value=5.8, step=0.1) / 100.0

        with st.expander("📘 Ajustes do Lucro Real (LALUR/LACS), Trava 30% e Incentivos LC 224/2025", expanded=False):
            c_lr1, c_lr2, c_lr3 = st.columns(3)
            adicoes = c_lr1.number_input("Adições ao LAIR (R$/mês):", min_value=0.0, value=0.0, step=500.0, help="Despesas não dedutíveis: brindes, multas punitivas, provisões não dedutíveis, MEP negativo.")
            exclusoes = c_lr2.number_input("Exclusões do LAIR (R$/mês):", min_value=0.0, value=0.0, step=500.0, help="Dividendos recebidos, MEP positivo, reversão de provisões.")
            lei_bem = c_lr3.number_input("Exclusão Lei do Bem — P&D (R$/mês):", min_value=0.0, value=0.0, step=500.0, help="Preservada em 100% pela LC nº 224/2025.")
            c_lr4, c_lr5, c_lr6 = st.columns(3)
            prej_fiscal = c_lr4.number_input("Prejuízo Fiscal Acumulado (R$):", min_value=0.0, value=0.0, step=5000.0, help="Compensação limitada a 30% do lucro ajustado (Lei nº 9.065/1995).")
            base_neg_csll = c_lr5.number_input("Base Negativa CSLL Acumulada (R$):", min_value=0.0, value=0.0, step=5000.0)
            incentivos_pat = c_lr6.number_input("Incentivos IRPJ — PAT/Cultura (R$/mês):", min_value=0.0, value=0.0, step=200.0, help="Teto reduzido em 10% pela LC nº 224/2025 (de 4% para 3,6% do IRPJ normal).")
            inst_fin = st.checkbox("Instituição Financeira / Equiparada (CSLL 22% — EC 103/2019)?", value=False)

        with st.expander("💰 Distribuição de Lucros e Dividendos — Regras 2026+ (Lei nº 15.270/2025)", expanded=True):
            c_d1, c_d2, c_d3 = st.columns(3)
            dist_lucros = c_d1.number_input("Distribuição Mensal por Sócio (R$):", min_value=0.0, value=0.0, step=5000.0)
            socio_tipo = c_d2.selectbox("Perfil do Sócio Beneficiário:", ["Pessoa Física Residente", "Pessoa Jurídica"])
            aplicar_sn_15270 = c_d3.checkbox(
                "Aplicar retenção de 10% no Simples Nacional?",
                value=True,
                help="Há controvérsia jurídica frente ao Art. 14 da LC nº 123/2006. Desmarque para simular liminar/tese de isenção.",
            )

        params = ParametrosSimulacao(
            faturamento_mes=fat_mes,
            rbt12=rbt12,
            atividade_presumido=atividade_lp,
            anexo_simples=anexo_sn,
            sujeito_fator_r=sujeito_fr,
            cmv_csp_mes=cmv_csp,
            despesas_op_dedutiveis_mes=desp_op,
            insumos_com_credito_mes=insumos_cred,
            folha_salarios_mes=folha_sal,
            pro_labore_mes=pro_labore,
            folha_encargos_12m=folha_12m_val,
            rat_fap_pct=rat_fap,
            terceiros_pct=terceiros,
            receita_exportacao_mes=rec_exp,
            receita_st_monofasico_mes=rec_st,
            receita_iss_retido_mes=rec_iss_ret,
            ano_referencia=ano_ref,
            aliq_icms_iss_media=aliq_icms_iss,
            cbs_ref_pct=cbs_ref,
            ibs_ref_pct=ibs_ref,
            reducao_iva_rotulo=reducao_rotulo,
            simples_opcao_iva_por_fora=opcao_iva_sn,
            adicoes_mes=adicoes,
            exclusoes_mes=exclusoes,
            lei_do_bem_exclusao_mes=lei_bem,
            prejuizo_fiscal_acumulado=prej_fiscal,
            base_negativa_csll_acumulada=base_neg_csll,
            incentivos_fiscais_irpj_mes=incentivos_pat,
            instituicao_financeira=inst_fin,
            distribuicao_lucros_mes=dist_lucros,
            socio_tipo=socio_tipo,
            aplicar_retencao_simples_15270=aplicar_sn_15270,
        )

        resultado = executar_simulacao_completa(params)
        sn = resultado["simples_nacional"]
        lp = resultado["lucro_presumido"]
        lr = resultado["lucro_real"]

        for al in resultado["alertas"]:
            if al["nivel"] == "erro":
                st.error(f"⛔ **{al['titulo']}**: {al['mensagem']}")
            elif al["nivel"] == "alerta_legal":
                st.warning(f"⚖️ **{al['titulo']}**: {al['mensagem']}")
            else:
                st.info(f"ℹ️ **{al['titulo']}**: {al['mensagem']}")

        st.divider()
        st.subheader("⚖️ Resumo Comparativo de Carga Tributária")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Regime Mais Econômico", resultado["regime_vencedor"])
        m2.metric(
            "Simples Nacional",
            formatar_br(sn["total_tributos"]) if sn["elegivel"] else "Inelegível (>4,8M)",
            f"{sn['aliquota_efetiva_global_pct']:.2f}%",
        )
        m3.metric(
            "Lucro Presumido",
            formatar_br(lp["total_tributos"]) if lp["elegivel"] else "Inelegível (>78M)",
            f"{lp['aliquota_efetiva_global_pct']:.2f}%",
        )
        m4.metric("Lucro Real", formatar_br(lr["total_tributos"]), f"{lr['aliquota_efetiva_global_pct']:.2f}%")

        df_comp = pd.DataFrame(
            [
                {
                    "Regime": "Simples Nacional" + ("" if sn["elegivel"] else " (Vedado)"),
                    "Tributos s/ Venda / DAS": formatar_br(sn["das"] + sn["cbs_fora"] + sn["ibs_fora"] + sn["icms_iss_fora"]),
                    "IRPJ + CSLL": "Incluso no DAS",
                    "CPP Patronal (Fora)": formatar_br(sn["cpp_fora"]),
                    "IRRF Dividendos": formatar_br(sn["irrf_dividendos"]),
                    "Carga Total": formatar_br(sn["total_tributos"]),
                    "Alíq. Efetiva": f"{sn['aliquota_efetiva_global_pct']:.2f}%",
                },
                {
                    "Regime": "Lucro Presumido" + ("" if lp["elegivel"] else " (Vedado)"),
                    "Tributos s/ Venda / DAS": formatar_br(lp["consumo"]["total_consumo"]),
                    "IRPJ + CSLL": formatar_br(lp["irpj"] + lp["csll"]),
                    "CPP Patronal (Fora)": formatar_br(lp["cpp_patronal"]),
                    "IRRF Dividendos": formatar_br(lp["irrf_dividendos"]),
                    "Carga Total": formatar_br(lp["total_tributos"]),
                    "Alíq. Efetiva": f"{lp['aliquota_efetiva_global_pct']:.2f}%",
                },
                {
                    "Regime": "Lucro Real",
                    "Tributos s/ Venda / DAS": formatar_br(lr["consumo"]["total_consumo"]),
                    "IRPJ + CSLL": formatar_br(lr["irpj"] + lr["csll"]),
                    "CPP Patronal (Fora)": formatar_br(lr["cpp_patronal"]),
                    "IRRF Dividendos": formatar_br(lr["irrf_dividendos"]),
                    "Carga Total": formatar_br(lr["total_tributos"]),
                    "Alíq. Efetiva": f"{lr['aliquota_efetiva_global_pct']:.2f}%",
                },
            ]
        )
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        # Exportação do Relatório HTML Executivo
        params_rel = {
            "Ano de Referência": str(ano_ref),
            "Faturamento Mensal": formatar_br(fat_mes),
            "RBT12": formatar_br(rbt12),
            "Atividade (Presumido)": atividade_lp,
            "Anexo Efetivo (Simples)": f"{sn['anexo_efetivo']} (Fator R: {sn['fator_r']*100:.2f}%)",
            "Distribuição de Lucros": formatar_br(dist_lucros),
        }
        dados_rel = [list(row.values()) for row in df_comp.to_dict(orient="records")]
        mem_sn_rel = {
            "Alíquota Nominal / PD": f"{sn['aliquota_nominal_pct']:.2f}% / {formatar_br(sn['parcela_deduzir'])}",
            "Alíquota Efetiva DAS": f"{sn['aliquota_efetiva_das_pct']:.2f}%",
            "DAS Apurado": formatar_br(sn["das"]),
            "CPP Fora (Anexo IV)": formatar_br(sn["cpp_fora"]),
        }
        mem_lp_rel = {
            "Presunção Base IRPJ/CSLL": f"{lp['presuncao_irpj_base_pct']:.1f}% / {lp['presuncao_csll_base_pct']:.1f}%",
            "Parcela Majorada LC 224 (>5M/ano)": formatar_br(lp["parcela_majorada_lc224"]),
            "IRPJ / CSLL": f"{formatar_br(lp['irpj'])} / {formatar_br(lp['csll'])}",
            "Consumo + CPP": f"{formatar_br(lp['consumo']['total_consumo'])} + {formatar_br(lp['cpp_patronal'])}",
        }
        mem_lr_rel = {
            "LAIR Contábil": formatar_br(lr["lair"]),
            "Adições / Exclusões": f"{formatar_br(lr['adicoes'])} / {formatar_br(lr['exclusoes'])}",
            "Compensação Prejuízo (30%)": formatar_br(lr["compensacao_prejuizo_irpj"]),
            "IRPJ / CSLL": f"{formatar_br(lr['irpj'])} / {formatar_br(lr['csll'])}",
        }
        html_rel = gerar_relatorio_html(
            "Relatório Estratégico de Planejamento Tributário Comparativo",
            params_rel,
            list(df_comp.columns),
            dados_rel,
            mem_lp_rel,
            mem_lr_rel,
            mem_sn_rel,
            f"O regime <strong>{resultado['regime_vencedor']}</strong> apresenta a menor carga tributária total de <strong>{formatar_br(resultado['menor_carga_total'])}</strong>/mês.",
            f"Cenário {ano_ref} — {lp['consumo']['fase']}.",
            resultado["alertas"],
        )
        b64_rel = base64.b64encode(html_rel.encode("utf-8")).decode("utf-8")
        st.markdown(
            f'<a href="data:text/html;charset=utf-8;base64,{b64_rel}" download="Relatorio_Planejamento_Tributario_{ano_ref}.html" '
            'style="display:inline-block;background:#0f2a4a;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600;">'
            '🖨️ Baixar Relatório Executivo Completo (HTML)</a>',
            unsafe_allow_html=True,
        )

    with tab_dre:
        st.subheader("📑 DRE Gerencial Comparativa (Mensal)")
        dre_rows = resultado["dre_comparativa"]
        linhas_dre = [k for k in dre_rows[0].keys() if k != "Regime"]
        tabela_dre = []
        for linha in linhas_dre:
            row_dict = {"Conta / Estrutura": linha}
            for r in dre_rows:
                val = r[linha]
                row_dict[r["Regime"]] = f"{val:.2f}%" if "Margem" in linha else formatar_br(val)
            tabela_dre.append(row_dict)
        st.dataframe(pd.DataFrame(tabela_dre), use_container_width=True, hide_index=True)

    with tab_b2b:
        st.subheader("🏷️ Precificação Alvo & Competitividade B2B")
        margem_desejada = st.slider("Margem Líquida Alvo (%):", min_value=5, max_value=50, value=20, step=1) / 100.0
        from tax_engine import calcular_precificacao_e_b2b

        b2b_calc = calcular_precificacao_e_b2b(params, sn, lp, lr, margem_desejada)
        df_b2b = pd.DataFrame(
            [
                {
                    "Regime": reg,
                    "Carga Tributária Efetiva": f"{dados['carga_tributaria_pct']:.2f}%",
                    "Faturamento Necessário p/ Margem Alvo": formatar_br(dados["faturamento_necessario_margem_alvo"]),
                    "Crédito Tributário Transferido ao Cliente B2B": f"{dados['credito_transferido_b2b_pct']:.2f}%",
                }
                for reg, dados in b2b_calc.items()
            ]
        )
        st.dataframe(df_b2b, use_container_width=True, hide_index=True)
        st.caption(
            "Nota Legal: No Simples Nacional Unificado, o adquirente não optante apropria crédito de IBS/CBS limitado ao "
            "montante cobrado no DAS (Art. 49, II, Dec. nº 12.955/2026 e Art. 58, § 4º, Res. CGSN nº 190/2026)."
        )

    with tab_transicao:
        st.subheader("📅 Projeção da Transição Tributária (2026–2033)")
        linhas_t = []
        for ano in range(2026, 2034):
            p_ano = ParametrosSimulacao(**{**params.__dict__, "ano_referencia": ano})
            res_ano = executar_simulacao_completa(p_ano)
            linhas_t.append(
                {
                    "Ano": ano,
                    "Fase Legal": CRONOGRAMA_TRANSICAO_IVA[ano]["fase"],
                    "Simples Nacional": formatar_br(res_ano["simples_nacional"]["total_tributos"]),
                    "Lucro Presumido": formatar_br(res_ano["lucro_presumido"]["total_tributos"]),
                    "Lucro Real": formatar_br(res_ano["lucro_real"]["total_tributos"]),
                    "Melhor Regime": res_ano["regime_vencedor"],
                }
            )
        st.dataframe(pd.DataFrame(linhas_t), use_container_width=True, hide_index=True)

    with tab_memoria:
        st.subheader("⚖️ Memória de Cálculo e Fundamentação Normativa")
        with st.expander("1. Simples Nacional", expanded=True):
            st.write(f"**Anexo Aplicado:** {sn['anexo_efetivo']} (Faixa {sn['faixa']})")
            st.write(f"**Fator R Apurado:** {sn['fator_r']*100:.2f}% | **Alíquota Efetiva DAS:** {sn['aliquota_efetiva_das_pct']:.4f}%")
            st.write(f"**Fundamentação:** {sn['base_legal']}")
        with st.expander("2. Lucro Presumido", expanded=True):
            st.write(f"**Presunção Base:** {lp['presuncao_irpj_base_pct']:.1f}% IRPJ / {lp['presuncao_csll_base_pct']:.1f}% CSLL")
            st.write(f"**Parcela Normal / Majorada LC 224 (+10% > R$ 5M/ano):** {formatar_br(lp['parcela_normal'])} / {formatar_br(lp['parcela_majorada_lc224'])}")
            st.write(f"**Base IRPJ / Base CSLL:** {formatar_br(lp['base_irpj'])} / {formatar_br(lp['base_csll'])}")
            st.write(f"**Fundamentação:** {lp['base_legal']}")
        with st.expander("3. Lucro Real", expanded=True):
            st.write(f"**LAIR:** {formatar_br(lr['lair'])} | **Lucro Real Tributável:** {formatar_br(lr['lucro_real_tributavel'])}")
            st.write(f"**Compensação Prejuízo Fiscal (Trava 30%):** {formatar_br(lr['compensacao_prejuizo_irpj'])}")
            st.write(f"**Incentivo Aplicado (Limite 3,6% LC 224/2025):** {formatar_br(lr['incentivo_aplicado_lc224'])}")
            st.write(f"**Fundamentação:** {lr['base_legal']}")


# ==============================================================================
# TELA 3: SIMULADOR SIMPLES NACIONAL (ATUALIZADO LC 123/2006 + RES. CGSN 190/2026)
# ==============================================================================
elif st.session_state.pagina_selecionada == "🧮 Simulador Simples Nacional":
    st.title("🧮 Simulador do Simples Nacional (LC 123/2006 & Res. CGSN 190/2026)")
    col1, col2, col3 = st.columns(3)
    rbt12_sn = col1.number_input("RBT12 (R$):", min_value=0.0, value=360000.0, step=10000.0)
    fat_sn = col2.number_input("Faturamento do Mês (R$):", min_value=0.0, value=30000.0, step=1000.0)
    ano_sn = col3.selectbox("Ano de Apuração:", list(range(2026, 2034)), index=0)

    col4, col5, col6 = st.columns(3)
    folha_12m_sn = col4.number_input("Folha + Encargos 12m (R$):", min_value=0.0, value=105000.0, step=5000.0)
    insumos_sn = col5.number_input("Compras c/ Crédito IBS/CBS (R$/mês):", min_value=0.0, value=5000.0, step=500.0)
    opcao_fora_sn = col6.checkbox("Simular Opção IBS/CBS Por Fora (2027+)", value=(ano_sn >= 2027), disabled=(ano_sn < 2027))

    linhas_sn = []
    for nome_anexo in TABELAS_SIMPLES_NACIONAL:
        p_item = ParametrosSimulacao(
            faturamento_mes=fat_sn,
            rbt12=rbt12_sn,
            anexo_simples=nome_anexo,
            sujeito_fator_r=False,
            folha_encargos_12m=folha_12m_sn,
            insumos_com_credito_mes=insumos_sn,
            ano_referencia=ano_sn,
            simples_opcao_iva_por_fora=False,
        )
        res_unif = calcular_simples_nacional(p_item)
        p_fora = ParametrosSimulacao(**{**p_item.__dict__, "simples_opcao_iva_por_fora": opcao_fora_sn})
        res_fora = calcular_simples_nacional(p_fora)
        linhas_sn.append(
            {
                "Anexo": nome_anexo,
                "Faixa": res_unif["faixa"],
                "Alíq. Efetiva DAS": f"{res_unif['aliquota_efetiva_das_pct']:.2f}%",
                "DAS Unificado": formatar_br(res_unif["das"]),
                "CPP Fora (Anexo IV)": formatar_br(res_unif["cpp_fora"]),
                "Total Unificado": formatar_br(res_unif["total_tributos"]),
                "Total c/ IBS/CBS Fora (2027+)": formatar_br(res_fora["total_tributos"]) if (ano_sn >= 2027 and opcao_fora_sn) else "N/A (2026)",
            }
        )
    st.dataframe(pd.DataFrame(linhas_sn), use_container_width=True, hide_index=True)


# ==============================================================================
# TELA 4: MÓDULO DE FOLHA & FATOR R
# ==============================================================================
elif st.session_state.pagina_selecionada == "📋 Módulo de Folha & Fator R":
    st.title("📋 Painel Estratégico de DP: Folha & Fator R (Art. 26 Res. CGSN 140/2018)")
    c1, c2, c3 = st.columns(3)
    rbt12_fr = c1.number_input("RBT12 (12 meses anteriores - R$):", min_value=1.0, value=600000.0, step=10000.0)
    folha_12m_fr = c2.number_input("Folha + Pró-Labore + CPP/FGTS 12m (R$):", min_value=0.0, value=150000.0, step=5000.0)
    fat_mes_fr = c3.number_input("Faturamento Mensal Atual (R$):", min_value=0.0, value=50000.0, step=5000.0)

    fator_r_atual = folha_12m_fr / rbt12_fr
    folha_alvo_12m = rbt12_fr * 0.28
    diferenca_anual = max(0.0, folha_alvo_12m - folha_12m_fr)

    m1, m2, m3 = st.columns(3)
    m1.metric("Fator R Atual", f"{fator_r_atual*100:.2f}%", "Anexo III" if fator_r_atual >= 0.28 else "Anexo V")
    m2.metric("Folha Mínima Anual (28%)", formatar_br(folha_alvo_12m))
    m3.metric("Ajuste Anual Necessário", formatar_br(diferenca_anual))

    res_iii = calcular_simples_nacional(
        ParametrosSimulacao(faturamento_mes=fat_mes_fr, rbt12=rbt12_fr, anexo_simples="Anexo III - Serviços (Fator R >= 28% / Locação / Contabilidade)", sujeito_fator_r=False)
    )
    res_v = calcular_simples_nacional(
        ParametrosSimulacao(faturamento_mes=fat_mes_fr, rbt12=rbt12_fr, anexo_simples="Anexo V - Serviços (Fator R < 28% / Engenharia, TI, Consultoria)", sujeito_fator_r=False)
    )
    economia_mensal_das = res_v["das"] - res_iii["das"]
    st.info(
        f"📌 **Comparativo Direto:** No **Anexo V** o DAS mensal é **{formatar_br(res_v['das'])}** ({res_v['aliquota_efetiva_das_pct']:.2f}%). "
        f"Atingindo Fator R >= 28%, cai para **{formatar_br(res_iii['das'])}** ({res_iii['aliquota_efetiva_das_pct']:.2f}%) no **Anexo III** — "
        f"economia bruta de DAS de **{formatar_br(economia_mensal_das)}/mês**."
    )


# ==============================================================================
# TELA 5: MÓDULO CONTÁBIL (PRESERVADO DO PROJETO GITHUB)
# ==============================================================================
elif st.session_state.pagina_selecionada == "💻 Módulo Contábil":
    sub_menu = st.radio(
        "Seções Contábeis:",
        ["🏢 Cadastro de Empresas", "📝 Lançamentos", "⚖️ Balancete", "📊 DRE", "⚖️ Balanço Patrimonial"],
        horizontal=True,
    )

    if sub_menu == "🏢 Cadastro de Empresas":
        st.title("🏢 Painel de Cadastro Corporativo")
        with st.form("form_cadastro_empresa", clear_on_submit=True):
            nome_empresa = st.text_input("Razão Social / Nome Fantasia")
            cnpj_empresa = st.text_input("CNPJ")
            if st.form_submit_button("Salvar Empresa Definitivamente"):
                if nome_empresa and cnpj_empresa:
                    try:
                        conn = conectar_db()
                        conn.execute("INSERT INTO empresas (nome, cnpj) VALUES (?, ?)", (nome_empresa, cnpj_empresa))
                        conn.commit()
                        conn.close()
                        st.success(f"Empresa '{nome_empresa}' cadastrada com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe uma empresa cadastrada com este CNPJ.")
                else:
                    st.error("Preencha todos os campos.")
        st.divider()
        if not df_empresas.empty:
            st.dataframe(df_empresas, use_container_width=True, hide_index=True)

    elif empresa_id_atual is None:
        st.warning("⚠️ Cadastre ou selecione uma empresa na aba '🏢 Cadastro de Empresas'.")

    elif sub_menu == "📝 Lançamentos":
        st.title("📝 Livro Diário de Lançamentos")
        st.info(f"Empresa Ativa: **{empresa_selecionada}** | CNPJ: {cnpj_empresa_atual}")
        with st.form("form_lancamento", clear_on_submit=True):
            c1, c2 = st.columns(2)
            data_l = c1.date_input("Data")
            valor_l = c2.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            c_deb = st.selectbox("Conta Débito", list(PLANO_DE_CONTAS.keys()), format_func=lambda x: f"{x} - {PLANO_DE_CONTAS[x]}")
            c_cred = st.selectbox("Conta Crédito", list(PLANO_DE_CONTAS.keys()), format_func=lambda x: f"{x} - {PLANO_DE_CONTAS[x]}")
            hist_l = st.text_input("Histórico")
            if st.form_submit_button("Confirmar Lançamento"):
                salvar_lancamento_db(empresa_id_atual, data_l, c_deb, c_cred, valor_l, hist_l)
                st.success("Lançamento salvo!")
                st.rerun()

        if st.session_state.livro_diario:
            df_d = pd.DataFrame(st.session_state.livro_diario)
            st.dataframe(df_d, use_container_width=True, hide_index=True)

    elif sub_menu == "⚖️ Balancete":
        st.title("⚖️ Balancete de Verificação")
        conn = conectar_db()
        df_l = pd.read_sql_query("SELECT * FROM lancamentos WHERE empresa_id = ?", conn, params=(int(empresa_id_atual),))
        conn.close()
        dados_bal = []
        for cod, nome in PLANO_DE_CONTAS.items():
            deb = float(df_l[df_l["debito"] == cod]["valor"].sum()) if not df_l.empty else 0.0
            cred = float(df_l[df_l["credito"] == cod]["valor"].sum()) if not df_l.empty else 0.0
            if deb > 0 or cred > 0:
                saldo = (deb - cred) if cod.startswith(("1", "5", "6")) else (cred - deb)
                dados_bal.append({"Código": cod, "Conta": nome, "Débito": formatar_br(deb), "Crédito": formatar_br(cred), "Saldo": formatar_br(saldo)})
        if dados_bal:
            st.table(pd.DataFrame(dados_bal))
        else:
            st.info("Sem movimentações registradas para esta empresa.")

    elif sub_menu == "📊 DRE":
        st.title("📊 Demonstrativo de Resultado do Exercício (DRE)")
        saldos = calcular_saldos(empresa_id_atual)
        lucro = saldos.get("4.01", 0.0) - saldos.get("5.01", 0.0) - saldos.get("5.02", 0.0) - saldos.get("6.01", 0.0)
        st.metric("LUCRO LÍQUIDO DO PERÍODO", formatar_br(lucro))
        st.table(
            pd.DataFrame(
                [
                    {"Estrutura": "Receita Bruta (4.01)", "Valor": formatar_br(saldos.get("4.01", 0.0))},
                    {"Estrutura": "(-) Despesas Operacionais (5.01)", "Valor": formatar_br(-saldos.get("5.01", 0.0))},
                    {"Estrutura": "(-) Distribuição de Dividendos (5.02)", "Valor": formatar_br(-saldos.get("5.02", 0.0))},
                    {"Estrutura": "(-) Impostos Incidentes (6.01)", "Valor": formatar_br(-saldos.get("6.01", 0.0))},
                    {"Estrutura": "(=) Resultado Líquido", "Valor": formatar_br(lucro)},
                ]
            )
        )

    elif sub_menu == "⚖️ Balanço Patrimonial":
        st.title("⚖️ Balanço Patrimonial Consolidado")
        saldos = calcular_saldos(empresa_id_atual)
        lucro = saldos.get("4.01", 0.0) - saldos.get("5.01", 0.0) - saldos.get("5.02", 0.0) - saldos.get("6.01", 0.0)
        saldos["2.05"] = saldos.get("2.05", 0.0) + lucro
        col_a, col_p = st.columns(2)
        with col_a:
            st.subheader("🔵 ATIVO")
            st.table(pd.DataFrame([{"Conta": n, "Valor": formatar_br(saldos.get(c, 0.0))} for c, n in PLANO_DE_CONTAS.items() if c.startswith("1")]))
        with col_p:
            st.subheader("🟡 PASSIVO + PL")
            st.table(pd.DataFrame([{"Conta": n, "Valor": formatar_br(saldos.get(c, 0.0))} for c, n in PLANO_DE_CONTAS.items() if c.startswith("2")]))
