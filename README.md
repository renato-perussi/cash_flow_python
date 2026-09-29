# Cash Flow — Painel de Fluxo de Caixa

Aplicação web para acompanhamento da liquidez, das receitas, dos custos e do risco de previsão da operação. O painel consolida lançamentos previstos e realizados em uma visão única, com filtros por período, tipo, categoria, centro de custo, status e recorrência.

Este documento atende a dois públicos: a Gestão, que encontra nas primeiras seções a descrição funcional do produto, e a equipe técnica, que encontra nas seções seguintes o contrato de dados, a arquitetura e os comandos de operação.

## 1. Visão para a Gestão

### O que o painel responde

- Qual é o saldo líquido do período (entradas menos saídas)?
- Quanto entrou e quanto saiu no período selecionado?
- Qual é a cobertura prevista, isto é, quanto do que está a pagar está coberto pelo que está a receber?
- Como o saldo evolui dia a dia e qual é o saldo acumulado?
- Quais categorias geram mais receita e quais centros de custo concentram mais despesa?
- Quanto do movimento já foi realizado (pago ou recebido) e quanto permanece como previsão?
- Qual é o peso das despesas recorrentes frente às pontuais?

### Visões disponíveis

| Visão | Finalidade |
|---|---|
| Saldo Líquido | Resultado do período: entradas menos saídas. |
| Total de Entradas | Soma de todas as entradas do período filtrado. |
| Total de Saídas | Soma de todas as saídas do período filtrado. |
| Cobertura Prevista | Razão entre valores previstos a receber e valores previstos a pagar. Acima de 1,00x indica cobertura; abaixo, atenção ao caixa. |
| Fluxo Líquido Diário | Barras diárias com o resultado de cada dia. |
| Saldo Acumulado | Evolução do saldo ao longo do período. |
| Entradas por Categoria | Comparativo das origens de receita. |
| Saídas por Centro de Custo | Comparativo dos centros que mais consomem recursos. |
| Realizado vs. Previsto | Separação entre o que já ocorreu (Pago, Recebido) e o que é expectativa (Previsto). |
| Recorrente vs. Pontual | Distinção entre compromissos contínuos e movimentos eventuais. |

### Filtros

Períodos de 7, 14, 30, 60, 90 ou 360 dias, ancorados na data prevista mais recente do conjunto de dados. Filtros adicionais por tipo (Entrada, Saída), categoria, centro de custo, status e recorrência. A exportação gera um arquivo CSV filtrado com o mesmo formato do original, pronto para reimportação ou análise em planilha.

### Observações de negócio

- Valores previstos ainda não ocorreram: a data de realização encontra-se vazia nesses lançamentos, o que é esperado e não representa dado faltante.
- Linhas com data prevista inválida são excluídas das métricas, com aviso exibido na interface, de modo que os totais dos cartões permanecem consistentes com os gráficos diários.
- Quando não há valores previstos a pagar, a cobertura prevista é apresentada como indisponível; quando não há previsão em nenhum sentido, é apresentada como 0,00x.

## 2. Arquitetura técnica

```
app.py                  Ponto de entrada Streamlit: carregamento, filtros, cartões e composição dos gráficos.
cashflow/data.py        Carregamento do CSV, validações e filtragem (load_cashflow, with_signed_value, filter_cashflow, group_daily_net).
cashflow/metrics.py     Agregações de negócio (build_summary, daily_flow).
cashflow/charts.py      Gráficos Plotly (fluxo diário, saldo acumulado, categorias, centros de custo, realizado vs. previsto, recorrência).
data/cash_flow.csv      Conjunto de dados canônico: 360 lançamentos, de 2025-10-06 a 2026-09-30.
tests/                  Testes por módulo (test_data, test_metrics, test_charts, test_app).
```

Ordem obrigatória do pipeline: `load_cashflow` seguido de `with_signed_value` antes de qualquer agregação diária, cálculo de fluxo ou gráfico que dependa de `signed_value`. As funções `group_daily_net`, `daily_net_flow`, `cumulative_balance` e `metrics.daily_flow` exigem a coluna `signed_value` e sinalizam sua ausência com `KeyError`. O resumo `build_summary` opera sobre a coluna `valor` (entradas menos saídas) e não exige `signed_value`, embora exija `valor` válido.

Tratamento de erros: `ValueError` representa falha apresentável ao usuário (a interface exibe a mensagem e interrompe a renderização); `KeyError` indica ausência de coluna estrutural (`tipo`, `signed_value`). Validações de colunas filtráveis utilizam `require_columns`, que converte ausência em `ValueError` para que a interface a capture corretamente.

A função `get_frame` é decorada com `st.cache_data` sem expiração, pois o conjunto de dados é estático em disco. Após qualquer alteração no CSV, invocar `get_frame.clear()`.

## 3. Contrato de dados

Arquivo `data/cash_flow.csv`, com separador `;` e codificação `utf-8-sig` (com ou sem BOM):

```
pd.read_csv(path, sep=";", encoding="utf-8-sig")
```

Colunas: `id_lancamento`, `data_prevista`, `data_realizada`, `tipo`, `categoria`, `descricao`, `centro_custo`, `status`, `valor`, `recorrente`.

Regras:

- `valor` é sempre numérico, finito e estritamente positivo (`> 0`), com ponto decimal. O sinal econômico deriva de `tipo` (`Entrada` soma, `Saída` subtrai) por meio de `with_signed_value`, que materializa a coluna `signed_value`.
- `tipo` restrito a `Entrada` e `Saída`; qualquer outro valor ou ausência implica erro de validação.
- Realizado corresponde a `status` em (`Pago`, `Recebido`); previsão corresponde a `Previsto`. Lançamentos previstos possuem `data_realizada` vazia por definição.
- Textos em português com acentuação (`Saída`, `Não`, `Previsto`) são preservados em dados, código e interface.
- Datas são interpretadas com `errors="coerce"`: valores inválidos tornam-se `NaT`. Linhas com `data_prevista` ausente são descartadas das agregações com registro de aviso, preservando a invariante de que o saldo do resumo equivale à soma do fluxo diário.
- A janela temporal filtra exclusivamente `data_prevista`, nunca `data_realizada`. A âncora do período é `max(data_prevista) - dias + 1`. Filtro `None` desativa a dimensão; lista vazia retorna conjunto vazio; intervalo com início posterior ao fim retorna vazio por definição, sem exceção.
- Exportação mantém `sep=";"` e codificação `utf-8-sig` para permitir reimportação sem perda.

## 4. Métricas — definição formal

`build_summary` retorna:

- `total_inflows`: soma de `valor` onde `tipo` é `Entrada`.
- `total_outflows`: soma de `valor` onde `tipo` é `Saída`.
- `net_balance`: `total_inflows - total_outflows`.
- `forecast_coverage`: `forecast_in / forecast_out`, onde ambos se restringem a `status` igual a `Previsto`. Retorna infinito quando há previsão de entrada sem previsão de saída (apresentado como indisponível na interface) e `0.0` quando não há previsão em nenhum sentido.
- `realized_share`: participação em volume do realizado (`Pago`, `Recebido`) sobre o total movimentado.
- `recurring_burn`: soma de `valor` onde `tipo` é `Saída` e `recorrente` é `Sim`.

`daily_flow` e `group_daily_net` agregam `signed_value` por `data_prevista`, ordenados cronologicamente; `daily_flow` acrescenta a coluna `cumulative` com a soma acumulada. Todos os gráficos são seguros para conjuntos vazios: um filtro sem resultados produz figuras vazias, sem exceção.

## 5. Instalação e execução

Pré-requisitos: Python 3.12. Executar sempre a partir da raiz do repositório, pois o caminho dos dados é relativo (`data/cash_flow.csv`).

```bash
.venv/bin/pip install -r requirements.txt -r requirements_dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py
```

Comandos de apoio:

```bash
.venv/bin/python -m pytest tests/test_data.py -q   # um único módulo de teste; acrescentar -k nome para um caso específico
.venv/bin/ruff check .                             # verificação estática (sem configuração dedicada; estado atual sem ocorrências)
.venv/bin/black --check .                          # conferência de formatação (o repositório não está integralmente formatado; evitar reformatação em massa)
```

Observação: invocar `pytest` diretamente pelo binário omite o diretório corrente do caminho de importação; utilizar `python -m pytest` corrige a resolução dos módulos.

Dependências principais: `streamlit==1.64.0`, `pandas==3.0.6`, `plotly==7.1.0`, `numpy==2.5.3`, `openpyxl==3.1.5`. Dependências de desenvolvimento: `pytest`, `pytest-cov`, `ruff`, `black` (versões em `requirements_dev.txt`).

## 6. Estrutura de apoio

- `DESIGN.md` é a referência de identidade visual: acento único `#0066cc` (`#2997ff` em superfícies escuras), corpo de 17px, botões em pílula e uma única sombra reservada ao produto. Alterações de interface devem seguir esse documento.
- Diretório `outputs/` (ignorado pelo controle de versão) destina-se a relatórios e exportações gerados; não deve ser versionado, assim como `.venv/`.
- Novos arquivos de código devem permanecer na raiz ou no pacote `cashflow/`, mantendo a estrutura atual sem subdivisões adicionais.
