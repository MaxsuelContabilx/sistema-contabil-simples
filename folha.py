"""Salário mensal de empregado: recorte geral de 2026, sem múltiplos vínculos."""
from decimal import Decimal as D
from tax_engine import numero,moeda,ZERO,Pendente

FUNDAMENTO=('INSS: Portaria Interministerial MPS/MF 13/2026, tabela de empregados. '
 'IRRF: tabela mensal de 2026 da Receita Federal, Lei 15.191/2025 e redução da Lei 15.270/2025. '
 'Não contempla múltiplos vínculos ou remunerações especiais.')


def inss_empregado(salario,ano=2026):
    if ano!=2026:raise Pendente('Tabela previdenciária do ano ainda não revisada.')
    salario=numero(salario);anterior=ZERO;imposto=ZERO
    for teto,taxa in [(D('1621'),D('.075')),(D('2902.84'),D('.09')),(D('4354.27'),D('.12')),(D('8475.55'),D('.14'))]:
        imposto+=max(ZERO,min(salario,teto)-anterior)*taxa
        anterior=teto
    return moeda(imposto)


def irrf_mensal(rendimento,inss,dependentes=0,*,simplificado=True,ano=2026):
    if ano!=2026:raise Pendente('Tabela de IRRF do ano ainda não revisada.')
    if isinstance(dependentes,bool) or not isinstance(dependentes,int) or dependentes<0:
        raise Pendente('Quantidade de dependentes inválida.')
    rendimento=numero(rendimento);inss=numero(inss)
    legal=inss+D('189.59')*dependentes
    deducao=max(legal,D('607.20')) if simplificado else legal
    base=max(ZERO,rendimento-deducao)
    bruto=ZERO
    for teto,taxa,parcela in [(D('2428.8'),ZERO,ZERO),(D('2826.65'),D('.075'),D('182.16')),
        (D('3751.05'),D('.15'),D('394.16')),(D('4664.68'),D('.225'),D('675.49')),(D('Infinity'),D('.275'),D('908.73'))]:
        if base<=teto:bruto=max(ZERO,base*taxa-parcela);break
    # A redução depende do rendimento tributável, não da base após INSS/deduções.
    reducao=min(bruto,D('312.89')) if rendimento<=D('5000') else max(ZERO,D('978.62')-D('.133145')*rendimento) if rendimento<=D('7350') else ZERO
    reducao=min(bruto,reducao)
    return dict(irrf=moeda(bruto-reducao),base=moeda(base),bruto=moeda(bruto),reducao=moeda(reducao),
        deducao=moeda(deducao),tipo_deducao='Simplificado' if simplificado and D('607.20')>legal else 'Deduções legais')


def salario_liquido(salario,dependentes=0,*,outros_descontos=0,ano=2026):
    salario=numero(salario);outros=numero(outros_descontos)
    inss=inss_empregado(salario,ano)
    ir=irrf_mensal(salario,inss,dependentes,ano=ano)
    liquido=salario-inss-ir['irrf']-outros
    if liquido<0:raise Pendente('Os descontos superam o salário; confira os valores.')
    return dict(salario=moeda(salario),inss=inss,**ir,outros_descontos=moeda(outros),liquido=moeda(liquido),fundamento=FUNDAMENTO)
