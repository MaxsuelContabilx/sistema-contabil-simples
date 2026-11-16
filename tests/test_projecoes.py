from copy import deepcopy
from decimal import Decimal as D
import unittest
from projecoes import gerar_cenario, projetar_ano
from regras import fotografia_regras, verificar_memoria
from tax_engine import Pendente


class Projecoes(unittest.TestCase):
    def entradas(self):
        return dict(meses=[dict(mes=i, comercio='50000', industria='0', servicos='0',
            custos_despesas='20000', fs_legal='14000', resultado_irpj='10000',
            resultado_csll='10000', acrescimos_irpj='0', acrescimos_csll='0') for i in range(1,13)],
            historico=[dict(mes=i, receita='50000', fs_legal='14000') for i in range(1,13)],
            saldos_irpj='0', saldos_csll='0', confirmado=True)

    def test_ano_completo_nao_e_multiplicacao_indevida_de_periodos(self):
        result = projetar_ano(**self.entradas())
        self.assertEqual(result['receita_anual'],D('600000'))
        self.assertEqual(result['simples']['anual']['das'],D('43140'))
        self.assertEqual(result['presumido']['anual']['irpj'],D('7200'))
        self.assertEqual(result['presumido']['anual']['csll'],D('6480'))
        self.assertTrue(result['presumido']['trimestral'][3]['resultado']['fechamento_sem_majoracao'])
        self.assertEqual(result['real']['anual']['irpj'],D('18000'))
        self.assertEqual(result['real']['anual']['csll'],D('10800'))

    def test_receita_movel_exclui_proprio_mes(self):
        entradas=self.entradas()
        entradas['meses'][0]['comercio']='100000'
        result=projetar_ano(**entradas)
        self.assertEqual(result['simples']['mensal'][0]['rbt12'],D('600000'))
        self.assertEqual(result['simples']['mensal'][1]['rbt12'],D('650000'))
        self.assertEqual(result['simples']['mensal'][0]['resultado']['das'],D('7190'))

    def test_fs_movel_altera_anexo_no_mes_seguinte(self):
        entradas=self.entradas()
        for x in entradas['meses']: x.update(comercio='0',servicos='50000',fs_legal='0')
        result=projetar_ano(**entradas,servicos_fator_r=True)
        self.assertEqual(result['simples']['mensal'][0]['resultado']['detalhes'][0]['anexo'],'III')
        self.assertEqual(result['simples']['mensal'][1]['resultado']['detalhes'][0]['anexo'],'V')

    def test_prejuizo_trimestral_compensado_apenas_adiante(self):
        entradas=self.entradas()
        for x in entradas['meses'][:3]:x.update(resultado_irpj='-10000',resultado_csll='-10000')
        result=projetar_ano(**entradas)
        linhas=result['real']['trimestral']
        self.assertEqual(linhas[0]['resultado']['irpj'],0)
        self.assertEqual(linhas[0]['saldo_irpj_final'],D('30000'))
        self.assertEqual(linhas[1]['resultado']['bases']['IRPJ']['compensacao'],D('9000'))
        self.assertEqual(linhas[3]['saldo_irpj_final'],D('3000'))

    def test_pendencia_real_impede_saldo_ficticio_nos_trimestres_seguintes(self):
        entradas=self.entradas();entradas['meses'][0]['resultado_irpj']=None
        result=projetar_ano(**entradas)
        self.assertIsNone(result['real']['anual']['irpj'])
        self.assertFalse(result['real']['trimestral'][1]['calculado'])
        self.assertTrue(result['presumido']['anual']['cobertura_completa'])

    def test_majoracao_no_ano_nao_resulta_total_anual_parcial_disfarcado(self):
        entradas=self.entradas()
        for x in entradas['meses']:x['comercio']='600000'
        result=projetar_ano(**entradas)
        self.assertFalse(result['presumido']['anual']['cobertura_completa'])
        self.assertIsNone(result['presumido']['anual']['irpj'])
        self.assertFalse(result['presumido']['trimestral'][3]['calculado'])
        self.assertIsNone(result['simples']['anual']['das'])

    def test_ajustes_mes_aplicados_ao_trimestre_correto(self):
        entradas=self.entradas()
        entradas['ajustes']=[dict(mes=4,descricao='Ajuste documentado',tipo='adicao',tributo='IRPJ',valor='10000',
            fundamento='Norma validada pelo revisor',documento='Doc 1',natureza='permanente')]
        result=projetar_ano(**entradas)
        self.assertEqual(result['real']['trimestral'][0]['resultado']['bases']['IRPJ']['ajustado'],D('30000'))
        self.assertEqual(result['real']['trimestral'][1]['resultado']['bases']['IRPJ']['ajustado'],D('40000'))

    def test_cenario_crescimento_e_queda_de_100_por_cento(self):
        serie=gerar_cenario({'comercio':'1000'},{'comercio':'.1'})
        self.assertEqual(serie[0]['comercio'],D('1000'))
        self.assertEqual(serie[2]['comercio'],D('1210'))
        serie=gerar_cenario({'comercio':'1000'},{'comercio':'-1'})
        self.assertEqual(serie[1]['comercio'],D('0'))
        with self.assertRaises(Pendente):gerar_cenario({'comercio':'1000'},{'comercio':'-1.01'})

    def test_dados_ausentes_ou_meses_duplicados_bloqueiam(self):
        entradas=self.entradas();entradas['historico'][0]['receita']=None
        with self.assertRaises(Pendente):projetar_ano(**entradas)
        entradas=self.entradas();entradas['meses'][0]['mes']=2
        with self.assertRaises(Pendente):projetar_ano(**entradas)

    def test_snapshot_independente_das_entradas_e_estavel(self):
        a=fotografia_regras(2026);b=fotografia_regras(2026)
        self.assertEqual(a['sha256'],b['sha256'])
        a['regras']['tabelas']['I'][0][1]='99'
        self.assertNotEqual(a['regras'],b['regras'])
        self.assertEqual(b['regras']['tabelas']['I'][0][1],'0.04')

    def test_2027_exige_regras_proprias(self):
        with self.assertRaises(Pendente):projetar_ano(**self.entradas(),ano=2027)

    def test_ir_dividendos_anual_aparece_em_todos_os_regimes(self):
        result=projetar_ano(**self.entradas(),distribuicoes=[dict(nome='Sócio 1',tipo='PF_RESIDENTE',origem='2026',valor='60000')])
        self.assertEqual(result['dividendos']['irrf_anual'],D('72000'))
        for regime in ('simples','presumido','real'):
            anual=result[regime]['anual']
            self.assertEqual(anual['irrf_dividendos'],D('72000'))
            self.assertIsNotNone(anual['subtotal_componentes_e_dividendos'])

    def test_memoria_salva_nao_recalculada_e_detecta_snapshot_alterado(self):
        dados=dict(entradas={'premissa':'original'},resultado={'valor':'123.45'},
                   fotografia_normativa=fotografia_regras(2026))
        copia=verificar_memoria(dados)
        self.assertEqual(copia['resultado'],{'valor':'123.45'})
        copia['entradas']['premissa']='nova'
        self.assertEqual(dados['entradas']['premissa'],'original')
        dados['fotografia_normativa']['regras']['atividades']['comercio'][0]='0.99'
        with self.assertRaises(Pendente):verificar_memoria(dados)

    def test_sublimite_ano_anterior_nao_desaparece_com_queda_da_rbt12(self):
        entradas=self.entradas()
        for x in entradas['historico']:x['receita']='400000'
        result=projetar_ano(**entradas)
        self.assertFalse(result['simples']['mensal'][11]['calculado'])
        self.assertIsNone(result['simples']['anual']['das'])


if __name__=='__main__':unittest.main()
