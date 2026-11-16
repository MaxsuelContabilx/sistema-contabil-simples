"""Orquestra cenários, distribuição do resultado e projeção explícita da reforma."""
from copy import deepcopy
from decimal import Decimal as D
from cenario import comparar,ir_dividendos_cenario
from folha import irrf_mensal
from tax_engine import ZERO,numero,moeda,Pendente


def prolabore_liquido(bruto,dependentes=0,ano=2026):
    bruto=numero(bruto)
    if ano!=2026:raise Pendente('Teto e tabela pessoal do ano ainda não revisados.')
    inss=moeda(min(bruto,D('8475.55'))*D('.11'))
    ir=irrf_mensal(bruto,inss,int(dependentes),ano=ano)
    notas=[]
    if ZERO<bruto<D('1621'):notas.append('Pró-labore inferior ao mínimo: confira eventual complementação previdenciária e outros vínculos.')
    return dict(bruto=moeda(bruto),inss=inss,irrf=ir['irrf'],liquido=moeda(bruto-inss-ir['irrf']),
        fundamento='Contribuinte individual remunerado por PJ: Lei 10.666/2003, art. 4º; Lei 8.212/1991; teto de 2026 da Portaria MPS/MF 13/2026; IRRF de 2026.',pendencias=notas)


def distribuir_resultado(saldo,p,*,mes=None):
    """Nunca presume rateio igual para mais de um beneficiário."""
    saldo=moeda(max(ZERO,numero(saldo,negativo=True)))
    if not saldo:return dict(irrf=ZERO,bruto=ZERO,liquido=ZERO,pendencias=[],detalhes=[],distribuicoes=[])
    titulares=deepcopy(p.get('distribuicoes') or [])
    if not titulares:
        if saldo:return dict(irrf=None,bruto=saldo,liquido=None,pendencias=['Informe o beneficiário da distribuição.'])
        return dict(irrf=ZERO,bruto=ZERO,liquido=ZERO,pendencias=[],detalhes=[])
    if len(titulares)==1:titulares[0]['valor']=saldo
    else:
        pesos=[]
        for item in titulares:
            try:pesos.append(numero(item.get('percentual_distribuicao')))
            except Pendente:raise Pendente('Informe o rateio de cada sócio. A soma precisa ser 100%; não foi presumida divisão igual.')
        if sum(pesos,ZERO)!=D('100'):raise Pendente('O rateio dos dividendos precisa somar 100%; não foi presumida divisão igual entre os sócios.')
        usados=ZERO
        for i,(item,peso) in enumerate(zip(titulares,pesos)):
            item['valor']=saldo-usados if i==len(titulares)-1 else moeda(saldo*peso/100)
            usados+=item['valor']
    r=ir_dividendos_cenario(titulares,ano=p['ano'],mes=mes or p['mes'],fonte=p['empresa'])
    r['distribuicoes']=titulares
    return r


def _preparar(p,modelo):
    p=deepcopy(p);r=sum((numero(p[k]) for k in ('comercio','industria','servicos')),ZERO)
    pend=[];hipoteses=[]
    fator_receita=D('1');iva={};credito_utilizado=ZERO
    if modelo=='reforma':
        cbs=numero(p.get('cbs_pct','11.3'))/100;ibs=numero(p.get('ibs_pct','18.7'))/100
        if cbs>1 or ibs>1:raise Pendente('Confira as alíquotas percentuais da projeção.')
        reducao=numero(p.get('reducao_iva_pct','0'))/100
        if reducao>1:raise Pendente('Redução de CBS/IBS acima de 100%.')
        cbs*=1-reducao;ibs*=1-reducao
        base=r/(1+cbs+ibs) if p.get('preco_reforma','final')=='final' else r
        fator_receita=base/r if r else D('1')
        deb_cbs=moeda(base*cbs);deb_ibs=moeda(base*ibs)
        cred_cbs=numero(p.get('credito_cbs','0'));cred_ibs=numero(p.get('credito_ibs','0'))
        credito_utilizado=min(deb_cbs,cred_cbs)+min(deb_ibs,cred_ibs)
        if credito_utilizado>numero(p['custos']):raise Pendente('Os créditos utilizados superam os custos declarados. Este cenário contempla créditos vinculados aos custos informados; confira as bases.')
        iva=dict(base=moeda(base),fatura=moeda(r if p.get('preco_reforma','final')=='final' else r+deb_cbs+deb_ibs),
            cbs=moeda(max(ZERO,deb_cbs-cred_cbs)),ibs=moeda(max(ZERO,deb_ibs-cred_ibs)),
            debito_cbs=deb_cbs,debito_ibs=deb_ibs,credito_utilizado=credito_utilizado,
            saldo_creditor_cbs=moeda(max(ZERO,cred_cbs-deb_cbs)),saldo_creditor_ibs=moeda(max(ZERO,cred_ibs-deb_ibs)))
        for k in ('comercio','industria','servicos'):p[k]=numero(p[k])*fator_receita
        p['custos']=numero(p['custos'])-credito_utilizado
        hipoteses += ['Projeção futura com CBS/IBS informados pelo usuário; não são alíquotas legais definitivas nem apuração de 2026.',
            'As regras de IRPJ, CSLL, renda pessoal e tabela do DAS são referências de 2026; vigência futura exige revisão.',
            'Preço final mantido: a base é o preço dividido por 1 + CBS + IBS.' if p.get('preco_reforma','final')=='final' else 'Tributos repassados por fora: a fatura aumenta, sem descontar o IVA novamente da receita-base.',
            'Créditos de CBS/IBS declarados e vinculados aos custos deste cenário; saldos credores não são tratados como dinheiro distribuível.']
    trib={}
    for regime in ('presumido','real'):
        original=(p.get('tributos') or {}).get(regime,{})
        d={}
        for nome in ('PIS','COFINS','ICMS/ISS/IPI','Encargos da folha'):
            v=original.get(nome)
            if modelo=='reforma' and nome in ('PIS','COFINS','ICMS/ISS/IPI'):d[nome]=ZERO;continue
            if nome in ('PIS','COFINS') and p.get('usar_regras_federais',True):
                taxa={('presumido','PIS'):D('.0065'),('presumido','COFINS'):D('.03'),('real','PIS'):D('.0165'),('real','COFINS'):D('.076')}[regime,nome]
                base_atual=sum((numero(p[k]) for k in ('comercio','industria','servicos')),ZERO)
                credito=numero(p.get('credito_pis' if nome=='PIS' else 'credito_cofins','0')) if regime=='real' else ZERO
                d[nome]=moeda(max(ZERO,base_atual*taxa-credito));continue
            if nome=='Encargos da folha' and v is None:
                d[nome]=moeda((numero(p['salarios'])+numero(p['prolabore']))*D('.20'))
                if numero(p['salarios'])>0:pend.append('RAT/FAP, terceiros e eventual regime previdenciário especial não informados; a projeção inclui apenas CPP geral de 20% fora do Simples.')
            elif v is None:
                d[nome]=ZERO;pend.append(nome+' não definido: o subtotal e o saldo são condicionais, sem este componente.')
            else:d[nome]=numero(v)
        trib[regime]=d
    p['tributos']=trib
    if modelo=='atual' and not p.get('dispensa_teste_2026_confirmada',False):
        pend.append('CBS/IBS de teste em 2026: falta confirmar a dispensa de recolhimento. Eventuais valores a recolher e compensações não estão neste subtotal (LC 214/2025, art. 348; Decreto 12.955/2026, art. 464; comunicado RFB/CGIBS).')
    if p.get('patronal_simples') is None:
        p['patronal_simples']=moeda((numero(p['salarios'])+numero(p['prolabore']))*D('.20'))
    # Primeira passagem calcula a empresa; os dividendos dependem desse resultado.
    p['distribuicoes']=[]
    return p,iva,sorted(set(pend)),hipoteses


def _comparar_com_cpp(motor,cenario):
    r=comparar(motor)
    # Sem nota no mês, o Anexo IV ainda pode dever CPP sobre a folha.
    if cenario.get('anexo')=='IV' and not cenario.get('fator_r') and cenario.get('atividade_anexo_iv',False) and not numero(cenario['servicos']):
        sn=r['resultados'][0]
        if sn['tributos_empresa'] is not None and 'Encargos fora do DAS' not in sn['componentes']:
            cpp=numero(motor['patronal_simples'])
            sn['componentes']['Encargos fora do DAS']=cpp;sn['tributos_empresa']+=cpp
            sn['resultado_gerencial']-=cpp
    return r


def planejar(cenario,modelo='atual'):
    if modelo not in ('atual','reforma'):raise Pendente('Cenário de consumo não reconhecido.')
    if int(cenario.get('ano',2026))!=2026:raise Pendente('As tabelas de renda e folha disponíveis são de 2026. A reforma é uma projeção separada, sem tratar essas referências como apuração legal de 2027.')
    motor,iva,pend,hipoteses=_preparar(cenario,modelo)
    r=_comparar_com_cpp(motor,cenario)
    from enquadramento import avaliar_simples
    enquadramento=avaliar_simples(cenario)
    if enquadramento:
        sn=r['resultados'][0];sn['enquadramento']=enquadramento
        sn['pendencias']=[enquadramento['motivo'],enquadramento['nota']]+sn['pendencias']
    try:
        if len(cenario.get('distribuicoes') or [])>1 and numero(cenario['prolabore'])>0:
            raise Pendente('Para calcular o pró-labore líquido de vários sócios, informe a remuneração individual; o teto não foi aplicado ao valor agregado.')
        pro=prolabore_liquido(cenario['prolabore'],int(cenario.get('dependentes_socio',0)),ano=cenario['ano'])
    except Pendente as exc:pro=dict(inss=None,irrf=None,liquido=None,pendencias=[str(exc)])
    for item in r['resultados']:
        item['itens_pendentes']=list(pend) if item['regime']!='Simples Nacional' else []
        if modelo=='reforma' and item['regime']!='Simples Nacional':
            item['itens_pendentes'].append('Projeção futura: parâmetros de CBS/IBS do usuário e regras de renda de referência 2026; confirmar legislação e vigência do período simulado.')
        avisos_motor=list(item['pendencias'])
        if item['regime']=='Simples Nacional' and numero(cenario['salarios'])>0 and numero(cenario['servicos'])>0 and cenario.get('anexo')=='IV' and not cenario.get('fator_r') and cenario.get('patronal_simples') is None:
            item['itens_pendentes'].append('Anexo IV: CPP geral de 20% incluída; RAT/FAP e demais encargos aplicáveis à folha precisam ser confirmados.')
        if item['tributos_empresa'] is None:
            if item['regime']=='Simples Nacional':
                item.update(dividendo_bruto=None,dividendo_liquido=None,ir_dividendos=None,total_consolidado=None,liquido_total_socios=None,prolabore=pro)
                continue
            item['itens_pendentes']+=avisos_motor
            item['tributos_empresa']=sum(item['componentes'].values(),ZERO)
            item['resultado_gerencial']=sum((numero(motor[k]) for k in ('comercio','industria','servicos')),ZERO)-numero(motor['custos'])-numero(motor['salarios'])-numero(motor['prolabore'])-item['tributos_empresa']
        saldo=item['resultado_gerencial']
        if modelo=='reforma' and item['regime']!='Simples Nacional':
            item['componentes'].pop('PIS',None);item['componentes'].pop('COFINS',None);item['componentes'].pop('ICMS/ISS/IPI',None)
            item['componentes']['CBS projetada']=iva['cbs'];item['componentes']['IBS projetado']=iva['ibs']
            item['tributos_empresa']+=iva['cbs']+iva['ibs']
            # O resultado do motor usa receita SEM IVA. Não se desconta o IVA duas vezes.
            item['memoria']['iva']=iva
        elif modelo=='reforma':
            # A tabela futura do Simples não é presumida: usa-se referência explicitamente identificada.
            ref_motor,_,_,_=_preparar(cenario,'atual')
            ref=_comparar_com_cpp(ref_motor,cenario)['resultados'][0]
            item.update(componentes=deepcopy(ref['componentes']),tributos_empresa=ref['tributos_empresa'],memoria=ref['memoria'])
            saldo=ref['resultado_gerencial']
            item['itens_pendentes'].append('Simples futuro: DAS de referência 2026, não tabela oficial futura.')
            if cenario.get('simples_reforma','dentro')=='fora':
                fatia=cenario.get('das_substituido')
                if fatia is None:
                    item['itens_pendentes'].append('Falta informar a parcela do DAS substituída na projeção por fora; preservado o DAS integral como referência conservadora, sem presumir partilha.')
                    fatia=ZERO
                fatia=numero(fatia)
                if fatia>item['componentes'].get('DAS',ZERO):raise Pendente('A parcela substituída supera o DAS de referência, sem os encargos externos.')
                restante=item['tributos_empresa']-fatia
                externos=ref['componentes'].get('Encargos fora do DAS',ZERO)
                item['componentes']={'DAS remanescente (projeção)':restante-externos,'CBS projetada':iva['cbs'],'IBS projetado':iva['ibs']}
                if externos:item['componentes']['Encargos fora do DAS']=externos
                item['tributos_empresa']=restante+iva['cbs']+iva['ibs']
                caixa=iva['fatura']-numero(cenario['custos'])-numero(cenario['salarios'])-numero(cenario['prolabore'])
                saldo=caixa-item['tributos_empresa']
        item['saldo_antes_distribuicao']=moeda(saldo)
        automatico=cenario.get('modo_distribuicao','manual')=='automatico'
        try:
            div=distribuir_resultado(saldo,cenario) if automatico else ir_dividendos_cenario(cenario.get('distribuicoes'),ano=cenario['ano'],mes=cenario['mes'],fonte=cenario['empresa'])
        except Pendente as exc:div=dict(irrf=None,bruto=moeda(max(ZERO,saldo)) if automatico else None,liquido=None,pendencias=[str(exc)])
        item['dividendos']=div;item['dividendo_bruto']=div.get('bruto');item['dividendo_liquido']=div.get('liquido');item['ir_dividendos']=div['irrf']
        item['prolabore']=pro
        item['total_consolidado']=item['tributos_empresa']+div['irrf'] if div['irrf'] is not None else None
        if item['total_consolidado'] is not None and pro['inss'] is not None:
            item['total_consolidado']+=pro['inss']+pro['irrf']
        elif pro['inss'] is None:item['total_consolidado']=None
        item['aporte_necessario']=moeda(max(ZERO,-saldo))
        item['liquido_recebido_socios']=div['liquido']+pro['liquido'] if div.get('liquido') is not None and pro['liquido'] is not None else None
        item['liquido_total_socios']=item['liquido_recebido_socios']-item['aporte_necessario'] if item['liquido_recebido_socios'] is not None else None
        avisos_motor=[n for n in avisos_motor if not n.startswith('Nenhuma distribuição')]
        item['pendencias']=list(dict.fromkeys(avisos_motor+item['itens_pendentes']+div.get('pendencias',[])+pro.get('pendencias',[])))
        if not automatico and div.get('bruto') is not None and div['bruto']>max(ZERO,saldo):
            item['pendencias'].append('A distribuição manual supera o resultado do cenário: confira lucros acumulados e disponibilidade financeira.')
        if saldo<0:item['pendencias'].append('Resultado negativo: não foi criado dividendo distribuível.')
        item['calculo_condicional']=bool(item['itens_pendentes'])
        item['resultado_gerencial']=moeda(saldo)
    r.update(cenario=cenario,modelo=modelo,iva=iva,hipoteses=hipoteses,
        dividendos={'por_regime':{i['regime']:i.get('dividendos',{'irrf':None,'bruto':None,'liquido':None}) for i in r['resultados']},
            'nota':'A distribuição e a retenção são próprias de cada regime, calculadas após os tributos da empresa.'},
        pendencias=['Distribuição automática representa saldo do cenário, sujeito à escrituração e disponibilidade financeira.',
            'Retenções mensais não equivalem ao imposto mínimo anual definitivo dos sócios.',
            'Subtotais condicionais não incluem os componentes explicitamente não definidos.']+hipoteses)
    return r
