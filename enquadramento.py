"""Classificação do cenário; não confunde sublimite de ICMS/ISS com exclusão."""
from decimal import Decimal as D
from tax_engine import numero,ZERO


def avaliar_simples(p):
    receita=sum((numero(p.get(k,0)) for k in ('comercio','industria','servicos')),ZERO)
    n=p.get('mes_atividade') or (1 if p.get('situacao')=='abertura' else None)
    projetada=receita*12
    if receita>D('4800000') or (n==1 and projetada>D('4800000')):
        return dict(status='nao_enquadrado',titulo='Não se enquadra no Simples neste cenário projetado',
            motivo='A receita mensal informada supera o limite anual de R$ 4.800.000,00.' if receita>D('4800000') else 'A projeção do primeiro mês × 12 supera R$ 4.800.000,00 por ano.',
            receita_mensal=receita,receita_anual_projetada=projetada,
            nota='Em início de atividade, o limite geral é proporcional a R$ 400 mil por mês de atividade no ano. Efeitos de excesso, tolerância de 20% e datas de exclusão dependem da receita efetivamente auferida; este aviso classifica a projeção, não formaliza exclusão fiscal.')
    if n==1 and receita>D('300000'):
        return dict(status='revisao_sublimite',titulo='Dentro do limite geral projetado · ICMS/ISS a revisar',
            motivo='A receita anualizada está entre R$ 3,6 milhões e R$ 4,8 milhões. R$ 300 mil mensais é referência de sublimite, não o limite geral do Simples.',
            receita_mensal=receita,receita_anual_projetada=projetada,
            nota='O DAS e o recolhimento de ICMS/ISS dependem dos efeitos temporais do excesso de sublimite. Esta versão sinaliza a análise e não presume alíquotas locais nem DAS completo.')
    return None
