"""Interface operacional com identidade Maxsuel e cenário compartilhado."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import os
import runpy
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from cadastros import listar_empresas,salvar_empresa,importar_lancamentos,conectar
from importacoes import texto_pdf,extrair_cartao,extrair_qsa,ler_lancamentos,ImportacaoInvalida
from cenario import comparar,ir_dividendos_cenario,simples_primeiro_mes
from relatorios import html_relatorio,pdf_relatorio
from tema import aplicar_tema
from planejador import planejar,distribuir_resultado
from tax_engine import Pendente,moeda,numero,faixa_simples,FONTES

BASE=Path(__file__).resolve().parent
DB=Path(os.environ.get('MAXSUEL_DB_PATH',str(BASE/'maxsuel_demonstracao.db')))
LOGO=BASE/'Logo - Empresa Max contabil_2.png'


def dinheiro(v):
    if v is None:return 'Pendente'
    return f'R$ {v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')


def iniciar(preservar_widgets=False):
    padrao={'sc_dark':False,'sc_empresa':'Empresa do planejamento','sc_situacao':'Vai começar agora','sc_atividade':'Comércio',
        'sc_receita':50000.0,'sc_custos':15000.0,'sc_salarios':8000.0,'sc_prolabore':3000.0,
        'sc_comercio':0.0,'sc_industria':0.0,'sc_servicos':0.0,
        'sc_encargos_fs':0.0,'sc_mes':1,'sc_ano':2026,'sc_anexo':'III','sc_fator':False,
        'sc_rbt12':'','sc_fs12':'','sc_impostos_local':'','sc_patronal':'','sc_patronal_sn':'',
        'sc_cnpj':'','sc_cnae':'','sc_municipio':'','sc_uf':'','sc_data_abertura':'',
        'sc_credito_pis':0.0,'sc_credito_cofins':0.0,'sc_pis_regra':True,
        'sc_saldo_ir':'0','sc_saldo_cs':'0','sc_outros_ir':'0','sc_outros_cs':'0',
        'sc_limite_ir':'1250000','sc_limite_cs':'1250000','sc_dividendo':0.0,
        'sc_beneficiario':'Sócio do cenário','sc_tipo_div':'PF residente no Brasil','sc_origem_div':'2026',
        'sc_modo_distribuicao':'Distribuir todo o saldo','sc_rateio_qsa':False,'sc_dependentes_socio':0,
        'sc_cbs':11.3,'sc_ibs':18.7,'sc_reducao_iva':0.0,'sc_preco_reforma':'Manter o preço final ao cliente',
        'sc_credito_cbs':0.0,'sc_credito_ibs':0.0,'sc_simples_reforma':'Manter no DAS (referência)',
        'sc_das_substituido':'','sc_dispensa_teste_2026':False,'menu_principal':'Planejamento','sc_socios':[],'sc_modo_socios':False}
    for k,v in padrao.items():
        if k not in st.session_state:st.session_state[k]=v
        elif preservar_widgets:st.session_state[k]=st.session_state[k]


def perfil():
    s=st.session_state
    receitas={'comercio':0,'industria':0,'servicos':0}
    if s.sc_atividade=='Mais de uma atividade':
        receitas={k:s.get('sc_'+k,0) for k in receitas}
    else:receitas[{'Comércio':'comercio','Indústria':'industria','Serviços em geral':'servicos'}[s.sc_atividade]]=s.sc_receita
    receita=sum(receitas.values())
    def monetario(v):
        if v is None or not str(v).strip():return None
        t=str(v).strip().replace('R$','').replace(' ','')
        if ',' in t:t=t.replace('.','').replace(',','.')
        return numero(t)
    def valor(k):return monetario(s.get(k))
    imposto=valor('sc_impostos_local');patronal=valor('sc_patronal')
    regra=s.sc_pis_regra
    tributos={'presumido':{'PIS':moeda(Decimal(str(receita))*Decimal('.0065')) if regra else None,
        'COFINS':moeda(Decimal(str(receita))*Decimal('.03')) if regra else None,'ICMS/ISS/IPI':imposto,'Encargos da folha':patronal},
        'real':{'PIS':max(Decimal('0'),moeda(Decimal(str(receita))*Decimal('.0165'))-Decimal(str(s.sc_credito_pis))) if regra else None,
        'COFINS':max(Decimal('0'),moeda(Decimal(str(receita))*Decimal('.076'))-Decimal(str(s.sc_credito_cofins))) if regra else None,
        'ICMS/ISS/IPI':imposto,'Encargos da folha':patronal}}
    if s.sc_modo_socios:
        distrib=[{'nome':x.get('nome'),'tipo':{'PF residente no Brasil':'PF_RESIDENTE'}.get(x.get('tipo_beneficiario'),'PENDENTE'),
            'origem':s.sc_origem_div,'valor':monetario(x.get('dividendo_mensal','0')) or 0,
            'percentual_distribuicao':monetario(x.get('participacao') if s.sc_rateio_qsa else x.get('percentual_distribuicao'))} for x in s.sc_socios]
    else:distrib=[dict(nome=s.sc_beneficiario,tipo='PF_RESIDENTE' if s.sc_tipo_div=='PF residente no Brasil' else 'PENDENTE',
                       origem=s.sc_origem_div,valor=s.sc_dividendo)]
    return dict(empresa=s.sc_empresa,ano=s.sc_ano,mes=s.sc_mes,situacao='abertura' if s.sc_situacao=='Vai começar agora' else 'existente',
        **receitas,custos=s.sc_custos,salarios=s.sc_salarios,prolabore=s.sc_prolabore,encargos_fs=s.sc_encargos_fs,
        anexo=s.sc_anexo,fator_r=s.sc_fator,rbt12=valor('sc_rbt12'),fs12=valor('sc_fs12'),
        patronal_simples=valor('sc_patronal_sn'),tributos=tributos,distribuicoes=distrib,
        limite_irpj=valor('sc_limite_ir'),limite_csll=valor('sc_limite_cs'),
        fundamento_limite='LC 224/2025, art. 4º §5º; limite nominal por trimestre, sem aproveitamento automático de sobras.',
        acrescimos_irpj=valor('sc_outros_ir'),acrescimos_csll=valor('sc_outros_cs'),
        saldo_irpj=valor('sc_saldo_ir'),saldo_csll=valor('sc_saldo_cs'),
        modo_distribuicao='automatico' if s.sc_modo_distribuicao=='Distribuir todo o saldo' else 'manual',
        atividade_anexo_iv=s.sc_atividade in ('Serviços em geral','Mais de uma atividade') and s.sc_anexo=='IV' and not s.sc_fator,
        dependentes_socio=s.sc_dependentes_socio,usar_regras_federais=regra,credito_pis=s.sc_credito_pis,credito_cofins=s.sc_credito_cofins,
        cbs_pct=s.sc_cbs,ibs_pct=s.sc_ibs,reducao_iva_pct=s.sc_reducao_iva,
        preco_reforma='final' if s.sc_preco_reforma=='Manter o preço final ao cliente' else 'repassar',
        credito_cbs=s.sc_credito_cbs,credito_ibs=s.sc_credito_ibs,
        simples_reforma='dentro' if s.sc_simples_reforma=='Manter no DAS (referência)' else 'fora',das_substituido=valor('sc_das_substituido'),
        dispensa_teste_2026_confirmada=s.sc_dispensa_teste_2026)


def botoes_relatorio(titulo,colunas,linhas,notas=(),chave='relatorio',memoria=None):
    kwargs=dict(empresa=st.session_state.sc_empresa,observacoes=notas,logo=LOGO)
    pdf=pdf_relatorio(titulo,colunas,linhas,**kwargs)
    html=html_relatorio(titulo,colunas,linhas,**kwargs)
    c1,c2=st.columns(2)
    c1.download_button('Baixar relatório em PDF',pdf,file_name=chave+'.pdf',mime='application/pdf',key=chave+'_pdf')
    c2.download_button('Baixar versão para impressão',html,file_name=chave+'.html',mime='text/html',key=chave+'_html')
    if memoria is not None:
        st.download_button('Baixar memória com os dados do cenário',json.dumps(memoria,ensure_ascii=False,indent=2,default=str),
            file_name=chave+'.json',mime='application/json',key=chave+'_json')
    with st.expander('Imprimir agora'):
        st.caption('Use o botão Imprimir relatório dentro do documento. Você também pode baixar o PDF e imprimir pelo navegador.')
        components.html(html,height=430,scrolling=True)


def resumo_dividendos(p,local):
    if p.get('modo_distribuicao')=='automatico':
        st.caption('Os dividendos são calculados pelo saldo de cada alternativa. Veja o bruto, o IR e o líquido no comparativo do planejamento.')
        return {'irrf':None}
    st.markdown('#### IR sobre a distribuição de lucros')
    try:
        r=ir_dividendos_cenario(p['distribuicoes'],ano=p['ano'],mes=p['mes'],fonte=p['empresa'])
        cols=st.columns(3)
        for col,label,campo in zip(cols,['Lucros previstos','IR retido dos sócios','Líquido para os sócios'],['bruto','irrf','liquido']):
            col.metric(label,dinheiro(r[campo]))
        st.caption('O IR é retido do valor distribuído. Ele entra no total empresa + sócios, sem ser deduzido novamente como despesa da empresa. O ajuste anual dos sócios ainda exige apuração própria.')
        return r
    except Pendente as exc:
        st.warning('Dividendos pendentes: '+str(exc));return {'irrf':None}


def dados_compartilhados():
    st.title('Vamos planejar sua empresa?')
    st.write('Preencha uma vez. Os dados serão aproveitados nas simulações e nos relatórios.')
    with st.container(border=True):
        st.radio('Como está sua empresa hoje?',['Vai começar agora','Já está funcionando'],horizontal=True,key='sc_situacao')
        a,b=st.columns(2)
        a.text_input('Nome da empresa ou do planejamento',key='sc_empresa')
        b.selectbox('O que a empresa faz?',['Comércio','Indústria','Serviços em geral','Mais de uma atividade'],key='sc_atividade')
        a,b=st.columns(2)
        a.selectbox('Ano do cenário',[2026,2027],key='sc_ano')
        b.selectbox('Mês de início do cenário',range(1,13),format_func=lambda n:['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][n-1],key='sc_mes')
        a,b=st.columns(2)
        if st.session_state.sc_atividade=='Mais de uma atividade':
            for k,label in [('comercio','Comércio'),('industria','Indústria'),('servicos','Serviços')]:
                st.number_input('Receita mensal prevista · '+label,min_value=0.0,value=0.0,key='sc_'+k)
        else:a.number_input('Quanto espera faturar por mês? (R$)',min_value=0.0,step=1000.0,key='sc_receita')
        b.number_input('Custos e despesas por mês, sem salários (R$)',min_value=0.0,step=500.0,key='sc_custos')
        a,b=st.columns(2)
        a.number_input('Total de salários por mês (R$)',min_value=0.0,step=500.0,key='sc_salarios')
        b.number_input('Pró-labore dos sócios por mês (R$)',min_value=0.0,step=500.0,key='sc_prolabore')
        st.caption('São previsões editáveis. Para empresa em abertura, o Simples usa a anualização do primeiro mês; não é criado um histórico fictício.')
    with st.expander('Atividade, impostos e particularidades'):
        st.caption('Os cartões mostram os impostos já calculados. Se faltar ICMS, ISS, IPI ou outro componente, o subtotal e o saldo ficam identificados como condicionais. Informe zero somente quando esse tributo não for devido.')
        a,b=st.columns(2);a.text_input('CNPJ da empresa',key='sc_cnpj');b.text_input('CNAE / atividade do cadastro',key='sc_cnae')
        a,b=st.columns(2);a.text_input('Município',key='sc_municipio');b.text_input('Estado / UF',key='sc_uf')
        a,b=st.columns(2)
        a.selectbox('Anexo dos serviços, quando não há fator R',['III','IV','V'],key='sc_anexo')
        b.checkbox('Serviços sujeitos ao fator R',key='sc_fator')
        st.number_input('CPP e FGTS integrantes da folha para o fator R (R$)',min_value=0.0,key='sc_encargos_fs')
        if st.session_state.sc_situacao=='Já está funcionando':
            a,b=st.columns(2);a.text_input('Receita dos 12 meses anteriores (RBT12)',key='sc_rbt12');b.text_input('Folha legal dos 12 meses anteriores (FS12)',key='sc_fs12')
        st.checkbox('Projetar PIS/Cofins pela regra geral, sem monofasia, isenção ou receitas especiais',key='sc_pis_regra')
        st.caption('Hipótese explícita: Presumido cumulativo, PIS 0,65% e Cofins 3% (Lei 9.718/1998); Real não cumulativo, PIS 1,65% e Cofins 7,6% (Leis 10.637/2002 e 10.833/2003). Enquadramentos especiais exigem revisão.')
        a,b=st.columns(2)
        a.number_input('Crédito de PIS previsto no Real (R$)',min_value=0.0,key='sc_credito_pis')
        b.number_input('Crédito de Cofins previsto no Real (R$)',min_value=0.0,key='sc_credito_cofins')
        a,b=st.columns(2)
        a.text_input('ICMS, ISS e IPI líquidos por mês · fora do Simples',key='sc_impostos_local',placeholder='Valor confirmado, com ponto para centavos')
        b.text_input('Encargos patronais por mês · fora do Simples',key='sc_patronal',placeholder='Valor confirmado, ou 0 se não houver')
        st.text_input('Encargos fora do DAS para serviços do Anexo IV',key='sc_patronal_sn')
        st.caption('Encargos em branco: hipótese geral de CPP de 20% sobre salários e pró-labore fora do Simples e no Anexo IV. RAT/FAP, terceiros e regimes especiais exigem complemento; não estão presumidos como zero.')
        st.checkbox('Confirmei a dispensa de recolhimento de CBS/IBS de teste em 2026',key='sc_dispensa_teste_2026')
        st.caption('A dispensa depende do cumprimento das obrigações acessórias ou de sua desobrigação, conforme LC 214/2025, art. 348, Decreto 12.955/2026, art. 464, e comunicado conjunto RFB/CGIBS. Sem confirmação, o subtotal fora do Simples fica condicional.')
    with st.expander('Lucros e dividendos dos sócios',expanded=st.session_state.sc_dividendo>0):
        st.caption('O imposto sobre dividendos entra em todas as comparações. Para PF residente, a regra mensal alcança o total quando a mesma empresa paga mais de R$ 50 mil ao mesmo beneficiário no mês. Não há retenção automática de 10% em qualquer distribuição.')
        st.radio('Como distribuir o resultado?',['Distribuir todo o saldo','Informar um valor'],key='sc_modo_distribuicao',horizontal=True)
        st.caption('Por padrão, cada regime distribui o que sobrar após custos, salários, pró-labore bruto e tributos da empresa. O IR é calculado sobre essa distribuição por beneficiário, sem descontar o imposto duas vezes.')
        st.checkbox('Usar os sócios do cadastro',key='sc_modo_socios')
        st.selectbox('Origem dos lucros previstos',['2026','2025 ou anteriores'],key='sc_origem_div')
        if st.session_state.sc_modo_socios:
            st.checkbox('Usar a participação societária como rateio dos dividendos',key='sc_rateio_qsa')
            st.caption('Confirme o tipo de beneficiário e o rateio. Para vários sócios, a soma precisa ser 100%. Pró-labore agregado de vários sócios exige divisão individual para calcular o líquido pessoal.')
            cols=['nome','qualificacao','participacao','tipo_beneficiario']
            cols+=['percentual_distribuicao'] if st.session_state.sc_modo_distribuicao=='Distribuir todo o saldo' else ['dividendo_mensal']
            dados=st.session_state.sc_socios or [dict(nome='',qualificacao='',participacao=None,tipo_beneficiario='Não informado',dividendo_mensal='0')]
            df=st.data_editor(pd.DataFrame(dados).reindex(columns=cols).fillna(''),num_rows='dynamic',key='socios_cenario',hide_index=True,column_config={
                'nome':'Sócio ou beneficiário','qualificacao':'Qualificação','participacao':'Participação (%)',
                'tipo_beneficiario':st.column_config.SelectboxColumn('Tipo do beneficiário',options=['Não informado','PF residente no Brasil','Exterior','Pessoa jurídica']),
                'percentual_distribuicao':'Rateio dos dividendos (%)','dividendo_mensal':'Lucros por mês (R$)'})
            st.session_state.sc_socios=df.to_dict('records')
        else:
            a,b=st.columns(2);a.text_input('Sócio ou beneficiário do cenário',key='sc_beneficiario')
            b.selectbox('Quem vai receber os lucros?',['Não informado','PF residente no Brasil','Exterior','Pessoa jurídica'],key='sc_tipo_div')
            if st.session_state.sc_modo_distribuicao=='Informar um valor':
                st.number_input('Quanto será distribuído por mês? (R$)',min_value=0.0,step=1000.0,key='sc_dividendo')
            st.number_input('Dependentes do sócio para o IRRF do pró-labore',min_value=0,step=1,key='sc_dependentes_socio')
        st.caption('Hipótese do cenário: beneficiário PF residente no Brasil e lucros de 2026, conforme os campos acima. Confirme ou altere conforme a empresa. IR mínimo anual e redutor dos sócios exigem apuração própria.')
    from comparativo_ui import controles_reforma
    controles_reforma()
    with st.expander('Ajustes do contador · quando precisar'):
        a,b=st.columns(2);a.text_input('Prejuízo fiscal anterior · IRPJ',key='sc_saldo_ir');b.text_input('Base negativa anterior · CSLL',key='sc_saldo_cs')
        a,b=st.columns(2);a.text_input('Outros acréscimos trimestrais · IRPJ',key='sc_outros_ir');b.text_input('Outros acréscimos trimestrais · CSLL',key='sc_outros_cs')
        a,b=st.columns(2);a.text_input('Limite disponível de receita · IRPJ',key='sc_limite_ir');b.text_input('Limite disponível de receita · CSLL',key='sc_limite_cs')
        st.caption('Os limites iniciais são os nominais por trimestre, sem aproveitar sobras. O fechamento anual com majoração da LC 224 ainda está pendente. Adições e exclusões individualizadas permanecem na área técnica.')
    if st.session_state.sc_modo_distribuicao=='Distribuir todo o saldo':
        titular='sócios do cadastro, conforme rateio confirmado' if st.session_state.sc_modo_socios else st.session_state.sc_beneficiario+' · '+st.session_state.sc_tipo_div
        st.caption('Dividendos: todo o saldo de cada regime para '+titular+'. Origem dos lucros: '+st.session_state.sc_origem_div+'. Ajuste em Lucros e dividendos dos sócios, se necessário.')
    if st.button('Comparar os três regimes',type='primary',key='comparar_cenario'):
        st.session_state.comparacao_solicitada=True
    if st.session_state.get('comparacao_solicitada'):mostrar_comparacao()


def mostrar_comparacao():
    from comparativo_ui import exibir_comparacao
    exibir_comparacao(perfil())


def cadastro_empresa():
    st.title('Empresas e sócios')
    st.write('Importe os documentos, confira os campos e salve o cadastro. Os dados ficam disponíveis no planejamento.')
    if st.session_state.pop('_mensagem_cadastro',False):st.success('Cadastro salvo. A empresa foi selecionada no menu lateral e os dados estão disponíveis no planejamento.')
    cartao=st.file_uploader('Cartão CNPJ em PDF',type=['pdf'],key='pdf_cartao')
    qsa=st.file_uploader('QSA em PDF · opcional, em documento separado',type=['pdf'],key='pdf_qsa')
    if st.button('Ler os documentos',key='ler_cadastro'):
        try:
            if cartao is None:raise ImportacaoInvalida('Selecione o PDF do cartão CNPJ.')
            dados=extrair_cartao(texto_pdf(cartao.getvalue()))
            if qsa is not None:
                socios=extrair_qsa(texto_pdf(qsa.getvalue()),dados['cnpj']);dados['qsa']=socios['socios']
                dados['pendencias']+=socios['pendencias']
            st.session_state.cadastro_extraido=dados
            for chave,valor in dados.items():
                if isinstance(valor,str):st.session_state['cad_'+chave]=valor
        except ImportacaoInvalida as exc:st.error(str(exc))
    dados=st.session_state.get('cadastro_extraido',{})
    st.markdown('### Confira o cadastro')
    with st.form('cadastro_conferencia'):
        valores={}
        campos=[('razao_social','Razão social'),('cnpj','CNPJ'),('nome_fantasia','Nome fantasia'),('data_abertura','Data de abertura · AAAA-MM-DD'),
            ('cnae_principal','Atividade principal / CNAE'),('natureza_juridica','Natureza jurídica'),('porte','Porte'),
            ('logradouro','Logradouro'),('numero','Número'),('complemento','Complemento'),('bairro','Bairro'),
            ('cep','CEP'),('municipio','Município'),('uf','Estado / UF'),('email','E-mail'),('telefone','Telefone'),('situacao','Situação cadastral')]
        a,b=st.columns(2)
        for i,(chave,label) in enumerate(campos):valores[chave]=(a if i%2==0 else b).text_input(label,key='cad_'+chave)
        socios=dados.get('qsa')
        st.markdown('**Quadro societário**')
        df=st.data_editor(pd.DataFrame(socios or [],columns=['nome','qualificacao','participacao','tipo_beneficiario','dividendo_mensal']),
            num_rows='dynamic',key='qsa_cadastro',hide_index=True,column_config={'nome':'Nome / nome empresarial',
                'qualificacao':'Qualificação','participacao':'Participação (%)','tipo_beneficiario':'Tipo e residência · confirmar','dividendo_mensal':'Distribuição prevista (R$)'})
        salvar_qsa=st.checkbox('Conferi este QSA e quero gravá-lo junto ao cadastro',value=socios is not None)
        atualizar=st.checkbox('Atualizar cadastro existente com o mesmo CNPJ')
        confirmado=st.checkbox('Conferi os dados e os documentos da empresa')
        enviado=st.form_submit_button('Salvar cadastro da empresa',type='primary')
    if enviado:
        try:
            valores['qsa']=df.to_dict('records') if salvar_qsa else None
            empresa_id=salvar_empresa(DB,valores,confirmado=confirmado,atualizar=atualizar)
            st.session_state._empresa_selecionar=empresa_id
            st.session_state._mensagem_cadastro=True
            st.rerun()
        except ImportacaoInvalida as exc:st.error(str(exc))
    for nota in dados.get('pendencias',[]):st.caption(nota)


def contabilidade():
    st.title('Contabilidade')
    empresas=listar_empresas(DB)
    if not empresas:
        st.info('Cadastre uma empresa em Empresas e sócios para importar os lançamentos.');return
    ids=[e['id'] for e in empresas];nomes={e['id']:e['nome'] for e in empresas}
    empresa_id=st.selectbox('Empresa que receberá os lançamentos',ids,format_func=nomes.get,key='empresa_lancamentos')
    st.markdown('### Importar lançamentos')
    st.download_button('Baixar modelo de CSV','Data;Debito;Credito;Valor;Historico\n16/11/2026;1.01;4.01;1234,56;Recebimento de venda\n',file_name='modelo_lancamentos.csv',mime='text/csv')
    arquivo=st.file_uploader('Planilha de lançamentos em CSV',type=['csv'],key='csv_lancamentos')
    if arquivo is not None:
        try:
            previa=ler_lancamentos(arquivo.getvalue())
            st.write(f"{len(previa['linhas'])} linhas válidas · {len(previa['erros'])} linhas com erro")
            exib=[{'Data':r['data'],'Débito':r['debito'],'Crédito':r['credito'],'Valor':dinheiro(Decimal(r['valor_centavos'])/100),'Histórico':r['historico']} for r in previa['linhas']]
            st.dataframe(pd.DataFrame(exib),hide_index=True,width='stretch')
            if previa['erros']:st.dataframe(pd.DataFrame(previa['erros']),hide_index=True)
            repetidos=st.checkbox('Permitir lançamentos iguais porque representam operações distintas',key='permitir_iguais')
            confirmar=st.checkbox('Conferi a empresa e os lançamentos deste arquivo',key='confirmar_csv')
            if st.button('Confirmar importação dos lançamentos',type='primary'):
                result=importar_lancamentos(DB,empresa_id,previa,confirmado=confirmar,permitir_iguais=repetidos)
                st.success(f"{result['inseridos']} lançamentos gravados. {result['duplicados_ignorados']} duplicados ignorados.")
        except ImportacaoInvalida as exc:st.error(str(exc))
    conn=conectar(DB)
    try:registros=[dict(r) for r in conn.execute('SELECT * FROM lancamentos WHERE empresa_id=? ORDER BY data,id',(empresa_id,))]
    finally:conn.close()
    if registros:
        st.markdown('### Lançamentos da empresa')
        linhas=[[r['data'],r['debito'],r['credito'],dinheiro(Decimal(r['valor_centavos'])/100 if r['valor_centavos'] is not None else Decimal(str(r['valor']))),r['historico']] for r in registros]
        st.dataframe(pd.DataFrame(linhas,columns=['Data','Débito','Crédito','Valor','Histórico']),hide_index=True,width='stretch')
        botoes_relatorio('Livro de lançamentos',['Data','Débito','Crédito','Valor','Histórico'],linhas,chave='lancamentos')
    st.caption('Balancete, DRE, balanço patrimonial e lançamentos manuais continuam disponíveis em Ferramentas originais, no mesmo banco de demonstração.')


def simples():
    from copy import deepcopy
    st.title('Simples Nacional')
    st.write('Compare os anexos usando o mesmo cenário. A atividade determina o enquadramento permitido; os anexos não são opções livres.')
    p=perfil();receita=sum(p[k] for k in ('comercio','industria','servicos'));linhas=[]
    for anexo in ('I','II','III','IV','V'):
        q=deepcopy(p);q.update(comercio=receita if anexo=='I' else 0,industria=receita if anexo=='II' else 0,
            servicos=receita if anexo not in ('I','II') else 0,anexo=anexo,fator_r=False,atividade_anexo_iv=anexo=='IV')
        try:
            item=planejar(q)['resultados'][0]
            linhas.append([anexo,dinheiro(item['componentes'].get('DAS')),dinheiro(item['tributos_empresa']),
                dinheiro(item['dividendo_bruto']),dinheiro(item['ir_dividendos']),dinheiro(item.get('liquido_total_socios'))])
        except Pendente as exc:st.warning('Anexo '+anexo+': '+str(exc))
    colunas=['Anexo','DAS projetado','Tributos da empresa','Dividendos brutos','IR dos dividendos','Líquido dos sócios']
    st.dataframe(pd.DataFrame(linhas,columns=colunas),hide_index=True,width='stretch')
    notas=['Cenário mensal com receitas ordinárias. A atividade determina quais anexos são permitidos.',
        'No Anexo IV, CPP fora do DAS incluída pela regra geral de 20% quando não informada; confira RAT/FAP, terceiros e exceções.',
        'Líquido dos sócios inclui pró-labore após INSS/IRRF e dividendos após retenção; depende de escrituração e caixa.',
        'Para serviços sujeitos ao fator R e cenários de reforma, use o Planejamento. Ajuste anual da pessoa física não incluído.']
    for nota in notas:st.caption(nota)
    botoes_relatorio('Simulação dos anexos do Simples',colunas,linhas,notas,chave='simples_com_dividendos')


def projecao():
    from projecoes import gerar_cenario
    st.title('Como será o próximo ano?')
    st.write('As previsões já vêm do planejamento. Ajuste o crescimento e confira os 12 meses.')
    crescimento=st.number_input('Variação da receita por mês (%)',min_value=-100.0,max_value=100.0,value=0.0,step=.5,key='crescimento_anual')
    p=perfil();base={k:p[k] for k in ('comercio','industria','servicos')}
    serie=gerar_cenario(base,{k:Decimal(str(crescimento))/100 for k in base})
    linhas=[]
    for i,row in enumerate(serie):
        mes=(p['mes']-1+i)%12+1;ano=p['ano']+(p['mes']-1+i)//12
        receita=sum(row[k] for k in base)
        try:
            if p.get('modo_distribuicao')=='automatico':raise Pendente('Saldo por regime não apurado nesta grade financeira.')
            ir=ir_dividendos_cenario(p['distribuicoes'],ano=ano,mes=mes,fonte=p['empresa'])['irrf']
        except Pendente:ir=None
        linhas.append([f'{mes:02d}/{ano}',dinheiro(receita),dinheiro(p['custos']+p['salarios']+p['prolabore']),dinheiro(ir)])
    st.line_chart(pd.DataFrame({'Receita prevista':[float(sum(r[k] for k in base)) for r in serie]},index=range(1,13)))
    colunas=['Mês','Receita prevista','Custos, salários e pró-labore','IR dos dividendos previsto']
    st.dataframe(pd.DataFrame(linhas,columns=colunas),hide_index=True,width='stretch')
    notas=['Projeção financeira de 12 meses, não equivalente a lucro distribuível ou carga tributária anual.',
        'Grade financeira: dividendos automáticos exigem saldo tributário por regime e permanecem pendentes aqui, sem imposto zero presumido. A comparação mensal completa está no Planejamento.',
        'A projeção tributária trimestral detalhada permanece em Ferramentas técnicas. Não extrapolar regras de 2026 para 2027.']
    botoes_relatorio('Projeção de 12 meses',colunas,linhas,notas,chave='projecao_compartilhada')


def original():
    st.caption('Ferramentas preservadas do sistema original. As fórmulas legadas continuam em revisão; o novo planejamento apresenta suas pendências separadamente.')
    # Compartilha o mesmo banco de demonstração com o cadastro e a importação novos.
    codigo=(BASE/'sistema_original.py').read_text()
    codigo=codigo.replace('DB_NOME = os.path.join(BASE_DIR, "maxsuel_demonstracao.db")','DB_NOME = '+repr(str(DB)))
    contexto={'__name__':'__main__','__file__':str(BASE/'sistema_original.py'),'ir_legado':ir_legado,'importar_csv_legado':importar_csv_legado}
    exec(compile(codigo,str(BASE/'sistema_original.py'),'exec'),contexto)
    pagina=st.session_state.get('pagina_selecionada','')
    if pagina in ('🧮 Simulador Simples Nacional','📊 Planejamento Tributário Comparativo'):
        resumo_dividendos(perfil(),'original')
    for variavel,titulo in [('df_res_exibir','Simples Nacional · simulador original'),('df_resumo','Comparação tributária · simulador original'),
                           ('df_holerite','Demonstrativo de salário'),('df_ferias','Demonstrativo de férias')]:
        df=contexto.get(variavel)
        if isinstance(df,pd.DataFrame) and not df.empty:
            st.markdown('#### '+titulo+' · impressão')
            df=df.copy()
            if variavel=='df_res_exibir':
                p=perfil();original_df=contexto.get('df_res')
                if isinstance(original_df,pd.DataFrame):
                    for c in ['DAS Tradicional','Carga Total (Reforma)']:
                        if c not in original_df:continue
                        irs=[]
                        for imposto in original_df[c]:
                            try:
                                if p.get('modo_distribuicao')=='automatico':
                                    saldo=Decimal(str(contexto.get('faturamento_mes',0)))-Decimal(str(p['custos']))-Decimal(str(p['salarios']))-Decimal(str(p['prolabore']))-Decimal(str(imposto))
                                    ir=distribuir_resultado(saldo,p)['irrf']
                                else:ir=ir_dividendos_cenario(p['distribuicoes'],ano=p['ano'],mes=p['mes'],fonte=p['empresa'])['irrf']
                            except Pendente:ir=None
                            irs.append(ir)
                        df[c+' · IR dividendos']=[dinheiro(v) for v in irs]
                        df[c+' + IR dividendos']=[dinheiro(Decimal(str(v))+ir) if ir is not None else 'Pendente' for v,ir in zip(original_df[c],irs)]
            botoes_relatorio(titulo,list(df.columns),df.astype(str).values.tolist(),
                ['Cálculos originais preservados, ainda em revisão. Não constituem apuração fiscal homologada.'],chave='legado_'+variavel)


def ir_legado(valor):
    p=perfil();valor=numero(valor)
    if not valor:return 0.0
    if p.get('modo_distribuicao')=='automatico':
        try:return float(distribuir_resultado(valor,p)['irrf'])
        except (Pendente,TypeError) as exc:st.warning('Dividendos: '+str(exc));st.stop()
    registros=p['distribuicoes']
    total=sum((numero(x['valor']) for x in registros),Decimal('0'))
    if len(registros)==1:registros=[dict(registros[0],valor=valor)]
    elif total!=valor:
        st.warning('O valor total difere da distribuição por sócio. Ajuste os dividendos no planejamento antes de comparar.');st.stop()
    try:return float(ir_dividendos_cenario(registros,ano=p['ano'],mes=p['mes'],fonte=p['empresa'])['irrf'])
    except Pendente as exc:st.warning('Dividendos: '+str(exc));st.stop()


def importar_csv_legado(empresa_id):
    st.subheader('Importar lançamentos com conferência')
    arquivo=st.file_uploader('Arquivo CSV de lançamentos',type=['csv'],key='csv_legado_validado')
    if arquivo is None:return
    try:
        previa=ler_lancamentos(arquivo.getvalue())
        st.write(f"{len(previa['linhas'])} linhas válidas · {len(previa['erros'])} erros")
        st.dataframe(pd.DataFrame(previa['linhas']),hide_index=True)
        if previa['erros']:st.dataframe(pd.DataFrame(previa['erros']),hide_index=True)
        ok=st.checkbox('Conferi a empresa e as linhas para importar',key='conferir_csv_legado')
        permitir=st.checkbox('Permitir lançamentos iguais que sejam operações distintas',key='iguais_legado')
        if st.button('Importar lote validado',key='importar_lote_legado'):
            r=importar_lancamentos(DB,empresa_id,previa,confirmado=ok,permitir_iguais=permitir)
            st.success(f"{r['inseridos']} lançamentos gravados; {r['duplicados_ignorados']} duplicados ignorados.")
    except ImportacaoInvalida as exc:st.error(str(exc))


def abrir_folha():
    st.session_state.menu_principal='Ferramentas originais'
    st.session_state.pagina_selecionada='📋 Módulo de Folha & Fator R'
    st.session_state.nav_radio='📋 Módulo de Folha & Fator R'
    st.session_state.operacao_folha='🧮 Simulador Prático de Salário Líquido (2026)'
    st.session_state.calcular_ferias_legado=True


def renderizar():
    iniciar(preservar_widgets=True)
    if '_empresa_selecionar' in st.session_state:
        st.session_state.empresa_ativa_nova=st.session_state.pop('_empresa_selecionar')
    aplicar_tema()
    if st.session_state.menu_principal!='Ferramentas originais' and LOGO.exists():st.sidebar.image(str(LOGO),width=155)
    st.sidebar.caption('MAXSUEL · PLANEJAMENTO E GESTÃO')
    empresas=listar_empresas(DB);mapa={e['id']:e for e in empresas}
    escolhido=st.sidebar.selectbox('Empresa cadastrada',[None]+list(mapa),format_func=lambda v:'Novo planejamento' if v is None else mapa[v]['nome'],key='empresa_ativa_nova')
    if escolhido is not None and st.session_state.get('_empresa_carregada')!=escolhido:
        registro=mapa[escolhido];dados=json.loads(registro.get('dados_json') or '{}')
        st.session_state.sc_empresa=registro['nome'];st.session_state.sc_socios=dados.get('qsa') or []
        for origem,destino in [('cnpj','sc_cnpj'),('cnae_principal','sc_cnae'),('municipio','sc_municipio'),('uf','sc_uf'),('data_abertura','sc_data_abertura')]:
            st.session_state[destino]=dados.get(origem,registro.get(origem,''))
        if dados.get('data_abertura'):
            try:
                abertura=date.fromisoformat(dados['data_abertura'])
                referencia=date(st.session_state.sc_ano,st.session_state.sc_mes,1)
                if abertura>referencia and abertura.year in (2026,2027):
                    st.session_state.sc_ano=abertura.year;st.session_state.sc_mes=abertura.month
                    referencia=date(abertura.year,abertura.month,1)
                st.session_state.sc_situacao='Vai começar agora' if (abertura.year,abertura.month)==(referencia.year,referencia.month) else 'Já está funcionando'
            except ValueError:pass
        if dados.get('qsa'):st.session_state.sc_modo_socios=True
        st.session_state._empresa_carregada=escolhido
    from comparativo_ui import menu_lateral
    menu=menu_lateral()
    st.sidebar.caption('Ambiente de testes · dados e previsões deste cenário. Regras em revisão.')
    if menu=='Planejamento':dados_compartilhados()
    elif menu=='PJ × CLT':
        from comparativo_ui import exibir_pj_clt
        exibir_pj_clt(perfil())
    elif menu=='Simples Nacional':simples()
    elif menu=='Empresas e sócios':cadastro_empresa()
    elif menu=='Contabilidade':contabilidade()
    elif menu=='Projeção de 1 ano':projecao()
    elif menu=='Relatórios':st.title('Relatórios do planejamento');mostrar_comparacao()
    elif menu=='Equipe e salários':
        from folha import salario_liquido
        st.title('Equipe e salários')
        st.write('Calcule o salário individual e aproveite a previsão de equipe no planejamento.')
        st.button('Abrir simulador de férias e adiantamentos',on_click=abrir_folha)
        salario=st.number_input('Salário bruto previsto por funcionário (R$)',min_value=0.0,value=4000.0,key='salario_equipe')
        quantidade=st.number_input('Quantidade de funcionários com esse salário',min_value=1,value=2,key='quantidade_equipe')
        dependentes=st.number_input('Dependentes desse funcionário',min_value=0,value=0,key='dependentes_equipe')
        outros=st.number_input('Outros descontos no salário líquido (R$)',min_value=0.0,value=0.0,key='outros_descontos_equipe')
        try:
            folha=salario_liquido(salario,int(dependentes),outros_descontos=outros,ano=st.session_state.sc_ano)
            colunas=st.columns(3)
            for coluna,label,chave in zip(colunas,['INSS do funcionário','IRRF do salário','Salário líquido'],['inss','irrf','liquido']):coluna.metric(label,dinheiro(folha[chave]))
            st.caption(folha['fundamento'])
            botoes_relatorio('Simulação de salário individual',['Item','Valor'],[
                ['Salário bruto',dinheiro(salario)],['Dependentes',int(dependentes)],['INSS',dinheiro(folha['inss'])],['IRRF',dinheiro(folha['irrf'])],
                ['Outros descontos',dinheiro(outros)],['Salário líquido',dinheiro(folha['liquido'])]],
                [folha['fundamento'],'Método da dedução: '+folha['tipo_deducao']],chave='salario_individual')
        except Pendente as exc:st.warning(str(exc))
        st.metric('Total previsto de salários',dinheiro(salario*quantidade))
        if st.button('Usar esse total no planejamento',type='primary'):
            st.session_state.sc_salarios=salario*quantidade;st.success('Total atualizado no cenário compartilhado.')
    elif menu=='Ferramentas originais':original()
    else:
        from planejamento_ui import renderizar as tecnico
        tecnico()

