# Versão 0.5 — presunção, início do Simples e destaque do regime

## Lucro Presumido visível

O cartão informa os percentuais básicos por atividade. O quadro **Presunção do Lucro Presumido · percentuais e bases** mostra receita trimestral, percentuais de IRPJ/CSLL, receitas sujeitas à majoração e bases efetivamente calculadas. O quadro não substitui enquadramentos específicos por percentuais de serviços gerais. Se a apuração estiver bloqueada, mostra apenas os percentuais básicos e identifica que a base efetiva está pendente.

Os relatórios PDF/HTML e a memória JSON incluem as presunções e bases. A majoração de 10% é relativa ao percentual básico e limitada à parcela sujeita à regra já implementada, não um acréscimo indiscriminado de dez pontos percentuais.

## Simples: idade desde o CNPJ e vigência

O início conta desde a abertura no CNPJ, inclusive meses sem receita. Não conta desde a primeira nota ou do primeiro faturamento. Sem data, é possível informar o número do mês de atividade. Um histórico necessário em branco é pendente; zero precisa ser informado e participa da média.

- **2026:** no primeiro mês, receita do período × 12; do segundo ao décimo segundo, média dos meses anteriores ao período × 12; do décimo terceiro em diante, soma dos 12 meses anteriores.
- **A partir de 01/01/2027, critério da Resolução CGSN 190/2026:** dois primeiros meses na primeira faixa, sem RBT12 proporcional; do terceiro ao décimo terceiro, média dos meses antecedentes ao mês anterior × 12, excluindo o mês imediatamente anterior ao período; do décimo quarto em diante, os 12 meses antecedentes ao mês anterior. Nos dois primeiros meses, fator R igual a 0,28; depois, janela de folha compatível com a janela de receita.

A regra temporal e o fator R de 2027 são calculados e exibidos na memória, com os meses usados e o divisor. **Isso não desbloqueia o DAS nem a comparação tributária global de 2027:** tabelas/partilhas e demais regras monetárias do período ainda exigem revisão. A plataforma não reutiliza silenciosamente as tabelas de 2026 em 2027. A projeção de CBS/IBS existente continua usando referências de 2026 expressamente identificadas.

O cálculo dos meses iniciais de 2026 já se integra ao Planejamento e à comparação dos anexos, com anualização da folha para fator R quando aplicável. O histórico da empresa existente não é substituído por previsões repetidas. O cálculo técnico anual de empresa madura mantém sua janela de 2026 e seu recorte próprio.

Exemplos oficiais reproduzidos nos testes:

- 2026, terceiro mês: receitas anteriores de R$ 9 mil e R$ 40 mil → média R$ 24,5 mil → RBT12 proporcional R$ 294 mil.
- 2026, quarto mês: R$ 0, R$ 0 e R$ 60 mil → média R$ 20 mil → RBT12 proporcional R$ 240 mil.
- 2027, terceiro mês: só o primeiro mês, de R$ 8 mil, entra na média → RBT12 proporcional R$ 96 mil.
- 2027, quarto mês: primeiro e segundo meses, R$ 8 mil e R$ 7 mil → RBT12 proporcional R$ 90 mil.

Fontes: documentos fornecidos pelo usuário (Resoluções CGSN 140/2018 e 190/2026), arts. 21, 22 e 26; art. 9º da Resolução 190/2026 para produção de efeitos. Conferência adicional nas seções 5.4.1 e 5.4.2 do [Perguntas e Respostas oficial do Simples](https://www8.receita.fazenda.gov.br/SimplesNacional/Arquivos/manual/PerguntaoSN.pdf) e na [Resolução 190/2026 no sistema de normas da Receita](https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=152832).

## Destaque inicial

O início da página, após solicitar a comparação, mostra o melhor resultado para **maior líquido dos sócios** ou **menor total de tributos**. O critério é editável e considera valores mensais comparáveis, inclusive retenção de dividendos e tributação do pró-labore. Empates são apresentados como empates.

Se qualquer regime tiver componente ausente ou cálculo incompleto, o destaque é **provisório**, com as pendências que podem alterar a classificação. Não se exclui silenciosamente um regime incompleto para declarar outro como vencedor definitivo. O ajuste anual da pessoa física e a elegibilidade jurídica continuam sujeitos à conferência. A projeção da reforma mantém seu próprio destaque condicional e não é misturada ao cenário atual.

## Formatação

Legendas que contêm mais de um valor em reais escapam o cifrão no Markdown. Isso impede que o Streamlit interprete o trecho entre dois valores como fórmula matemática, como ocorria na tela PJ × CLT. Relatórios continuam recebendo valores monetários sem barras de escape.
