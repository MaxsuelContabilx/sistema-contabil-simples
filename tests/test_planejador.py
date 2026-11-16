from copy import deepcopy
from decimal import Decimal as D
import unittest
from planejador import planejar,distribuir_resultado,prolabore_liquido
from pj_clt import comparar_vinculos
from folha import inss_empregado,salario_liquido
from tax_engine import Pendente


def cenario():
    return dict(empresa='Empresa fictícia',ano=2026,mes=1,situacao='abertura',comercio=280000,industria=0,servicos=0,
        custos=0,salarios=0,prolabore=8750,encargos_fs=0,anexo='III',fator_r=False,
        distribuicoes=[dict(nome='Sócio',tipo='PF_RESIDENTE',origem='2026',valor=0)],
        tributos={},limite_irpj=1250000,limite_csll=1250000,fundamento_limite='LC 224/2025, nominal',
        acrescimos_irpj=0,acrescimos_csll=0,saldo_irpj=0,saldo_csll=0,modo_distribuicao='automatico')


class Planejador(unittest.TestCase):
    def test_exemplo_do_usuario(self):
        itens=planejar(cenario())['resultados'];sn=itens[0]
        self.assertEqual(sn['tributos_empresa'],D('32765'))
        self.assertEqual(sn['dividendo_bruto'],D('238485'))
        self.assertEqual(sn['ir_dividendos'],D('23848.50'))
        self.assertEqual(sn['dividendo_liquido'],D('214636.50'))
        self.assertEqual(sn['liquido_total_socios'],D('221213.06'))
        self.assertEqual(itens[1]['tributos_empresa'],D('18594'))
        self.assertTrue(itens[1]['calculo_condicional'])
        self.assertEqual(itens[2]['tributos_empresa'],D('108474'))
        self.assertTrue(itens[2]['calculo_condicional'])
        self.assertEqual(len({v['ir_dividendos'] for v in itens}),3)
        self.assertNotIn('Nenhuma distribuição',str(itens[0]['pendencias']))

    def test_inss_clt_progressivo_e_ci(self):
        self.assertEqual(inss_empregado(20000),D('988.09'))
        self.assertEqual(prolabore_liquido(20000)['inss'],D('932.31'))
        self.assertEqual(prolabore_liquido(8750)['irrf'],D('1241.13'))

    def test_rateio_limite_por_beneficiario(self):
        p=cenario();p['distribuicoes']=[dict(nome=x,tipo='PF_RESIDENTE',origem='2026',percentual_distribuicao=50) for x in ['A','B']]
        self.assertEqual(distribuir_resultado(100000,p)['irrf'],0)
        self.assertEqual(distribuir_resultado(120000,p)['irrf'],12000)
        p['distribuicoes'][1]['percentual_distribuicao']=40
        with self.assertRaises(Pendente):distribuir_resultado(100000,p)
        p['distribuicoes'][1]['percentual_distribuicao']=None
        with self.assertRaises(Pendente):distribuir_resultado(100000,p)

    def test_falta_residencia(self):
        p=cenario();p['distribuicoes'][0]['tipo']='PENDENTE'
        for r in planejar(p)['resultados']:self.assertIsNone(r['ir_dividendos'])

    def test_deficit(self):
        p=cenario();p['custos']=300000
        for r in planejar(p)['resultados']:
            self.assertEqual(r['dividendo_bruto'],0);self.assertEqual(r['ir_dividendos'],0)
            self.assertGreater(r['aporte_necessario'],0)

    def test_locais_confirmados(self):
        p=cenario();p['dispensa_teste_2026_confirmada']=True
        p['tributos']={k:{'ICMS/ISS/IPI':12000,'Encargos da folha':1750} for k in ['presumido','real']}
        for r in planejar(p)['resultados'][1:]:self.assertFalse(r['calculo_condicional'])

    def test_reforma_sem_desconto_duplo(self):
        p=cenario();p.update(cbs_pct=11.3,ibs_pct=18.7,preco_reforma='final')
        r=planejar(p,'reforma');self.assertEqual(r['iva']['fatura'],280000)
        for v in r['resultados'][1:]:
            self.assertLess(abs(v['dividendo_bruto']-(D('280000')-D('8750')-v['tributos_empresa'])),D('.02'))
        p['preco_reforma']='repassar';r=planejar(p,'reforma')
        self.assertEqual(r['iva']['fatura'],364000)
        for v in r['resultados'][1:]:self.assertEqual(v['dividendo_bruto'],D('364000')-8750-v['tributos_empresa'])

    def test_creditos_sem_caixa_ficticio(self):
        p=cenario();p.update(preco_reforma='repassar',custos=10000,credito_cbs=1000,credito_ibs=2000)
        r=planejar(p,'reforma')
        for v in r['resultados'][1:]:self.assertEqual(v['dividendo_bruto'],r['iva']['fatura']-D('10000')-D('8750')-v['tributos_empresa'])
        p['credito_cbs']=50000
        with self.assertRaises(Pendente):planejar(p,'reforma')

    def test_ano_sem_tabela(self):
        p=cenario();p['ano']=2027
        with self.assertRaises(Pendente):planejar(p)

    def test_sem_historico_do_simples_nao_inventa_ir_zero(self):
        p=cenario();p.update(situacao='existente',rbt12=None)
        sn=planejar(p)['resultados'][0]
        self.assertIsNone(sn['tributos_empresa']);self.assertIsNone(sn['ir_dividendos'])

    def test_quarto_trimestre_mostra_componentes_e_sinaliza_irpj_csll(self):
        p=cenario();p['mes']=10
        lp=planejar(p)['resultados'][1]
        self.assertIsNotNone(lp['tributos_empresa']);self.assertTrue(lp['calculo_condicional'])
        self.assertIn('Quarto trimestre',str(lp['pendencias']))

    def test_dispensa_2026_nao_e_presumida(self):
        p=cenario();lp=planejar(p)['resultados'][1]
        self.assertIn('falta confirmar a dispensa',str(lp['pendencias']))

    def test_simples_fora_sem_partilha(self):
        p=cenario();p.update(simples_reforma='fora',das_substituido=None)
        r=planejar(p,'reforma')['resultados'][0]
        self.assertTrue(r['calculo_condicional'])
        self.assertEqual(r['componentes']['DAS remanescente (projeção)'],32765)
        p['das_substituido']=40000
        with self.assertRaises(Pendente):planejar(p,'reforma')

    def test_manual_excessivo(self):
        p=cenario();p['modo_distribuicao']='manual';p['distribuicoes'][0]['valor']=400000
        self.assertIn('supera o resultado',str(planejar(p)['resultados'][0]['pendencias']))

    def test_clt_sem_duplicar_ferias(self):
        r=comparar_vinculos(6000,15000,cenario(),beneficios=1000);c=r['clt']
        self.assertEqual(c['liquido_anual'],11*salario_liquido(6000)['liquido']+salario_liquido(8000)['liquido']+salario_liquido(6000)['liquido'])
        self.assertEqual(c['fgts_anual'],6400);self.assertEqual(c['beneficios_anuais'],12000)
        for v in r['pj']['resultados']:self.assertEqual(v['liquido_anual_pj'],v['liquido_total_socios']*12)

    def test_meses_sem_nota(self):
        p=cenario();p.update(custos=1000,prolabore=3000)
        a=comparar_vinculos(6000,15000,p,meses_faturados=12)['pj']['resultados'][0]
        b=comparar_vinculos(6000,15000,p,meses_faturados=11)['pj']['resultados'][0]
        self.assertEqual(b['liquido_anual_pj'],a['liquido_total_socios']*11-D('1330'))
        self.assertEqual(b['aporte_mes_sem_nota'],4000)

    def test_nao_altera_entradas(self):
        p=cenario();c=deepcopy(p);planejar(p,'reforma');comparar_vinculos(6000,20000,p)
        self.assertEqual(p,c)

    def test_anexo_iv_sem_nota_mantem_cpp(self):
        p=cenario();p.update(comercio=0,servicos=15000,anexo='IV',prolabore=3000,custos=1000)
        a=comparar_vinculos(6000,15000,p,meses_faturados=12)['pj']['resultados'][0]
        b=comparar_vinculos(6000,15000,p,meses_faturados=11)['pj']['resultados'][0]
        self.assertEqual(b['liquido_anual_pj'],a['liquido_total_socios']*11-D('1930'))
        self.assertEqual(b['aporte_mes_sem_nota'],4600)

if __name__=='__main__':unittest.main()
