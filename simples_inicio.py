"""Janelas legais de receita e folha no início: vigências 2026 e 2027.

A regra temporal de 2027 não autoriza reutilizar tabelas monetárias de 2026.
"""
from datetime import date
from decimal import Decimal as D
from tax_engine import ZERO,Pendente,numero,moeda,faixa_simples

FONTE_2026='Resolução CGSN 140/2018, art. 22, §§ 2º a 4º, e art. 26, §§ 4º, 6º e 7º; redação com efeitos até 31/12/2026.'
FONTE_2027='Resolução CGSN 140/2018, arts. 21, 22 e 26, com redação da Resolução CGSN 190/2026; art. 9º da Resolução 190: efeitos em 01/01/2027.'


def idade_meses(abertura,ano,mes):
    try:d=date.fromisoformat(str(abertura));pa=date(int(ano),int(mes),1)
    except (ValueError,TypeError):raise Pendente('Informe a data de abertura do CNPJ no formato AAAA-MM-DD.')
    n=(pa.year-d.year)*12+pa.month-d.month+1
    if n<1:raise Pendente('O período de apuração é anterior à abertura no CNPJ.')
    return n


def referencia_inicio(ano,mes_atividade,receita_atual,folha_atual=0,historico=None,*,sujeito_fator=False):
    """Histórico indexado por mês desde o CNPJ; zero é dado, ausência é pendência.

    Registros: {mes_atividade:1, receita:..., folha:...}. Não preenche mês sem dado.
    """
    if ano not in (2026,2027):raise Pendente('Regra temporal revisada somente para 2026 e 2027.')
    if isinstance(mes_atividade,bool) or not isinstance(mes_atividade,int) or mes_atividade<1:
        raise Pendente('Mês de atividade inválido.')
    n=mes_atividade;atual=numero(receita_atual);folha=numero(folha_atual)
    primeira=ano==2027 and n<=2
    if primeira:indices=[];rotulo='Primeira faixa nos dois primeiros meses; sem RBT12 proporcional.'
    elif ano==2026 and n==1:indices=[];rotulo='Receita do próprio primeiro mês × 12.'
    else:
        fim=n-(2 if ano==2027 else 1)
        indices=list(range(max(1,fim-11),fim+1))
        media=n<=(13 if ano==2027 else 12)
        rotulo=('Média aritmética dos meses '+('antecedentes ao mês anterior' if ano==2027 else 'anteriores ao período')+' × 12.') if media else ('Soma dos 12 meses '+('antecedentes ao mês anterior.' if ano==2027 else 'anteriores ao período.'))
    mapa={}
    for linha in historico or []:
        m=linha.get('mes_atividade')
        if isinstance(m,bool) or not isinstance(m,int) or m<1 or m>=n:raise Pendente('Histórico com mês de atividade inválido, atual ou futuro.')
        if m in mapa:raise Pendente('Há mês duplicado no histórico do Simples.')
        mapa[m]=linha
    receitas=[];folhas=[]
    for m in indices:
        if m not in mapa:raise Pendente(f'Falta o histórico do {m}º mês de atividade. Meses sem receita precisam ter zero explícito; não foram omitidos da média.')
        receitas.append(numero(mapa[m].get('receita')))
        if sujeito_fator:folhas.append(numero(mapa[m].get('folha')))
    if primeira:rbt=None;fs=None;fator=D('.28') if sujeito_fator else None
    elif ano==2026 and n==1:
        rbt=atual*12;fs=folha*12
        fator=(folha/atual if atual else D('.28')) if folha else D('.01')
    else:
        multiplicador=D(12)/len(indices) if n<=(13 if ano==2027 else 12) else D(1)
        rbt=sum(receitas,ZERO)*multiplicador
        fs=sum(folhas,ZERO)*multiplicador if sujeito_fator else ZERO
        fator=fs/rbt if rbt and fs else D('.28') if fs else D('.01')
    return dict(ano=ano,mes_atividade=n,primeira_faixa=primeira,rbt12_proporcional=rbt,fs12_proporcional=fs,
        fator_r=fator if sujeito_fator else None,meses_utilizados=indices,receitas_utilizadas=receitas,
        divisor_media=len(indices) if indices and n<=(13 if ano==2027 else 12) else None,
        regra=rotulo,fundamento=FONTE_2027 if ano==2027 else FONTE_2026,
        historico_utilizado=[mapa[m] for m in indices])


def calcular_inicio(receitas,folha,*,ano=2026,mes_atividade=1,historico=None,anexo='III',sujeito_fator=False):
    total=sum((numero(v) for v in receitas.values()),ZERO)
    ref=referencia_inicio(ano,mes_atividade,total,folha,historico,sujeito_fator=sujeito_fator)
    if ano!=2026:raise Pendente('A janela e o fator R da Resolução 190/2026 estão disponíveis na memória temporal. O DAS de 2027 depende das tabelas e partilhas do período; não foi repetida a tabela de 2026.')
    if ref['rbt12_proporcional']>D('3600000'):raise Pendente('RBT12 proporcional acima do sublimite: revisar ICMS/ISS e efeitos do excesso.')
    # Início de atividade também exige observar o acumulado do ano e o sublimite proporcional.
    if mes_atividade<=12:
        anteriores=ref['receitas_utilizadas']
        if sum(anteriores,ZERO)+total>D('300000')*mes_atividade:
            raise Pendente('Receita acumulada acima do sublimite proporcional de início; revisar ICMS/ISS e efeitos do excesso.')
    if sujeito_fator:anexo='III' if ref['fator_r']>=D('.28') else 'V'
    detalhes=[];das=ZERO
    for atividade,tabela in [('comercio','I'),('industria','II'),('servicos',anexo)]:
        valor=numero(receitas.get(atividade,0))
        if not valor:continue
        # Art. 21, parágrafo único: RBT12 zero é R$1 apenas para a alíquota.
        faixa=faixa_simples(ref['rbt12_proporcional'] or D(1),tabela,ano)
        imposto=moeda(valor*faixa['efetiva']);das+=imposto
        detalhes.append(dict(atividade=atividade,anexo=tabela,receita=valor,**faixa,das=imposto))
    return dict(ref,das=das,anexo_servicos=anexo,detalhes=detalhes)
