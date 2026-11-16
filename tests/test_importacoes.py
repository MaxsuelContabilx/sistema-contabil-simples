from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from importacoes import (extrair_cartao,extrair_qsa,validar_cnpj,ler_lancamentos,texto_pdf,ImportacaoInvalida)
from cadastros import salvar_empresa,listar_empresas,importar_lancamentos,conectar
from relatorios import html_relatorio,pdf_relatorio

CARTAO='''REPÚBLICA FEDERATIVA DO BRASIL
COMPROVANTE DE INSCRIÇÃO E DE SITUAÇÃO CADASTRAL
NÚMERO DE INSCRIÇÃO
11.222.333/0001-81
DATA DE ABERTURA
01/01/2026
NOME EMPRESARIAL
EMPRESA FICTICIA DE TESTE LTDA
TÍTULO DO ESTABELECIMENTO (NOME DE FANTASIA)
TESTE
PORTE
ME
CÓDIGO E DESCRIÇÃO DA ATIVIDADE ECONÔMICA PRINCIPAL
62.01-5-01 - Desenvolvimento de programas
LOGRADOURO
RUA DE TESTE
NÚMERO
123
MUNICÍPIO
FORTALEZA
UF
CE
SITUAÇÃO CADASTRAL
ATIVA
'''
QSA='''CONSULTA QUADRO DE SÓCIOS E ADMINISTRADORES - QSA
CNPJ: 11.222.333/0001-81
Nome/Nome Empresarial:
SOCIO FICTICIO UM
Qualificação:
49-Sócio-Administrador
Nome/Nome Empresarial:
SOCIO FICTICIO DOIS
Qualificação:
22-Sócio
'''


class Documentos(unittest.TestCase):
    def test_cartao_com_campos_e_cnpj_validado(self):
        r=extrair_cartao(CARTAO)
        self.assertEqual(r['cnpj'],'11222333000181')
        self.assertEqual(r['razao_social'],'EMPRESA FICTICIA DE TESTE LTDA')
        self.assertEqual(r['data_abertura'],'2026-01-01')
        self.assertEqual(r['municipio'],'FORTALEZA')
        self.assertIsNone(r['qsa'])

    def test_qsa_nao_inventa_participacao_ou_residencia(self):
        r=extrair_qsa(QSA,'11222333000181')
        self.assertEqual(len(r['socios']),2)
        self.assertIsNone(r['socios'][0]['participacao'])
        self.assertEqual(r['socios'][0]['tipo_beneficiario'],'Não informado')
        with self.assertRaises(ImportacaoInvalida):extrair_qsa(QSA,'11444777000161')

    def test_cnpj_numerico_alfanumerico_e_invalido(self):
        self.assertTrue(validar_cnpj('11.222.333/0001-81'))
        self.assertTrue(validar_cnpj('12.ABC.345/01DE-35'))
        self.assertFalse(validar_cnpj('11.222.333/0001-82'))
        self.assertFalse(validar_cnpj('00.000.000/0000-00'))

    def test_pdf_real_com_texto_e_imagem_sem_ocr(self):
        from reportlab.pdfgen.canvas import Canvas
        buf=BytesIO();c=Canvas(buf)
        y=800
        for linha in CARTAO.splitlines():c.drawString(30,y,linha);y-=18
        c.save()
        self.assertEqual(extrair_cartao(texto_pdf(buf.getvalue()))['cnpj'],'11222333000181')
        blank=BytesIO();c=Canvas(blank);c.showPage();c.save()
        with self.assertRaises(ImportacaoInvalida):texto_pdf(blank.getvalue())

    def test_pdf_e_html_com_escape_e_paginacao(self):
        html=html_relatorio('Teste <script>', ['Campo'], [['<script>alert(1)</script>']],empresa='TESTE & CIA')
        self.assertNotIn('<script>alert',html)
        self.assertIn('window.print()',html)
        pdf=pdf_relatorio('Teste & impressão',['Campo','Valor'],[[str(i),'R$ 1.234,56'] for i in range(100)])
        self.assertTrue(pdf.startswith(b'%PDF'))
        from pypdf import PdfReader
        self.assertGreater(len(PdfReader(BytesIO(pdf)).pages),1)


class BancoEImportacao(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.db=Path(self.tmp.name)/'teste.db'
        self.empresa=salvar_empresa(self.db,extrair_cartao(CARTAO),confirmado=True)
    def tearDown(self):self.tmp.cleanup()

    def csv(self,linhas='01/01/2026;1.01;4.01;1.234,56;Venda\n'):
        return ler_lancamentos(('Data;Débito;Crédito;Valor;Histórico\n'+linhas).encode('utf-8-sig'))

    def test_valor_brasileiro_e_data_e_transacao(self):
        previa=self.csv();self.assertEqual(previa['linhas'][0]['valor_centavos'],123456)
        r=importar_lancamentos(self.db,self.empresa,previa,confirmado=True)
        self.assertEqual(r['inseridos'],1)
        conn=conectar(self.db)
        try:r=conn.execute('SELECT * FROM lancamentos').fetchone();self.assertEqual(r['valor_centavos'],123456)
        finally:conn.close()

    def test_duplicidade_entre_importacoes_e_dentro_do_lote(self):
        p=self.csv('01/01/2026;1.01;4.01;100,00;Venda\n'*2)
        a=importar_lancamentos(self.db,self.empresa,p,confirmado=True)
        b=importar_lancamentos(self.db,self.empresa,p,confirmado=True)
        self.assertEqual(a,dict(inseridos=1,duplicados_ignorados=1))
        self.assertEqual(b,dict(inseridos=0,duplicados_ignorados=2))

    def test_erros_bloqueiam_todo_o_lote(self):
        p=self.csv('01/01/2026;1.01;4.01;100;Venda\n31/02/2026;1.01;4.01;100;Erro\n')
        with self.assertRaises(ImportacaoInvalida):importar_lancamentos(self.db,self.empresa,p,confirmado=True)
        conn=conectar(self.db)
        try:self.assertEqual(conn.execute('SELECT COUNT(*) FROM lancamentos').fetchone()[0],0)
        finally:conn.close()

    def test_empresa_inexistente_e_confirmacao(self):
        with self.assertRaises(ImportacaoInvalida):importar_lancamentos(self.db,999,self.csv(),confirmado=True)
        with self.assertRaises(ImportacaoInvalida):importar_lancamentos(self.db,self.empresa,self.csv())

    def test_duplicidade_cnpj_e_qsa_preservado_ao_importar_so_cartao(self):
        dados=extrair_cartao(CARTAO);dados['qsa']=extrair_qsa(QSA)['socios']
        salvar_empresa(self.db,dados,confirmado=True,atualizar=True)
        salvar_empresa(self.db,extrair_cartao(CARTAO),confirmado=True,atualizar=True)
        import json
        empresas=listar_empresas(self.db)
        self.assertEqual(len(empresas),1)
        self.assertEqual(len(json.loads(empresas[0]['dados_json'])['qsa']),2)
        with self.assertRaises(ImportacaoInvalida):salvar_empresa(self.db,dados,confirmado=True)

    def test_nao_permite_conta_invalida_mesma_conta_ou_valor_negativo(self):
        for l in ['01/01/2026;9.99;4.01;100;X\n','01/01/2026;1.01;1.01;100;X\n','01/01/2026;1.01;4.01;-1;X\n']:
            self.assertTrue(self.csv(l)['erros'])
