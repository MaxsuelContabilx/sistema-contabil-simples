import unittest

from tax_engine import (
    ParametrosSimulacao,
    calcular_irrf_dividendos_2026,
    calcular_lucro_presumido,
    calcular_lucro_real,
    calcular_simples_nacional,
    calcular_tributos_consumo_transicao,
    executar_simulacao_completa,
    validar_premissas,
)


class TestTaxEngineLegal(unittest.TestCase):
    def test_simples_anexo_iii_faixa6_corrigida(self):
        # LC 123/2006 Anexo III Faixa 6: Aliq 33%, PD = 648.000,00 (corrigido de 848.000)
        p = ParametrosSimulacao(
            faturamento_mes=350000.0,
            rbt12=4200000.0,
            anexo_simples="Anexo III - Serviços (Fator R >= 28% / Locação / Contabilidade)",
            sujeito_fator_r=False,
        )
        res = calcular_simples_nacional(p)
        aliq_esperada = ((4200000.0 * 0.33) - 648000.0) / 4200000.0 * 100.0
        self.assertAlmostEqual(res["aliquota_efetiva_das_pct"], aliq_esperada, places=4)
        self.assertEqual(res["parcela_deduzir"], 648000.0)

    def test_fator_r_anexo_iii_vs_v(self):
        # Fator R >= 28% migra para Anexo III; < 28% fica no Anexo V
        p_baixo = ParametrosSimulacao(
            faturamento_mes=50000.0,
            rbt12=600000.0,
            anexo_simples="Anexo V - Serviços (Fator R < 28% / Engenharia, TI, Consultoria)",
            sujeito_fator_r=True,
            folha_encargos_12m=120000.0,  # 20%
        )
        res_baixo = calcular_simples_nacional(p_baixo)
        self.assertIn("Anexo V", res_baixo["anexo_efetivo"])

        p_alto = ParametrosSimulacao(
            faturamento_mes=50000.0,
            rbt12=600000.0,
            anexo_simples="Anexo V - Serviços (Fator R < 28% / Engenharia, TI, Consultoria)",
            sujeito_fator_r=True,
            folha_encargos_12m=168000.0,  # 28% exato
        )
        res_alto = calcular_simples_nacional(p_alto)
        self.assertIn("Anexo III", res_alto["anexo_efetivo"])

    def test_anexo_iv_cpp_por_fora(self):
        p = ParametrosSimulacao(
            faturamento_mes=50000.0,
            rbt12=300000.0,
            anexo_simples="Anexo IV - Serviços (Obras, Limpeza, Vigilância, Advocacia - CPP por fora)",
            sujeito_fator_r=False,
            folha_salarios_mes=10000.0,
            rat_fap_pct=0.02,
            terceiros_pct=0.058,
        )
        res = calcular_simples_nacional(p)
        self.assertAlmostEqual(res["cpp_fora"], 10000.0 * 0.278, places=2)

    def test_lucro_presumido_lc224_apenas_excedente(self):
        # Exemplo conceitual da LC 224/2025: receita trimestral 3M -> mensal eq. 1M
        # Limite anual R$ 5M => mensal eq. 416.666,67 a 32% e 583.333,33 a 35,2%
        p = ParametrosSimulacao(
            faturamento_mes=1_000_000.0,
            rbt12=12_000_000.0,
            atividade_presumido="Serviços em Geral / Profissões Regulamentadas / Intermediação",
            faturamento_acumulado_ano_anterior_ou_atual=12_000_000.0,
        )
        res = calcular_lucro_presumido(p)
        limite_mensal = 5_000_000.0 / 12.0
        base_esperada = (limite_mensal * 0.32) + ((1_000_000.0 - limite_mensal) * 0.352)
        self.assertAlmostEqual(res["base_irpj"], base_esperada, places=2)
        self.assertAlmostEqual(res["parcela_normal"], limite_mensal, places=2)

    def test_lucro_presumido_abaixo_5m_sem_majoracao(self):
        p = ParametrosSimulacao(
            faturamento_mes=200_000.0,
            rbt12=2_400_000.0,
            atividade_presumido="Comércio / Indústria / Hospitalar / Transporte de Cargas",
            faturamento_acumulado_ano_anterior_ou_atual=2_400_000.0,
        )
        res = calcular_lucro_presumido(p)
        self.assertEqual(res["parcela_majorada_lc224"], 0.0)
        self.assertAlmostEqual(res["base_irpj"], 200_000.0 * 0.08, places=2)
        self.assertAlmostEqual(res["base_csll"], 200_000.0 * 0.12, places=2)

    def test_lucro_real_lalur_trava_30_e_lc224(self):
        p = ParametrosSimulacao(
            faturamento_mes=200_000.0,
            rbt12=2_400_000.0,
            cmv_csp_mes=50_000.0,
            despesas_op_dedutiveis_mes=30_000.0,
            insumos_com_credito_mes=50_000.0,
            folha_salarios_mes=10_000.0,
            rat_fap_pct=0.02,
            terceiros_pct=0.058,
            adicoes_mes=10_000.0,
            exclusoes_mes=5_000.0,
            prejuizo_fiscal_acumulado=100_000.0,
            incentivos_fiscais_irpj_mes=1_000.0,
            ano_referencia=2026,
        )
        res = calcular_lucro_real(p)
        # Compensação deve ser exatamente 30% do lucro real antes da compensação
        self.assertAlmostEqual(res["compensacao_prejuizo_irpj"], res["lucro_real_antes_comp"] * 0.30, places=2)
        # Incentivo limitado a 3,6% do IRPJ normal (LC 224/2025)
        self.assertAlmostEqual(res["incentivo_aplicado_lc224"], min(1_000.0, res["irpj_normal"] * 0.036), places=2)

    def test_transicao_2026_dispensado_vs_2027_e_2033(self):
        c2026 = calcular_tributos_consumo_transicao(100000.0, 20000.0, 2026, "Presumido", 0.05, 0.088, 0.177, 0.0)
        self.assertTrue(c2026["dispensado_2026"])
        self.assertEqual(c2026["cbs"], 0.0)
        self.assertEqual(c2026["ibs"], 0.0)
        self.assertAlmostEqual(c2026["pis_cofins"], 3650.0, places=2)

        c2027 = calcular_tributos_consumo_transicao(100000.0, 20000.0, 2027, "Real", 0.05, 0.088, 0.177, 0.0)
        self.assertEqual(c2027["pis_cofins"], 0.0)
        self.assertAlmostEqual(c2027["cbs"], 80000.0 * 0.088, places=2)
        self.assertAlmostEqual(c2027["ibs"], 80000.0 * 0.001, places=2)

        c2033 = calcular_tributos_consumo_transicao(100000.0, 20000.0, 2033, "Real", 0.05, 0.088, 0.177, 0.0)
        self.assertEqual(c2033["icms_iss"], 0.0)
        self.assertAlmostEqual(c2033["ibs"], 80000.0 * 0.177, places=2)

    def test_dividendos_lei_15270_efeito_degrau(self):
        d50 = calcular_irrf_dividendos_2026(50000.0, "Pessoa Física Residente")
        self.assertEqual(d50["irrf"], 0.0)

        d50_01 = calcular_irrf_dividendos_2026(50000.01, "Pessoa Física Residente")
        self.assertAlmostEqual(d50_01["irrf"], 5000.001, places=3)  # 10% sobre o TOTAL

        dpj = calcular_irrf_dividendos_2026(200000.0, "Pessoa Jurídica")
        self.assertEqual(dpj["irrf"], 0.0)

    def test_validador_premissas_sinaliza_folha_ausente(self):
        p = ParametrosSimulacao(faturamento_mes=50000.0, rbt12=600000.0, sujeito_fator_r=True, folha_encargos_12m=None)
        alertas = validar_premissas(p)
        titulos = [a["titulo"] for a in alertas]
        self.assertTrue(any("Fator R" in t for t in titulos))

    def test_simulacao_completa_executa(self):
        p = ParametrosSimulacao(faturamento_mes=80000.0, rbt12=960000.0, folha_encargos_12m=300000.0)
        res = executar_simulacao_completa(p)
        self.assertIn(res["regime_vencedor"], ("Simples Nacional", "Lucro Presumido", "Lucro Real"))
        self.assertEqual(len(res["dre_comparativa"]), 3)


if __name__ == "__main__":
    unittest.main()
