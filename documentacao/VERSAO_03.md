# Interface operacional, cadastros e importações — versão 0.3

## Implementado

- Interface nativa no Streamlit baseada no visual aprovado, com logo original, cores da marca e menu do escritório.
- Cenário compartilhado entre telas: receitas, custos, salários, pró-labore, informações cadastrais e distribuições. Os dados não são apagados ao navegar pelos módulos.
- Caminho de empresa em abertura: Simples do primeiro mês com receita anualizada e fator R do período, conforme Res. CGSN 140/2018, art. 21 §2º e art. 26 §6º. Não inventa 12 meses de histórico.
- Comparação dos componentes disponíveis dos três regimes, distinguindo tributos da pessoa jurídica e IRRF dos dividendos. Campos necessários em branco impedem um total aparentemente completo.
- IRRF por fonte, beneficiário e mês, com soma de pagamentos ao mesmo sócio. Quando o enquadramento é PF residente e o total do mês supera R$ 50 mil, a regra geral incide sobre todo o valor alcançado. Não há retenção automática em distribuições de qualquer valor. Residência desconhecida, lucros antigos e situações fora do recorte permanecem pendentes.
- O IRRF é apresentado também no comparativo matemático dos anexos, na projeção de 12 meses, na projeção tributária técnica e nas memórias mensais/trimestrais. Não é deduzido uma segunda vez como despesa própria da empresa.
- Cadastro por cartão CNPJ em PDF com texto; QSA opcional em PDF separado; edição e confirmação antes de gravar. CNPJ numérico e alfanumérico com verificação dos dígitos. Não verifica autenticidade ou atualidade do documento perante a Receita.
- Persistência de razão social, CNPJ, CNAE, abertura, endereço, contato, porte, situação e quadro societário. Um novo cartão sem QSA não apaga os sócios já conferidos. Importações não substituem silenciosamente empresas existentes.
- Importação de lançamentos CSV: UTF-8/BOM ou Windows-1252, separador ponto e vírgula/vírgula/tabulação, datas brasileiras/ISO, valores brasileiros, contas existentes, bloqueio de erros e transação única. Duplicados são ignorados, salvo opção explícita para operações distintas.
- PDF com paginação e HTML escapado com botão de impressão. Impressão disponível também para demonstrativos de salários/férias e resultados dos simuladores originais.
- Salário mensal de empregado em 2026: INSS progressivo e teto; tabela de IRRF atualizada; dedução simplificada mais vantajosa; redução calculada sobre rendimento tributável. Não aplica tabela de empregado a pró-labore ou a múltiplos vínculos.

## Preservação dos recursos

O sistema original continua em `sistema_original.py`, acessível pelo menu. Cadastro, importação, folha, férias, balancete, DRE, balanço e simulador do Simples continuam disponíveis. O comparativo antigo passa a usar o cenário compartilhado, em vez de recomendar regimes com o acréscimo de presunção aplicado indistintamente. Os relatórios antigos dos simuladores foram substituídos por exportações que incluem o IR dos dividendos.

Algumas fórmulas legadas, especialmente partilha do DAS e transição IBS/CBS, continuam identificadas como em revisão. Preservar a ferramenta não significa homologar a fórmula anterior.

## Limitações que continuam explícitas

- Fechamento anual completo da LC 224 com majoração e seus ajustes; regras de 2027; receitas especiais; partilha do DAS; enquadramentos condicionados por atividade.
- ICMS/ISS/IPI e encargos precisam de valores/critério confirmados. O cadastro de UF/município não determina automaticamente as alíquotas locais.
- Projeções de PIS/Cofins pela regra geral são uma hipótese expressamente selecionada, não classificação automática de todas as operações.
- A projeção nativa de 12 meses é financeira e inclui a retenção projetada dos dividendos. A projeção tributária detalhada continua na área técnica e não extrapola regras para anos não revisados.
- A simulação não efetua pagamentos, recolhe valores ou transmite declarações. Apura previsões de retenção; guias e obrigações exigem seu fluxo próprio.
- A tributação mínima anual do sócio e o redutor do art. 16-B não equivalem à retenção mensal e ainda não estão implementados.
- OCR para PDFs escaneados não está implementado. Leiautes não reconhecidos ficam para revisão manual.
- Banco de demonstração local: não há migração da produção, novo provedor de persistência ou autenticação implantados nesta etapa. Faça backup antes de usar cadastros de forma definitiva.

## Fontes da revisão da folha

- Receita Federal, tabela de tributação de 2026: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026
- Lei 15.191/2025: tabela mensal de IRRF.
- Lei 15.270/2025: redução do IRRF mensal, retenção de dividendos e demais disposições.
- INSS, tabela de contribuição mensal: https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/tabela-de-contribuicao-mensal
- Portaria Interministerial MPS/MF 13/2026: faixas e teto de contribuição de empregado.

## Verificação

Os testes de documentos usam PDFs gerados com dados fictícios. A compatibilidade com o PDF específico do usuário precisa ser conferida na importação. O teste de navegador verifica o download de PDF, o acionamento de `window.print`, a troca de telas sem perder o cenário, os dividendos nos três regimes, a importação CNPJ/QSA e a prevenção de CSV duplicado. Não verifica impressora física ou recolhimento de tributos.
