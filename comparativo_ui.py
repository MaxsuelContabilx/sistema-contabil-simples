"""Comparação com uma entrada compartilhada e informações adicionais sob demanda."""
from decimal import Decimal as D
import pandas as pd
import streamlit as st
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
        st.caption('Esses percentuais são hipóteses de planejamento, não alíquotas legais definitivas. Este modelo representa a substituição integral futura dos tributos de consumo; não é a apuração da transição de 2026 a 2032.')
        a,b=st.columns(2)
        a.number_input('CBS projetada (%)',min_value=0.0,max_value=100.0,step=.1,key='sc_cbs')
        b.number_input('IBS projetado (%)',min_value=0.0,max_value=100.0,step=.1,key='sc_ibs')
        st.radio('Como tratar o preço na projeção?',['Manter o preço final ao cliente','Repassar CBS e IBS por fora'],key='sc_preco_reforma')
        st.number_input('Redução de CBS e IBS confirmada para a atividade (%)',min_value=0.0,max_value=100.0,key='sc_reducao_iva')
        st.caption('A redução exige enquadramento legal confirmado. Não é deduzida automaticamente pelo CNAE.')
        a,b=st.columns(2)
        a.number_input('Crédito de CBS nos custos informados (R$)',min_value=0.0,key='sc_credito_cbs')
        b.number_input('Crédito de IBS nos custos informados (R$)',min_value=0.0,key='sc_credito_ibs')
        st.caption('Informe somente créditos elegíveis e vinculados aos custos deste cenário. Saldo credor não é considerado dinheiro disponível para dividendos.')
        st.radio('Simples Nacional na projeção',['Manter no DAS (referência)','CBS e IBS por fora do DAS'],key='sc_simples_reforma')
        if st.session_state.sc_simples_reforma=='CBS e IBS por fora do DAS':
            st.text_input('Parcela mensal do DAS substituída por CBS e IBS (R$)',key='sc_das_substituido',placeholder='Valor confirmado da partilha')
        st.caption('O DAS futuro exige a tabela e a partilha do período. Enquanto não revisadas, usa-se a referência de 2026 com identificação expressa; nenhuma partilha é inventada.')


def exibir_resultado(p,modelo,*,chave):
    from plataforma_ui import dinheiro,botoes_relatorio
    from regras import fotografia_regras
    try:r=planejar(p,modelo)
    except Pendente as exc:st.warning(str(exc));return
    if modelo=='reforma':
        st.info(f"Projeção futura · CBS {p['cbs_pct']:g}% e IBS {p['ibs_pct']:g}% antes da redução informada. Não representa a apuração legal da transição.")
        st.caption('Preço ao cliente nesta projeção: '+dinheiro(r['iva']['fatura'])+'. IRPJ, CSLL, DAS e renda dos sócios usam referências de 2026, sujeitas à revisão para o período futuro.')
    linhas=[]
    for coluna,item in zip(st.columns(3),r['resultados']):
        cond=item.get('calculo_condicional',False)
        with coluna,st.container(border=True):
            st.markdown('#### '+item['regime'])
            if cond:st.caption('CENÁRIO CONDICIONAL · veja os componentes não incluídos abaixo')
            st.metric('Líquido dos sócios',dinheiro(item.get('liquido_total_socios')))
            st.metric('Tributos da empresa'+(' · subtotal' if cond else ''),dinheiro(item['tributos_empresa']))
            st.metric('Dividendos brutos',dinheiro(item.get('dividendo_bruto')))
            st.metric('IR sobre dividendos',dinheiro(item['ir_dividendos']))
            st.metric('Total empresa + sócios',dinheiro(item['total_consolidado']))
            st.caption('Total inclui tributos da empresa, IR dos dividendos e INSS/IRRF do pró-labore. Não inclui o ajuste anual da pessoa física.')
            if item.get('aporte_necessario',0):st.warning('Aporte necessário: '+dinheiro(item['aporte_necessario']))
            for nota in item.get('itens_pendentes',[]):st.caption(nota)
            if item['tributos_empresa'] is None:
                for nota in item['pendencias']:st.caption(nota)
        linhas.append([item['regime']+(' (condicional)' if cond else ''),dinheiro(item['tributos_empresa']),
            dinheiro(item.get('dividendo_bruto')),dinheiro(item['ir_dividendos']),dinheiro(item['total_consolidado']),dinheiro(item.get('liquido_total_socios'))])
    with st.expander('Ver impostos, pró-labore e memória do cálculo'):
        for item in r['resultados']:
            st.markdown('**'+item['regime']+'**')
            for nome,valor in item['componentes'].items():st.write(nome+': '+dinheiro(valor))
            pro=item.get('prolabore',{})
            for label,k in [('INSS do pró-labore','inss'),('IRRF do pró-labore','irrf'),('Pró-labore líquido','liquido')]:st.write(label+': '+dinheiro(pro.get(k)))
            if pro.get('fundamento'):st.caption(pro['fundamento'])
            st.write('Dividendos líquidos: '+dinheiro(item.get('dividendo_liquido')))
            if item.get('dividendos',{}).get('distribuicoes'):
                st.dataframe(pd.DataFrame(item['dividendos']['distribuicoes']).astype(str),hide_index=True)
            if item['memoria'].get('fundamento'):st.caption(item['memoria']['fundamento'])
            for nota in item['pendencias']:st.caption(nota)
    notas=[f"Competência de referência: {p['mes']:02d}/{p['ano']}. Modelo: {modelo}.",
        'Receita: '+dinheiro(sum(D(str(p[k])) for k in ('comercio','industria','servicos'))),
        'Custos: '+dinheiro(p['custos'])+'; salários: '+dinheiro(p['salarios'])+'; pró-labore bruto: '+dinheiro(p['prolabore']),
        'Distribuição: '+p['modo_distribuicao']]+r['pendencias']
    for item in r['resultados']:notas.extend(item['regime']+': '+n for n in item['pendencias'])
    notas+=list(FONTES.values())
    if modelo=='reforma':notas += [f"Premissas: CBS {p['cbs_pct']}%, IBS {p['ibs_pct']}%, redução {p['reducao_iva_pct']}%; preço {p['preco_reforma']}; créditos CBS {p['credito_cbs']} e IBS {p['credito_ibs']}; Simples {p['simples_reforma']}."]
    botoes_relatorio('Planejamento tributário · '+('atual' if modelo=='atual' else 'projeção da reforma'),
        ['Regime','Tributos empresa','Dividendo bruto','IR dividendos','Empresa + sócios','Líquido sócios'],linhas,notas,
        chave=chave,memoria=dict(r,regras=fotografia_regras(p['ano'])))


def exibir_comparacao(p):
    st.markdown('### Seu cenário, três alternativas')
    st.caption('Projeções mensais a partir dos mesmos dados. IRPJ e CSLL representam um trimestre constante dividido por três. Campos locais ausentes permanecem identificados; não há indicação definitiva do melhor regime com informações incompletas.')
    atual,reforma=st.tabs(['Tributação atual · referência 2026','Reforma · projeção CBS e IBS'])
    with atual:exibir_resultado(p,'atual',chave='comparativo_atual')
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
    st.caption('No cenário PJ: custos mensais '+dinheiro(p['custos'])+', salários '+dinheiro(p['salarios'])+' e pró-labore bruto '+dinheiro(p['prolabore'])+'. Altere esses valores em Comparar regimes.')
    if p['situacao']=='existente':st.caption('O RBT12 e a folha histórica são os informados no planejamento; não são recalculados pela proposta. Confirme se o histórico corresponde ao cenário PJ.')
    try:r=comparar_vinculos(salario,receita,p,dependentes=int(dep),beneficios=beneficios,meses_faturados=int(meses),modelo='reforma' if modelo.startswith('Reforma') else 'atual')
    except Pendente as exc:st.warning(str(exc));return
    st.markdown('### Contrato CLT')
    c=r['clt'];col=st.columns(3)
    col[0].metric('Salário líquido mensal',dinheiro(c['mensal']['liquido']))
    col[1].metric('Líquido no ano · CLT',dinheiro(c['liquido_anual']))
    col[2].metric('Média mensal do líquido anual',dinheiro(c['media_mensal_anual']))
    st.caption('INSS mensal progressivo: '+dinheiro(c['mensal']['inss'])+' · IRRF mensal: '+dinheiro(c['mensal']['irrf']))
    st.caption('FGTS anual: '+dinheiro(c['fgts_anual'])+' · benefícios anuais: '+dinheiro(c['beneficios_anuais'])+' — apresentados separadamente do dinheiro disponível.')
    linhas=[['CLT',dinheiro(c['liquido_anual']),dinheiro(c['media_mensal_anual']),'FGTS e benefícios separados']]
    st.markdown('### Empresa PJ · três regimes')
    for col,item in zip(st.columns(3),r['pj']['resultados']):
        valor=item.get('liquido_anual_pj');cond=item.get('calculo_condicional',False)
        with col,st.container(border=True):
            st.markdown('#### '+item['regime'])
            st.metric('Líquido anual · PJ',dinheiro(valor))
            st.metric('Média mensal no ano',dinheiro(valor/12 if valor is not None else None))
            st.caption('Condicional: componentes a confirmar.' if cond else 'Projeção financeira com as referências e hipóteses do cenário.')
            st.write('IR dos dividendos por mês faturado: '+dinheiro(item['ir_dividendos']))
            st.write('INSS mensal do pró-labore: '+dinheiro(item.get('prolabore',{}).get('inss')))
            if meses<12:st.caption('Aporte previsto por mês sem nota: '+dinheiro(item.get('aporte_mes_sem_nota')))
            for nota in item['pendencias']:st.caption(nota)
        linhas.append([item['regime']+(' (condicional)' if cond else ''),dinheiro(valor),dinheiro(valor/12 if valor is not None else None),'Sem FGTS ou benefícios presumidos'])
    with st.expander('Como foram calculadas as férias e o 13º'):
        st.write('Ano CLT: 11 salários líquidos regulares + férias líquidas com 1/3 + 13º líquido. O salário do mês de férias não é contado duas vezes.')
        st.write('Férias líquidas: '+dinheiro(c['ferias']['liquido'])+' · 13º líquido: '+dinheiro(c['decimo_terceiro']['liquido']))
        st.caption(c['mensal']['fundamento'])
    notas=r['notas']+r['pj']['pendencias']
    notas += ['Proposta CLT: '+dinheiro(salario)+'; proposta PJ: '+dinheiro(receita)+f'; meses faturados: {meses}; dependentes: {dep}; modelo: {modelo}.',
        'Custos PJ: '+dinheiro(p['custos'])+'; salários: '+dinheiro(p['salarios'])+'; pró-labore: '+dinheiro(p['prolabore']),
        'FGTS anual separado: '+dinheiro(c['fgts_anual'])+'; benefícios anuais separados: '+dinheiro(c['beneficios_anuais'])]
    notas += ['CLT mensal: INSS '+dinheiro(c['mensal']['inss'])+'; IRRF '+dinheiro(c['mensal']['irrf'])+'; férias líquidas '+dinheiro(c['ferias']['liquido'])+'; 13º líquido '+dinheiro(c['decimo_terceiro']['liquido']),
        f"Premissas da reforma: CBS {p['cbs_pct']}%; IBS {p['ibs_pct']}%; redução {p['reducao_iva_pct']}%; preço {p['preco_reforma']}; créditos CBS {p['credito_cbs']} e IBS {p['credito_ibs']}."]
    for item in r['pj']['resultados']:notas.extend(item['regime']+': '+n for n in item['pendencias'])
    for nota in r['notas']:st.caption(nota)
    botoes_relatorio('Comparação PJ × CLT',['Alternativa','Líquido anual','Média mensal','Observação'],linhas,notas,chave='pj_clt',memoria=r)
