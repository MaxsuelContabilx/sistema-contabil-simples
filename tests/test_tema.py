"""Alternar a aparência mantém o cenário e a navegação da sessão."""
import importlib.util
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit não instalado')
class Tema(unittest.TestCase):
    def test_alternar_tema_preserva_cenario_e_navegacao(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
        app.number_input(key='sc_receita').set_value(65000.0).run()
        app.toggle(key='sc_dark').set_value(True).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.number_input(key='sc_receita').value, 65000.0)
        app.radio(key='menu_principal').set_value('Equipe e salários').run()
        self.assertTrue(app.toggle(key='sc_dark').value)
        app.radio(key='menu_principal').set_value('Planejamento').run()
        app.toggle(key='sc_dark').set_value(False).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.number_input(key='sc_receita').value, 65000.0)


if __name__ == '__main__':
    unittest.main()
