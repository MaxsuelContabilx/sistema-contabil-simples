"""Comparação com uma entrada compartilhada e informações adicionais sob demanda."""
from decimal import Decimal as D
import pandas as pd
import streamlit as st
from texto_ui import legenda
from planejador import planejar
from pj_clt import comparar_vinculos
from tax_engine import Pendente,FONTES


def menu_lateral():
    grupos=[('PLANEJAR',[('Planejamento','Comparar regimes'),('Simples Nacional','Simples Nacional'),
        ('PJ × CLT','PJ × CLT'),('Projeção de 1 ano','Projeção de 1 ano')]),
        ('EMPRESA E ROTINA',[('Empresas e sócios','Empresas e sócios'),('Equipe e salários','Equipe e salários'),
        ('Contabilidade','Contabilidade'),('Relatórios','Relatórios')])]
    def escolher(nome):st.session_state.menu_principal=nome
    for titulo,itens in grupos:
        st.sidebar.caption(titulo)
        for nome,label in itens:
            st.sidebar.button(label,key='nav_'+nome,on_click=escolher,args=(nome,),width='stretch',
                type='primary' if st.session_state.menu_principal==nome else 'secondary')
    with st.sidebar.expander('Mais ferramentas'):
        for nome in ['Ferramentas originais','Ferramentas técnicas']:
            st.button(nome,key='nav_'+nome,on_click=escolher,args=(nome,),width='stretch')
    return st.session_state.menu_principal


def controles_reforma():
    with st.expander('Reforma tributária · comparar cenários'):
        st.write('A comparação já inclui uma projeção com CBS de 11,3% e IBS de 18,7%. Você pode ajustar essas premissas.')
        legenda('Esses percentuais são hipóteses de planejamento, não alíquotas legais definitivas. Este modelo representa a substituição integral futura dos tributos de consumo; não é a apuração da transição de 2026 a 2032.')
        a,b=st.columns(2)
        a.number_input('CBS projetada (%)',min_value=0.0,max_value=100.0,step=.1,key='sc_cbs')
        b.number_input('IBS projetado (%)',min_value=0.0,max_value=100.0,step=.1,key='sc_ibs')
        st.radio('Como tratar o preço na projeção?',['Manter o preço final ao cliente','Repassar CBS e IBS por fora'],key='sc_preco_reforma')
        st.number_input('Redução de CBS e IBS confirmada para a atividade (%)',min_value=0.0,max_value=100.0,key='sc_reducao_iva')
        legenda('A redução exige enquadramento legal confirmado. Não é deduzida automaticamente pelo CNAE.')
        a,b=st.columns(2)
        a.number_input('Crédito de CBS nos custos informados (R$)',min_value=0.0,key='sc_credito_cbs')
        b.number_input('Crédito de IBS nos custos informados (R$)',min_value=0.0,key='sc_credito_ibs')
        legenda('Informe somente créditos elegíveis e vinculados aos custos deste cenário. Saldo credor não é considerado dinheiro disponível para dividendos.')
        st.radio('Simples Nacional na projeção',['Manter no DAS (referência)','CBS e IBS por fora do DAS'],key='sc_simples_reforma')
        if st.session_state.sc_simples_reforma=='CBS e IBS por fora do DAS':
            st.text_input('Parcela mensal do DAS substituída por CBS e IBS (R$)',key='sc_das_substituido',placeholder='Valor confirmado da partilha')
        legenda('O DAS futuro exige a tabela e a partilha do período. Enquanto não revisadas, usa-se a referência de 2026 com identificação expressa; nenhuma partilha é inventada.')


def card_destaque(resultado,criterio):
    from indicadores import destacar_regime
    from plataforma_ui import dinheiro
    d=destacar_regime(resultado,criterio)
    with st.container(border=True):
        if not d['disponivel']:
            st.markdown('#### Melhor regime · aguardando dados')
            st.write(d['motivo']);return d
        st.markdown('#### '+('Melhor resultado provisório' if d['provisorio'] else 'Melhor resultado nos critérios informados'))
        st.markdown('**'+('Empate: ' if d['empate'] else '')+' / '.join(d['regimes'])+'**')
        label='Líquido mensal para os sócios' if criterio=='liquido' else 'Total mensal de tributos · empresa + sócios'
        st.metric(label,dinheiro(d['valor']))
        if d['diferenca'] is not None:legenda('Diferença para o próximo resultado distinto: '+dinheiro(d['diferenca']))
        if d['provisorio']:
            st.warning('Há componentes pendentes. O destaque usa os valores disponíveis e pode mudar após a conferência; não é recomendação definitiva.')
            with st.expander('O que pode mudar esse destaque'):
                for nota in d['pendencias']:legenda(nota)
        legenda(d['nota'])
    return d


def exibir_resultado(p,modelo,*,chave,mostrar_destaque=True):
    from plataforma_ui import dinheiro,botoes_relatorio
    from regras import fotografia_regras
    try:r=planejar(p,modelo)
    except Pendente as exc:st.warning(str(exc));return
    if modelo=='reforma':
        st.info(f"Projeção futura · CBS {p['cbs_pct']:g}% e IBS {p['ibs_pct']:g}% antes da redução informada. Não representa a apuração legal da transição.")
        legenda('Preço ao cliente nesta projeção: '+dinheiro(r['iva']['fatura'])+'. IRPJ, CSLL, DAS e renda dos sócios usam referências de 2026, sujeitas à revisão para o período futuro.')
    criterio='liquido' if st.session_state.sc_criterio=='Maior líquido para os sócios' else 'tributos'
    from indicadores import destacar_regime
    destaque=card_destaque(r,criterio) if mostrar_destaque else destacar_regime(r,criterio)
    linhas=[]
    for coluna,item in zip(st.columns(3),r['resultados']):
        cond=item.get('calculo_condicional',False)
        with coluna,st.container(border=True):
            st.markdown('#### '+item['regime'])
            if cond:legenda('CENÁRIO CONDICIONAL · veja os componentes não incluídos abaixo')
            st.metric('Líquido dos sócios',dinheiro(item.get('liquido_total_socios')))
            st.metric('Tributos da empresa'+(' · subtotal' if cond else ''),dinheiro(item['tributos_empresa']))
            if item['regime']=='Lucro Presumido':
                from tax_engine import ATIVIDADES
                taxas=[]
                for receita_chave,atividade in [('comercio','comercio'),('industria','industria'),('servicos','servicos_gerais')]:
                    if p[receita_chave]:
                        pi,pc=ATIVIDADES[atividade];taxas.append(f"{atividade.replace('_',' ')}: IRPJ {pi*100:g}% / CSLL {pc*100:g}%")
                legenda('Presunção básica · '+'; '.join(taxas))
            st.metric('Dividendos brutos',dinheiro(item.get('dividendo_bruto')))
            st.metric('IR sobre dividendos',dinheiro(item['ir_dividendos']))
            st.metric('Total empresa + sócios',dinheiro(item['total_consolidado']))
            legenda('Total inclui tributos da empresa, IR dos dividendos e INSS/IRRF do pró-labore. Não inclui o ajuste anual da pessoa física.')
            if item.get('aporte_necessario',0):st.warning('Aporte necessário: '+dinheiro(item['aporte_necessario']))
            for nota in item.get('itens_pendentes',[]):legenda(nota)
            if item['tributos_empresa'] is None:
                for nota in item['pendencias']:legenda(nota)
        linhas.append([item['regime']+(' (condicional)' if cond else ''),dinheiro(item['tributos_empresa']),
            dinheiro(item.get('dividendo_bruto')),dinheiro(item['ir_dividendos']),dinheiro(item['total_consolidado']),dinheiro(item.get('liquido_total_socios'))])
    with st.expander('Presunção do Lucro Presumido · percentuais e bases'):
        from presuncao_ui import mostrar_presuncao
        mostrar_presuncao(r['resultados'][1],p)
    sn=r['resultados'][0]['memoria']
    if sn.get('regra'):
        legenda('Simples: '+sn['regra']+' RBT12 para alíquota: '+dinheiro(sn.get('rbt12_proporcional')))
    with st.expander('Ver impostos, pró-labore e memória do cálculo'):
        for item in r['resultados']:
            st.markdown('**'+item['regime']+'**')
            for nome,valor in item['componentes'].items():st.write(nome+': '+dinheiro(valor))
            pro=item.get('prolabore',{})
            for label,k in [('INSS do pró-labore','inss'),('IRRF do pró-labore','irrf'),('Pró-labore líquido','liquido')]:st.write(label+': '+dinheiro(pro.get(k)))
            if pro.get('fundamento'):legenda(pro['fundamento'])
            st.write('Dividendos líquidos: '+dinheiro(item.get('dividendo_liquido')))
            if item.get('dividendos',{}).get('distribuicoes'):
                st.dataframe(pd.DataFrame(item['dividendos']['distribuicoes']).astype(str),hide_index=True)
            if item['memoria'].get('fundamento'):legenda(item['memoria']['fundamento'])
            for nota in item['pendencias']:legenda(nota)
    notas=[f"Competência de referência: {p['mes']:02d}/{p['ano']}. Modelo: {modelo}.",
        'Receita: '+dinheiro(sum(D(str(p[k])) for k in ('comercio','industria','servicos'))),
        'Custos: '+dinheiro(p['custos'])+'; salários: '+dinheiro(p['salarios'])+'; pró-labore bruto: '+dinheiro(p['prolabore']),
        'Distribuição: '+p['modo_distribuicao']]+r['pendencias']
    for item in r['resultados']:notas.extend(item['regime']+': '+n for n in item['pendencias'])
    pres=r['resultados'][1]['memoria']
    for d in pres.get('detalhes',[]):
        if d['receita']:notas.append(f"Presunção {d['atividade']}: receita trimestral {dinheiro(d['receita'])}; IRPJ {d['presuncao_irpj']*100:g}%; CSLL {d['presuncao_csll']*100:g}%; bases IRPJ {dinheiro(d['base_irpj'])} e CSLL {dinheiro(d['base_csll'])}; receitas majoradas IRPJ {dinheiro(d['receita_majorada_irpj'])} e CSLL {dinheiro(d['receita_majorada_csll'])}.")
    if sn.get('regra'):notas.append('Simples: '+sn['regra']+' Meses usados: '+str(sn['meses_utilizados'])+'; RBT12: '+dinheiro(sn['rbt12_proporcional'])+'; '+sn['fundamento'])
    notas.append('Destaque comparativo: '+str(destaque))
    notas+=list(FONTES.values())
    if modelo=='reforma':notas += [f"Premissas: CBS {p['cbs_pct']}%, IBS {p['ibs_pct']}%, redução {p['reducao_iva_pct']}%; preço {p['preco_reforma']}; créditos CBS {p['credito_cbs']} e IBS {p['credito_ibs']}; Simples {p['simples_reforma']}."]
    botoes_relatorio('Planejamento tributário · '+('atual' if modelo=='atual' else 'projeção da reforma'),
        ['Regime','Tributos empresa','Dividendo bruto','IR dividendos','Empresa + sócios','Líquido sócios'],linhas,notas,
        chave=chave,memoria=dict(r,destaque=destaque,regras=fotografia_regras(p['ano'])))


def exibir_comparacao(p,resumo_inicial=None):
    st.markdown('### Seu cenário, três alternativas')
    legenda('Projeções mensais a partir dos mesmos dados. IRPJ e CSLL representam um trimestre constante dividido por três. Campos locais ausentes permanecem identificados; não há indicação definitiva do melhor regime com informações incompletas.')
    if resumo_inicial is None:st.radio('Critério do destaque',['Maior líquido para os sócios','Menor total de tributos'],horizontal=True,key='sc_criterio')
    else:
        with resumo_inicial:
            try:card_destaque(planejar(p),'liquido' if st.session_state.sc_criterio=='Maior líquido para os sócios' else 'tributos')
            except Pendente as exc:st.info('Melhor regime: '+str(exc))
    if p['ano']==2027:
        from inicio_ui import exibir_memoria_temporal
        exibir_memoria_temporal()
    atual,reforma=st.tabs(['Tributação atual · referência 2026','Reforma · projeção CBS e IBS'])
    with atual:exibir_resultado(p,'atual',chave='comparativo_atual',mostrar_destaque=resumo_inicial is None)
    with reforma:exibir_resultado(p,'reforma',chave='comparativo_reforma')


def exibir_pj_clt(p):
    from plataforma_ui import dinheiro,botoes_relatorio
    st.title('PJ × CLT')
    st.write('Compare quanto fica disponível no ano. O lado PJ aproveita atividade, custos, pró-labore e dados dos sócios do planejamento.')
    a,b=st.columns(2)
    salario=a.number_input('Salário bruto mensal da proposta CLT (R$)',min_value=0.0,value=6000.0,step=500.0,key='pj_clt_salario')
    receita=b.number_input('Valor mensal da proposta PJ (R$)',min_value=0.0,value=float(sum(p[k] for k in ('comercio','industria','servicos'))),step=500.0,key='pj_clt_receita')
    a,b=st.columns(2)
    dep=a.number_input('Dependentes na comparação',min_value=0,value=0,key='pj_clt_dependentes')
    meses=b.number_input('Meses com faturamento PJ no ano',min_value=1,max_value=12,value=12,key='pj_clt_meses')
    beneficios=st.number_input('Benefícios mensais da proposta CLT (R$) · separados do salário',min_value=0.0,value=0.0,key='pj_clt_beneficios')
    modelo=st.radio('Tributação do lado PJ',['Atual · referência 2026','Reforma · projeção'],horizontal=True,key='pj_clt_modelo')
    legenda('No cenário PJ: custos mensais '+dinheiro(p['custos'])+', salários '+dinheiro(p['salarios'])+' e pró-labore bruto '+dinheiro(p['prolabore'])+'. Altere esses valores em Comparar regimes.')
    if p['situacao']=='existente':legenda('O RBT12 e a folha histórica são os informados no planejamento; não são recalculados pela proposta. Confirme se o histórico corresponde ao cenário PJ.')
    try:r=comparar_vinculos(salario,receita,p,dependentes=int(dep),beneficios=beneficios,meses_faturados=int(meses),modelo='reforma' if modelo.startswith('Reforma') else 'atual')
    except Pendente as exc:st.warning(str(exc));return
    st.markdown('### Contrato CLT')
    c=r['clt'];col=st.columns(3)
    col[0].metric('Salário líquido mensal',dinheiro(c['mensal']['liquido']))
    col[1].metric('Líquido no ano · CLT',dinheiro(c['liquido_anual']))
    col[2].metric('Média mensal do líquido anual',dinheiro(c['media_mensal_anual']))
    legenda('INSS mensal progressivo: '+dinheiro(c['mensal']['inss'])+' · IRRF mensal: '+dinheiro(c['mensal']['irrf']))
    legenda('FGTS anual: '+dinheiro(c['fgts_anual'])+' · benefícios anuais: '+dinheiro(c['beneficios_anuais'])+' — apresentados separadamente do dinheiro disponível.')
    linhas=[['CLT',dinheiro(c['liquido_anual']),dinheiro(c['media_mensal_anual']),'FGTS e benefícios separados']]
    st.markdown('### Empresa PJ · três regimes')
    for col,item in zip(st.columns(3),r['pj']['resultados']):
        valor=item.get('liquido_anual_pj');cond=item.get('calculo_condicional',False)
        with col,st.container(border=True):
            st.markdown('#### '+item['regime'])
            st.metric('Líquido anual · PJ',dinheiro(valor))
            st.metric('Média mensal no ano',dinheiro(valor/12 if valor is not None else None))
            legenda('Condicional: componentes a confirmar.' if cond else 'Projeção financeira com as referências e hipóteses do cenário.')
            st.write('IR dos dividendos por mês faturado: '+dinheiro(item['ir_dividendos']))
            st.write('INSS mensal do pró-labore: '+dinheiro(item.get('prolabore',{}).get('inss')))
            if meses<12:legenda('Aporte previsto por mês sem nota: '+dinheiro(item.get('aporte_mes_sem_nota')))
            for nota in item['pendencias']:legenda(nota)
        linhas.append([item['regime']+(' (condicional)' if cond else ''),dinheiro(valor),dinheiro(valor/12 if valor is not None else None),'Sem FGTS ou benefícios presumidos'])
    with st.expander('Como foram calculadas as férias e o 13º'):
        st.write('Ano CLT: 11 salários líquidos regulares + férias líquidas com 1/3 + 13º líquido. O salário do mês de férias não é contado duas vezes.')
        st.write('Férias líquidas: '+dinheiro(c['ferias']['liquido'])+' · 13º líquido: '+dinheiro(c['decimo_terceiro']['liquido']))
        legenda(c['mensal']['fundamento'])
    notas=r['notas']+r['pj']['pendencias']
    notas += ['Proposta CLT: '+dinheiro(salario)+'; proposta PJ: '+dinheiro(receita)+f'; meses faturados: {meses}; dependentes: {dep}; modelo: {modelo}.',
        'Custos PJ: '+dinheiro(p['custos'])+'; salários: '+dinheiro(p['salarios'])+'; pró-labore: '+dinheiro(p['prolabore']),
        'FGTS anual separado: '+dinheiro(c['fgts_anual'])+'; benefícios anuais separados: '+dinheiro(c['beneficios_anuais'])]
    notas += ['CLT mensal: INSS '+dinheiro(c['mensal']['inss'])+'; IRRF '+dinheiro(c['mensal']['irrf'])+'; férias líquidas '+dinheiro(c['ferias']['liquido'])+'; 13º líquido '+dinheiro(c['decimo_terceiro']['liquido']),
        f"Premissas da reforma: CBS {p['cbs_pct']}%; IBS {p['ibs_pct']}%; redução {p['reducao_iva_pct']}%; preço {p['preco_reforma']}; créditos CBS {p['credito_cbs']} e IBS {p['credito_ibs']}."]
    for item in r['pj']['resultados']:notas.extend(item['regime']+': '+n for n in item['pendencias'])
    for nota in r['notas']:legenda(nota)
    botoes_relatorio('Comparação PJ × CLT',['Alternativa','Líquido anual','Média mensal','Observação'],linhas,notas,chave='pj_clt',memoria=r)
