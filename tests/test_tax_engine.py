import unittest
from decimal import Decimal as D
from tax_engine import (Ajuste, Pendente, dividendos_mensais, faixa_simples,
                        fator_r, imposto_renda, lucro_real_trimestre,
                        numero, presumido_trimestre, simples_mensal)


class CalculosTributarios(unittest.TestCase):
    def evento(self, valor, **kwargs):
        return dict(data='2026-01-10', fonte='Empresa A', beneficiario='Sócio A',
                    beneficiario_tipo='PF_RESIDENTE', origem_resultado='2026',
                    valor=valor, **kwargs)

    def test_dividendo_limite_e_total(self):
        self.assertEqual(dividendos_mensais([self.evento('50000')])['irrf'], 0)
        self.assertEqual(dividendos_mensais([self.evento('60000')])['irrf'], D('6000'))
        self.assertEqual(dividendos_mensais([self.evento('50000.01')])['irrf'], D('5000.00'))

    def test_dividendos_agregam_eventos_mes(self):
        result = dividendos_mensais([self.evento('30000'), self.evento('30000')])
        self.assertEqual(result['irrf'], D('6000'))
        self.assertEqual(result['detalhes'][0]['liquido'], D('54000'))

    def test_dividendos_separam_fonte_socio_mes(self):
        eventos = [self.evento('40000')]
        for key, value in [('fonte', 'Empresa B'), ('beneficiario', 'Sócio B'), ('data', '2026-02-10')]:
            item = self.evento('40000'); item[key] = value; eventos.append(item)
        self.assertEqual(dividendos_mensais(eventos)['irrf'], 0)

    def test_dividendos_bloqueiam_transicao_e_exterior(self):
        for field, value in [('origem_resultado', '2025'), ('beneficiario_tipo', 'EXTERIOR'), ('data', '2025-01-01')]:
            item = self.evento('60000'); item[field] = value
            with self.assertRaises(Pendente): dividendos_mensais([item])

    def test_anexo_iii_sexta_faixa_regressao_848mil(self):
        result = faixa_simples('4800000', 'III')
        self.assertEqual(result['deducao'], D('648000'))
        self.assertEqual(result['efetiva'], D('.195'))

    def test_limites_simples_e_nao_zerar_excesso(self):
        self.assertEqual(faixa_simples('180000', 'I')['faixa'], 1)
        self.assertEqual(faixa_simples('180000.01', 'I')['faixa'], 2)
        for value in ('0', '4800000.01'):
            with self.assertRaises(Pendente): faixa_simples(value, 'I')

    def test_fator_r_exato_28(self):
        self.assertEqual(fator_r('168000', '600000'), D('.28'))
        resultado = simples_mensal('600000', '168000', [dict(valor='50000', anexo='V',
            sujeita_fator_r=True, tratamento='ordinario')], enquadramento_confirmado=True,
            empresa_madura=True, sublimite_confirmado=True)
        self.assertEqual(resultado['detalhes'][0]['anexo'], 'III')
        self.assertEqual(resultado['das'], D('5280'))

    def test_fator_r_abaixo_28_e_segregacao(self):
        result = simples_mensal('600000', '167999.99', [
            dict(valor='50000', anexo='III', sujeita_fator_r=True, tratamento='ordinario'),
            dict(valor='20000', anexo='I', sujeita_fator_r=False, tratamento='ordinario')],
            enquadramento_confirmado=True, empresa_madura=True, sublimite_confirmado=True)
        self.assertEqual(result['detalhes'][0]['anexo'], 'V')
        # Anexo V: R$ 8.925,00; comércio (I): R$ 1.438,00.
        self.assertEqual(result['das'], D('10363.00'))

    def test_simples_bloqueia_dados_e_tratamentos_pendentes(self):
        with self.assertRaises(Pendente): simples_mensal('600000', None, [])
        with self.assertRaises(Pendente): simples_mensal('3700000', '0', [],
            enquadramento_confirmado=True, empresa_madura=True, sublimite_confirmado=True)
        with self.assertRaises(Pendente): simples_mensal('600000', '0', [
            dict(valor='10', anexo='I', sujeita_fator_r=False, tratamento='monofasico')],
            enquadramento_confirmado=True, empresa_madura=True, sublimite_confirmado=True)

    def presumido(self, trimestre, receitas=None):
        return presumido_trimestre(receitas or [dict(atividade='comercio', valor='1500000')],
            trimestre=trimestre, limite_irpj_confirmado='1250000',
            limite_csll_confirmado='1250000', fundamento_limite='LC 224, art. 4º; limite trimestral sem ajustes',
            acrescimos_irpj='0', acrescimos_csll='0', enquadramento_confirmado=True)

    def test_presumido_primeiro_trimestre_nao_majora_csll(self):
        result = self.presumido(1)
        self.assertEqual(result['base_irpj'], D('122000'))
        self.assertEqual(result['base_csll'], D('180000'))
        self.assertEqual(result['irpj'], D('24500'))
        self.assertEqual(result['csll'], D('16200'))

    def test_presumido_segundo_trimestre_csll_e_proporcao(self):
        result = self.presumido(2, [dict(atividade='comercio', valor='1000000'),
                                    dict(atividade='servicos_gerais', valor='500000')])
        self.assertEqual(result['base_irpj'], D('244000'))
        self.assertEqual(result['base_csll'], D('284666.67'))
        self.assertEqual(result['csll'], D('25620'))

    def test_presumido_sem_aumento_abaixo_limite(self):
        result = self.presumido(2, [dict(atividade='servicos_gerais', valor='150000')])
        self.assertEqual(result['base_irpj'], D('48000'))
        self.assertEqual(result['irpj_adicional'], 0)

    def test_presumido_ajuste_anual_nao_inventado(self):
        with self.assertRaises(Pendente): self.presumido(4)
        with self.assertRaises(Pendente): presumido_trimestre([])

    def test_real_exemplo_material_fornecido_slides_94_95(self):
        ajustes = [Ajuste('Custos não dedutíveis', 'adicao', t, '100000', 'Exemplo didático, validar classificação real', 'slide 94', 'permanente') for t in ('IRPJ', 'CSLL')]
        ajustes += [Ajuste('Exclusões do exemplo', 'exclusao', 'IRPJ', '10000', 'Exemplo didático', 'slide 94', 'temporaria'),
                    Ajuste('Exclusões do exemplo', 'exclusao', 'CSLL', '15000', 'Exemplo didático', 'slide 94', 'temporaria')]
        result = lucro_real_trimestre('-20000', '-20000', ajustes,
            prejuizo_fiscal='10000', base_negativa_csll='5000', regra_geral_confirmada=True)
        self.assertEqual(result['bases']['IRPJ']['base_tributavel'], D('60000'))
        self.assertEqual(result['bases']['CSLL']['base_tributavel'], D('60000'))
        self.assertEqual(result['irpj'], D('9000'))
        self.assertEqual(result['csll'], D('5400'))

    def test_real_trava_independente_e_saldos(self):
        result = lucro_real_trimestre('100000', '200000', [],
            prejuizo_fiscal='80000', base_negativa_csll='20000', regra_geral_confirmada=True)
        self.assertEqual(result['bases']['IRPJ']['compensacao'], D('30000'))
        self.assertEqual(result['bases']['IRPJ']['saldo_anterior_remanescente'], D('50000'))
        self.assertEqual(result['bases']['CSLL']['base_tributavel'], D('180000'))

    def test_real_perda_nao_consumir_saldo(self):
        result = lucro_real_trimestre('-10000', '-5000', [], prejuizo_fiscal='1000',
            base_negativa_csll='2000', regra_geral_confirmada=True)
        self.assertEqual(result['irpj'], 0)
        self.assertEqual(result['csll'], 0)
        self.assertEqual(result['bases']['IRPJ']['saldo_anterior_remanescente'], D('1000'))
        self.assertEqual(result['bases']['IRPJ']['perda_do_periodo'], D('10000'))

    def test_ajuste_sem_fundamento_nao_calculado(self):
        with self.assertRaises(Pendente): lucro_real_trimestre('1000', '1000',
            [Ajuste('Despesa', 'adicao', 'IRPJ', '10', '', 'nota', 'permanente')],
            prejuizo_fiscal='0', base_negativa_csll='0', regra_geral_confirmada=True)

    def test_adicional_respeita_trimestre(self):
        self.assertEqual(imposto_renda('60000'), (D('9000'), D('0')))
        self.assertEqual(imposto_renda('90000'), (D('13500'), D('3000')))
        # Receita sazonal não pode ser reduzida a uma média mensal.
        self.assertNotEqual(imposto_renda('90000')[1], imposto_renda('90000', meses=1)[1])

    def test_nao_extrapolar_2027(self):
        with self.assertRaises(Pendente): faixa_simples('100000', 'I', 2027)
        with self.assertRaises(Pendente): dividendos_mensais([], ano=2027)

    def test_nao_converter_ausencia_nan_infinito_em_zero(self):
        for value in (None, True, '-1', 'NaN', 'Infinity', 'abc'):
            with self.assertRaises(Pendente): numero(value)


if __name__ == '__main__':
    unittest.main()
