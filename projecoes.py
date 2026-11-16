"""Projeções anuais por competência; não equivalem a fluxo de pagamento."""
from decimal import Decimal as D
from tax_engine import (Ajuste, Pendente, ZERO, numero, moeda, simples_mensal,
                        presumido_trimestre, lucro_real_trimestre)
from regras import fotografia_regras


def gerar_cenario(bases, crescimentos):
    """Hipóteses financeiras declaradas; nunca altera alíquotas legais."""
    if set(bases) != set(crescimentos):
        raise Pendente('Informe uma taxa de crescimento para cada premissa financeira.')
    taxas = {k: numero(v, negativo=True) for k, v in crescimentos.items()}
    if any(v < D('-1') for v in taxas.values()):
        raise Pendente('Queda mensal não pode superar 100%.')
    valores = {k: numero(v, negativo=k.startswith('resultado_')) for k, v in bases.items()}
    return [dict(mes=i + 1, **{k: moeda(v * (D('1') if i == 0 else (D('1') + taxas[k]) ** i))
                              for k, v in valores.items()}) for i in range(12)]


def _periodos(linhas, nome):
    if len(linhas) != 12 or [x.get('mes') for x in linhas] != list(range(1, 13)):
        raise Pendente(f'{nome}: informe exatamente 12 meses, ordenados de janeiro a dezembro, sem duplicidade.')


def _anual(linhas, campos):
    completo = len(linhas) > 0 and all(x['calculado'] for x in linhas)
    return {campo: sum((x['resultado'][campo] for x in linhas), ZERO) if completo else None
            for campo in campos} | {'cobertura_completa': completo}


def projetar_ano(meses, historico, *, ano=2026, anexo_servicos='III', servicos_fator_r=False,
                 saldos_irpj=None, saldos_csll=None, ajustes=None, confirmado=False, distribuicoes=None):
    """12 meses projetados + 12 meses históricos anteriores ao ano.

    O histórico contém receita total e FS legal de cada mês anterior. Custos
    gerenciais não são convertidos automaticamente em base fiscal do Real.
    Os resultados contábeis de partida são entradas separadas e conciliadas.
    """
    snapshot = fotografia_regras(ano)
    _periodos(meses, 'Projeção')
    _periodos(historico, 'Histórico do ano anterior')
    if not confirmado:
        raise Pendente('Confirme enquadramentos, histórico, resultados conciliados e premissas do cenário.')
    anterior_receita = [numero(x.get('receita')) for x in historico]
    anterior_folha = [numero(x.get('fs_legal')) for x in historico]
    atual_receita = [sum((numero(x.get(k)) for k in ('comercio', 'industria', 'servicos')), ZERO) for x in meses]
    atual_folha = [numero(x.get('fs_legal')) for x in meses]
    despesas = [numero(x.get('custos_despesas')) for x in meses]
    ajustes = [] if ajustes is None else ajustes
    for ajuste in ajustes:
        if ajuste.get('mes') not in range(1, 13):
            raise Pendente('Ajuste do Real fora dos 12 meses projetados.')
    sn, lp, lr, financeiro = [], [], [], []
    # A série móvel usa os meses anteriores ao PA; nunca inclui a receita do próprio PA.
    for i, linha in enumerate(meses):
        rbt12 = sum((anterior_receita + atual_receita)[i:i+12], ZERO)
        fs12 = sum((anterior_folha + atual_folha)[i:i+12], ZERO)
        receitas = [dict(valor=linha[chave], anexo=anexo, sujeita_fator_r=fator, tratamento='ordinario')
                    for chave, anexo, fator in [('comercio', 'I', False), ('industria', 'II', False),
                                               ('servicos', anexo_servicos, servicos_fator_r)]]
        registro = dict(mes=i+1, rbt12=moeda(rbt12), fs12=moeda(fs12))
        try:
            if sum(anterior_receita, ZERO) > D('3600000') or sum(atual_receita[:i+1], ZERO) > D('3600000'):
                raise Pendente('Receita anual anterior ou projetada acima do sublimite: analisar efeitos temporais de ICMS/ISS antes de apurar este cenário.')
            resultado = simples_mensal(rbt12, fs12, receitas, ano=ano, enquadramento_confirmado=True,
                empresa_madura=True, sublimite_confirmado=True)
            registro.update(calculado=True, resultado=resultado)
        except Pendente as exc:
            registro.update(calculado=False, pendencia=str(exc))
        sn.append(registro)
        financeiro.append(dict(mes=i+1, receita=moeda(atual_receita[i]), custos_despesas=moeda(despesas[i]),
                               saldo_gerencial_antes_tributos=moeda(atual_receita[i]-despesas[i])))
    historico_trimestral = [sum(atual_receita[i:i+3], ZERO) for i in range(0, 12, 3)]
    try:
        saldo_ir, saldo_cs = numero(saldos_irpj), numero(saldos_csll)
        saldos_validos = True
    except Pendente:
        saldo_ir = saldo_cs = None
        saldos_validos = False
    for t in range(1, 5):
        fatia = meses[(t-1)*3:t*3]
        registro = {'trimestre': t}
        try:
            if sum(anterior_receita, ZERO) > D('78000000'):
                raise Pendente('Receita do ano anterior acima do limite geral de opção ao Presumido; revisar elegibilidade.')
            receitas = [dict(atividade=atividade, valor=sum((numero(x[chave]) for x in fatia), ZERO))
                for chave, atividade in [('comercio', 'comercio'), ('industria', 'industria'), ('servicos', 'servicos_gerais')]]
            resultado = presumido_trimestre(receitas, ano=ano, trimestre=t,
                limite_irpj_confirmado='1250000', limite_csll_confirmado='1250000',
                fundamento_limite='Limite trimestral nominal, sem aproveitamento de sobras; LC 224/2025, art. 4º, § 5º. Cenário parcial.',
                acrescimos_irpj=sum((numero(x.get('acrescimos_irpj')) for x in fatia), ZERO),
                acrescimos_csll=sum((numero(x.get('acrescimos_csll')) for x in fatia), ZERO),
                enquadramento_confirmado=True, historico_anual=historico_trimestral if t == 4 else None)
            registro.update(calculado=True, resultado=resultado)
        except Pendente as exc:
            registro.update(calculado=False, pendencia=str(exc))
        lp.append(registro)
        registro = {'trimestre': t, 'saldo_irpj_inicial': saldo_ir, 'saldo_csll_inicial': saldo_cs}
        try:
            if not saldos_validos:
                raise Pendente('Saldo inicial ou trimestre anterior do Real pendente; não transportar saldo presumido.')
            itens = [Ajuste(**{k:v for k,v in a.items() if k != 'mes'}) for a in ajustes if (a['mes']-1)//3+1 == t]
            resultado = lucro_real_trimestre(
                sum((numero(x.get('resultado_irpj'), negativo=True) for x in fatia), ZERO),
                sum((numero(x.get('resultado_csll'), negativo=True) for x in fatia), ZERO), itens,
                prejuizo_fiscal=saldo_ir, base_negativa_csll=saldo_cs, ano=ano, trimestre=t, regra_geral_confirmada=True)
            bases = resultado['bases']
            saldo_ir = bases['IRPJ']['saldo_anterior_remanescente'] + bases['IRPJ']['perda_do_periodo']
            saldo_cs = bases['CSLL']['saldo_anterior_remanescente'] + bases['CSLL']['perda_do_periodo']
            registro.update(calculado=True, resultado=resultado,
                            saldo_irpj_final=saldo_ir, saldo_csll_final=saldo_cs)
        except Pendente as exc:
            registro.update(calculado=False, pendencia=str(exc))
            saldo_ir = saldo_cs = None
            saldos_validos = False
        lr.append(registro)
    from cenario import ir_dividendos_cenario
    div_meses=[]
    for mes in range(1,13):
        try:
            div=ir_dividendos_cenario(distribuicoes,ano=ano,mes=mes)
            div_meses.append(dict(mes=mes,irrf=div['irrf']))
        except Pendente as exc:div_meses.append(dict(mes=mes,irrf=None,pendencia=str(exc)))
    div_anual=sum((x['irrf'] for x in div_meses),ZERO) if all(x['irrf'] is not None for x in div_meses) else None
    anuais={'simples':_anual(sn,('das',)),'presumido':_anual(lp,('irpj','csll')),'real':_anual(lr,('irpj','csll'))}
    for chave,valores in anuais.items():
        valores['irrf_dividendos']=div_anual
        subtotal=valores.get('das') if chave=='simples' else valores['irpj']+valores['csll'] if valores['cobertura_completa'] else None
        valores['subtotal_componentes_e_dividendos']=subtotal+div_anual if subtotal is not None and div_anual is not None else None
    return {'ano': ano, 'status': 'parcial', 'regras': snapshot,'dividendos':{'mensal':div_meses,'irrf_anual':div_anual},
            'simples': {'mensal': sn, 'anual': anuais['simples']},
            'presumido': {'trimestral': lp, 'anual': anuais['presumido']},
            'real': {'trimestral': lr, 'anual': anuais['real']},
            'financeiro': financeiro, 'receita_anual': sum(atual_receita, ZERO),
            'custos_despesas_anuais': sum(despesas, ZERO),
            'fundamento': 'Apuração mensal do DAS e trimestral de IRPJ/CSLL; fundamentos e regras incluídos na fotografia normativa.',
            'pendencias': ['Totais representam componentes diferentes: DAS versus IRPJ/CSLL. Não classificar o melhor regime com esses subtotais.',
                          'IRRF mensal dos dividendos é apresentado separadamente e somado ao subtotal consolidado quando informado. Consumo, folha e ajuste anual dos sócios não estão integralmente contemplados.',
                          'Saldos gerenciais são anteriores aos tributos; não equivalem a lucro distribuível ou fluxo de caixa.',
                          'Real trimestral: sem estimativas mensais ou compensação retroativa; exceções à trava geral exigem revisão.',
                          'Presumido: sem aproveitamento de sobras de limites; fechamento com majoração permanece pendente.',
                          'A projeção usa regras em revisão e exige conferência da legislação aplicável a cada competência.']}
