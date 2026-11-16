"""Leitura local de PDFs cadastrais e CSV contábil, sempre com conferência."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
import csv
import re
import unicodedata


class ImportacaoInvalida(ValueError):
    pass


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(texto)) if not unicodedata.combining(c)).upper()


def cnpj_limpo(valor):
    return re.sub(r'[^A-Z0-9]', '', str(valor).upper())


def validar_cnpj(valor):
    """Dígitos verificadores: numérico e novo formato alfanumérico da RFB."""
    s=cnpj_limpo(valor)
    if not re.fullmatch(r'[A-Z0-9]{12}\d{2}',s) or len(set(s))==1:
        return False
    dados=[ord(c)-48 for c in s[:12]]
    for pesos, esperado in [([5,4,3,2,9,8,7,6,5,4,3,2],s[12]),([6,5,4,3,2,9,8,7,6,5,4,3,2],s[13])]:
        resto=sum(v*p for v,p in zip(dados,pesos))%11
        dv=0 if resto<2 else 11-resto
        if str(dv)!=esperado:return False
        dados.append(dv)
    return True


def texto_pdf(conteudo):
    if not conteudo or len(conteudo)>10*1024*1024:
        raise ImportacaoInvalida('Use um PDF de até 10 MB.')
    if not conteudo.lstrip().startswith(b'%PDF'):
        raise ImportacaoInvalida('O arquivo não é um PDF reconhecido.')
    from pypdf import PdfReader
    try:
        reader=PdfReader(BytesIO(conteudo))
        if reader.is_encrypted:
            raise ImportacaoInvalida('O PDF está protegido. Envie uma cópia sem senha.')
        if len(reader.pages)>25:
            raise ImportacaoInvalida('Envie apenas o cartão CNPJ ou o QSA, com até 25 páginas.')
        texto='\n'.join(page.extract_text(extraction_mode='layout') or '' for page in reader.pages)
    except ImportacaoInvalida:raise
    except Exception as exc:
        raise ImportacaoInvalida('Não foi possível ler o PDF. Gere uma nova cópia do documento.') from exc
    if len(re.sub(r'\s','',texto))<30:
        raise ImportacaoInvalida('Este PDF parece ser uma imagem. A leitura por OCR ainda não está disponível; use um PDF com texto ou cadastre manualmente.')
    return texto


CAMPOS={
 'razao_social':'NOME EMPRESARIAL', 'nome_fantasia':'TITULO DO ESTABELECIMENTO',
 'data_abertura':'DATA DE ABERTURA', 'porte':'PORTE',
 'cnae_principal':'CODIGO E DESCRICAO DA ATIVIDADE ECONOMICA PRINCIPAL',
 'natureza_juridica':'CODIGO E DESCRICAO DA NATUREZA JURIDICA',
 'logradouro':'LOGRADOURO','numero':'NUMERO','complemento':'COMPLEMENTO',
 'cep':'CEP','bairro':'BAIRRO/DISTRITO','municipio':'MUNICIPIO','uf':'UF',
 'email':'ENDERECO ELETRONICO','telefone':'TELEFONE','situacao':'SITUACAO CADASTRAL'}
ROTULOS=list(CAMPOS.values())+['NUMERO DE INSCRICAO','CODIGO E DESCRICAO DAS ATIVIDADES ECONOMICAS SECUNDARIAS',
 'DATA DA SITUACAO CADASTRAL','MOTIVO DE SITUACAO CADASTRAL','SITUACAO ESPECIAL','DATA DA SITUACAO ESPECIAL',
 'ENTE FEDERATIVO RESPONSAVEL','NOME/NOME EMPRESARIAL','QUALIFICACAO','CAPITAL SOCIAL']


def valor_campo(texto,rotulo):
    linhas=texto.splitlines()
    for i,linha in enumerate(linhas):
        norm=normalizar(linha)
        if 'COMPROVANTE DE INSCRICAO' in norm:continue
        pos=norm.find(rotulo)
        if pos<0:continue
        # Evita NUMERO em NUMERO DE INSCRICAO e SITUACAO em DATA DA SITUACAO.
        if rotulo in ('NUMERO','SITUACAO CADASTRAL') and norm.strip().startswith(('NUMERO DE INSCRICAO','DATA DA SITUACAO')):
            continue
        outras=sorted({normalizar(linha).find(r) for r in ROTULOS if r!=rotulo and normalizar(linha).find(r)>pos})
        direita=outras[0] if outras else None
        cauda=linha[pos+len(rotulo):direita].strip(' :\t')
        if cauda and not cauda.startswith('(') and not any(r in normalizar(cauda) for r in ROTULOS):
            return cauda
        for proxima in linhas[i+1:i+5]:
            if not proxima.strip():continue
            if any(r in normalizar(proxima) for r in ROTULOS):break
            valor=(proxima[pos:direita] if direita is not None else proxima[pos:] if pos>4 else proxima).strip()
            if valor:return valor
        return ''
    return ''


def encontrar_cnpj(texto):
    for match in re.finditer(r'(?<![A-Z0-9])(?:[A-Z0-9]{2}\.[A-Z0-9]{3}\.[A-Z0-9]{3}/[A-Z0-9]{4}-\d{2}|[A-Z0-9]{12}\d{2})(?![A-Z0-9])',normalizar(texto)):
        if validar_cnpj(match.group()):return cnpj_limpo(match.group())
    return ''


def extrair_cartao(texto):
    if 'NOME EMPRESARIAL' not in normalizar(texto) or 'COMPROVANTE DE INSCRICAO' not in normalizar(texto):
        raise ImportacaoInvalida('Não identifiquei o cartão CNPJ. Confira se selecionou o documento correto.')
    dados={k:valor_campo(texto,r) for k,r in CAMPOS.items()}
    dados['cnpj']=encontrar_cnpj(texto)
    if not dados['cnpj']:
        raise ImportacaoInvalida('Não encontrei um CNPJ com dígitos verificadores válidos. Confira o PDF ou cadastre manualmente.')
    if dados['data_abertura']:
        try:dados['data_abertura']=datetime.strptime(dados['data_abertura'],'%d/%m/%Y').date().isoformat()
        except ValueError:dados['data_abertura']=''
    dados['qsa']=None
    dados['pendencias']=['Confira os campos antes de salvar. O PDF não valida a autenticidade ou a atualidade do cadastro.',
                         'O cartão CNPJ normalmente não contém os sócios. Envie o PDF do QSA separadamente, se tiver.']
    return dados


def extrair_qsa(texto,cnpj_esperado=None):
    cnpj=encontrar_cnpj(texto)
    if cnpj_esperado and cnpj and cnpj!=cnpj_limpo(cnpj_esperado):
        raise ImportacaoInvalida('O CNPJ do QSA é diferente do cartão. Nenhum dado foi salvo.')
    partes=re.split(r'NOME\s*/\s*NOME\s+EMPRESARIAL\s*:',texto,flags=re.I)
    socios=[]
    for bloco in partes[1:]:
        nome=next((l.strip() for l in bloco.splitlines() if l.strip()),'')
        qualificacao=re.search(r'QUALIFICA[ÇC][ÃA]O\s*:\s*([^\n]+)',bloco,re.I)
        if qualificacao is None:
            qualificacao=re.search(r'QUALIFICA[ÇC][ÃA]O\s*:\s*\n\s*([^\n]+)',bloco,re.I)
        participacao=re.search(r'PARTICIPA[ÇC][ÃA]O(?:\s+(?:NO CAPITAL|SOCIET[ÁA]RIA))?\s*:?\s*([\d.,]+)\s*%',bloco,re.I)
        if nome:
            socios.append({'nome':nome,'qualificacao':qualificacao.group(1).strip() if qualificacao else '',
                'participacao':participacao.group(1).replace(',','.') if participacao else None,
                'tipo_beneficiario':'Não informado','dividendo_mensal':'0'})
    if not socios:raise ImportacaoInvalida('Não identifiquei os sócios neste PDF. Confira o documento ou preencha o QSA manualmente.')
    return {'cnpj':cnpj,'socios':socios,'pendencias':[
        'Percentuais, residência fiscal e tipo do beneficiário não são presumidos quando ausentes do QSA.',
        'QSA sem CNPJ legível exige confirmação da empresa à qual pertence.']}


CONTAS={'1.01','1.02','1.03','1.04','2.01','2.02','2.03','2.04','2.05','2.06','4.01','5.01','5.02','6.01','7.01'}


def moeda_csv(valor):
    s=re.sub(r'R\$|\s','',str(valor)).strip()
    if ',' in s:s=s.replace('.','').replace(',','.')
    try:numero=Decimal(s)
    except InvalidOperation:raise ImportacaoInvalida('Valor monetário inválido.') from None
    if not numero.is_finite() or numero<=0 or numero!=numero.quantize(Decimal('.01')):
        raise ImportacaoInvalida('Use um valor positivo com até duas casas decimais.')
    return int(numero*100)


def ler_lancamentos(conteudo):
    if len(conteudo)>10*1024*1024:raise ImportacaoInvalida('Use um CSV de até 10 MB.')
    try:texto=conteudo.decode('utf-8-sig')
    except UnicodeDecodeError:texto=conteudo.decode('cp1252')
    cabecalho=texto.splitlines()[0] if texto.splitlines() else ''
    sep=';' if ';' in cabecalho else '\t' if '\t' in cabecalho else ','
    reader=csv.DictReader(StringIO(texto),delimiter=sep)
    nomes={normalizar(c).replace(' ','').replace('_',''):c for c in reader.fieldnames or []}
    obrigatorias=['DATA','DEBITO','CREDITO','VALOR','HISTORICO']
    if any(c not in nomes for c in obrigatorias):
        raise ImportacaoInvalida('O CSV precisa das colunas Data, Debito, Credito, Valor e Historico.')
    linhas=[];erros=[]
    for numero,raw in enumerate(reader,2):
        if numero>5001:raise ImportacaoInvalida('Importe até 5.000 lançamentos por arquivo.')
        if not any(str(v or '').strip() for v in raw.values()):continue
        try:
            valores={c:str(raw.get(nomes[c]) or '').strip() for c in obrigatorias}
            data=None
            for formato in ('%d/%m/%Y','%Y-%m-%d','%d.%m.%Y'):
                try:data=datetime.strptime(valores['DATA'],formato).date().isoformat();break
                except ValueError:pass
            if not data:raise ImportacaoInvalida('Data inválida; use DD/MM/AAAA ou AAAA-MM-DD.')
            if valores['DEBITO'] not in CONTAS or valores['CREDITO'] not in CONTAS:
                raise ImportacaoInvalida('Conta não cadastrada no plano de contas.')
            if valores['DEBITO']==valores['CREDITO']:raise ImportacaoInvalida('Débito e crédito não podem ser a mesma conta.')
            linhas.append(dict(data=data,debito=valores['DEBITO'],credito=valores['CREDITO'],
                valor_centavos=moeda_csv(valores['VALOR']),historico=valores['HISTORICO'],linha=numero))
        except ImportacaoInvalida as exc:erros.append({'linha':numero,'erro':str(exc)})
    return {'linhas':linhas,'erros':erros,'total':len(linhas)+len(erros)}
