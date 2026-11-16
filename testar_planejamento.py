"""Entrada única: prévia visual, sistema original e cálculos em revisão."""
from pathlib import Path
import base64
import runpy
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Maxsuel · Teste do planejamento tributário', layout='wide')
base = Path(__file__).resolve().parent
modo = st.radio('O que você quer ver?', ['Prévia do novo visual', 'Sistema original', 'Cálculos em revisão'],
                horizontal=True, key='modo_apresentacao')

if modo == 'Prévia do novo visual':
    st.caption('PRÉVIA DE NAVEGAÇÃO · experimente os menus e o preenchimento compartilhado. Esta tela ainda não calcula os tributos.')
    fragmento = (base / 'interface' / 'previa_navegacao.html').read_text(encoding='utf-8')
    logo = base / 'Logo - Empresa Max contabil_2.png'
    if logo.exists():
        imagem = base64.b64encode(logo.read_bytes()).decode('ascii')
        origem = 'https://cdn.jsdelivr.net/gh/MaxsuelContabilx/sistema-contabil-simples@2c3319c413d08f6c5d4af5dbe43a667e93f6ee78/Logo%20-%20Empresa%20Max%20contabil_2.png'
        fragmento = fragmento.replace(origem, 'data:image/png;base64,' + imagem)
    pagina = ('<!doctype html><html lang="pt-BR" translate="no"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              '<meta name="google" content="notranslate">'
              '<style>body{margin:0;padding:0;background:transparent}#maxsuel-planejamento-preview{max-width:1250px;margin:0 auto}</style>'
              '<script src="https://cdn.jsdelivr.net/npm/lucide@0.468.0/dist/umd/lucide.min.js"></script>'
              '</head><body>' + fragmento + '<script>if(window.lucide){lucide.createIcons();}</script></body></html>')
    components.html(pagina, height=1320, scrolling=True)
elif modo == 'Sistema original':
    st.caption('SEU SISTEMA ORIGINAL · logo, Simples, salários, férias e contabilidade. Os cálculos originais ainda precisam da revisão tributária. Os lançamentos desta demonstração usam um banco separado.')
    runpy.run_path(str(base / 'sistema_original.py'), run_name='__main__')
else:
    st.caption('CÁLCULOS EM REVISÃO · versão técnica parcial para conferir os componentes já implementados.')
    from planejamento_ui import renderizar
    renderizar()
