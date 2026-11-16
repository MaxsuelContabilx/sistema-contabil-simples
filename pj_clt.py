"""Comparação econômica CLT x PJ, separando caixa e direitos não disponíveis."""
from decimal import Decimal as D
from copy import deepcopy
from folha import salario_liquido
from planejador import planejar
from tax_engine import numero,moeda,Pendente


def comparar_vinculos(salario_clt,faturamento_pj,cenario,*,dependentes=0,beneficios=0,meses_faturados=12,modelo='atual'):
    if meses_faturados not in range(1,13):raise Pendente('Informe entre 1 e 12 meses faturados por ano.')
    salario=numero(salario_clt);faturamento=numero(faturamento_pj);beneficios=numero(beneficios)
    normal=salario_liquido(salario,dependentes,ano=cenario['ano'])
    # 11 pagamentos regulares + 1 de férias com 1/3 + 13º; não duplica o salário de férias.
    ferias=salario_liquido(moeda(salario*D('4')/3),dependentes,ano=cenario['ano'])
    decimo=salario_liquido(salario,dependentes,ano=cenario['ano'])
    anual=moeda(normal['liquido']*11+ferias['liquido']+decimo['liquido'])
    # Arredonda cada remuneração: 11 meses regulares, 13º e mês de férias.
    fgts=moeda(salario*D('.08'))*12+moeda(moeda(salario*D('4')/3)*D('.08'))
    p=deepcopy(cenario);total=sum((numero(p[k]) for k in ('comercio','industria','servicos')),D('0'))
    if total:
        for k in ('comercio','industria','servicos'):p[k]=faturamento*numero(p[k])/total
    else:p.update(comercio=0,industria=0,servicos=faturamento)
    p['modo_distribuicao']='automatico';p['dependentes_socio']=dependentes
    p['atividade_anexo_iv']=numero(p['servicos'])>0 and p.get('anexo')=='IV' and not p.get('fator_r')
    resultado=planejar(p,modelo)
    for indice,item in enumerate(resultado['resultados']):
        mensal=item.get('liquido_total_socios')
        # Meses sem nota ainda têm custos fixos e pró-labore. Mantém tais saídas e os tributos pessoais.
        meses_sem=12-meses_faturados
        sem=deepcopy(p)
        for k in ('comercio','industria','servicos'):sem[k]=0
        # Créditos da operação com nota não são automaticamente repetidos em mês sem nota.
        sem.update(credito_pis=0,credito_cofins=0,credito_cbs=0,credito_ibs=0)
        vazio=planejar(sem,modelo)['resultados'][indice] if meses_sem else None
        custo_sem=(numero(p['custos'])+numero(p['salarios'])+numero(p['prolabore'])+(vazio['tributos_empresa'] or 0)) if vazio else 0
        if mensal is not None:
            retencoes_sem=(vazio.get('prolabore',{}).get('inss') or 0)+(vazio.get('prolabore',{}).get('irrf') or 0) if vazio else 0
            # Transferências de pró-labore nos meses sem receita são internas ao conjunto PJ+sócio;
            # o custo econômico é custos externos + tributos, com eventual aporte a financiar a PJ.
            custo_economico_sem=numero(p['custos'])+numero(p['salarios'])+(vazio['tributos_empresa'] or 0)+retencoes_sem if vazio else 0
            item['liquido_anual_pj']=moeda(mensal*meses_faturados-custo_economico_sem*meses_sem)
        else:item['liquido_anual_pj']=None
        if vazio and vazio['tributos_empresa'] is None:item['liquido_anual_pj']=None
        item['aporte_mes_sem_nota']=moeda(custo_sem)
    return dict(clt={'mensal':normal,'ferias':ferias,'decimo_terceiro':decimo,'liquido_anual':anual,'media_mensal_anual':moeda(anual/12),
        'fgts_anual':fgts,'beneficios_anuais':beneficios*12},pj=resultado,
        notas=['CLT: ano completo com 30 dias de férias e 13º integral. A redução do IRRF é aplicada também ao 13º, conforme Lei 9.250/1995, art. 3º-A §3º.',
        'FGTS (regra geral de 8%, Lei 8.036/1990, art. 15) e benefícios são separados do salário líquido; não representam dinheiro mensal livre.',
        'PJ: meses sem faturamento continuam com os custos e obrigações informados; não foram zerados automaticamente.',
        'PJ anual: referência mensal constante multiplicada pelos meses faturados, com custos dos demais meses. Não substitui apuração anual com RBT12/FS12 móveis, sazonalidade e ajustes trimestrais. Valores condicionais mantêm as pendências do cenário.',
        'Fluxo líquido projetado após retenções. Ajuste anual da pessoa física e redutor de dividendos não estão calculados.',
        'Comparação econômica não determina a regularidade jurídica da contratação.'])
