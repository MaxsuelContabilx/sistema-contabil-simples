from io import BytesIO
import unittest
from enquadramento import avaliar_simples
from relatorio_executivo import gerar_pdf,gerar_html
from planejador import planejar
from indicadores import destacar_regime
from test_planejador import cenario

class Relatorio(unittest.TestCase):
    def test_limite_e_sublimite_distintos(self):
        p=cenario();p['comercio']=300000;self.assertIsNone(avaliar_simples(p))
        for v in [300001,350000,400000]:
            p['comercio']=v;self.assertEqual(avaliar_simples(p)['status'],'revisao_sublimite')
        for v in [400001,8000000]:
            p['comercio']=v;self.assertEqual(avaliar_simples(p)['status'],'nao_enquadrado')
        p.update(situacao='existente',comercio=500000);self.assertIsNone(avaliar_simples(p))

    def test_fora_do_cenario_nao_vence_ranking(self):
        p=cenario();p['comercio']=8000000;r=planejar(p)
        self.assertEqual(r['resultados'][0]['enquadramento']['status'],'nao_enquadrado')
        self.assertNotIn('Simples Nacional',destacar_regime(r)['regimes'])

    def test_pdf_e_html_destacam_regime_sem_dump_de_dicionario(self):
        from pypdf import PdfReader
        p=cenario();r=planejar(p);d=destacar_regime(r);painel=dict(resultado=r,destaque=d,cenario=p)
        pdf=gerar_pdf('Comparativo',painel);doc=PdfReader(BytesIO(pdf));texto=' '.join(p.extract_text() for p in doc.pages)
        self.assertIn('Destaque provisório'.upper(),texto);self.assertIn(d['regimes'][0],texto)
        self.assertIn('Comparação mensal',texto);self.assertIn('Memória e pontos',texto)
        self.assertNotIn("'provisorio':",texto)
        html=gerar_html('Comparativo',painel)
        self.assertIn('id="imprimir"',html);self.assertIn('window.print()',html)
        self.assertIn(d['regimes'][0],html)
        p['empresa']='<script>alert(1)</script>';html=gerar_html('Comparativo',painel)
        self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html)

    def test_relatorio_nao_enquadrado_explica_em_vez_de_zero(self):
        p=cenario();p['comercio']=8000000;r=planejar(p)
        html=gerar_html('Comparativo',dict(resultado=r,destaque=destacar_regime(r),cenario=p))
        self.assertIn('Não se enquadra',html)

if __name__=='__main__':unittest.main()
