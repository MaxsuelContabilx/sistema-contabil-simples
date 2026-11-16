from decimal import Decimal as D
import unittest
from folha import inss_empregado,irrf_mensal,salario_liquido


class Folha(unittest.TestCase):
    def test_inss_por_faixa_e_teto(self):
        self.assertEqual(inss_empregado('1621'),D('121.58'))
        self.assertEqual(inss_empregado('8475.55'),D('988.09'))
        self.assertEqual(inss_empregado('20000'),D('988.09'))

    def test_irrf_isento_ate_5000_e_reducao_sobre_rendimento(self):
        self.assertEqual(salario_liquido('5000')['irrf'],0)
        r=salario_liquido('5500')
        self.assertEqual(r['tipo_deducao'],'Simplificado')
        self.assertEqual(r['base'],D('4892.80'))
        self.assertEqual(r['irrf'],D('190.47'))

    def test_deducao_legal_quando_maior_e_sem_reducao_acima_7350(self):
        r=salario_liquido('8000',dependentes=2)
        self.assertEqual(r['tipo_deducao'],'Deduções legais')
        self.assertEqual(r['reducao'],0)

    def test_dois_saldos_distintos_salario_e_dividendos(self):
        r=salario_liquido('4000')
        self.assertEqual(r['irrf'],0)
        self.assertEqual(r['liquido'],r['salario']-r['inss'])
