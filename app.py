"""Entrada principal da plataforma Maxsuel, preservando o sistema original no menu."""
import streamlit as st
from plataforma_ui import renderizar

st.set_page_config(page_title='Maxsuel · Planejamento e gestão', layout='wide')
renderizar()
