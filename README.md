# Maxsuel — Planejamento tributário, versão 0.3 de revisão

**Cópia de desenvolvimento local, ainda sem comparação global validada.**

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

CSV contábil: datas e contas validadas, valores brasileiros, importação transacional e prevenção de duplicidade. Relatórios: PDF paginado e HTML com impressão no próprio documento. O IRRF dos dividendos é apresentado nos cenários, anexos, projeções e subtotais consolidados; a apuração mínima anual dos sócios ainda está pendente.

Veja `COMO_TESTAR.md` para o passo a passo no computador ou em um aplicativo separado no Streamlit Community Cloud.

## Validar o motor

```sh
python -m unittest discover -s tests -v
```

Leia `documentacao/REVISAO_TECNICA.md` para regras implementadas, pendências, limitações das fontes e diferenças entre os dois códigos originais. `documentacao/inventario_fontes.json` contém os hashes dos uploads. O HTML original está em `documentacao/referencia_interface_original.html` apenas como referência de interface e recursos; seus cálculos não devem ser usados como versão validada.

O menu comparativo abre os componentes em revisão. Não indica um vencedor enquanto a carga global e a elegibilidade não estiverem completas. As exportações JSON/HTML incluem as entradas do cálculo, fundamento e pendências. O módulo de folha permanece legado e não foi validado nesta etapa.
