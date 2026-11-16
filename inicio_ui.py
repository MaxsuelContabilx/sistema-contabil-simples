"""Histórico opcional do início de atividade; não inventa receitas passadas."""
import pandas as pd
import streamlit as st
from texto_ui import legenda
from tax_engine import Pendente
from simples_inicio import idade_meses,referencia_inicio


def periodo_do_cenario():
    s=st.session_state
    if s.sc_situacao=='Vai começar agora':return 1
    if not s.sc_inicio_sn:return None
    return idade_meses(s.sc_data_abertura,s.sc_ano,s.sc_mes) if s.sc_data_abertura.strip() else int(s.sc_mes_atividade)


def controles_inicio():
    s=st.session_state
    with st.expander('Simples Nacional · primeiros meses e histórico'):
        legenda('Até 2026: primeiro mês × 12; do 2º ao 12º, média dos meses anteriores × 12. A Resolução 190/2026 muda o critério a partir de 01/01/2027.')
        if s.sc_situacao!='Vai começar agora':
            st.checkbox('Empresa ainda nos primeiros meses de atividade',key='sc_inicio_sn')
            if s.sc_inicio_sn:
                st.text_input('Data de abertura no CNPJ · AAAA-MM-DD (opcional)',key='sc_data_abertura')
                if not s.sc_data_abertura.strip():st.number_input('Qual é o mês de atividade desde a abertura?',min_value=2,max_value=120,step=1,key='sc_mes_atividade')
        try:n=periodo_do_cenario()
        except Pendente as exc:st.warning(str(exc));return
        if n is None:return
        legenda(f'{n}º mês de atividade desde o CNPJ. Meses sem faturamento também entram na contagem e na média.')
        ano=int(s.sc_ano)
        fim=n-(2 if ano==2027 else 1)
        necessarios=list(range(max(1,fim-11),fim+1)) if n>(2 if ano==2027 else 1) else []
        if necessarios:
            salvos={int(x['mes_atividade']):x for x in s.sc_historico_inicio}
            dados=[dict(mes_atividade=m,receita=salvos.get(m,{}).get('receita'),folha=salvos.get(m,{}).get('folha')) for m in necessarios]
            df=st.data_editor(pd.DataFrame(dados).astype({'receita':'float64','folha':'float64'}),hide_index=True,num_rows='fixed',disabled=['mes_atividade'],key=f'historico_inicio_{ano}_{n}',column_config={
                'mes_atividade':'Mês desde a abertura',
                'receita':st.column_config.NumberColumn('Receita total do mês (R$)',min_value=0.0,format='%.2f'),
                'folha':st.column_config.NumberColumn('Folha legal do mês (R$) · se fator R',min_value=0.0,format='%.2f')})
            # Mantém meses não utilizados, mas não preenche os ausentes como zero.
            for linha in df.to_dict('records'):salvos[linha['mes_atividade']]=linha
            s.sc_historico_inicio=[salvos[k] for k in sorted(salvos)]
        exibir_memoria_temporal()


def exibir_memoria_temporal():
    from plataforma_ui import dinheiro,perfil
    s=st.session_state
    try:
        n=periodo_do_cenario()
        if n is None:return
        p=perfil()
        r=referencia_inicio(p['ano'],n,sum(p[k] for k in ('comercio','industria','servicos')),
            p['salarios']+p['prolabore']+p['encargos_fs'],p.get('historico_inicio'),sujeito_fator=p['fator_r'])
        st.write(r['regra'])
        st.write('Faixa aplicável: primeira faixa dos anexos.' if r['primeira_faixa'] else 'RBT12 para a alíquota: '+dinheiro(r['rbt12_proporcional']))
        if r['meses_utilizados']:legenda('Meses de atividade usados: '+', '.join(map(str,r['meses_utilizados'])))
        if r['fator_r'] is not None:legenda('Fator R: '+f"{r['fator_r']*100:.2f}%".replace('.',','))
        legenda(r['fundamento'])
        if p['ano']==2027:legenda('Regra temporal de 2027 implementada. O DAS e a comparação global de 2027 aguardam as demais tabelas e regras do período; não se repete a tabela de 2026.')
    except Pendente as exc:st.warning('Simples: '+str(exc))
