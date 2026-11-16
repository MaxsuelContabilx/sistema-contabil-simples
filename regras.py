"""Identidade reproduzível do conjunto de regras, sem atualização silenciosa."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tax_engine import ATIVIDADES, FONTES, TABELAS, Pendente

CATALOGO = Path(__file__).with_name('regras') / 'catalogo.json'


def fotografia_regras(ano):
    catalogo = json.loads(CATALOGO.read_text(encoding='utf-8'))
    versoes = [v for v in catalogo['versoes'] if v['inicio'] <= f'{ano}-01-01'
               and v['fim'] >= f'{ano}-12-31' and v['estado'] in ('revisao', 'validada')]
    if len(versoes) != 1:
        raise Pendente('Não há conjunto de regras conferido para todo esse ano. Não repetir automaticamente as regras de 2026.')
    # Inclui o código efetivamente executado, não só a descrição do catálogo.
    codigos = {nome: sha256(Path(__file__).with_name(nome).read_bytes()).hexdigest()
               for nome in ('tax_engine.py', 'projecoes.py', 'regras.py', 'cenario.py', 'folha.py')}
    dados = {'versao': versoes[0], 'tabelas': TABELAS, 'atividades': ATIVIDADES,
             'fundamentos': FONTES, 'codigo_sha256': codigos}
    serializado = json.dumps(dados, default=str, sort_keys=True, ensure_ascii=False)
    return {'id': versoes[0]['id'], 'sha256': sha256(serializado.encode()).hexdigest(),
            'regras': deepcopy(json.loads(serializado))}


def verificar_memoria(dados):
    """Verifica consistência do snapshot, não certifica autoria nem verdade legal."""
    if not isinstance(dados, dict) or not all(k in dados for k in ('entradas', 'resultado', 'fotografia_normativa')):
        raise Pendente('Arquivo não contém uma memória de cálculo desta versão.')
    snapshot = dados['fotografia_normativa']
    if not isinstance(snapshot, dict) or not all(k in snapshot for k in ('id', 'sha256', 'regras')):
        raise Pendente('Fotografia normativa ausente ou incompleta.')
    canonical = json.dumps(snapshot['regras'], ensure_ascii=False, sort_keys=True)
    if sha256(canonical.encode()).hexdigest() != snapshot['sha256']:
        raise Pendente('A fotografia normativa não corresponde ao hash registrado no arquivo.')
    return deepcopy(dados)
