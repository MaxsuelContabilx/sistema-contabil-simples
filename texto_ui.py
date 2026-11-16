"""Evita que dois valores em reais sejam interpretados como fórmula LaTeX."""
import streamlit as st


def legenda(texto):
    st.caption(str(texto).replace('$',r'\$'))
