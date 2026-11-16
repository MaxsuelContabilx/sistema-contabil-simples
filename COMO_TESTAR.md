# Como testar a plataforma Maxsuel — versão 0.3

Se você já abriu o aplicativo de testes, use o mesmo endereço e atualize com **Ctrl + F5** depois que o Streamlit concluir a atualização. Agora a página inicial é o planejamento com logo e menu lateral, não a prévia estática.

## Planejamento

1. Selecione uma empresa cadastrada ou dê um nome ao cenário.
2. Escolha **Vai começar agora** ou **Já está funcionando**.
3. Informe atividade, faturamento, custos, salários e pró-labore uma vez.
4. Em **Lucros e dividendos dos sócios**, informe o beneficiário e quanto prevê distribuir. O QSA cadastrado pode ser reaproveitado, sem presumir participações ou residência fiscal.
5. Clique em **Comparar os três regimes**. A comparação distingue tributos da empresa, IR dos dividendos e total consolidado.
6. Se um imposto estiver pendente, abra **Atividade, impostos e particularidades**. Informe zero somente quando realmente não houver aquele tributo.

As previsões são mantidas ao navegar pelo Simples, salários, relatórios e projeções. São hipóteses de planejamento, não apuração fiscal definitiva. O fator R e as regras de abertura não usam um histórico fictício.

## Empresa por PDF e QSA

1. Abra **Empresas e sócios**.
2. Envie o cartão CNPJ em PDF com texto. O QSA, quando disponível, é um segundo PDF, pois normalmente não consta do cartão.
3. Clique em **Ler os documentos**.
4. Confira e corrija os campos e os sócios. Confirme o QSA somente se corresponder à empresa.
5. Marque a conferência e clique em **Salvar cadastro da empresa**. A empresa passa a ficar selecionada no menu lateral.
6. Se o CNPJ já existir, marque explicitamente a atualização do cadastro. Um cartão sem QSA não apaga sócios já registrados.

PDFs escaneados como imagem exigem OCR, ainda não disponível. Se o leiaute não for reconhecido, os campos ficam para conferência ou preenchimento manual. A leitura não consulta a Receita nem autentica o documento.

## Importar lançamentos

1. Abra **Contabilidade** e confira a empresa de destino.
2. Baixe o modelo de CSV e preencha Data, Debito, Credito, Valor e Historico.
3. Envie o arquivo. O formato brasileiro `1.234,56` é aceito, assim como datas `DD/MM/AAAA` e `AAAA-MM-DD`.
4. Confira a prévia. Datas, contas ou valores inválidos impedem a gravação do lote inteiro.
5. Confirme e importe. Ao repetir o arquivo, os lançamentos iguais são ignorados. Só permita iguais explicitamente quando forem operações distintas.

Os módulos originais de lançamentos manuais, DRE, balancete e balanço permanecem em **Ferramentas originais**, usando o mesmo banco de demonstração.

## Imprimir

Nos resultados, use **Baixar relatório em PDF**, **Baixar versão para impressão** ou abra **Imprimir agora** e clique em **Imprimir relatório** dentro do documento. O PDF pode ser aberto no navegador e impresso normalmente. O relatório comparativo também permite baixar a memória JSON com premissas e regras.

## Salários e férias

Em **Equipe e salários**, informe o salário individual e os dependentes para a simulação mensal de empregado. O total da equipe pode ser levado ao planejamento com um clique. O botão de férias abre o simulador preservado, com exportação de demonstrativos. Situações fora do recorte geral continuam exigindo conferência técnica.

## Projeções

**Projeção de 1 ano** aproveita o cenário e gera 12 meses financeiros, com a retenção projetada dos dividendos apresentada separadamente. A projeção tributária detalhada por trimestre continua em **Ferramentas técnicas**. Regras ainda não revisadas, incluindo 2027, ficam pendentes.

## Executar no computador

Baixe a branch `revisao-planejamento-tributario-v02` em **Code → Download ZIP** e extraia em uma pasta nova. É necessário Python 3.11 ou 3.12.

Windows:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run testar_planejamento.py
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run testar_planejamento.py
```

No Streamlit Community Cloud, o aplicativo de testes deve usar o repositório `MaxsuelContabilx/sistema-contabil-simples`, a branch `revisao-planejamento-tributario-v02` e `testar_planejamento.py` como arquivo principal. `app.py` também abre a nova plataforma.

O banco padrão é `maxsuel_demonstracao.db`. O banco e o CSV originais não são substituídos. Faça backup dos cadastros e lançamentos: o armazenamento local do Streamlit Community Cloud não garante persistência após reinicializações.

Testes:

```sh
python -m unittest discover -s tests -v
```

Leia `documentacao/VERSAO_03.md` para o escopo implementado, as fontes e as pendências.
