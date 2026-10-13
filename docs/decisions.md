# Decisões técnicas

Registro das decisões do projeto, com contexto e consequências. Datas no formato AAAA-MM-DD.

## ADR-001: DuckDB local como data warehouse (2026-10-12)

**Contexto.** O objetivo é zero custo e nenhuma dependência de cartão. O BigQuery em modo
sandbox não suporta DML (`INSERT`, `UPDATE`, `DELETE`, `MERGE`) e expira tabelas em 60 dias
(documentação do Google consultada em 2026-10-12). Isso inviabiliza carga idempotente por
`DELETE` e modelos incrementais no dbt, e faria os dados sumirem. Ativar o faturamento
exigiria cartão.

**Decisão.** Usar DuckDB em arquivo local (`warehouse/observatorio.duckdb`), com `dbt-duckdb`
nas próximas etapas.

**Consequências.** Custo zero, DML completo e dbt incremental disponíveis. O DuckDB aceita um
processo escritor por vez, então as tasks de orquestração que escrevem no banco devem rodar em
sequência. Não há componente em nuvem; uma cópia no MotherDuck pode ser avaliada depois.

## ADR-002: camada `raw` com tudo em texto e metadados de carga (2026-10-12)

**Decisão.** `raw.anp_precos` guarda todas as colunas como `VARCHAR`, exatamente como a ANP
publica, mais três colunas de linhagem: `_source_file`, `_source_group` e `_ingested_at`.
Cada carga grava uma linha em `raw._load_metadata` (arquivo, SHA-256, tamanho, linhas lidas,
descartadas e carregadas, status, erro, duração).

**Por quê.** Evita falhas de carga por tipo, preserva o original e permite reprocessar sem
baixar de novo. Tipagem e limpeza ficam no staging (dbt).

## ADR-003: idempotência por arquivo (2026-10-12)

**Decisão.** Cada arquivo é substituído de forma atômica: dentro de uma transação, apaga as
linhas do mesmo `_source_file` e insere as novas. Um arquivo com SHA-256 igual ao da última carga
bem-sucedida (e com as linhas ainda presentes) é pulado. `--force` recarrega tudo. Um arquivo com
erro não impede os demais e fica registrado como `failed` nos metadados.

**Por quê.** Rodar duas vezes não duplica dados. O arquivo das quatro últimas semanas muda toda
semana com o mesmo nome; o SHA-256 diferente faz o loader substituir apenas as linhas dele.

## ADR-004: linhas totalmente vazias são descartadas na carga (2026-10-12)

O arquivo do 1º semestre de 2025 traz 9.114 linhas completamente vazias no final (probe de
2026-10-12). Elas não têm informação e são descartadas no loader; a contagem fica registrada em
`rows_dropped_empty`. Linhas com qualquer campo preenchido são mantidas.

## ADR-005: sobreposição e duplicidade tratadas no staging (2026-10-12)

**Fatos verificados no probe (2026-10-12).**
- O mensal de setembro/2026 e o arquivo das quatro últimas semanas se sobrepõem em 48.899
  chaves (CNPJ, produto, data da coleta, entre 14 e 30/09/2026), com preços idênticos.
- Há 20 grupos de chave repetida dentro de um mesmo arquivo (1S/2024 e 1S/2026); 4 deles têm
  preços diferentes.

**Decisão.** O `raw` mantém tudo o que cada arquivo entregou (inclusive a sobreposição). No
staging: em duplicidade entre arquivos, o mensal prevalece sobre o de quatro semanas; dentro do
mesmo arquivo, usar a média do preço por chave.

## ADR-006: API sources loaded per series, raw keeps what the API serves

- **Context:** SGS (3 series) and SIDRA (IPCA, table 7060) have no files, so the ANP per-file idempotency does not apply. The local probe (2026-10-12) showed SGS series 432 (Selic target) returning dates after today (02-04/11/2026, all 13.75).
- **Decision:** the unit of load is the *source key* (`sgs/<code>`, `sidra/7060`). Each key is replaced in one transaction (DELETE + INSERT + metadata) and skipped if the payload SHA-256 is unchanged. Empty payloads fail without deleting existing rows. SGS history is fetched in ~5-year windows; HTTP uses retry with exponential backoff. Raw stays all VARCHAR.
- **Data-quality rule:** series 432 may carry future dates; dbt staging must filter `data <= current_date`. The cause of those dates is not yet confirmed.
- **Consequence:** one failing series does not block the others; the run exits with code 1 if anything failed.

## ADR-007: dbt-duckdb staging layer

- **Context:** raw is all VARCHAR and keeps the overlaps and format quirks of the sources (ADR-002, ADR-005).
- **Decision:** `dbt-duckdb` with one schema per layer (`staging`, later `marts`) through a `generate_schema_name` override. `profiles.yml` lives in `dbt/`, has no credentials and reads `DUCKDB_PATH`. No external dbt packages: extra checks are singular SQL tests in `dbt/tests/`.
- **Staging rules:**
  - ANP: types parsed with `try_*`; CNPJ reduced to digits; unit standardised (`R$/litro`, `R$/m3`); brand `VIBRA ENERGIA` mapped to `VIBRA`; one row per (cnpj_revenda, produto, data_coleta). Source priority `mensal > semestral > ultimas_4_semanas`; repeated keys inside the winning group are averaged. `stg_anp_precos` is a table because it is the large model.
  - SGS: typed; rows with `data > current_date` dropped (ADR-006).
  - IPCA: `mes_referencia` as a date; SIDRA's `...` marker (no data) becomes NULL. Variable 2265 (12-month change) has no value for 202001-202011 (11 rows) because the series starts in 2020-01.
- **Evidence (copy of the real warehouse, 2026-10-13):** 4,227,065 raw rows -> 4,178,146 staged. The 48,919 removed rows are the 48,899 cross-file overlaps plus 20 in-file duplicates found by the probe. 23 dbt tests pass.
- **Consequence:** brand harmonisation covers only the documented VIBRA case; other possible variants (e.g. ALE vs ALESAT) are left as delivered because the equivalence is not confirmed.

## ADR-008: star schema and monthly mart

- **Decision:** `marts` schema with `dim_data`, `dim_produto`, `dim_localidade` (uf, municipio), `dim_revenda` (latest attributes per CNPJ), `fact_preco_combustivel` (grain: cnpj_revenda, produto, data_coleta) and `mart_preco_inflacao_mensal` (grain: mes_referencia, produto, uf). Surrogate keys are md5 hashes built by a local macro (no external dbt packages).
- **Mart metrics:** simple average price of all observations in the month; month-over-month and 12-month price change; monthly, year-to-date and 12-month IPCA; average Selic target (series 432, % per year); average USD/BRL sell rate (series 1).
- **Evidence (copy of the real warehouse, 2026-10-13):** fact 4,178,146 rows (same as staging), 18,172 stations, 465 municipalities, 6 products; mart 8,833 rows over 58 months (2022-01 to 2026-10) and 27 states. 62 dbt tests pass, including a reconciliation test (mart observations = fact rows).
- **Known limitations:**
  - The latest month is partial (see `n_dias_coleta`) and has no IPCA until IBGE publishes it.
  - The price is not weighted by station volume; ANP collects a sample of stations.
  - 241 of the 8,833 mart rows have fewer than 10 observations (minimum 1); the largest monthly price moves come from such thin cells (for example 23.8% for aditivada gasoline in AP with 1 observation). Dashboards must filter by `n_observacoes`.
