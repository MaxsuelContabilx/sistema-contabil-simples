"""Núcleo independente da interface. Recorte: regras gerais de 2026.

Resultados parciais não representam carga tributária global ou elegibilidade.
Valores desconhecidos nunca são convertidos automaticamente em zero.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from collections import defaultdict
from datetime import date

D = Decimal
ZERO = D('0')


class Pendente(ValueError):
    """Entrada, enquadramento ou regra ainda não confirmados."""


def numero(value, *, negativo=False):
    if value is None or isinstance(value, bool):
        raise Pendente('Informe um valor numérico confirmado; ausência não equivale a zero.')
    try:
        result = D(str(value))
    except (InvalidOperation, ValueError):
        raise Pendente('Valor numérico inválido.') from None
    if not result.is_finite() or (result < ZERO and not negativo):
        raise Pendente('Valor não finito ou negativo não permitido.')
    return result


def moeda(value):
    return numero(value, negativo=True).quantize(D('.01'), rounding=ROUND_HALF_UP)


def competencia_2026(ano, trimestre=None):
    if ano != 2026 or isinstance(ano, bool):
        raise Pendente('Esta versão contém apenas o recorte normativo de 2026. Não extrapolar para 2027.')
    if trimestre is not None and (trimestre not in (1, 2, 3, 4) or isinstance(trimestre, bool)):
        raise Pendente('Trimestre inválido.')


FONTES = {
    'simples': 'LC 123/2006, art. 18, §§ 1º, 1º-A, 1º-B, 5º-J e 5º-M, e Anexos I a V; Res. CGSN 140/2018, arts. 21, 25 e 26.',
    'presumido': 'Lei 9.249/1995, arts. 3º, 15 e 20; Lei 9.430/1996, arts. 1º, 25 e 26; LC 224/2025, art. 4º, § 4º, VII, e § 5º.',
    'real': 'DL 1.598/1977, art. 6º; Lei 9.249/1995, art. 3º; Lei 7.689/1988, arts. 2º e 3º; Lei 9.065/1995, arts. 15 e 16.',
    'dividendos': 'Lei 15.270/2025, art. 2º, que inclui o art. 6º-A na Lei 9.250/1995; arts. 16-A e 16-B para o ajuste anual.',
    'folha': 'INSS de empregado: Portaria MPS/MF 13/2026. IRRF mensal: Leis 15.191/2025 e 15.270/2025; tabelas oficiais de 2026 da Receita Federal.',
}

# Tuplas (teto da faixa, alíquota nominal, parcela a deduzir).
# Recorte anterior aos efeitos de 2027. Não aplicar o novo rateio em 2026.
LIMITES = tuple(map(D, ('180000', '360000', '720000', '1800000', '3600000', '4800000')))
TABELAS = {
    'I': tuple(zip(LIMITES, map(D, ('.04', '.073', '.095', '.107', '.143', '.19')), map(D, ('0', '5940', '13860', '22500', '87300', '378000')))),
    'II': tuple(zip(LIMITES, map(D, ('.045', '.078', '.10', '.112', '.147', '.30')), map(D, ('0', '5940', '13860', '22500', '85500', '720000')))),
    'III': tuple(zip(LIMITES, map(D, ('.06', '.112', '.135', '.16', '.21', '.33')), map(D, ('0', '9360', '17640', '35640', '125640', '648000')))),
    'IV': tuple(zip(LIMITES, map(D, ('.045', '.09', '.102', '.14', '.22', '.33')), map(D, ('0', '8100', '12420', '39780', '183780', '828000')))),
    'V': tuple(zip(LIMITES, map(D, ('.155', '.18', '.195', '.205', '.23', '.305')), map(D, ('0', '4500', '9900', '17100', '62100', '540000')))),
}


def faixa_simples(rbt12, anexo, ano=2026):
    """Consulta de tabela; não confirma elegibilidade nem tributos fora do DAS."""
    competencia_2026(ano)
    receita = numero(rbt12)
    if receita <= 0:
        raise Pendente('RBT12 zerada: analisar início de atividade/anualização; não presumir primeira faixa.')
    if anexo not in TABELAS:
        raise Pendente('Anexo não reconhecido.')
    for indice, (limite, aliquota, deducao) in enumerate(TABELAS[anexo], 1):
        if receita <= limite:
            return {'faixa': indice, 'nominal': aliquota, 'deducao': deducao,
                    'efetiva': (receita * aliquota - deducao) / receita,
                    'fundamento': FONTES['simples']}
    raise Pendente('RBT12 acima de R$ 4,8 milhões: avaliar regras de excesso e exclusão antes de calcular o DAS.')


def fator_r(fs12, rbt12):
    folha, receita = numero(fs12), numero(rbt12)
    if receita == 0:
        raise Pendente('Fator R com receita zerada requer tratamento específico; não calculado automaticamente.')
    return folha / receita


def simples_mensal(rbt12, fs12, receitas, *, ano=2026, enquadramento_confirmado=False,
                   empresa_madura=False, sublimite_confirmado=False):
    """Segregação ordinária por anexo, sem monofasia, ST, exportação ou retenção.

    Cada receita contém valor, anexo e sujeita_fator_r. FS12 já deve incluir
    os encargos legalmente integrantes; não é a folha de um único mês.
    """
    competencia_2026(ano)
    if not (enquadramento_confirmado and empresa_madura and sublimite_confirmado):
        raise Pendente('Confirme enquadramento, empresa fora das regras de início e situação do sublimite.')
    if numero(rbt12) > D('3600000'):
        raise Pendente('Acima do sublimite: esta versão não calcula ICMS/ISS fora do DAS nem efeitos do excesso.')
    if not receitas:
        raise Pendente('Informe as receitas segregadas, inclusive zero explícito se não houve operações.')
    detalhes = []
    for receita in receitas:
        valor = numero(receita.get('valor'))
        if valor == 0:
            continue
        if receita.get('tratamento') != 'ordinario':
            raise Pendente('Receita com tratamento especial: informar segregação e partilha legal específica.')
        if not isinstance(receita.get('sujeita_fator_r'), bool):
            raise Pendente('Indique expressamente se a atividade está sujeita ao fator R.')
        anexo = receita.get('anexo')
        if receita['sujeita_fator_r']:
            anexo = 'III' if fator_r(fs12, rbt12) >= D('.28') else 'V'
        tabela = faixa_simples(rbt12, anexo, ano)
        detalhes.append({'receita': valor, 'anexo': anexo, **tabela,
                         'das': valor * tabela['efetiva']})
    # Arredondamento por anexo, evitando dependência da quantidade de linhas.
    por_anexo = defaultdict(lambda: ZERO)
    for detalhe in detalhes:
        por_anexo[detalhe['anexo']] += detalhe['das']
    return {'das': sum((moeda(v) for v in por_anexo.values()), ZERO),
            'detalhes': detalhes, 'fundamento': FONTES['simples'], 'status': 'parcial',
            'pendencias': ['Partilha por tributo não implementada.',
                          'Anexo IV: contribuição patronal fora do DAS deve ser apurada separadamente.',
                          'Elegibilidade e carga global dependem de outros tributos e dados da empresa.']}


# Atividades gerais. Regras condicionadas (hospitalar, construção, ESC etc.)
# exigem cadastro e evidências próprios e não recebem enquadramento presumido.
ATIVIDADES = {
    'comercio': (D('.08'), D('.12')),
    'industria': (D('.08'), D('.12')),
    'servicos_gerais': (D('.32'), D('.32')),
    'transporte_cargas': (D('.08'), D('.12')),
    'transporte_passageiros': (D('.16'), D('.12')),
    'revenda_combustiveis': (D('.016'), D('.12')),
}


def imposto_renda(base, meses=3):
    if meses not in (1, 2, 3, 12) or isinstance(meses, bool):
        raise Pendente('Quantidade de meses não suportada.')
    base = max(ZERO, numero(base, negativo=True))
    return moeda(base * D('.15')), moeda(max(ZERO, base - D('20000') * meses) * D('.10'))


def presumido_trimestre(receitas, *, ano=2026, trimestre=1,
                        limite_irpj_confirmado=None, limite_csll_confirmado=None,
                        fundamento_limite='', acrescimos_irpj=None, acrescimos_csll=None,
                        enquadramento_confirmado=False, historico_anual=None):
    """Aplica limites disponíveis expressamente validados pelo revisor.

    Não infere histórico anual nem transporta automaticamente sobras entre
    trimestres. Q4 exige rotina própria de ajuste anual e permanece bloqueado.
    """
    competencia_2026(ano, trimestre)
    if not enquadramento_confirmado:
        raise Pendente('Confirme elegibilidade ao Lucro Presumido e o enquadramento das receitas.')
    fechamento_sem_majoracao = False
    if trimestre == 4:
        if historico_anual is None or len(historico_anual) != 4:
            raise Pendente('Quarto trimestre: ajuste anual da LC 224 depende do histórico completo; rotina ainda pendente.')
        historico = [numero(v) for v in historico_anual]
        atual = sum((numero(item.get('valor')) for item in receitas), ZERO)
        if historico[3] != atual or any(v > D('1250000') for v in historico):
            raise Pendente('Fechamento com majoração ou ajuste da LC 224 ainda pendente; não estimar o quarto trimestre.')
        if numero(limite_irpj_confirmado) != D('1250000') or numero(limite_csll_confirmado) != D('1250000'):
            raise Pendente('Fechamento sem majoração requer limites trimestrais de R$ 1.250.000 confirmados.')
        fechamento_sem_majoracao = True
    if not fundamento_limite.strip():
        raise Pendente('Registre a referência que fundamenta o limite disponível e o histórico dos períodos anteriores.')
    limite_ir = numero(limite_irpj_confirmado)
    limite_cs = numero(limite_csll_confirmado) if trimestre >= 2 else ZERO
    outras_ir = numero(acrescimos_irpj)
    outras_cs = numero(acrescimos_csll)
    if not receitas:
        raise Pendente('Informe as receitas por atividade; ausência não representa faturamento zero.')
    linhas = []
    for item in receitas:
        atividade = item.get('atividade')
        if atividade not in ATIVIDADES:
            raise Pendente('Atividade não cadastrada ou sujeita a requisitos específicos.')
        linhas.append((atividade, numero(item.get('valor'))))
    total = sum((valor for _, valor in linhas), ZERO)
    excedente_ir = max(ZERO, total - limite_ir)
    excedente_cs = max(ZERO, total - limite_cs) if trimestre >= 2 else ZERO
    base_ir, base_cs = outras_ir, outras_cs
    detalhes = []
    for atividade, valor in linhas:
        pi, pc = ATIVIDADES[atividade]
        proporcao = valor / total if total else ZERO
        maj_ir, maj_cs = excedente_ir * proporcao, excedente_cs * proporcao
        bi = valor * pi + maj_ir * pi * D('.10')
        bc = valor * pc + maj_cs * pc * D('.10')
        base_ir += bi
        base_cs += bc
        detalhes.append({'atividade': atividade, 'receita': valor, 'presuncao_irpj': pi,
                         'presuncao_csll': pc, 'receita_majorada_irpj': maj_ir,
                         'receita_majorada_csll': maj_cs, 'base_irpj': bi, 'base_csll': bc})
    normal, adicional = imposto_renda(base_ir)
    return {'base_irpj': moeda(base_ir), 'base_csll': moeda(base_cs),
            'irpj_normal': normal, 'irpj_adicional': adicional, 'irpj': normal + adicional,
            'csll': moeda(base_cs * D('.09')), 'detalhes': detalhes,
            'fundamento': FONTES['presumido'], 'fundamento_limite': fundamento_limite,
            'fechamento_sem_majoracao': fechamento_sem_majoracao,
            'status': 'parcial', 'pendencias': [('Fechamento sem majoração: os quatro trimestres estão abaixo ou no limite.'
            if fechamento_sem_majoracao else 'Limites e histórico validados manualmente; ajuste anual com majoração ainda não implementado.'),
            'Não inclui consumo, folha, retenções, deduções ou créditos tributários.']}


@dataclass(frozen=True)
class Ajuste:
    descricao: str
    tipo: str
    tributo: str
    valor: object
    fundamento: str
    documento: str
    natureza: str


def lucro_real_trimestre(lucro_contabil_irpj, resultado_contabil_csll, ajustes, *,
                         prejuizo_fiscal=None, base_negativa_csll=None, ano=2026,
                         trimestre=1, regra_geral_confirmada=False):
    """Duas bases de partida conciliadas; ajustes explícitos por tributo.

    O solicitante deve informar valores de partida conciliados, com tratamento
    das próprias provisões de IRPJ/CSLL. Não resolve circularidade contábil.
    """
    competencia_2026(ano, trimestre)
    if not regra_geral_confirmada:
        raise Pendente('Confirme CSLL geral de 9%, trava geral de 30% e saldos documentalmente aptos à compensação.')
    bases = {'IRPJ': numero(lucro_contabil_irpj, negativo=True),
             'CSLL': numero(resultado_contabil_csll, negativo=True)}
    for ajuste in ajustes:
        if (ajuste.tipo not in ('adicao', 'exclusao') or ajuste.tributo not in bases
                or ajuste.natureza not in ('temporaria', 'permanente')):
            raise Pendente('Tipo, tributo ou natureza do ajuste inválido.')
        if not all(isinstance(v, str) and v.strip() for v in (ajuste.descricao, ajuste.fundamento, ajuste.documento)):
            raise Pendente('Cada ajuste exige descrição, fundamento normativo e documento de suporte.')
        bases[ajuste.tributo] += numero(ajuste.valor) * (1 if ajuste.tipo == 'adicao' else -1)
    saldos = {'IRPJ': numero(prejuizo_fiscal), 'CSLL': numero(base_negativa_csll)}
    resultado = {}
    for tributo, base in bases.items():
        compensacao = min(saldos[tributo], max(ZERO, base) * D('.30'))
        resultado[tributo] = {'ajustado': moeda(base), 'compensacao': moeda(compensacao),
                             'base_tributavel': moeda(max(ZERO, base - compensacao)),
                             'saldo_anterior_remanescente': moeda(saldos[tributo] - compensacao),
                             'perda_do_periodo': moeda(max(ZERO, -base))}
    normal, adicional = imposto_renda(resultado['IRPJ']['base_tributavel'])
    return {'bases': resultado, 'irpj_normal': normal, 'irpj_adicional': adicional,
            'irpj': normal + adicional, 'csll': moeda(resultado['CSLL']['base_tributavel'] * D('.09')),
            'ajustes': ajustes, 'fundamento': FONTES['real'], 'status': 'parcial',
            'pendencias': ['Classificação e vigência de cada ajuste exigem validação documental.',
                          'Controle de reversões temporárias na Parte B ainda não implementado.',
                          'Não inclui consumo, folha, retenções, incentivos ou créditos de imposto.']}


def dividendos_mensais(eventos, *, ano=2026):
    """Eventos agregados por fonte pagadora, beneficiário e mês.

    Suporte apenas a PF residente e resultados a partir de 2026. Não presume
    isenção de lucros antigos; tais casos são bloqueados para análise.
    """
    competencia_2026(ano)
    if not eventos:
        raise Pendente('Informe os eventos; ausência não confirma inexistência de distribuições.')
    grupos = defaultdict(lambda: ZERO)
    for item in eventos:
        if item.get('beneficiario_tipo') != 'PF_RESIDENTE':
            raise Pendente('Beneficiário fora do recorte de PF residente; analisar regra própria.')
        if item.get('origem_resultado') != '2026':
            raise Pendente('Lucros anteriores exigem análise do ato de aprovação, exigibilidade e transição.')
        if not item.get('fonte') or not item.get('beneficiario'):
            raise Pendente('Identifique fonte pagadora e beneficiário.')
        try:
            data = date.fromisoformat(str(item.get('data')))
        except ValueError:
            raise Pendente('Data do evento inválida.') from None
        if data.year != ano:
            raise Pendente('Evento fora do ano-calendário selecionado.')
        grupos[(str(item['fonte']), str(item['beneficiario']), data.strftime('%Y-%m'))] += numero(item.get('valor'))
    linhas = []
    for (fonte, beneficiario, mes), valor in sorted(grupos.items()):
        imposto = moeda(valor * D('.10')) if valor > D('50000') else ZERO
        linhas.append({'fonte': fonte, 'beneficiario': beneficiario, 'mes': mes,
                       'bruto': moeda(valor), 'irrf': imposto, 'liquido': moeda(valor - imposto)})
    return {'detalhes': linhas, 'irrf': sum((x['irrf'] for x in linhas), ZERO),
            'fundamento': FONTES['dividendos'], 'status': 'parcial',
            'pendencias': ['IRRF mensal não é o imposto definitivo do sócio.',
                          'Tributação mínima anual, exclusões e redutor do art. 16-B ainda pendentes.',
                          'IRRF é retido do valor distribuído e não é nova despesa da empresa.']}
