# Observatório de Preços e Inflação (Brasil)

> **Status: em andamento (etapa S5, qualidade e documentação: concluída).** Este README cresce a cada etapa.

Pipeline ELT com dados públicos para analisar como o preço dos combustíveis ao
consumidor se relaciona com inflação (IPCA), Selic e câmbio.

**Fontes:** ANP (preços de revenda), IBGE SIDRA (IPCA) e Banco Central SGS (Selic e câmbio).
**Stack:** Python, DuckDB, dbt, Airflow (ou Kestra), Docker, GitHub Actions.

## O que já existe

| Etapa | Entrega | Status |
| --- | --- | --- |
| S3 | Loaders da ANP, SIDRA e SGS para DuckDB (camada `raw`), com testes | Pronto |
| S4 | dbt: camada `staging` (tipagem, limpeza, deduplicação) com testes | Pronto |
| S4 | dbt: dimensões, fato e mart mensal (preço x IPCA x Selic x câmbio) | Pronto |
| S5 | Testes de qualidade (dados e unitários), staging incremental, freshness e docs | Pronto |
| S6 | Orquestração em Docker | Pendente |
| S7 | CI, diagrama e dashboard | Pendente |

## Como rodar a ingestão da ANP

Requer Python 3.10 ou superior. Os CSVs da ANP não ficam no Git: baixe-os da
[página de dados abertos da ANP](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis)
e organize assim:

```
data/raw/anp/
├── semestral/           # CSVs semestrais (descompactados dos ZIPs)
├── mensal/              # CSVs mensais
└── ultimas_4_semanas/   # CSVs das quatro últimas semanas
```

Em seguida (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
python -m ingestion anp
```

Para as APIs: `python -m ingestion sgs`, `python -m ingestion sidra` ou
`python -m ingestion all` (ANP + SGS + SIDRA, em sequência: o DuckDB aceita um
escritor por vez).

O banco é criado em `warehouse/observatorio.duckdb` (ignorado pelo Git). Rodar o
comando de novo não duplica dados: arquivos inalterados são pulados, e `--force`
recarrega todos.

## Como rodar o dbt

Na raiz do repositório, com a venv ativa e o `raw` já carregado:

```powershell
dbt build --project-dir dbt --profiles-dir dbt
```

Cria os schemas `staging` e `marts` (dimensões, fato e mart mensal) e roda os testes
(de dados e unitários). Comandos úteis:

```powershell
dbt build --full-refresh --project-dir dbt --profiles-dir dbt   # reconstrói tudo (use após mudar a lógica do staging)
dbt source freshness --project-dir dbt --profiles-dir dbt       # confere se as fontes estão atualizadas
dbt docs generate --project-dir dbt --profiles-dir dbt          # gera a documentação
dbt docs serve --project-dir dbt --profiles-dir dbt             # abre o catálogo e o grafo de linhagem
```

O `stg_anp_precos` é incremental: depois de carregar um arquivo novo no `raw`, o dbt
recalcula só as chaves afetadas. Se um arquivo for **removido** do `raw`, use `--full-refresh`. O caminho do banco
vem de `DUCKDB_PATH` (padrão `warehouse/observatorio.duckdb`).

## Estrutura

```
ingestion/    # loaders Python (anp, sgs, sidra, cli) e testes
dbt/          # projeto dbt: models/staging, tests, macros, profiles.yml
scripts/      # probe_sources.py (cobertura das fontes) e check_raw.py (sanidade do raw)
docs/         # decisions.md: decisões técnicas e justificativas
data/         # dados brutos (fora do Git)
warehouse/    # arquivo DuckDB (fora do Git)
```

## Limitações conhecidas

- Os preços da ANP vêm de uma pesquisa semanal por **amostra** de postos, não de um censo.
- A frequência de atualização depende de cada fonte.
