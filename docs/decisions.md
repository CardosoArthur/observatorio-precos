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
