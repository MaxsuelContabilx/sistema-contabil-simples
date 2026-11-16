from decimal import Decimal as D
import unittest
from cenario import comparar,ir_dividendos_cenario,simples_primeiro_mes
from tax_engine import Pendente


class CenarioCompartilhado(unittest.TestCase):
    def dados(self):
        return dict(empresa='Empresa fictícia',ano=2026,mes=1,situacao='abertura',comercio='50000',industria='0',servicos='0',
            custos='15000',salarios='8000',prolabore='3000',encargos_fs='0',anexo='III',fator_r=False,
            distribuicoes=[dict(nome='Sócio 1',tipo='PF_RESIDENTE',origem='2026',valor='60000')],
            tributos={k:{'PIS':'325' if k=='presumido' else '825','COFINS':'1500' if k=='presumido' else '3800',
                'ICMS/ISS/IPI':'0','Encargos da folha':'0'} for k in ('presumido','real')},
            limite_irpj='1250000',limite_csll='1250000',fundamento_limite='LC224, nominal',
            acrescimos_irpj='0',acrescimos_csll='0',saldo_irpj='0',saldo_csll='0')

    def test_dividendos_entram_nos_tres_regimes_sem_deduzir_como_despesa(self):
        r=comparar(self.dados())
        for item in r['resultados']:
            self.assertEqual(item['ir_dividendos'],D('6000'))
            self.assertEqual(item['total_consolidado'],item['tributos_empresa']+D('6000'))
            self.assertEqual(item['resultado_gerencial'],D('24000')-item['tributos_empresa'])

    def test_dividendos_por_socio_sem_rateio_presumido(self):
        d=[dict(nome='A',tipo='PF_RESIDENTE',origem='2026',valor='40000'),dict(nome='B',tipo='PF_RESIDENTE',origem='2026',valor='40000')]
        self.assertEqual(ir_dividendos_cenario(d)['irrf'],0)
        d[1]['nome']='A';self.assertEqual(ir_dividendos_cenario(d)['irrf'],D('8000'))

    def test_sem_distribuicao_zero_explicito_nao_mesma_coisa_que_ausencia(self):
        self.assertEqual(ir_dividendos_cenario([])['irrf'],0)
        with self.assertRaises(Pendente):ir_dividendos_cenario(None)

    def test_residencia_nao_informada_nao_retorna_imposto_zero(self):
        p=self.dados();p['distribuicoes'][0]['tipo']='PENDENTE'
        for item in comparar(p)['resultados']:
            self.assertIsNone(item['ir_dividendos']);self.assertIsNone(item['total_consolidado'])

    def test_dados_ausentes_nao_viram_tributos_zero(self):
        p=self.dados();p['tributos']['presumido']['ICMS/ISS/IPI']=None
        r=comparar(p)['resultados'][1]
        self.assertIsNone(r['tributos_empresa']);self.assertIsNone(r['total_consolidado'])
        self.assertIn('IRPJ (equivalente mensal)',r['componentes'])
        self.assertEqual(r['ir_dividendos'],D('6000'))

    def test_inicio_empresa_anualizacao_e_fator_r_primeiro_mes(self):
        r=simples_primeiro_mes({'servicos':'50000','comercio':'0','industria':'0'},'14000',sujeito_fator=True)
        self.assertEqual(r['rbt12_proporcional'],D('600000'));self.assertEqual(r['anexo_servicos'],'III')
        self.assertEqual(r['das'],D('5280'))
        r=simples_primeiro_mes({'servicos':'50000'},'0',sujeito_fator=True)
        self.assertEqual(r['anexo_servicos'],'V')

    def test_nao_extrapola_para_2027(self):
        p=self.dados();p['ano']=2027
        with self.assertRaises(Pendente):comparar(p)
