# Atualizações periódicas e projeções anuais

## Versão 0.2 — 15/11/2026

Nova aba **Projeção de 1 ano** no planejamento tributário:

- Doze competências mensais de um ano-calendário; primeiro recorte implementado: 2026.
- Gerador de hipóteses de receita por comércio, indústria e serviços, custos/despesas e FS legal. Taxas financeiras de crescimento ou retração são declaradas pelo usuário, não confundidas com alterações de lei.
- Edição manual por mês para sazonalidade.
- Histórico mensal do ano anterior, sem inferência por médias. RBT12 e FS12 são recalculados para cada mês, excluindo o próprio mês de apuração.
- Simples: receitas ordinárias segregadas, regras de fator R e bloqueios existentes. Valores acima do sublimite ou em situações especiais não são preenchidos por aproximação.
- Presumido: agrupamento trimestral; majoração conforme recorte já implementado. Fechamento sem majoração calculado somente se todos os quatro trimestres tiverem receita sujeita à presunção de até R$ 1.250.000. Não há aproveitamento automático de sobras de limite. Se houver necessidade de ajuste anual com majoração, o quarto trimestre e o total anual ficam pendentes.
- Real: bases contábeis mensais conciliadas, ajustes documentados por mês e tributo, apuração trimestral e transporte prospectivo de saldos. O prejuízo de um trimestre não reduz retroativamente imposto de trimestre anterior. Resultados gerenciais não são convertidos automaticamente em bases fiscais.
- Totais anuais só aparecem quando todas as competências do componente foram calculadas. Totais ausentes não são zero nem a soma de apenas alguns períodos.
- Gráfico mensal de receitas e custos/despesas, memória detalhada e exportação JSON/HTML.

O quadro anual apresenta **DAS** para o Simples e **IRPJ/CSLL** para Presumido/Real. São componentes distintos; não há ranking entre esses subtotais. Consumo, folha e sócios continuam pendentes, conforme a revisão técnica. A projeção é por competência, não calendário de pagamentos ou fluxo de caixa.

2027 aparece como opção pendente e permanece bloqueado. A inclusão do ano exige a implementação e conferência das regras próprias e da transição, não apenas uma nova linha no catálogo.

## Estrutura de manutenção

- `regras/catalogo.json`: identificador, vigência, estado de revisão, data da revisão e pendências.
- `regras.py`: seleção da versão por ano e fotografia das tabelas, percentuais, fundamentos e hashes do código executado.
- Relatórios: incorporam os dados de entrada e a fotografia normativa. O arquivo exportado não é alterado por atualizações futuras do sistema.
- Consulta de memória salva: valida a consistência do hash da fotografia e mostra o arquivo anterior sem recalcular. Isso não é assinatura digital ou certificação de veracidade dos resultados.
- Testes: casos de limites e regressão acompanham o código. A base não é homologada por passar em testes.

Para reproduzir os cálculos de uma versão antiga, preserve também o pacote de código daquela versão. A consulta do relatório salvo funciona sem recalcular; reprodução computacional com motor antigo ainda não é executada automaticamente.

## Procedimento para uma melhoria ou mudança normativa

1. Registrar fonte oficial, artigo, redação e datas de vigência/efeitos. Distinguir proposta, texto publicado e regra aplicável.
2. Descrever critérios de enquadramento, transição, exceções e dados necessários.
3. Implementar a regra em módulo independente da interface, com casos de referência e limites.
4. Conferir cálculos e impactos sobre os demais regimes e relatórios.
5. Criar novo identificador de versão; preservar código anterior e registrar a mudança. Não reescrever regras antigas silenciosamente.
6. Recalcular cenários somente como novas simulações, mantendo a memória anterior.

Não foi criado um agendamento automático. A estrutura permite revisões periódicas, mas não promete atualização normativa sem análise das fontes.

## Próximos itens da evolução

Fechamento completo da LC 224; PIS/Cofins; cadastro por UF/município e operação para ICMS/ISS; partilha do DAS; monofasia/ST; Parte B; folha; tributação anual dos sócios; transição e tabelas de 2027; integração de DRE, precificação e indicadores do HTML ao motor comum.
