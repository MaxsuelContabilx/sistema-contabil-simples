"""Relatórios escapados e PDF paginado; botão de impressão no próprio documento."""
import base64
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path


def texto(valor):
    return escape(str(valor if valor is not None else 'Pendente'))


def html_relatorio(titulo,colunas,linhas,*,empresa='',observacoes=(),logo=None):
    imagem=''
    if logo and Path(logo).is_file():
        imagem='<img class="logo" alt="Maxsuel Contabilidade" src="data:image/png;base64,'+base64.b64encode(Path(logo).read_bytes()).decode()+'">'
    cabecalho=''.join('<th>'+texto(c)+'</th>' for c in colunas)
    corpo=''.join('<tr>'+''.join('<td>'+texto(v)+'</td>' for v in linha)+'</tr>' for linha in linhas)
    notas=''.join('<li>'+texto(o)+'</li>' for o in observacoes)
    return ('<!doctype html><html lang="pt-BR" translate="no"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'+texto(titulo)+'</title>'
        '<style>body{font:14px/1.5 Arial,sans-serif;color:#16303a;max-width:1100px;margin:30px auto;padding:20px}'
        '.logo{width:110px;height:110px;object-fit:contain}header{display:flex;gap:24px;align-items:center;border-bottom:2px solid #b49c7e}'
        'h1{font-size:23px}table{width:100%;border-collapse:collapse;margin-top:24px}th,td{padding:10px;text-align:left;border-bottom:1px solid #dbe3e7;overflow-wrap:anywhere}'
        'th{background:#edf2f4}button{background:#16303a;color:white;padding:12px 18px;border:0;border-radius:6px;cursor:pointer}'
        '@media print{button{display:none}body{margin:0;max-width:none;padding:0}thead{display:table-header-group}tr{break-inside:avoid}a{color:inherit}}</style>'
        '</head><body><button type="button" id="imprimir" onclick="window.print()">Imprimir relatório</button><header>'+imagem+
        '<div><h1>'+texto(titulo)+'</h1><p>'+texto(empresa)+'</p></div></header><table><thead><tr>'+cabecalho+
        '</tr></thead><tbody>'+corpo+'</tbody></table><ul>'+notas+'</ul></body></html>')


def pdf_relatorio(titulo,colunas,linhas,*,empresa='',observacoes=(),logo=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    buf=BytesIO();styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=30,leftMargin=30,topMargin=24,bottomMargin=28)
    story=[]
    if logo and Path(logo).is_file():story.append(Image(str(logo),width=64,height=64,hAlign='LEFT'))
    story.extend([Paragraph(texto(titulo),styles['Title']),Paragraph(texto(empresa),styles['Normal']),Spacer(1,14)])
    dados=[[Paragraph(texto(c),styles['BodyText']) for c in colunas]]
    dados += [[Paragraph(texto(v),styles['BodyText']) for v in linha] for linha in linhas]
    tabela=Table(dados,repeatRows=1,colWidths=[doc.width/max(1,len(colunas))]*len(colunas))
    tabela.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf2f4')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dbe3e7')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.extend([tabela,Spacer(1,14)])
    for nota in observacoes:story.extend([Paragraph(texto(nota),styles['Normal']),Spacer(1,5)])
    def rodape(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawRightString(doc.pagesize[0]-30,15,f'Maxsuel Contabilidade | Página {doc.page}')
    doc.build(story,onFirstPage=rodape,onLaterPages=rodape)
    return buf.getvalue()
