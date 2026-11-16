"""Persistência local, compatível com o cadastro legado; operações transacionais."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
import math
from decimal import Decimal,InvalidOperation
from importacoes import cnpj_limpo, validar_cnpj, ImportacaoInvalida


def conectar(caminho):
    conn=sqlite3.connect(str(caminho));conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS empresas(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,cnpj TEXT UNIQUE NOT NULL);
      CREATE TABLE IF NOT EXISTS lancamentos(id INTEGER PRIMARY KEY AUTOINCREMENT,empresa_id INTEGER NOT NULL,data TEXT NOT NULL,debito TEXT NOT NULL,credito TEXT NOT NULL,valor REAL NOT NULL,historico TEXT,FOREIGN KEY(empresa_id) REFERENCES empresas(id));
      CREATE TABLE IF NOT EXISTS cadastro_detalhes(empresa_id INTEGER PRIMARY KEY,dados_json TEXT NOT NULL,atualizado_em TEXT NOT NULL,FOREIGN KEY(empresa_id) REFERENCES empresas(id));
      CREATE TABLE IF NOT EXISTS importacoes_linhas(empresa_id INTEGER NOT NULL,assinatura TEXT NOT NULL,lancamento_id INTEGER NOT NULL,PRIMARY KEY(empresa_id,assinatura),FOREIGN KEY(empresa_id) REFERENCES empresas(id));
    ''')
    if 'valor_centavos' not in {r[1] for r in conn.execute('PRAGMA table_info(lancamentos)')}:
        conn.execute('ALTER TABLE lancamentos ADD COLUMN valor_centavos INTEGER')
    conn.commit();return conn


def listar_empresas(caminho):
    conn=conectar(caminho)
    try:
        return [dict(x) for x in conn.execute('SELECT e.*,d.dados_json FROM empresas e LEFT JOIN cadastro_detalhes d ON d.empresa_id=e.id ORDER BY e.nome')]
    finally:conn.close()


def salvar_empresa(caminho,dados,*,confirmado=False,atualizar=False):
    if not confirmado:raise ImportacaoInvalida('Confira o cadastro e confirme antes de salvar.')
    nome=str(dados.get('razao_social') or '').strip();cnpj=cnpj_limpo(dados.get('cnpj',''))
    if not nome or not validar_cnpj(cnpj):raise ImportacaoInvalida('Informe a razão social e um CNPJ válido.')
    if dados.get('data_abertura'):
        try:datetime.strptime(dados['data_abertura'],'%Y-%m-%d')
        except (ValueError,TypeError):raise ImportacaoInvalida('Confira a data de abertura: use AAAA-MM-DD.') from None
    def limpar(v):
        if isinstance(v,float) and not math.isfinite(v):return None
        if isinstance(v,dict):return {k:limpar(x) for k,x in v.items()}
        if isinstance(v,list):return [limpar(x) for x in v]
        return v
    dados=limpar(dados)
    soma=Decimal('0')
    for socio in dados.get('qsa') or []:
        if not str(socio.get('nome') or '').strip():raise ImportacaoInvalida('Informe o nome de cada sócio do QSA.')
        participacao=socio.get('participacao')
        if participacao not in (None,''):
            try:p=Decimal(str(participacao).replace(',','.'))
            except InvalidOperation:raise ImportacaoInvalida('Participação societária inválida.') from None
            if not p.is_finite() or p<0 or p>100:raise ImportacaoInvalida('A participação deve ficar entre 0% e 100%.')
            soma+=p
    if soma>100:raise ImportacaoInvalida('A soma das participações informadas supera 100%.')
    conn=conectar(caminho)
    try:
        conn.execute('BEGIN IMMEDIATE')
        existentes=[r for r in conn.execute('SELECT id,cnpj FROM empresas') if cnpj_limpo(r['cnpj'])==cnpj]
        if len(existentes)>1:raise ImportacaoInvalida('Há cadastros duplicados deste CNPJ; revise antes de atualizar.')
        if existentes and not atualizar:raise ImportacaoInvalida('Esta empresa já existe. Marque a opção de atualizar o cadastro existente.')
        if existentes:
            empresa_id=existentes[0]['id'];conn.execute('UPDATE empresas SET nome=? WHERE id=?',(nome,empresa_id))
        else:
            empresa_id=conn.execute('INSERT INTO empresas(nome,cnpj) VALUES(?,?)',(nome,cnpj)).lastrowid
        anterior=conn.execute('SELECT dados_json FROM cadastro_detalhes WHERE empresa_id=?',(empresa_id,)).fetchone()
        anterior=json.loads(anterior[0]) if anterior else {}
        novo=dict(dados,cnpj=cnpj,razao_social=nome)
        if novo.get('qsa') is None:novo['qsa']=anterior.get('qsa',[])
        # Ausência no novo documento não apaga os dados já conferidos.
        for k,v in anterior.items():
            if k!='qsa' and novo.get(k) in (None,''):novo[k]=v
        conn.execute('INSERT OR REPLACE INTO cadastro_detalhes VALUES(?,?,?)',
            (empresa_id,json.dumps(novo,ensure_ascii=False,allow_nan=False),datetime.now(timezone.utc).isoformat()))
        conn.commit();return empresa_id
    except Exception:conn.rollback();raise
    finally:conn.close()


def importar_lancamentos(caminho,empresa_id,previa,*,confirmado=False,permitir_iguais=False):
    if not confirmado:raise ImportacaoInvalida('Confira a prévia e confirme a importação.')
    if previa.get('erros'):raise ImportacaoInvalida('Corrija todas as linhas com erro. Nenhum lançamento foi gravado.')
    if not previa.get('linhas'):raise ImportacaoInvalida('O arquivo não contém lançamentos válidos.')
    conn=conectar(caminho);inseridos=ignorados=0
    try:
        conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM empresas WHERE id=?',(empresa_id,)).fetchone():
            raise ImportacaoInvalida('Selecione uma empresa cadastrada.')
        # Considera também lançamentos anteriores feitos pelo módulo legado.
        existentes=set()
        for r in conn.execute('SELECT * FROM lancamentos WHERE empresa_id=?',(empresa_id,)):
            from decimal import Decimal, ROUND_HALF_UP
            centavos=r['valor_centavos'] if r['valor_centavos'] is not None else int((Decimal(str(r['valor']))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            existentes.add((r['data'],r['debito'],r['credito'],centavos,' '.join((r['historico'] or '').split())))
        for r in previa['linhas']:
            chave=(r['data'],r['debito'],r['credito'],r['valor_centavos'],' '.join(r['historico'].split()))
            if chave in existentes and not permitir_iguais:ignorados+=1;continue
            assinatura=sha256(json.dumps(chave,ensure_ascii=False).encode()).hexdigest()
            cur=conn.execute('INSERT INTO lancamentos(empresa_id,data,debito,credito,valor,historico,valor_centavos) VALUES(?,?,?,?,?,?,?)',
                (empresa_id,r['data'],r['debito'],r['credito'],r['valor_centavos']/100,r['historico'],r['valor_centavos']))
            conn.execute('INSERT OR IGNORE INTO importacoes_linhas VALUES(?,?,?)',(empresa_id,assinatura,cur.lastrowid))
            existentes.add(chave);inseridos+=1
        conn.commit();return dict(inseridos=inseridos,duplicados_ignorados=ignorados)
    except Exception:conn.rollback();raise
    finally:conn.close()
