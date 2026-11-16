# Versão 0.6 — relatório executivo e situação do Simples

## Relatório comparativo

PDF e HTML agora têm um resumo executivo com logo, empresa, competência, data de emissão em Brasília, melhor resultado, critério, diferença para a próxima alternativa, premissas financeiras e tabela comparativa com a linha destacada. O destaque provisório mantém a ressalva visível na primeira página. Não se imprime mais um dicionário técnico como texto de conclusão.

A memória começa em página separada e organiza tributos por regime, presunção do Lucro Presumido e pontos que podem alterar a classificação. Referências completas e dados estruturados continuam na memória JSON. A fonte do PDF é incorporada a partir dos arquivos distribuídos com ReportLab. PDF e HTML mantêm impressão clara independente do tema da interface.

## Limite geral não é sublimite

O campo da interface é **receita mensal**. Para empresa no primeiro mês, a classificação da projeção usa receita mensal × 12:

- Até R$ 300 mil/mês: este aviso de sublimite não é acionado.
- Acima de R$ 300 mil e até R$ 400 mil/mês: identifica o intervalo anualizado de R$ 3,6 milhões a R$ 4,8 milhões; não declara exclusão do Simples. Explica que o DAS completo depende da análise dos efeitos temporais do sublimite e do ICMS/ISS.
- Acima de R$ 400 mil/mês no primeiro mês, a receita anualizada ultrapassa R$ 4,8 milhões: informa **Não se enquadra no Simples neste cenário projetado**.
- Receita de um único mês acima de R$ 4,8 milhões também recebe aviso explícito. O exemplo de R$ 8 milhões mensais corresponde à projeção de R$ 96 milhões anuais.

A classificação de projeção não formaliza exclusão fiscal, nem afirma que toda anualização acima do limite causa exclusão imediata. A receita efetivamente auferida, os meses entre abertura e final do ano, a tolerância de 20% e os efeitos temporais precisam de apuração própria. Receita mensal alta em empresa madura, sem histórico suficiente, não é automaticamente multiplicada por 12 para decretar sua exclusão. Exportações e regimes especiais permanecem fora deste recorte ordinário.

O aviso aparece ao alterar a receita e também no cartão do Simples, na tela específica e no relatório. Regime explicitamente fora do cenário projetado não participa do destaque; componentes faltantes dos demais regimes continuam tornando a classificação provisória.

Fontes: LC 123/2006, arts. 3º, 19 e 20; Resolução CGSN 140/2018; [Manual oficial de exclusão](https://www8.receita.fazenda.gov.br/SimplesNacional/Arquivos/manual/MANUAL_EXCLUSAO.pdf) e [Perguntas e Respostas oficial](https://www8.receita.fazenda.gov.br/SimplesNacional/Arquivos/manual/PerguntaoSN.pdf). O limite de R$ 4,8 milhões é anual no mercado interno; o sublimite de R$ 3,6 milhões não se confunde com o limite geral.
