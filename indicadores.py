"""Destaque comparativo explicável; pendências nunca viram recomendação definitiva."""
from tax_engine import Pendente,moeda


def destacar_regime(resultado,criterio='liquido'):
    if criterio not in ('liquido','tributos'):raise Pendente('Critério de comparação não reconhecido.')
    campo='liquido_total_socios' if criterio=='liquido' else 'total_consolidado'
    todos=resultado['resultados'];validos=[i for i in todos if i.get(campo) is not None]
    if not validos:return dict(disponivel=False,motivo='Complete os dados pendentes para comparar os regimes.',criterio=criterio)
    ordenados=sorted(validos,key=lambda x:x[campo],reverse=criterio=='liquido')
    valor=ordenados[0][campo];vencedores=[i['regime'] for i in ordenados if i[campo]==valor]
    proximo=next((i[campo] for i in ordenados if i[campo]!=valor),None)
    faltas=[]
    for i in todos:
        if i.get(campo) is None:faltas.append(i['regime']+': cálculo incompleto.')
        faltas += [i['regime']+': '+s for s in i.get('itens_pendentes',[])]
    return dict(disponivel=True,regimes=vencedores,valor=valor,campo=campo,criterio=criterio,
        provisorio=bool(faltas),pendencias=list(dict.fromkeys(faltas)),empate=len(vencedores)>1,
        diferenca=moeda(abs(valor-proximo)) if proximo is not None else None,
        nota='Comparação mensal pelas hipóteses informadas; não inclui o ajuste anual da pessoa física nem confirma elegibilidade ao regime.')
