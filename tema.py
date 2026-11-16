"""Tema por sessão: não altera opções globais nem os documentos de impressão."""
import streamlit as st


def aplicar_tema():
    st.sidebar.toggle('Modo escuro', key='sc_dark',
        help='Alterne entre o tema claro e o escuro sem perder os dados deste cenário.')
    escuro = st.session_state.sc_dark
    fundo, painel, campo, texto, suave, borda, destaque = (
        ('#101820', '#182630', '#21333f', '#eef4f7', '#b5c5cf', '#405563', '#dec68d')
        if escuro else
        ('#f4f5f7', '#ffffff', '#ffffff', '#16303a', '#526875', '#dbe3e7', '#16303a'))
    st.markdown(f'''<style>
    @media screen {{
      .stApp, [data-testid="stAppViewContainer"] {{background:{fundo}!important;color:{texto}!important}}
      [data-testid="stHeader"] {{background:{fundo}!important;color:{texto}!important}}
      [data-testid="stSidebar"] {{background:{painel}!important;color:{texto}!important;border-right:1px solid {borda}}}
      .block-container {{max-width:1250px;padding-top:2rem}}
      .stApp h1 {{font-size:1.9rem!important}}
      .stApp h1,.stApp h2,.stApp h3,.stApp h4,
      [data-testid="stWidgetLabel"], [data-testid="stMetricLabel"],
      [data-testid="stMetricValue"], [data-testid="stRadio"] label,
      [data-testid="stCheckbox"] label {{color:{texto}!important}}
      [data-testid="stCaptionContainer"] {{color:{suave}!important}}
      [data-testid="stCaptionContainer"] p {{color:{suave}!important}}
      [data-testid="stMetric"] {{padding:8px 0}}
      [data-testid="stMetricValue"] {{font-size:1.45rem}}
      [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stVerticalBlockBorderWrapper"]>div,
      [data-testid="stForm"], [data-testid="stExpander"] {{border-color:{borda}!important;border-radius:12px}}
      [data-testid="stForm"], [data-testid="stExpander"] {{background:{painel}!important}}
      [data-testid="stExpander"] summary {{color:{texto}!important}}
      .stApp input:not([type="checkbox"]):not([type="radio"]),.stApp textarea,
      [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"]>div,
      [data-testid="stNumberInputContainer"], [data-testid="stDateInput"]>div,
      [data-testid="stFileUploaderDropzone"] {{background:{campo}!important;color:{texto}!important;border-color:{borda}!important}}
      .stApp input::placeholder,.stApp textarea::placeholder {{color:{suave}!important}}
      [data-baseweb="popover"], [data-baseweb="popover"] ul,
      [data-baseweb="menu"], [role="listbox"], [role="option"] {{background:{painel}!important;color:{texto}!important}}
      [role="option"]:hover, [role="option"][aria-selected="true"] {{background:{campo}!important}}
      [data-testid="stNumberInput"] button, [data-testid="stSelectbox"] button {{background:{campo}!important;color:{texto}!important}}
      .stApp button {{border-radius:7px!important}}
      .stApp button[kind="secondary"], .stApp button[kind="tertiary"] {{background:{painel}!important;color:{texto}!important;border-color:{borda}!important}}
      .stApp button[kind="primary"] {{background:{destaque}!important;border-color:{destaque}!important;color:{fundo if escuro else '#ffffff'}!important}}
      .stApp button[kind="primary"] p {{color:{fundo if escuro else '#ffffff'}!important}}
      .stApp button:focus-visible, .stApp input:focus-visible {{outline:2px solid {destaque}!important;outline-offset:2px}}
      [data-testid="stTabs"] button {{color:{texto}!important}}
      [data-testid="stTabs"] button[aria-selected="true"] {{color:{destaque}!important}}
      [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] {{border:1px solid {borda};border-radius:8px;overflow:hidden}}
      [data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td {{background:{painel}!important;color:{texto}!important;border-color:{borda}!important}}
    }}
    </style>''', unsafe_allow_html=True)
    if escuro:
        st.markdown('''<style>@media screen {
          [data-testid="stMarkdownContainer"] {color:#eef4f7}
          [data-testid="stMarkdownContainer"] a {color:#dec68d!important}
          [data-testid="stMarkdownContainer"] code {background:#21333f;color:#f1d99e}
          [data-testid="stMarkdownContainer"] div[style*="background"] {background:#182630!important;border-color:#405563!important}
          [data-testid="stMarkdownContainer"] [style*="color"] {color:#eef4f7!important}
          [data-testid="stSidebar"] h2 {color:#eef4f7!important}
          [data-testid="stAlert"] {background:#21333f;color:#eef4f7}
          [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {color:#eef4f7}
          [data-testid="stFileUploaderDropzone"] small {color:#b5c5cf!important}
        }</style>''', unsafe_allow_html=True)
