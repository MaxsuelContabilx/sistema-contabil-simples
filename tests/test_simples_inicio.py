from decimal import Decimal as D
import unittest
from simples_inicio import referencia_inicio,calcular_inicio,idade_meses
from indicadores import destacar_regime
from tax_engine import Pendente


def hist(valores,folhas=None):
    return [dict(mes_atividade=i+1,receita=r,folha=(folhas or [0]*len(valores))[i]) for i,r in enumerate(valores)]


class Inicio(unittest.TestCase):
    def test_2026_media_exclui_atual_inclui_zeros(self):
        self.assertEqual(referencia_inicio(2026,1,9000)['rbt12_proporcional'],108000)
        self.assertEqual(referencia_inicio(2026,2,40000,historico=hist([9000]))['rbt12_proporcional'],108000)
        self.assertEqual(referencia_inicio(2026,3,6000,historico=hist([9000,40000]))['rbt12_proporcional'],294000)
        self.assertEqual(referencia_inicio(2026,4,50000,historico=hist([0,0,60000]))['rbt12_proporcional'],240000)

    def test_2026_12_media_13_soma(self):
        self.assertEqual(referencia_inicio(2026,12,999999,historico=hist([1000]*11))['rbt12_proporcional'],12000)
        self.assertEqual(referencia_inicio(2026,13,999999,historico=hist([1000]*12))['rbt12_proporcional'],12000)
        self.assertIsNone(referencia_inicio(2026,13,0,historico=hist([1000]*12))['divisor_media'])

    def test_190_primeiros_dois_meses_faixa_e_fator(self):
        for n in [1,2]:
            r=referencia_inicio(2027,n,280000,0,sujeito_fator=True)
            self.assertTrue(r['primeira_faixa']);self.assertIsNone(r['rbt12_proporcional'])
            self.assertEqual(r['fator_r'],D('.28'));self.assertEqual(r['meses_utilizados'],[])
        self.assertFalse(referencia_inicio(2026,1,280000)['primeira_faixa'])
        self.assertEqual(referencia_inicio(2026,1,280000)['rbt12_proporcional'],3360000)

    def test_190_terceiro_e_quarto_exemplos_oficiais(self):
        self.assertEqual(referencia_inicio(2027,3,9000,historico=hist([8000,7000]))['rbt12_proporcional'],96000)
        self.assertEqual(referencia_inicio(2027,4,5000,historico=hist([8000,7000,9000]))['rbt12_proporcional'],90000)
        self.assertEqual(referencia_inicio(2027,3,9000,historico=hist([8000]))['meses_utilizados'],[1])

    def test_190_treze_media_quatorze_soma_defasada(self):
        r=referencia_inicio(2027,13,0,historico=hist([1000]*11+[999999]))
        self.assertEqual(r['rbt12_proporcional'],12000);self.assertEqual(r['divisor_media'],11)
        r=referencia_inicio(2027,14,0,historico=hist([1000]*12+[999999]))
        self.assertEqual(r['rbt12_proporcional'],12000);self.assertEqual(r['meses_utilizados'],list(range(1,13)))
        self.assertIsNone(r['divisor_media'])

    def test_mes_ausente_nao_e_zero(self):
        with self.assertRaises(Pendente):referencia_inicio(2026,3,1000,historico=hist([9000]))
        with self.assertRaises(Pendente):referencia_inicio(2026,2,1000,historico=[dict(mes_atividade=1,receita=None)])
        with self.assertRaises(Pendente):referencia_inicio(2026,2,1000,historico=hist([1])+hist([2]))

    def test_fator_r_media_e_zeros(self):
        r=calcular_inicio({'servicos':50000},0,mes_atividade=3,historico=hist([50000,50000],[14000,14000]),sujeito_fator=True)
        self.assertEqual(r['anexo_servicos'],'III');self.assertEqual(r['das'],5280)
        r=calcular_inicio({'servicos':50000},0,mes_atividade=3,historico=hist([50000,50000],[0,0]),sujeito_fator=True)
        self.assertEqual(r['anexo_servicos'],'V')
        r=calcular_inicio({'comercio':50000},0,mes_atividade=2,historico=hist([0]))
        self.assertEqual(r['das'],2000)

    def test_2027_nao_repete_tabelas_monetarias_2026(self):
        with self.assertRaises(Pendente):calcular_inicio({'comercio':10000},0,ano=2027)

    def test_conta_desde_cnpj_inclusive_mes_sem_receita(self):
        self.assertEqual(idade_meses('2026-01-31',2026,3),3)
        self.assertEqual(idade_meses('2026-12-31',2027,1),2)
        with self.assertRaises(Pendente):idade_meses('2027-02-01',2027,1)


class Indicadores(unittest.TestCase):
    def dados(self):
        return {'resultados':[dict(regime=n,liquido_total_socios=D(v),total_consolidado=D(t),itens_pendentes=[]) for n,v,t in [('SN','100','40'),('LP','120','20'),('LR','110','30')]]}

    def test_maior_liquido_e_menor_tributo(self):
        for criterio in ['liquido','tributos']:
            r=destacar_regime(self.dados(),criterio)
            self.assertEqual(r['regimes'],['LP']);self.assertFalse(r['provisorio']);self.assertEqual(r['diferenca'],10)

    def test_condicional_sinaliza_mesmo_se_outro_regime_vencer(self):
        d=self.dados();d['resultados'][0]['itens_pendentes']=['ISS não informado']
        self.assertTrue(destacar_regime(d)['provisorio'])
        d=self.dados();d['resultados'][0]['liquido_total_socios']=None
        self.assertTrue(destacar_regime(d)['provisorio'])

    def test_empate_e_ausencia(self):
        d=self.dados();d['resultados'][0]['liquido_total_socios']=D(120)
        self.assertTrue(destacar_regime(d)['empate'])
        for i in d['resultados']:i['liquido_total_socios']=None
        self.assertFalse(destacar_regime(d)['disponivel'])

if __name__=='__main__':unittest.main()
