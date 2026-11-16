"""Resumo executivo e memória técnica estruturados, iguais em HTML e PDF."""
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path
from io import BytesIO
import base64

NAVY='#16303a';GOLD='#b49c7e';PALE='#edf2f4'


def dinheiro(v):
    if v is None:return 'Não apurado'
    return f'R$ {v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')


def dados(painel):
    r=painel['resultado'];p=painel['cenario'];d=painel['destaque']
    criterio='Maior líquido para os sócios' if d['criterio']=='liquido' else 'Menor total de tributos'
    vencedor=' / '.join(d.get('regimes',[])) if d.get('disponivel') else 'Aguardando dados'
    status='Destaque provisório' if d.get('provisorio') else 'Melhor resultado nos critérios informados'
    if not d.get('disponivel'):status='Comparação incompleta'
    comparacao=[];pend=[]
    for i in r['resultados']:
        e=i.get('enquadramento',{});rotulo=e.get('titulo') or ('Condicional' if i.get('calculo_condicional') else 'Calculado no recorte')
        comparacao.append([i['regime'],rotulo,dinheiro(i['tributos_empresa']),dinheiro(i['ir_dividendos']),dinheiro(i['total_consolidado']),dinheiro(i.get('liquido_total_socios'))])
        avisos=[e.get('motivo'),e.get('nota')]+i.get('itens_pendentes',[])
        if i.get('liquido_total_socios') is None:avisos+=i.get('pendencias',[])
        pend += [i['regime']+': '+n for n in avisos if n]
    pend=list(dict.fromkeys(pend))
    return dict(r=r,p=p,d=d,criterio=criterio,vencedor=vencedor,status=status,tabela=comparacao,pendencias=pend,
        emitido=datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M'),
        periodo=f"{p['mes']:02d}/{p['ano']}",modelo='Referência atual' if r['modelo']=='atual' else 'Projeção da reforma')


def gerar_pdf(titulo,painel,*,logo=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
    from reportlab.graphics.shapes import Drawing,Rect,String
    v=dados(painel);p=v['p'];r=v['r'];d=v['d'];buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=landscape(A4),leftMargin=32,rightMargin=32,topMargin=26,bottomMargin=34)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
    fonts=Path(reportlab.__file__).parent/'fonts'
    if 'MaxsuelRegular' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('MaxsuelRegular',str(fonts/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('MaxsuelBold',str(fonts/'VeraBd.ttf')))
    styles=getSampleStyleSheet()
    for style in styles.byName.values():style.fontName='MaxsuelRegular'
    styles['Heading2'].fontName='MaxsuelBold'
    styles.add(ParagraphStyle(name='ResumoMax',fontName='MaxsuelBold',fontSize=18,leading=23,textColor=colors.HexColor(NAVY)))
    styles.add(ParagraphStyle(name='CorpoMax',fontName='MaxsuelRegular',fontSize=9,leading=12,textColor=colors.HexColor(NAVY)))
    styles.add(ParagraphStyle(name='PequenoMax',fontName='MaxsuelRegular',fontSize=8,leading=10,textColor=colors.HexColor(NAVY)))
    styles.add(ParagraphStyle(name='TituloMax',fontName='MaxsuelBold',fontSize=21,leading=25,textColor=colors.HexColor(NAVY),spaceAfter=7))
    def par(t,style='CorpoMax'):return Paragraph(escape(str(t)),styles[style])
    def tabela(linhas,larguras=None,cab=True):
        t=Table([[c if isinstance(c,Paragraph) else par(c,'PequenoMax') for c in row] for row in linhas],colWidths=larguras,repeatRows=1 if cab else 0,hAlign='LEFT')
        regras=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#dbe3e7'))]
        if cab:regras += [('BACKGROUND',(0,0),(-1,0),colors.HexColor(PALE))]
        t.setStyle(TableStyle(regras));return t
    story=[]
    img=Image(str(logo),width=62,height=62) if logo and Path(logo).exists() else par('MAXSUEL')
    story.append(Table([[img,par('Planejamento tributário','TituloMax'),par(v['modelo']+' · '+v['periodo']+'\nEmitido em '+v['emitido'])]],colWidths=[82,doc.width-260,178]))
    story += [par(p['empresa']),Spacer(1,12)]
    resumo=tabela([[v['status'].upper(),v['criterio']],[par(v['vencedor'],'ResumoMax'),par(dinheiro(d.get('valor')),'ResumoMax')],['Diferença para o próximo resultado distinto',dinheiro(d.get('diferenca'))]], [doc.width*.57,doc.width*.43],False)
    resumo.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f3eee7')),('BOX',(0,0),(-1,-1),1,colors.HexColor(GOLD))]))
    story += [resumo,Spacer(1,10)]
    if d.get('provisorio'):story += [par('Resultado provisório: há componentes pendentes. A classificação pode mudar; veja a segunda página.'),Spacer(1,8)]
    receita=sum(p[k] for k in ('comercio','industria','servicos'))
    story += [tabela([['Receita mensal','Custos e despesas','Salários','Pró-labore bruto'],[dinheiro(receita),dinheiro(p['custos']),dinheiro(p['salarios']),dinheiro(p['prolabore'])]],[doc.width/4]*4),Spacer(1,12)]
    story += [par('Comparação mensal dos regimes','Heading2')]
    t=tabela([['Regime','Situação','Tributos empresa','IR dividendos','Empresa + sócios','Líquido sócios']]+v['tabela'],[doc.width*x for x in [.16,.23,.15,.14,.16,.16]])
    for n,i in enumerate(r['resultados'],1):
        if i['regime'] in d.get('regimes',[]):t.setStyle(TableStyle([('BACKGROUND',(0,n),(-1,n),colors.HexColor('#edf5ef'))]))
    story += [t,Spacer(1,10),par('Empresa + sócios inclui tributos da empresa, IR dos dividendos e INSS/IRRF do pró-labore. Não inclui ajuste anual da pessoa física. IRPJ/CSLL são equivalentes mensais de um trimestre constante.','PequenoMax')]
    story += [PageBreak(),par('Memória e pontos de conferência','TituloMax'),par(p['empresa']+' · '+v['periodo']),Spacer(1,10)]
    componentes=sorted(set(k for i in r['resultados'] for k in i['componentes']))
    linhas=[['Tributo / componente']+[i['regime'] for i in r['resultados']]]
    for k in componentes:linhas.append([k]+[dinheiro(i['componentes'].get(k)) if k in i['componentes'] else '—' for i in r['resultados']])
    for label,k in [('INSS do pró-labore','inss'),('IRRF do pró-labore','irrf')]:linhas.append([label]+[dinheiro(i.get('prolabore',{}).get(k)) for i in r['resultados']])
    story += [tabela(linhas,[doc.width*.4]+[doc.width*.2]*3),Spacer(1,10)]
    pres=r['resultados'][1].get('memoria',{})
    if pres.get('detalhes'):
        linhas=[['Presunção por atividade','Receita trimestral','IRPJ / CSLL','Base IRPJ','Base CSLL']]
        for x in pres['detalhes']:
            if x['receita']:linhas.append([x['atividade'],dinheiro(x['receita']),f"{x['presuncao_irpj']*100:g}% / {x['presuncao_csll']*100:g}%",dinheiro(x['base_irpj']),dinheiro(x['base_csll'])])
        story += [par('Lucro Presumido · bases trimestrais','Heading2'),tabela(linhas,[doc.width/5]*5),Spacer(1,8)]
    if v['pendencias']:
        story.append(par('O que pode alterar o resultado','Heading2'))
        for nota in v['pendencias']:story += [par('• '+nota,'PequenoMax'),Spacer(1,4)]
    if r.get('hipoteses'):
        story.append(par('Premissas da reforma','Heading2'))
        story.append(par(f"CBS {p['cbs_pct']}%; IBS {p['ibs_pct']}%; redução {p['reducao_iva_pct']}%. Hipóteses de projeção, não alíquotas legais definitivas.",'PequenoMax'))
        for n in r['hipoteses']:story += [par(n,'PequenoMax'),Spacer(1,3)]
    story += [Spacer(1,9),par('Referências: LC 123/2006; Res. CGSN 140/2018; LC 224/2025; Leis 9.249/1995, 7.689/1988 e 15.270/2025. Regras e hipóteses completas acompanham a memória JSON do cenário. Distribuição de lucro depende de escrituração e caixa; retenção não é imposto anual definitivo.','PequenoMax')]
    def rodape(c,doc):
        c.setStrokeColor(colors.HexColor(GOLD));c.line(32,27,doc.pagesize[0]-32,27)
        c.setFont('MaxsuelRegular',8);c.drawString(32,15,'MAXSUEL CONTABILIDADE · PLANEJAMENTO TRIBUTÁRIO');c.drawRightString(doc.pagesize[0]-32,15,f'Página {doc.page}')
    doc.build(story,onFirstPage=rodape,onLaterPages=rodape);return buf.getvalue()


def gerar_html(titulo,painel,*,logo=None):
    v=dados(painel);p=v['p'];r=v['r'];d=v['d'];esc=lambda x:escape(str(x))
    img='<img alt="Maxsuel Contabilidade" src="data:image/png;base64,'+base64.b64encode(Path(logo).read_bytes()).decode()+'">' if logo and Path(logo).exists() else ''
    linhas=''.join('<tr class="'+('vencedor' if x[0] in d.get('regimes',[]) else '')+'">'+''.join('<td>'+esc(c)+'</td>' for c in x)+'</tr>' for x in v['tabela'])
    detalhes=''
    for i in r['resultados']:
        detalhes+='<section><h3>'+esc(i['regime'])+'</h3><table>'+''.join('<tr><td>'+esc(k)+'</td><td>'+esc(dinheiro(n))+'</td></tr>' for k,n in i['componentes'].items())+'</table></section>'
    pend=''.join('<li>'+esc(n)+'</li>' for n in v['pendencias'])
    pres=r['resultados'][1].get('memoria',{});bases=''
    for x in pres.get('detalhes',[]):
        if x['receita']:bases+='<tr>'+''.join('<td>'+esc(t)+'</td>' for t in [x['atividade'],dinheiro(x['receita']),f"{x['presuncao_irpj']*100:g}% / {x['presuncao_csll']*100:g}%",dinheiro(x['base_irpj']),dinheiro(x['base_csll'])])+'</tr>'
    return '''<!doctype html><html lang="pt-BR" translate="no"><head><meta charset="utf-8"><title>'''+esc(titulo)+'''</title><style>
    @page{size:A4 landscape;margin:14mm}body{font:13px/1.5 Arial;color:#16303a;max-width:1120px;margin:24px auto;padding:16px}header{display:flex;align-items:center;gap:24px;border-bottom:2px solid #b49c7e}header img{width:90px}h1{font-size:26px}h2{font-size:20px}.resumo{background:#f3eee7;border-left:5px solid #b49c7e;padding:20px;margin:22px 0}.valor{font-size:25px;font-weight:bold}.premissas{display:flex;justify-content:space-between;background:#edf2f4;padding:16px}table{width:100%;border-collapse:collapse;margin:14px 0}td,th{text-align:left;padding:10px;border-bottom:1px solid #dbe3e7}th{background:#edf2f4}.vencedor{background:#edf5ef}.nota{font-size:11px}.detalhes{display:flex;gap:20px}.detalhes section{flex:1}button{background:#16303a;color:white;padding:12px;border:0;border-radius:6px}.tecnica{margin-top:32px}@media print{button{display:none}.tecnica{break-before:page}thead{display:table-header-group}tr{break-inside:avoid}body{margin:0;padding:0}}
    </style></head><body><button id="imprimir" onclick="window.print()">Imprimir relatório</button><header>'''+img+'<div><h1>Planejamento tributário</h1><p>'+esc(p['empresa'])+' · '+esc(v['periodo'])+' · '+esc(v['modelo'])+'</p><p class="nota">Emitido em '+esc(v['emitido'])+'</p></div></header><div class="resumo"><div>'+esc(v['status'])+'</div><h2>'+esc(v['vencedor'])+'</h2><div>'+esc(v['criterio'])+'</div><div class="valor">'+esc(dinheiro(d.get('valor')))+'</div><p>Diferença para o próximo resultado distinto: '+esc(dinheiro(d.get('diferenca')))+'</p>'+('<p>Classificação provisória: confira os componentes pendentes na memória.</p>' if d.get('provisorio') else '')+'</div><div class="premissas">'+''.join('<span>'+esc(k)+'<br><b>'+esc(dinheiro(n))+'</b></span>' for k,n in [('Receita mensal',sum(p[k] for k in ('comercio','industria','servicos'))),('Custos',p['custos']),('Salários',p['salarios']),('Pró-labore',p['prolabore'])])+'</div><h2>Comparação mensal</h2><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in ['Regime','Situação','Tributos empresa','IR dividendos','Empresa + sócios','Líquido sócios'])+'</tr></thead><tbody>'+linhas+'</tbody></table><p class="nota">Empresa + sócios inclui tributos da empresa e INSS/IRRF do pró-labore, além do IR dos dividendos. Não inclui ajuste anual da pessoa física. IRPJ/CSLL são equivalentes mensais de um trimestre constante.</p><div class="tecnica"><h2>Memória e pontos de conferência</h2><div class="detalhes">'+detalhes+'</div><h3>Presunção do Lucro Presumido</h3><table><thead><tr><th>Atividade</th><th>Receita trimestral</th><th>IRPJ / CSLL</th><th>Base IRPJ</th><th>Base CSLL</th></tr></thead><tbody>'+bases+'</tbody></table><h3>O que pode alterar o resultado</h3><ul>'+pend+'</ul><h3>Premissas</h3><ul>'+''.join('<li>'+esc(n)+'</li>' for n in r.get('hipoteses',[]))+'</ul><p class="nota">Referências e hipóteses completas na memória JSON. A distribuição exige suporte contábil e disponibilidade de caixa; retenção mensal não é o imposto anual definitivo.</p></div></body></html>'
