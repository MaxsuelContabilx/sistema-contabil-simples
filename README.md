# Maxsuel — Planejamento tributário, versão 0.5 de revisão

**Versão de testes com cenários financeiros condicionais; não homologada para apuração fiscal definitiva.**

Integra ao Streamlit um núcleo separado de cálculos para o recorte de 2026. A interface mostra limitações e bloqueia casos não contemplados. Esta versão é preparada para uma branch de testes; a publicação dessa branch não altera a `main` nem configura a hospedagem em produção.

Inclui projeção de 12 meses com sazonalidade, RBT12/FS12 móveis, apuração trimestral e saldos do Lucro Real. A aba de atualizações identifica versões e permite consultar memórias JSON antigas sem recalcular. Leia `documentacao/ATUALIZACOES.md` para cobertura, restrições e manutenção.

## Executar

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run testar_planejamento.py
```

`app.py` e `testar_planejamento.py` abrem a interface operacional com logo e cenário compartilhado. Use o menu lateral para planejamento, Simples, salários, contabilidade, projeções, relatórios e cadastro CNPJ/QSA. **Ferramentas originais** preserva os módulos anteriores; **Ferramentas técnicas** mantém as apurações detalhadas.

O banco padrão continua separado: `maxsuel_demonstracao.db`. O SQLite original e o CSV do repositório não são substituídos. Para um banco próprio, configure `MAXSUEL_DB_PATH` com um caminho gravável. Faça backup: o armazenamento local do Streamlit Community Cloud não garante persistência após reinicializações/reimplantações.

O cadastro lê PDFs com texto do cartão CNPJ e, opcionalmente, um QSA separado. Exige conferência antes de salvar e não presume participação societária ou residência fiscal. PDFs de imagem precisam de OCR, ainda não implementado. Os documentos enviados não são publicados no GitHub.

CSV contábil: datas e contas validadas, valores brasileiros, importação transacional e prevenção de duplicidade. Relatórios: PDF paginado e HTML com impressão no próprio documento. O planejamento distribui automaticamente o saldo de cada regime e calcula o IRRF por beneficiário. Inclui referência atual, projeção futura com CBS/IBS informados, menu organizado, tema claro/escuro e PJ × CLT. Projeções e apurações técnicas de componentes isolados não presumem saldo distribuível: sem o saldo completo, o IRRF permanece pendente. A apuração mínima anual dos sócios ainda está pendente. Veja `documentacao/VERSAO_04.md`.

Veja `COMO_TESTAR.md` para o passo a passo no computador ou em um aplicativo separado no Streamlit Community Cloud.

## Validar o motor

```sh
python -m unittest discover -s tests -v
```

Leia `documentacao/REVISAO_TECNICA.md` para regras implementadas, pendências, limitações das fontes e diferenças entre os dois códigos originais. `documentacao/inventario_fontes.json` contém os hashes dos uploads. O HTML original está em `documentacao/referencia_interface_original.html` apenas como referência de interface e recursos; seus cálculos não devem ser usados como versão validada.

O menu comparativo abre os componentes em revisão. Não indica um vencedor enquanto a carga global e a elegibilidade não estiverem completas. As exportações JSON/HTML incluem as entradas do cálculo, fundamento e pendências. O módulo de folha permanece legado e não foi validado nesta etapa.

A versão 0.5 mostra percentuais e bases de presunção, permite o histórico dos primeiros meses do Simples e destaca o melhor resultado mensal nos critérios informados, com pendências explícitas. Inclui memória temporal da Resolução CGSN 190/2026 para 2027, sem desbloquear indevidamente tabelas monetárias de 2027. Veja `documentacao/VERSAO_05.md`.
