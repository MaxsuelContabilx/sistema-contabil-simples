# Maxsuel — Planejamento tributário, versão 0.2 de revisão

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

`testar_planejamento.py` abre inicialmente a prévia interativa do novo visual. No topo, escolha **Sistema original** para acessar os simuladores e módulos antigos, ou **Cálculos em revisão** para conferir a versão técnica. A prévia não apura tributos. O sistema original nessa entrada usa o banco separado `maxsuel_demonstracao.db`; as fórmulas antigas ainda precisam de revisão. Os arquivos que já existem no repositório são preservados pela branch. Use uma pasta separada para testar. `app.py` contém a integração técnica anterior com o sistema completo e acessa o SQLite existente.

Veja `COMO_TESTAR.md` para o passo a passo no computador ou em um aplicativo separado no Streamlit Community Cloud.

## Validar o motor

```sh
python -m unittest discover -s tests -v
```

Leia `documentacao/REVISAO_TECNICA.md` para regras implementadas, pendências, limitações das fontes e diferenças entre os dois códigos originais. `documentacao/inventario_fontes.json` contém os hashes dos uploads. O HTML original está em `documentacao/referencia_interface_original.html` apenas como referência de interface e recursos; seus cálculos não devem ser usados como versão validada.

O menu comparativo abre os componentes em revisão. Não indica um vencedor enquanto a carga global e a elegibilidade não estiverem completas. As exportações JSON/HTML incluem as entradas do cálculo, fundamento e pendências. O módulo de folha permanece legado e não foi validado nesta etapa.
