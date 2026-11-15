# Revisão dos projetos — 15/11/2026

Este documento registra o diagnóstico e a primeira etapa (0.1). A evolução posterior para projeções anuais e manutenção está em `ATUALIZACOES.md`, versão 0.2. A exceção implementada para fechamento do Presumido sem majoração consta nesse histórico.

## Escopo e estado da entrega de trabalho

Versão 0.1 de revisão, local, para serviços, comércio e indústria. O código do site enviado é Python/Streamlit, não apenas HTML. A interface HTML permanece como referência de recursos e apresentação; seus cálculos não foram importados automaticamente.

Esta versão não é a plataforma final solicitada. Não determina o regime globalmente mais vantajoso. Implementa componentes verificáveis e bloqueia alguns casos não cobertos, sem substituir valores desconhecidos por alíquotas aproximadas. Todos os resultados são parciais e registram entradas, fundamento e pendências.

O estado e o município não foram informados. Não há regra local presumida para ICMS/ISS. O ano inicial de implementação é 2026; isso é uma decisão de desenvolvimento, não uma indicação de preferência do usuário por excluir 2027.

## Documentos recebidos e limitações

Todos os arquivos foram abertos. Os sete PDFs tiveram texto extraído, totalizando 581 páginas. Extração e pesquisa não equivalem a validação jurídica integral de todos os dispositivos. O inventário registra tamanho e SHA-256 de cada upload.

| Arquivo | Páginas | Uso e limitações identificadas |
|---|---:|---|
| Lcp 214.pdf | 20 | Fragmento: termina no art. 26, § 9º-A, no meio de uma frase. Não contém toda a LC 214, suas regras finais e anexos. Texto já tem referências à LC 227/2026; não tratar como redação original de janeiro de 2025. |
| d12955.pdf | 169 | Regulamentação da CBS. Contém alterações posteriores, entre elas referências aos Decretos 13.075, 13.133 e 13.140/2026. Exige versão temporal, não mera aplicação do texto compilado a todo o ano. Art. 464 trata de dispensa condicionada de recolhimento em 2026. |
| LUCRO REAL ON LINE.pdf | 68 | Material didático: subsidia revisão e testes, mas não substitui lei. Slides 94–95 contêm exemplo de bases diferentes e compensações separadas de IRPJ/CSLL, usado em teste de referência. |
| LUCRO PRESUMIDO ON LINE.pdf | 56 | Material didático com atividades e percentuais. Contém exemplos de 2025 e regras condicionadas, como serviços hospitalares e redução para certos pequenos prestadores. Exige atualização normativa, sem generalizar exemplos. |
| Resol. CGSN nº 190-2026.pdf | 18 | Art. 9º prevê efeitos a partir de 01/01/2027. O anexo único é um link externo, não está incorporado ao PDF. |
| Resol. CGSN nº 140-2018.pdf | 116 | Visão multivigente: mostra dispositivos alterados e modificações previstas para 2027. Anexos I–V aparecem como links externos; as tabelas não estão incorporadas ao PDF. |
| Gestão do ISS I e II 29.10 e 05.11.2026_SL.pdf | 134 | Material de treinamento: local de incidência, retenção e discussões jurisprudenciais. Não substitui código tributário municipal nem autoriza alíquota única de ISS. |
| sistema-contabil-simples-main.zip | — | app.py com 1.690 linhas e regras acopladas à interface; tax_engine.py praticamente vazio. Banco SQLite e CSV não foram incorporados à cópia de revisão nem seus registros usados em testes. |
| sistema_de_planejamento_tributario_e_dr.txt | — | HTML com JavaScript, DRE, precificação, ponto de equilíbrio, gráficos e projeções de reforma. Recursos gerenciais aproveitáveis; motor não está juridicamente completo. |

## Divergências verificadas nos códigos originais

1. Python aplica +10% a toda a base presumida, sem limite ou vigência. HTML não implementa a alteração. A regra legal alcança a parcela de receita definida pela LC 224/2025, com critérios trimestrais, histórico e ajuste anual próprios.
2. Python usa adicional mensal de IRPJ como se fosse apuração definitiva do Presumido. HTML agrega receita anual e usa R$ 240 mil como corte, perdendo o efeito de sazonalidade trimestral.
3. Python calcula o IRRF de dividendos sobre o excedente de R$ 50 mil. A regra do art. 6º-A da Lei 9.250 é sobre o total quando superado o limite, por fonte/beneficiário/mês. Não há no original agregação por esses identificadores.
4. Python mistura retenção dos dividendos com tributos próprios da empresa e não distingue o ajuste anual do sócio.
5. Python usa parcela a deduzir de R$ 848 mil na sexta faixa do Anexo III; o correto na tabela anterior a 2027 é R$ 648 mil. HTML tem R$ 648 mil. A tabela do manual oficial PGDAS-D confirma esse valor.
6. Ambos os projetos carecem de validação completa de opção, vedações, início de atividade, sublimites e efeitos do excesso. Uma empresa acima do limite não pode receber DAS zero e ser classificada como melhor alternativa.
7. Python usa repartição fixa por anexo; partilha varia por faixa e há regras próprias. HTML soma ICMS/ISS fora do DAS sem tratamento completo da parcela interna e da data de impedimento.
8. HTML usa setor genérico para escolha de Anexo III/V e aplica um piso artificial de alíquota. Fator R exige enquadramento e FS12 legal, com janela temporal correta, não simplesmente folha genérica dividida por receita.
9. Lucro Real original não tem bases separadas, catálogo de ajustes, compensações independentes ou controle de saldos/reversões temporárias.
10. Ambos os projetos assumem créditos amplos sobre custos/insumos. Crédito de PIS/Cofins, ICMS e IBS/CBS depende do regime, operação e requisitos documentais.
11. Python fixa ICMS/ISS em 5% e contribuição patronal em 27,8%. Esses valores não foram adotados pelo novo motor.
12. Alíquotas futuras de CBS/IBS aparecem como valores fixos no HTML e no Python. No Python há inclusive rótulos diferentes dos multiplicadores usados (9,21% versus 8,8%; 18,70% versus 17,7%). Não são bases aceitáveis para comparação legal automática.
13. A transição de 2026 não pode ser tratada simplesmente como acréscimo da CBS e IBS sobre a carga antiga. O Decreto 12.955, art. 464, exige verificar as condições de dispensa/obrigações acessórias. A versão de revisão ainda não calcula esse componente.
14. Há lançamento de dividendos como despesa no demonstrativo contábil legado. O módulo contábil não foi reescrito nesta etapa; essa classificação deve ser revisada antes de usar a DRE como base automática do Lucro Real.

## Regras novas ou propostas

### LC 224/2025

Fundamento principal: art. 4º, § 4º, VII, e § 5º. O corte de benefícios não significa redução do imposto devido. No Presumido, o mecanismo eleva os percentuais de presunção sobre a parcela alcançada.

IRPJ e CSLL têm marcos distintos em 2026. A orientação oficial consultada da Receita indica IRPJ a partir do primeiro trimestre, CSLL a partir do segundo, com limite anual aplicável à CSLL em 2026 de R$ 3,75 milhões. A IN RFB 2.305/2025 e suas alterações, inclusive IN 2.306/2026, devem compor o cadastro normativo.

Nesta versão, limites disponíveis precisam ser informados com base e memória documental. Não há cálculo automático de aproveitamento de limites anteriores, recálculo anual, dedução, restituição ou compensação dos acréscimos. Quarto trimestre está bloqueado para o Presumido até essa implementação. Isso impede que um cálculo trimestral isolado seja apresentado como fechamento anual.

### PLP 299/2026 — percentual de 20%

Consulta oficial em 15/11/2026: matéria em tramitação no Senado. Não foi ativado como regra legal vigente nem somado aos 10%. É necessário confirmar texto final, sanção, publicação e produção de efeitos antes de qualquer ativação.

### Lei 15.270/2025

Retenção mensal implementada para PF residente e lucros de 2026, com eventos agregados por fonte/beneficiário/mês. Valores acima de R$ 50 mil são sujeitos a 10% sobre o total alcançado pela regra. Lucros antigos e outros tipos de beneficiários são bloqueados, sem pressupor isenção.

Ainda pendem a tributação mínima anual, composição e exclusões da base, impostos dedutíveis, redutor do art. 16-B, tratamento de não residentes e documentação de transição. O IRRF não é somado como nova despesa própria da pessoa jurídica.

## Arquitetura implementada

- tax_engine.py: funções independentes, Decimal, validação de entradas ausentes/não finitas, fundamentos e resultados parciais.
- planejamento_ui.py: telas do Simples, Presumido, Real e dividendos; relatório com snapshot das entradas e resultados, em JSON e HTML escapado para impressão.
- app.py: integração no menu existente. Calculadoras antigas do Simples e comparativo foram substituídas na cópia de trabalho. Módulos contábeis e folha permanecem legados, com aviso na folha.
- tests/test_tax_engine.py: testes de limites, agregações e exemplo de referência do material de Lucro Real.

## O que falta para a plataforma final

1. Cadastro de empresas, estabelecimentos, CNAEs e caracterização concreta das operações; UF, município, tipo de cliente e produto/serviço.
2. Repositório normativo completo, com artigos, redações, vigências, revogações e status de revisão. Complementar LC 214, LC 123 e anexos oficiais ausentes dos PDFs.
3. Partilha do DAS por faixa e tributo; fator R com composição e histórico validado; início de atividade; sublimites; segregações especiais; efeitos de exclusão e opção IBS/CBS.
4. Presumido: histórico de receitas, regras de caixa/competência, demais receitas e ganhos, limites e ajustes do ano, exceções por atividade e situações especiais.
5. Real: catálogo normativo de ajustes, reversões temporárias/Parte B, saldos e restrições específicas de compensação, estimativas/suspensão/redução no regime anual, deduções e retenções.
6. PIS/Cofins por operação, créditos elegíveis, ICMS/IPI/ISS com normas estaduais e municipais e folha por estabelecimento/atividade.
7. Dividendos e tributação anual dos sócios com redutor e tratamento de transição.
8. Comparação de períodos homogêneos com todos os componentes e elegibilidade; DRE, fluxo de caixa, precificação e indicadores gerenciais do HTML integrados ao mesmo motor.
9. Testes de referência adicionais com apurações reais anonimizadas e revisão técnica das regras.

## Fontes oficiais complementares consultadas

- LC 123/2006: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm
- Manual PGDAS-D: https://www8.receita.fazenda.gov.br/simplesnacional/arquivos/manual/manual_pgdas-d_2018_v4.pdf
- LC 224/2025: https://normas.leg.br/?urn=urn:lex:br:federal:lei.complementar:2025-12-26;224!art4
- Lei 15.270/2025: https://normas.leg.br/?urn=urn:lex:br:federal:lei:2025-11-26;15270
- Tramitação PLP 299/2026: https://www25.senado.leg.br/web/atividade/materias/-/materia/176328
- P&R da Receita sobre redução de benefícios, consulta a resultados oficiais e à versão 3 indexada. Há indicação de versão 5 posterior que precisa ser obtida e integralmente conferida antes de automatizar o fechamento anual. A versão antiga não é tratada como cadastro normativo completo.

As tentativas de baixar textos completos diretamente do Planalto nesta sessão tiveram timeout. Isso não foi interpretado como validação ou como ausência de alteração normativa. As páginas oficiais consultadas pela ferramenta de pesquisa e os documentos fornecidos sustentam os achados delimitados acima.
