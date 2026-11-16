"""Mostra os percentuais e a base efetivamente usados pelo motor do Presumido."""
from decimal import Decimal as D
import pandas as pd
import streamlit as st
from texto_ui import legenda
from tax_engine import ATIVIDADES


def mostrar_presuncao(item,p):
    from plataforma_ui import dinheiro
    nomes={'comercio':'Comércio','industria':'Indústria','servicos_gerais':'Serviços gerais'}
    memoria=item.get('memoria',{});detalhes=memoria.get('detalhes',[])
    st.markdown('##### Presunção do Lucro Presumido')
    if detalhes:
        linhas=[]
        for d in detalhes:
            if not d['receita']:continue
            linhas.append({'Atividade':nomes.get(d['atividade'],d['atividade']),
                'Receita trimestral':dinheiro(d['receita']),
                'Presunção IRPJ':f"{d['presuncao_irpj']*100:g}%".replace('.',','),
                'Presunção CSLL':f"{d['presuncao_csll']*100:g}%".replace('.',','),
                'Receita com majoração IRPJ':dinheiro(d['receita_majorada_irpj']),
                'Receita com majoração CSLL':dinheiro(d['receita_majorada_csll']),
                'Base IRPJ':dinheiro(d['base_irpj']),'Base CSLL':dinheiro(d['base_csll'])})
        st.dataframe(pd.DataFrame(linhas),hide_index=True,width='stretch')
        legenda('Base trimestral total do IRPJ: '+dinheiro(memoria['base_irpj'])+' · CSLL: '+dinheiro(memoria['base_csll']))
        legenda('IRPJ de 15%: '+dinheiro(memoria['irpj_normal'])+' · adicional de 10%: '+dinheiro(memoria['irpj_adicional'])+' · CSLL de 9%: '+dinheiro(memoria['csll']))
    else:
        for k,atividade in [('comercio','comercio'),('industria','industria'),('servicos','servicos_gerais')]:
            if p.get(k,0):
                pi,pc=ATIVIDADES[atividade];st.write(f"{nomes[atividade]}: presunção IRPJ {pi*100:g}% · CSLL {pc*100:g}% (percentuais básicos).")
        legenda('Base efetiva do período pendente: veja os dados ou regras ainda necessários no cartão. Os percentuais básicos acima não representam uma apuração concluída.')
    legenda('Majoração da presunção: acréscimo de 10% relativo ao percentual básico somente sobre a parcela sujeita à regra da LC 224/2025, conforme limites e vigência do motor. Não é alíquota adicional de 10 pontos percentuais. Serviços específicos podem ter enquadramento diferente.')
