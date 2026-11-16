"""Um cadastro de premissas para comparar os componentes implementados."""
from decimal import Decimal as D
from tax_engine import (ZERO, Pendente, moeda, numero, faixa_simples, simples_mensal,
    presumido_trimestre,lucro_real_trimestre,dividendos_mensais)


def ir_dividendos_cenario(distribuicoes,*,ano=2026,mes=1,fonte='Empresa do cenário'):
    if not isinstance(distribuicoes,list):raise Pendente('Informe a previsão de distribuição de lucros.')
    eventos=[]
    for item in distribuicoes:
        valor=numero(item.get('valor'))
        if valor==0:continue
        eventos.append(dict(data=f'{ano}-{mes:02d}-01',fonte=fonte,beneficiario=item.get('nome'),
            beneficiario_tipo=item.get('tipo'),origem_resultado=item.get('origem'),valor=valor))
    if not eventos:
        return {'irrf':ZERO,'bruto':ZERO,'liquido':ZERO,'detalhes':[],
                'pendencias':['Nenhuma distribuição foi prevista neste cenário. Se houver pagamento, atualize o cenário.']}
    result=dividendos_mensais(eventos,ano=ano)
    result['bruto']=sum((x['bruto'] for x in result['detalhes']),ZERO)
    result['liquido']=sum((x['liquido'] for x in result['detalhes']),ZERO)
    return result


def simples_primeiro_mes(receitas,fs_legal,*,anexo='III',sujeito_fator=False,ano=2026):
    from simples_inicio import calcular_inicio
    return calcular_inicio(receitas,fs_legal,anexo=anexo,sujeito_fator=sujeito_fator,ano=ano)


def comparar(cenario):
    """Retorna componentes comparáveis por mês, sem declarar carga global incompleta.

    IRPJ/CSLL do Presumido/Real: equivalente mensal de um trimestre com
    faturamento e resultado constantes, identificado expressamente no relatório.
    Tributos não informados ficam pendentes, não são assumidos como zero.
    """
    ano=int(cenario.get('ano',2026));mes=int(cenario.get('mes',1))
    if ano!=2026 or mes not in range(1,13):raise Pendente('Ano ou mês ainda não contemplado pelas regras revisadas.')
    receitas={k:numero(cenario.get(k)) for k in ('comercio','industria','servicos')}
    receita=sum(receitas.values(),ZERO)
    custos=numero(cenario.get('custos'));salarios=numero(cenario.get('salarios'));prolabore=numero(cenario.get('prolabore'))
    pendencias=[]
    try:dividendos=ir_dividendos_cenario(cenario.get('distribuicoes'),ano=ano,mes=mes,fonte=cenario.get('empresa') or 'Empresa do cenário')
    except Pendente as exc:
        dividendos={'irrf':None,'bruto':None,'liquido':None,'pendencias':[str(exc)]};pendencias.append('Dividendos: '+str(exc))
    resultados=[]
    for regime in ('Simples Nacional','Lucro Presumido','Lucro Real'):
        item=dict(regime=regime,tributos_empresa=None,ir_dividendos=dividendos['irrf'],total_consolidado=None,
                  componentes={},pendencias=[],memoria={},resultado_gerencial=None)
        try:
            if regime=='Simples Nacional':
                if cenario.get('inicio_pendencia'):raise Pendente(cenario['inicio_pendencia'])
                if cenario.get('situacao')=='abertura' or cenario.get('mes_atividade') is not None:
                    from simples_inicio import calcular_inicio
                    resultado=calcular_inicio(receitas,numero(cenario.get('encargos_fs'))+salarios+prolabore,
                        anexo=cenario.get('anexo','III'),sujeito_fator=cenario.get('fator_r',False),ano=ano,
                        mes_atividade=cenario.get('mes_atividade') or 1,historico=cenario.get('historico_inicio'))
                else:
                    fs12=numero(cenario.get('fs12')) if cenario.get('fator_r') else ZERO
                    resultado=simples_mensal(cenario.get('rbt12'),fs12,[dict(valor=v,
                        anexo={'comercio':'I','industria':'II','servicos':cenario.get('anexo','III')}[k],
                        sujeita_fator_r=k=='servicos' and cenario.get('fator_r',False),tratamento='ordinario') for k,v in receitas.items()],
                        enquadramento_confirmado=True,empresa_madura=True,sublimite_confirmado=True)
                item['componentes']['DAS']=resultado['das'];item['memoria']=resultado
                if receitas['servicos'] and cenario.get('anexo')=='IV' and not cenario.get('fator_r'):
                    patronal=numero(cenario.get('patronal_simples'))
                    item['componentes']['Encargos fora do DAS']=patronal
                item['tributos_empresa']=sum(item['componentes'].values(),ZERO)
            else:
                # Tributos de consumo e folha são informados por regime, sem alíquota local inventada.
                chave='presumido' if regime=='Lucro Presumido' else 'real'
                informados=cenario.get('tributos',{}).get(chave,{})
                consumo={}
                faltantes=[]
                for k in ('PIS','COFINS','ICMS/ISS/IPI','Encargos da folha'):
                    try:consumo[k]=numero(informados.get(k))
                    except Pendente:faltantes.append(k)
                item['componentes'].update(consumo)
                if regime=='Lucro Presumido':
                    trimestre=(mes-1)//3+1
                    if cenario.get('situacao')=='abertura' and mes not in (1,4,7,10):
                        raise Pendente('Abertura dentro do trimestre: confirme o período e os limites proporcionais antes da comparação do Presumido.')
                    resultado=presumido_trimestre([dict(atividade={'comercio':'comercio','industria':'industria','servicos':'servicos_gerais'}[k],valor=v*3) for k,v in receitas.items()],
                        trimestre=trimestre,limite_irpj_confirmado=cenario.get('limite_irpj'),limite_csll_confirmado=cenario.get('limite_csll'),
                        fundamento_limite=cenario.get('fundamento_limite',''),acrescimos_irpj=cenario.get('acrescimos_irpj'),
                        acrescimos_csll=cenario.get('acrescimos_csll'),enquadramento_confirmado=True)
                else:
                    if faltantes:raise Pendente('Para projetar o Lucro Real, falta estimar: '+', '.join(faltantes)+'.')
                    # Resultado contábil projetado antes de IRPJ/CSLL, usando os tributos explicitamente informados.
                    base=(receita-custos-salarios-prolabore-sum(consumo.values(),ZERO))*3
                    resultado=lucro_real_trimestre(base,base,cenario.get('ajustes',[]),
                        prejuizo_fiscal=cenario.get('saldo_irpj'),base_negativa_csll=cenario.get('saldo_csll'),regra_geral_confirmada=True)
                item['memoria']=resultado
                item['componentes']['IRPJ (equivalente mensal)']=moeda(resultado['irpj']/3)
                item['componentes']['CSLL (equivalente mensal)']=moeda(resultado['csll']/3)
                if faltantes:
                    item['pendencias'].append('Total da empresa pendente: '+', '.join(faltantes)+'.')
                else:item['tributos_empresa']=sum(item['componentes'].values(),ZERO)
            if item['ir_dividendos'] is not None:
                if item['tributos_empresa'] is not None:item['total_consolidado']=item['tributos_empresa']+item['ir_dividendos']
            if item['tributos_empresa'] is not None:item['resultado_gerencial']=receita-custos-salarios-prolabore-item['tributos_empresa']
            if dividendos.get('bruto') is not None and item['resultado_gerencial'] is not None and dividendos['bruto']>max(ZERO,item['resultado_gerencial']):
                item['pendencias'].append('A distribuição prevista supera o resultado gerencial do mês. Confira lucros acumulados e suporte contábil antes de distribuir.')
        except Pendente as exc:item['pendencias'].append(str(exc))
        item['pendencias'].extend(dividendos['pendencias'])
        resultados.append(item)
    return dict(cenario=cenario,resultados=resultados,dividendos=dividendos,receita=receita,
        pendencias=pendencias+['IRRF dos dividendos é retido dos sócios; não é nova despesa da empresa.',
            'A tributação mínima anual e o redutor dos sócios ainda não estão incluídos no total mensal.',
            'A comparação contempla apenas enquadramentos ordinários confirmados e um trimestre projetado com valores mensais constantes.'],
        status='Simulação projetada; exige conferência de enquadramento e tributos informados.')
