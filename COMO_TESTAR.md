# Como testar a versão revisada

Esta é uma versão parcial para avaliação, com projeções anuais e regras tributárias em revisão. Não atualiza o sistema em produção nem homologa apurações fiscais.

## O que abre agora

A entrada `testar_planejamento.py` abre inicialmente a **Prévia do novo visual**, no mesmo aplicativo de testes. Use os menus da prévia para experimentar o preenchimento único e o fluxo de empresa em abertura. Os valores tributários não são calculados nessa prévia.

No topo da página há outras duas opções:

- **Sistema original:** recupera seu logo, a navegação e os simuladores originais de Simples, fator R, salários individuais, férias e contabilidade. Usa o banco separado `maxsuel_demonstracao.db`; as fórmulas antigas continuam identificadas como pendentes de revisão.
- **Cálculos em revisão:** abre a versão técnica disponibilizada anteriormente, com as limitações já documentadas.

Se você estava com o aplicativo aberto antes dessa atualização, recarregue a página depois que o Streamlit terminar de atualizar. O novo topo mostra as três opções acima.

## Baixar

1. Abra a branch `revisao-planejamento-tributario-v02` no GitHub.
2. Clique em **Code → Download ZIP**.
3. Extraia o ZIP em uma pasta nova do computador. Não extraia sobre a pasta usada em produção.

## Executar no computador

É necessário ter Python 3.11 ou 3.12 instalado. Abra um terminal na pasta extraída que contém `testar_planejamento.py`.

No Windows:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run testar_planejamento.py
```

No Linux ou macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run testar_planejamento.py
```

O navegador deve abrir o endereço local informado pelo Streamlit, normalmente `http://localhost:8501`. A prévia e os cálculos em revisão não abrem o SQLite contábil. A opção Sistema original usa exclusivamente o banco de demonstração separado.

## Alternativa: outro aplicativo no Streamlit Community Cloud

Se você usa esse serviço e quer testar pelo navegador, crie um aplicativo separado com:

- Repositório: `MaxsuelContabilx/sistema-contabil-simples`.
- Branch: `revisao-planejamento-tributario-v02`.
- Arquivo principal: `testar_planejamento.py`.
- Python: 3.11 ou 3.12.

Mantenha o aplicativo atual apontando para a branch e o arquivo que ele já utiliza. Criar a branch no GitHub não publica automaticamente esse aplicativo de teste.

## Primeiro teste simples

1. Abra **Simples Nacional**.
2. Informe RBT12 de R$ 600.000,00.
3. Na receita ordinária do Anexo I, informe R$ 50.000,00.
4. Confirme os requisitos indicados na tela somente se o cenário atender a eles.
5. O DAS parcial esperado é R$ 3.595,00, sem tratamentos especiais. Baixe a memória de cálculo em JSON ou HTML.

## Projeção de um ano

1. Abra **Projeção de 1 ano** e selecione 2026.
2. Informe as premissas iniciais e clique em **Preencher os 12 meses com estas premissas**.
3. Ajuste as receitas, custos e despesas de cada mês para representar sazonalidade.
4. Informe o histórico de receita e FS legal dos 12 meses anteriores, sem substituir informação ausente por média.
5. Preencha as bases contábeis de IRPJ/CSLL, os outros acréscimos do Presumido, os saldos iniciais e eventuais ajustes do Real. Informe zero explicitamente quando for o caso.
6. Confira os enquadramentos e clique em **Projetar os 12 meses**.

Se um componente estiver pendente, o sistema informa o motivo e não apresenta um total anual incompleto como se fosse definitivo. O total de DAS não equivale à soma de IRPJ/CSLL dos demais regimes; a carga global ainda não está concluída. As regras de 2027 permanecem bloqueadas até a conferência correspondente.

## Conferir testes automatizados

No ambiente Python com as dependências instaladas:

```sh
python -m unittest discover -s tests -v
```

Leia `documentacao/REVISAO_TECNICA.md` e `documentacao/ATUALIZACOES.md` para as limitações e o histórico das melhorias. Não incorpore a branch de testes à `main` apenas por conseguir abrir as telas.
