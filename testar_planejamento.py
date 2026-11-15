"""Entrada isolada para testar as simulações sem abrir o banco contábil."""
import streamlit as st
from planejamento_ui import renderizar

st.set_page_config(page_title='Maxsuel · Teste do planejamento tributário', layout='wide')
st.warning('AMBIENTE DE TESTES · versão parcial em revisão. Não usar como apuração fiscal definitiva.')
renderizar()
