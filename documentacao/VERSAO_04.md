# Versão 0.4 — saldo automático, reforma e PJ × CLT

Atualização de testes de 16/11/2026. A `main`, o banco original e o CSV original são preservados.

## Fluxo de planejamento

Uma entrada compartilhada alimenta a comparação. O padrão **Distribuir todo o saldo** calcula separadamente, para cada regime:

1. Receita menos custos, salários, pró-labore bruto e tributos da empresa.
2. Dividendo bruto igual ao saldo positivo. Resultado negativo não gera dividendo e identifica o aporte necessário.
3. Retenção de dividendos por fonte, beneficiário e mês, conforme o recorte de PF residente e lucros de 2026 da Lei 15.270/2025.
4. Líquido dos sócios: dividendo após retenção mais pró-labore após INSS/IRRF, menos eventual aporte do cenário.

O IR dos dividendos não é deduzido duas vezes. Um beneficiário recebe todo o saldo; com vários, o rateio precisa ser confirmado e somar 100%. Participação do QSA só é usada como rateio quando o usuário escolhe essa opção. Residência e origem dos lucros permanecem campos explícitos. O pró-labore agregado de vários sócios não é tributado como se fosse de um só: o líquido pessoal fica pendente de remunerações individuais.

A distribuição é uma previsão financeira, sujeita à escrituração, suporte do lucro e disponibilidade de caixa. Não equivale a autorização legal para distribuir todo saldo bancário. O imposto mínimo anual da pessoa física, o redutor e outras rendas do sócio ainda precisam de apuração própria.

## Impostos nos cartões

Presumido e Real mostram os componentes calculados, inclusive IRPJ/CSLL. Valores desconhecidos permanecem discriminados, com subtotal e saldo **condicionais**; não se recomenda um regime definitivo com componentes ausentes.

A hipótese geral de PIS/Cofins vem selecionada e é editável: cumulativo no Presumido e não cumulativo no Real. Créditos do Real são informados pelo usuário e precisam ser elegíveis. Encargos em branco usam, como hipótese expressa, CPP geral de 20% sobre salários e pró-labore fora do Simples e no Anexo IV; RAT/FAP, terceiros e regimes especiais não são presumidos como completos. ICMS, ISS e IPI não recebem alíquotas genéricas.

Em 2026, a dispensa dos tributos de teste depende das condições legais. Há confirmação específica para a dispensa de recolhimento de CBS/IBS; sem ela, o subtotal fora do Simples fica condicional quanto ao eventual recolhimento/compensação. Não se aplica 30% como apuração efetiva de 2026.

IRPJ/CSLL mensais do comparativo são equivalentes de um trimestre constante dividido por três. Abertura dentro do trimestre e fechamento anual do Presumido com majoração ainda exigem rotinas próprias; quando bloqueados, o subtotal disponível e os tributos ausentes são identificados. Não foram introduzidas novas presunções a partir de notícias sobre redução de benefícios sem norma e vigência confirmadas.

## Reforma

A segunda aba modela uma **substituição futura integral** com CBS de 11,3% e IBS de 18,7%, percentuais solicitados pelo usuário e editáveis. Não são declarados como alíquotas legais definitivas, nem representam a transição de 2026 a 2032. IRPJ/CSLL, dividendos e DAS mantêm referências de 2026 e precisam ser revistos para vigências futuras.

- Preço final mantido: base = preço final / (1 + CBS + IBS), após eventual redução confirmada.
- Repasse por fora: base = valor informado; a fatura cresce pelos débitos de CBS e IBS.
- Créditos declarados: vinculados aos custos informados, limitados ao débito para uso no caixa; saldos credores não viram dividendos. Crédito utilizado é retirado do custo fiscal para não gerar dedução duplicada. O IVA não é descontado novamente do resultado cuja receita já exclui o IVA.
- Simples dentro do DAS: referência atual identificada como condicional, sem inventar uma tabela futura.
- Simples por fora: usuário informa a parcela do DAS substituída. Sem essa partilha confirmada, o DAS é mantido integralmente e a projeção é marcada como condicional/conservadora. Encargos externos não podem ser usados como parcela substituída.

Regimes diferenciados, créditos especiais, IPI remanescente e exceções não são automaticamente enquadrados pelo CNAE.

## PJ × CLT

CLT: contribuição progressiva do empregado, IRRF mensal de 2026 e redução aplicável. Ano completo = 11 salários regulares líquidos + férias líquidas com 1/3 + 13º líquido. Não se duplica o salário do mês de férias. FGTS geral de 8% e benefícios ficam separados do dinheiro disponível.

PJ: atividade, custos, salários e pró-labore do planejamento são reutilizados; a proposta altera a receita do cenário. INSS do contribuinte individual pago por PJ é 11% até o teto, distinto do cálculo progressivo do empregado. Distribui-se automaticamente o saldo de cada regime. Meses sem nota mantêm custos e obrigações; pró-labore é transferência interna na visão consolidada PJ + sócio, sem dupla despesa. RBT12/FS12 reais de empresa existente não são substituídos por histórico inventado.

O anual PJ é uma referência mensal constante pelos meses faturados, descontando custos dos meses sem nota. Não substitui uma apuração anual com sazonalidade, RBT12/FS12 móveis, ajustes trimestrais e renda anual da pessoa física. A comparação econômica não determina a regularidade jurídica do contrato.

## Navegação, relatórios e módulos preservados

Menu dividido em Planejar e Empresa e rotina; simuladores originais e ferramentas técnicas ficam em Mais ferramentas. Logo, salários, férias, cadastro PDF/QSA e importação CSV foram preservados. Tema claro/escuro continua por sessão.

PDF, HTML e memória JSON acompanham os resultados. Os relatórios identificam hipóteses e pendências e permanecem claros para impressão. Botão de impressão aciona o navegador; impressora física não foi testada.

Apurações técnicas isoladas e a grade financeira de 12 meses não possuem todos os componentes para inferir o saldo distribuível: no modo automático, IRRF permanece pendente nesses módulos, sem presumir zero ou repetir um dividendo de outro regime. Distribuição manual continua disponível para cenários de pagamentos definidos.

## Referências verificadas

- LC 123/2006, anexos e Resolução CGSN 140/2018: núcleo do Simples já existente, mantido em revisão para tratamentos especiais.
- [Lei 15.270/2025, texto do Senado](https://normas.leg.br/?urn=urn%3Alex%3Abr%3Afederal%3Alei%3A2025-11-26%3B15270%402025-11-26): retenção de dividendos e redução do IRPF.
- [Receita Federal — tabelas de 2026](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026).
- [INSS — tabela de contribuição mensal](https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/tabela-de-contribuicao-mensal), Portaria MPS/MF 13/2026.
- [Receita Federal — redução também no 13º](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/dezembro/receita-federal-orienta-fontes-pagadoras-e-contribuintes-a-calcular-a-reducao-do-imposto-de-renda-a-partir-de-1o-de-janeiro-de-2026).
- [SC Cosit 101/2018](https://normas.receita.fazenda.gov.br/sijut2consulta/anexoOutros.action?idArquivoBinario=49462), Lei 10.666/2003, art. 4º e Lei 8.212/1991, arts. 22 e 28: contribuinte individual e contribuição patronal na regra geral. Lei 8.036/1990, art. 15: FGTS.
- [RFB/CGIBS — comunicado sobre 2026](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/dezembro/comunicado-conjunto/), atualizado em 28/10/2026; LC 214/2025, art. 348; Decreto 12.955/2026, art. 464 (PDF fornecido).

## Atualizações periódicas

Regras seguem em módulos independentes, catálogo versionado e fotografia com hashes dos códigos de cálculo. Nesta versão, `planejador.py` e `pj_clt.py` entram na identificação da memória. Atualizações de tabelas e normas devem registrar fonte, vigência e testes de regressão; o sistema não altera regras silenciosamente.
