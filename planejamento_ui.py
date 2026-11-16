"""Interface de revisão: cada saída explicita seu recorte e suas pendências."""
import json
from dataclasses import asdict, is_dataclass
from html import escape
import pandas as pd
import streamlit as st
from tax_engine import (ATIVIDADES, Ajuste, Pendente, TABELAS, dividendos_mensais,
                        lucro_real_trimestre, presumido_trimestre, simples_mensal)


def serializar(obj):
    return asdict(obj) if is_dataclass(obj) else str(obj)


def mostrar(resultado, entradas, nome):
    st.warning('Resultado parcial. Não representa carga tributária total ou recomendação de regime.')
    from regras import fotografia_regras
    dados = {'modulo': nome, 'versao': '0.3-revisao-2026', 'entradas': entradas,
             'fotografia_normativa': resultado.get('regras') or fotografia_regras(2026), 'resultado': resultado}
    if nome in ('simples','presumido','real'):
        from plataforma_ui import iniciar,perfil
        from cenario import ir_dividendos_cenario
        from tax_engine import Pendente
        iniciar();p=perfil()
        try:
            meses=[entradas.get('mes',p['mes'])] if nome=='simples' else list(range((entradas.get('trimestre',1)-1)*3+1,entradas.get('trimestre',1)*3+1))
            divs=[ir_dividendos_cenario(p['distribuicoes'],ano=2026,mes=m,fonte=p['empresa']) for m in meses]
            ir=sum((x['irrf'] for x in divs),0)
            base=resultado.get('das') if nome=='simples' else resultado.get('irpj',0)+resultado.get('csll',0)
            dados['dividendos_do_cenario']={'meses':meses,'irrf':ir,'detalhes':divs,'subtotal_componentes_e_irrf':base+ir,
                'nota':'Subtotal dos componentes calculados, não carga tributária global. Retenção dos sócios não é nova despesa da empresa.'}
            st.info(f'IR dos dividendos previsto no mesmo período: R$ {ir:,.2f}. Subtotal dos componentes + IRRF: R$ {base+ir:,.2f}.')
        except Pendente as exc:
            dados['dividendos_do_cenario']={'irrf':None,'pendencia':str(exc)}
            st.warning('IR dos dividendos pendente: '+str(exc))
    campos = [(k, v) for k, v in resultado.items() if k in ('das', 'irpj', 'csll', 'irrf')]
    colunas = st.columns(max(1, len(campos)))
    for coluna, (nome_campo, valor) in zip(colunas, campos):
        coluna.metric(nome_campo.upper(), f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.caption(resultado['fundamento'])
    for pendencia in resultado['pendencias']:
        st.write('• ' + pendencia)
    st.json(json.loads(json.dumps(dados, default=serializar)))
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2, default=serializar)
    st.download_button('Baixar memória de cálculo em JSON', conteudo,
                       file_name=f'{nome}_2026.json', mime='application/json', key=nome+'_json')
    html = ('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Memória de cálculo</title>'
            '<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{color:#0f2a4a}'
            '@media print{button{display:none}}</style>'
            '<h1>Maxsuel · Memória de cálculo</h1><p>Versão de revisão · 2026 · Resultado parcial</p>'
            '<button onclick="window.print()">Imprimir / salvar como PDF</button><pre>'
            + escape(conteudo) + '</pre></html>')
    st.download_button('Baixar relatório para impressão', html, file_name=f'{nome}_2026.html',
                       mime='text/html', key=nome+'_html')


def calcular(acao, entradas, nome):
    try:
        mostrar(acao(), entradas, nome)
    except (Pendente, KeyError, TypeError, ValueError) as exc:
        st.error(f'Cálculo pendente: {exc}')


def renderizar(somente_simples=False):
    st.title('Planejamento tributário · versão de revisão')
    st.info('Recorte implementado: 2026, regras gerais, serviços, comércio e indústria. '
            'Não há alíquotas genéricas de ICMS/ISS nem indicação automática do melhor regime.')
    st.caption('As entradas deste módulo são próprias da simulação. Não importam automaticamente o livro contábil. '
               'Resultados precisam de enquadramento e documentos de suporte.')
    nomes = ['Simples Nacional'] if somente_simples else [
        'Simples Nacional', 'Lucro Presumido', 'Lucro Real', 'Lucros e dividendos', 'Comparação e cobertura',
        'Projeção de 1 ano', 'Atualizações e melhorias']
    abas = st.tabs(nomes)
    with abas[0]:
        st.subheader('DAS mensal · segregação por atividade')
        st.write('Receitas ordinárias de empresa fora das regras de início de atividade e abaixo do sublimite. '
                 'Monofasia, ST, exportação, retenção, isenção, locação com dedução de ISS e demais tratamentos '
                 'especiais exigem rotina própria e são bloqueados nesta versão.')
        with st.form('sn_form'):
            mes = st.number_input('Mês de apuração em 2026', min_value=1, max_value=12, value=1)
            rbt12 = st.number_input('RBT12 anterior ao mês de apuração (R$)', min_value=0.0, value=600000.0)
            fs12 = st.number_input('FS12 legal, incluindo encargos integrantes (R$)', min_value=0.0, value=0.0)
            st.caption('FS12 não é apenas o salário mensal ou o pró-labore. Confirme a composição legal e a janela temporal.')
            receitas = st.data_editor(pd.DataFrame([
                {'descricao': 'Atividade 1', 'valor': 0.0, 'anexo': 'I', 'sujeita_fator_r': False, 'tratamento': 'ordinario'}]),
                num_rows='dynamic', key='receitas_sn', column_config={
                    'anexo': st.column_config.SelectboxColumn(options=list(TABELAS)),
                    'tratamento': st.column_config.SelectboxColumn(options=['ordinario', 'especial_pendente'])})
            confirmado = st.checkbox('Enquadramento por atividade, elegibilidade, empresa madura e situação do sublimite conferidos')
            enviado = st.form_submit_button('Calcular DAS parcial')
        if enviado:
            entradas = dict(mes=mes, ano=2026, rbt12=rbt12, fs12=fs12, receitas=receitas.to_dict('records'), confirmado=confirmado)
            calcular(lambda: simples_mensal(rbt12, fs12, entradas['receitas'],
                enquadramento_confirmado=confirmado, empresa_madura=confirmado,
                sublimite_confirmado=confirmado), entradas, 'simples')
    if somente_simples:
        return
    with abas[1]:
        st.subheader('IRPJ e CSLL trimestrais · limites documentados')
        st.write('O acréscimo de 10% não é aplicado à receita inteira. '
                 'Informe os limites disponíveis confirmados após análise dos períodos anteriores. '
                 'O ajuste de fechamento anual ainda não está implementado.')
        with st.form('lp_form'):
            trimestre = st.selectbox('Trimestre de 2026', [1, 2, 3, 4], key='lp_trimestre')
            receitas = st.data_editor(pd.DataFrame([{'atividade': 'comercio', 'valor': 0.0}]),
                num_rows='dynamic', key='receitas_lp', column_config={
                    'atividade': st.column_config.SelectboxColumn(options=list(ATIVIDADES))})
            limite_ir = st.text_input('Limite disponível IRPJ confirmado (R$; ponto para centavos)', placeholder='Ex.: 1250000.00')
            limite_cs = st.text_input('Limite disponível CSLL confirmado (R$; a partir do 2º trimestre)', placeholder='Ex.: 1250000.00')
            referencia = st.text_area('Base normativa e memória que fundamentam os limites disponíveis')
            outros_ir = st.text_input('Outros acréscimos à base de IRPJ confirmados (R$; informe 0 se inexistentes)')
            outros_cs = st.text_input('Outros acréscimos à base de CSLL confirmados (R$; informe 0 se inexistentes)')
            confirmado = st.checkbox('Enquadramento e elegibilidade ao Lucro Presumido conferidos')
            enviado = st.form_submit_button('Calcular IRPJ/CSLL do Presumido')
        if enviado:
            entradas = dict(ano=2026, trimestre=trimestre, receitas=receitas.to_dict('records'),
                limite_irpj=limite_ir, limite_csll=limite_cs, fundamento=referencia,
                acrescimos_irpj=outros_ir, acrescimos_csll=outros_cs, confirmado=confirmado)
            calcular(lambda: presumido_trimestre(entradas['receitas'], trimestre=trimestre,
                limite_irpj_confirmado=limite_ir, limite_csll_confirmado=limite_cs,
                fundamento_limite=referencia, acrescimos_irpj=outros_ir, acrescimos_csll=outros_cs,
                enquadramento_confirmado=confirmado), entradas, 'presumido')
    with abas[2]:
        st.subheader('Lucro Real trimestral · ajustes separados por tributo')
        st.write('Informe bases contábeis de partida conciliadas, com o tratamento correto das provisões de IRPJ/CSLL. '
                 'Cada adição ou exclusão exige norma, documento e natureza. '
                 'Esta tela aplica a trava geral de 30%; atividades e situações com exceções não estão abrangidas.')
        with st.form('lr_form'):
            trimestre = st.selectbox('Trimestre de 2026', [1, 2, 3, 4], key='lr_trimestre')
            base_ir = st.text_input('Resultado contábil de partida conciliado para IRPJ (R$)')
            base_cs = st.text_input('Resultado contábil de partida conciliado para CSLL (R$)')
            saldo_ir = st.text_input('Prejuízo fiscal apto à compensação (R$; informe 0 se inexistente)')
            saldo_cs = st.text_input('Base negativa de CSLL apta à compensação (R$; informe 0 se inexistente)')
            ajustes_df = st.data_editor(pd.DataFrame(columns=[
                'descricao', 'tipo', 'tributo', 'valor', 'fundamento', 'documento', 'natureza']),
                num_rows='dynamic', key='ajustes_lr', column_config={
                    'tipo': st.column_config.SelectboxColumn(options=['adicao', 'exclusao']),
                    'tributo': st.column_config.SelectboxColumn(options=['IRPJ', 'CSLL']),
                    'natureza': st.column_config.SelectboxColumn(options=['temporaria', 'permanente']),
                    'valor': st.column_config.NumberColumn(min_value=0.0)})
            confirmado = st.checkbox('Regra geral de CSLL 9%, trava de 30%, saldos e bases de partida conferidos')
            enviado = st.form_submit_button('Calcular IRPJ/CSLL do Real')
        if enviado:
            entradas = dict(ano=2026, trimestre=trimestre, resultado_irpj=base_ir, resultado_csll=base_cs,
                prejuizo_fiscal=saldo_ir, base_negativa_csll=saldo_cs, ajustes=ajustes_df.to_dict('records'), confirmado=confirmado)
            def apurar_real():
                ajustes = [Ajuste(**linha) for linha in entradas['ajustes']]
                return lucro_real_trimestre(base_ir, base_cs, ajustes, trimestre=trimestre,
                    prejuizo_fiscal=saldo_ir, base_negativa_csll=saldo_cs, regra_geral_confirmada=confirmado)
            calcular(apurar_real, entradas, 'real')
    with abas[3]:
        st.subheader('IRRF mensal de dividendos · pessoa física residente')
        st.write('Cadastre os eventos de pagamento, crédito, emprego ou entrega. '
                 'A soma é feita por fonte pagadora, beneficiário e mês. '
                 'Acima de R$ 50 mil, os 10% incidem sobre o total alcançado pela regra. '
                 'Não duplique um mesmo fato econômico em datas distintas.')
        with st.form('div_form'):
            eventos_df = st.data_editor(pd.DataFrame([dict(data='2026-01-10', fonte='', beneficiario='',
                beneficiario_tipo='PF_RESIDENTE', origem_resultado='2026', valor=0.0)]),
                num_rows='dynamic', key='eventos_div', column_config={
                    'beneficiario_tipo': st.column_config.SelectboxColumn(options=['PF_RESIDENTE', 'EXTERIOR', 'PJ']),
                    'origem_resultado': st.column_config.SelectboxColumn(options=['2026', '2025_ou_anterior'])})
            enviado = st.form_submit_button('Calcular retenção mensal')
        if enviado:
            entradas = dict(ano=2026, eventos=eventos_df.to_dict('records'))
            calcular(lambda: dividendos_mensais(entradas['eventos']), entradas, 'dividendos')
    with abas[4]:
        st.subheader('Comparação global pendente')
        st.warning('Não comparar o DAS mensal com IRPJ/CSLL trimestrais como se fossem cargas equivalentes. '
                   'A recomendação automática foi retirada desta cópia de revisão até completar todos os componentes.')
        st.dataframe(pd.DataFrame([
            {'Componente': 'DAS ordinário por anexo e fator R', 'Situação': 'Implementado com restrições explícitas'},
            {'Componente': 'IRPJ/CSLL do Presumido', 'Situação': 'Parcial; limites documentados manualmente; fechamento anual pendente'},
            {'Componente': 'Lucro Real e compensações separadas', 'Situação': 'Implementado para regra geral; Parte B e catálogo de ajustes pendentes'},
            {'Componente': 'IRRF mensal de dividendos', 'Situação': 'Implementado para PF residente e lucros de 2026'},
            {'Componente': 'Tributação anual de sócios e redutor', 'Situação': 'Pendente'},
            {'Componente': 'ICMS, ISS, IPI, folha e PIS/Cofins', 'Situação': 'Pendente por operação, local e regime'},
            {'Componente': 'Partilha do DAS, ST e monofasia', 'Situação': 'Pendente'},
            {'Componente': 'IBS/CBS e regras de 2027', 'Situação': 'Pendente; não usar alíquotas estimadas como oficiais'},
        ]), hide_index=True, use_container_width=True)
        st.caption('PLP 299/2026: proposta em tramitação na consulta de 15/11/2026. '
                   'O percentual de 20% não foi ativado como legislação vigente. '
                   'A Res. CGSN 190/2026 prevê efeitos a partir de 01/01/2027.')
    from projecoes_ui import renderizar_projecoes, renderizar_atualizacoes
    with abas[5]:
        renderizar_projecoes()
    with abas[6]:
        renderizar_atualizacoes()
