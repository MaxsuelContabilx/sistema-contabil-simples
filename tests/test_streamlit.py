"""Verificação dos fluxos reais da interface, sem abrir navegador."""
import importlib.util
import logging
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit não instalado')
class Interface(unittest.TestCase):
    def test_botao_de_ferias_abre_recibo_com_salario_compartilhado(self):
        from streamlit.testing.v1 import AppTest
        logging.disable(logging.CRITICAL)
        try:
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
            app.radio(key='menu_principal').set_value('Equipe e salários').run()
            app.number_input(key='salario_equipe').set_value(4000.0).run()
            next(x for x in app.button if x.label=='Abrir simulador de férias e adiantamentos').click().run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(app.checkbox(key='calcular_ferias_legado').value)
            self.assertTrue(any('Demonstrativo de Recibo de Férias' in x.value for x in app.subheader))
            bruto=next(x for x in app.number_input if 'Salário Bruto do empregado' in x.label)
            self.assertEqual(bruto.value,4000.0)
        finally:logging.disable(logging.NOTSET)

    def test_cenario_persistente_e_dividendos_nas_tres_alternativas(self):
        from streamlit.testing.v1 import AppTest
        logging.disable(logging.CRITICAL)
        try:
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
            app.number_input(key='sc_receita').set_value(65000.0)
            app.number_input(key='sc_dividendo').set_value(60000.0)
            app.selectbox(key='sc_tipo_div').set_value('PF residente no Brasil')
            app.button(key='comparar_cenario').click().run()
            self.assertEqual(len(app.exception),0)
            valores=[x.value for x in app.metric if x.label=='IR sobre dividendos']
            self.assertEqual(valores,['R$ 6.000,00']*3)
            app.radio(key='menu_principal').set_value('Simples Nacional').run()
            self.assertEqual(len(app.exception),0)
            app.radio(key='menu_principal').set_value('Planejamento').run()
            self.assertEqual(app.number_input(key='sc_receita').value,65000.0)
            self.assertEqual(app.number_input(key='sc_dividendo').value,60000.0)
        finally:logging.disable(logging.NOTSET)

    def test_acesso_ao_original_preserva_simulador_de_salario(self):
        from streamlit.testing.v1 import AppTest
        logging.disable(logging.CRITICAL)
        try:
            base=Path(__file__).resolve().parents[1]
            banco=base/'maxsuel_contabilidade.db'
            antes=banco.read_bytes() if banco.exists() else None
            app=AppTest.from_file(str(base/'testar_planejamento.py'),default_timeout=30).run()
            app.radio(key='menu_principal').set_value('Ferramentas originais').run()
            self.assertEqual(len(app.exception),0)
            app.radio(key='nav_radio').set_value('📋 Módulo de Folha & Fator R').run()
            operacao=next(x for x in app.radio if x.label=='Escolha a Operação:')
            operacao.set_value('🧮 Simulador Prático de Salário Líquido (2026)').run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(any('Demonstrativo de Pagamento Mensal Emitido' in x.value for x in app.subheader))
            self.assertTrue(any('Salário Bruto do empregado' in x.label for x in app.number_input))
            self.assertEqual(banco.read_bytes() if banco.exists() else None,antes)
        finally:
            logging.disable(logging.NOTSET)

    def test_entrada_isolada_nao_abre_banco_contabil(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        import sqlite3
        real_connect=sqlite3.connect
        logging.disable(logging.CRITICAL)
        try:
            def somente_demo(caminho,*args,**kwargs):
                self.assertFalse(str(caminho).endswith('maxsuel_contabilidade.db'))
                return real_connect(caminho,*args,**kwargs)
            with patch('sqlite3.connect', side_effect=somente_demo):
                app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'testar_planejamento.py'),default_timeout=30).run()
                self.assertEqual(len(app.exception),0)
                self.assertEqual(app.radio(key='menu_principal').value, 'Planejamento')
                self.assertTrue(any('Vamos planejar sua empresa?' in x.value for x in app.title))
        finally:
            logging.disable(logging.NOTSET)

    def test_navegacao_e_calculos_com_memoria(self):
        from streamlit.testing.v1 import AppTest
        logging.disable(logging.CRITICAL)
        try:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            app.radio(key='menu_principal').set_value('Ferramentas técnicas').run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.button), 5)
            # Faturamento mensal ordinário de R$ 50 mil no Anexo I.
            app.session_state['receitas_sn'] = {
                'edited_rows': {0: {'valor': 50000.0}}, 'added_rows': [], 'deleted_rows': []}
            app.checkbox[0].check()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual([(x.label, x.value) for x in app.metric], [('DAS', 'R$ 3.595,00')])
            self.assertTrue(len(app.json))
            # Retenção sobre todo o dividendo, com fonte e beneficiário identificados.
            app.session_state['eventos_div'] = {
                'edited_rows': {0: {'fonte': 'Empresa A', 'beneficiario': 'Sócio A', 'valor': 60000.0}},
                'added_rows': [], 'deleted_rows': []}
            app.button[3].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual([(x.label, x.value) for x in app.metric], [('IRRF', 'R$ 6.000,00')])
            # Bases e saldos independentes; trava do IRPJ diferente da CSLL.
            valores = {
                'Resultado contábil de partida conciliado para IRPJ': '100000',
                'Resultado contábil de partida conciliado para CSLL': '200000',
                'Prejuízo fiscal apto': '80000', 'Base negativa de CSLL apta': '20000'}
            for widget in app.text_input:
                for prefixo, valor in valores.items():
                    if widget.label.startswith(prefixo):
                        widget.input(valor)
            app.checkbox[2].check()
            app.button[2].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual([(x.label, x.value) for x in app.metric],
                             [('IRPJ', 'R$ 11.500,00'), ('CSLL', 'R$ 16.200,00')])
            # Formulário do Presumido não transforma limites vazios em zero.
            app.button[1].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(len(app.error))
            self.assertEqual(len(app.metric), 0)
        finally:
            logging.disable(logging.NOTSET)

    def test_projecao_anual_e_bloqueio_2027(self):
        from streamlit.testing.v1 import AppTest
        logging.disable(logging.CRITICAL)
        try:
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
            app.radio(key='menu_principal').set_value('Ferramentas técnicas').run()
            for widget in app.number_input:
                if widget.label=='Receita de comércio no 1º mês (R$)':widget.set_value(50000.0)
            app.button[4].click().run()
            self.assertEqual(len(app.exception),0)
            app.session_state['historico_projecao']={'edited_rows':{
                i:{'receita':50000.0,'fs_legal':0.0} for i in range(12)},'added_rows':[],'deleted_rows':[]}
            app.session_state['grade_projecao_1']={'edited_rows':{i:{
                'resultado_irpj':10000.0,'resultado_csll':10000.0,'acrescimos_irpj':0.0,'acrescimos_csll':0.0}
                for i in range(12)},'added_rows':[],'deleted_rows':[]}
            for widget in app.text_input:
                if widget.key in ('proj_saldo_ir','proj_saldo_cs'):widget.set_value('0')
            app.checkbox(key='proj_confirmado').check()
            app.button[5].click().run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(len(app.error),0)
            tabela=next(x.value for x in app.dataframe if 'Total anual dos componentes (R$)' in x.value.columns)
            self.assertEqual(tabela['Total anual dos componentes (R$)'].tolist(),[43140.0,13680.0,28800.0])
            app.selectbox(key='projecao_ano').set_value(2027).run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(any('Não há conjunto de regras' in x.value for x in app.warning))
        finally:
            logging.disable(logging.NOTSET)
