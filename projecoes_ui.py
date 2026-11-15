"""Planejamento anual: entradas editáveis, gráficos e exportação reproduzível."""
import json
import pandas as pd
import streamlit as st
from tax_engine import Pendente
from projecoes import gerar_cenario, projetar_ano
from regras import fotografia_regras, verificar_memoria


def renderizar_projecoes():
    st.subheader('Projeção de 1 ano · 12 meses')
    st.write('Planeje um ano-calendário completo, com sazonalidade mensal e apuração por competência. '
             'O Simples usa RBT12 e FS12 móveis; Presumido e Real usam trimestres. '
             'Os componentes calculados não representam a carga global.')
    ano = st.selectbox('Ano da projeção', [2026, 2027], key='projecao_ano')
    try:
        regras = fotografia_regras(ano)
    except Pendente as exc:
        st.warning(str(exc))
        st.caption('2027 ficará disponível após revisão das normas, tabelas e regras de transição correspondentes.')
        return
    st.caption(f"Conjunto normativo: {regras['id']} · em revisão. Sem atualização automática de alíquotas.")
    with st.expander('Preparar premissas financeiras do cenário', expanded=True):
        st.caption('O preenchimento abaixo cria hipóteses financeiras editáveis. Não cria um histórico fiscal real '
                   'nem converte automaticamente despesas em base do Lucro Real.')
        c1, c2, c3 = st.columns(3)
        comercio = c1.number_input('Receita de comércio no 1º mês (R$)', min_value=0.0, value=0.0)
        industria = c2.number_input('Receita de indústria no 1º mês (R$)', min_value=0.0, value=0.0)
        servicos = c3.number_input('Receita de serviços no 1º mês (R$)', min_value=0.0, value=0.0)
        c1, c2, c3 = st.columns(3)
        custos = c1.number_input('Custos e despesas no 1º mês (R$)', min_value=0.0, value=0.0)
        folha = c2.number_input('FS legal no 1º mês (R$)', min_value=0.0, value=0.0)
        crescimento = c3.number_input('Variação mensal das receitas (%)', min_value=-100.0, value=0.0, step=0.5)
        crescimento_custos = st.number_input('Variação mensal de custos, despesas e FS (%)', min_value=-100.0, value=0.0, step=0.5)
        if st.button('Preencher os 12 meses com estas premissas', key='gerar_cenario'):
            bases = dict(comercio=comercio, industria=industria, servicos=servicos,
                         custos_despesas=custos, fs_legal=folha)
            taxas = {k: crescimento/100 if k in ('comercio', 'industria', 'servicos') else crescimento_custos/100 for k in bases}
            cenario = gerar_cenario(bases, taxas)
            for linha in cenario:
                linha.update(resultado_irpj=None, resultado_csll=None,
                             acrescimos_irpj=None, acrescimos_csll=None)
            st.session_state['premissas_projecao'] = cenario
            st.session_state['premissas_gerador'] = dict(bases=bases, taxas=taxas)
            # Uma nova base invalida as edições anteriores para evitar mistura de cenários.
            st.session_state['grade_projecao_versao'] = st.session_state.get('grade_projecao_versao', 0) + 1
    if 'premissas_projecao' not in st.session_state:
        st.info('Preencha as premissas e clique no botão acima. Depois confira ou edite mês a mês.')
        return
    with st.form('projecao_anual_form'):
        st.markdown('**Dados mensais projetados**')
        st.caption('Resultados de partida de IRPJ/CSLL são valores contábeis conciliados, não o saldo gerencial. '
                   'Nos acréscimos do Presumido, informe zero explicitamente quando não houver outros valores. '
                   'Deixar vazio torna o componente pendente.')
        colunas = {campo: st.column_config.NumberColumn(format='%.2f') for campo in
                   ('comercio', 'industria', 'servicos', 'custos_despesas', 'fs_legal',
                    'resultado_irpj', 'resultado_csll', 'acrescimos_irpj', 'acrescimos_csll')}
        grade = st.data_editor(pd.DataFrame(st.session_state['premissas_projecao']),
            key=f"grade_projecao_{st.session_state.get('grade_projecao_versao', 0)}",
            disabled=['mes'], hide_index=True, column_config=colunas)
        st.markdown(f'**Histórico real dos 12 meses de {ano-1}**')
        st.caption('Receita total da empresa e FS legal em cada mês, usadas nas janelas móveis. '
                   'A projeção não substitui dados históricos ausentes por médias.')
        historico = st.data_editor(pd.DataFrame([
            dict(mes=i, receita=None, fs_legal=None) for i in range(1,13)]),
            key='historico_projecao', disabled=['mes'], hide_index=True, column_config={
                'receita': st.column_config.NumberColumn(min_value=0.0, format='%.2f'),
                'fs_legal': st.column_config.NumberColumn(min_value=0.0, format='%.2f')})
        c1,c2 = st.columns(2)
        anexo = c1.selectbox('Anexo dos serviços não sujeitos ao fator R', ['III', 'IV', 'V'], key='proj_anexo')
        fator = c2.checkbox('Serviços sujeitos ao fator R', key='proj_fator')
        st.caption('Receitas especiais, empresa em início de atividade e ICMS/ISS fora do DAS ainda não são abrangidos.')
        saldo_ir = st.text_input('Saldo de prejuízo fiscal em 1º de janeiro (R$; ponto decimal)', key='proj_saldo_ir')
        saldo_cs = st.text_input('Saldo de base negativa de CSLL em 1º de janeiro (R$; ponto decimal)', key='proj_saldo_cs')
        st.markdown('**Adições e exclusões do Real por mês**')
        ajustes = st.data_editor(pd.DataFrame(columns=['mes','descricao','tipo','tributo','valor','fundamento','documento','natureza']),
            num_rows='dynamic', key='ajustes_projecao', column_config={
                'mes': st.column_config.NumberColumn(min_value=1,max_value=12,step=1),
                'tipo': st.column_config.SelectboxColumn(options=['adicao','exclusao']),
                'tributo': st.column_config.SelectboxColumn(options=['IRPJ','CSLL']),
                'valor': st.column_config.NumberColumn(min_value=0.0),
                'natureza': st.column_config.SelectboxColumn(options=['temporaria','permanente'])})
        confirmado = st.checkbox('Conferi as premissas, o histórico, as bases conciliadas e os enquadramentos do cenário', key='proj_confirmado')
        enviado = st.form_submit_button('Projetar os 12 meses')
    if enviado:
        entradas = dict(meses=grade.to_dict('records'), historico=historico.to_dict('records'),
            ano=ano, anexo_servicos=anexo, servicos_fator_r=fator, saldos_irpj=saldo_ir,
            saldos_csll=saldo_cs, ajustes=ajustes.to_dict('records'), confirmado=confirmado)
        try:
            resultado = projetar_ano(**entradas)
        except (Pendente, ValueError, TypeError, KeyError) as exc:
            st.error(f'Projeção pendente: {exc}')
            return
        from planejamento_ui import mostrar
        st.markdown('**Componentes anuais apurados**')
        resumo = []
        for chave, nome in [('simples', 'Simples Nacional'), ('presumido','Lucro Presumido'), ('real','Lucro Real')]:
            total = resultado[chave]['anual']
            resumo.append({'Regime': nome, 'Componentes': 'DAS' if chave=='simples' else 'IRPJ + CSLL',
                'Total anual dos componentes (R$)':
                    float(total['das'] if chave=='simples' else total['irpj']+total['csll']) if total['cobertura_completa'] else None,
                'Situação': 'Componentes calculados; carga global parcial' if total['cobertura_completa'] else 'Pendente; total anual não apresentado'})
        st.dataframe(pd.DataFrame(resumo), hide_index=True, use_container_width=True)
        financeiro = pd.DataFrame(resultado['financeiro'])
        st.markdown('**Receitas e custos/despesas projetados**')
        st.line_chart(financeiro.set_index('mes')[['receita','custos_despesas']].astype(float))
        st.dataframe(financeiro.astype({'receita':float,'custos_despesas':float,'saldo_gerencial_antes_tributos':float}),
                     hide_index=True, use_container_width=True)
        st.markdown('**Apurações e pendências por competência**')
        periodos=[]
        for chave in ('simples','presumido','real'):
            linhas = resultado[chave].get('mensal',resultado[chave].get('trimestral'))
            for linha in linhas:
                result = linha.get('resultado',{})
                periodos.append({'Regime':chave,'Período': f"Mês {linha['mes']}" if 'mes' in linha else f"Trimestre {linha['trimestre']}",
                    'Calculado':linha['calculado'], 'DAS':str(result.get('das','')),
                    'IRPJ':str(result.get('irpj','')), 'CSLL':str(result.get('csll','')), 'Pendência':linha.get('pendencia','')})
        st.dataframe(pd.DataFrame(periodos),hide_index=True,use_container_width=True)
        mostrar(resultado, entradas, 'projecao_anual')


def renderizar_atualizacoes():
    st.subheader('Atualizações e melhorias periódicas')
    snapshot = fotografia_regras(2026)
    st.write('Cada versão registra vigência, fontes, regras implementadas e pendências. '
             'As exportações guardam uma cópia das premissas e das regras, com identificador e hash. '
             'Atualizar o sistema não altera os arquivos de simulação já exportados.')
    st.json(snapshot['regras']['versao'])
    st.caption('Uma mudança de lei precisa de fonte oficial, data de efeitos, revisão e testes. '
               'Não há atualização automática de alíquotas por notícias ou propostas legislativas.')
    st.markdown('**Roteiro de manutenção**')
    st.write('1. Registrar a fonte e comparar a nova redação com a anterior.\n'
             '2. Classificar como proposta, publicada com efeitos futuros ou aplicável ao período.\n'
             '3. Implementar e testar as regras, incluindo transição e exceções.\n'
             '4. Publicar uma nova versão com vigência e histórico de alterações.\n'
             '5. Recalcular um cenário apenas quando solicitado, preservando o relatório anterior.')
    st.caption('Estrutura preparada para manutenção periódica; nenhum agendamento de tarefas externas foi criado.')
    st.markdown('**Consultar uma simulação salva**')
    arquivo = st.file_uploader('Abrir memória JSON exportada pelo sistema', type=['json'], key='memoria_antiga')
    if arquivo is not None:
        try:
            if arquivo.size > 10 * 1024 * 1024:
                raise Pendente('Arquivo acima de 10 MB; use uma memória individual de cálculo.')
            dados = verificar_memoria(json.loads(arquivo.getvalue()))
            st.info(f"Consulta ao arquivo salvo · regras {dados['fotografia_normativa']['id']}. Não foi recalculado.")
            st.caption('O hash verifica a consistência da fotografia normativa. Não certifica autoria, entradas ou resultados.')
            st.json(dados)
        except (Pendente, ValueError, TypeError) as exc:
            st.error(f'Memória não carregada: {exc}')
