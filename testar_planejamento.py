"""Entrada operacional da plataforma aprovada; banco de demonstração separado."""
import streamlit as st
from plataforma_ui import renderizar

st.set_page_config(page_title='Maxsuel · Planejamento e gestão', layout='wide')
renderizar()
