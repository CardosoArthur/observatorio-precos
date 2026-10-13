
    -- Build actual result given inputs
with dbt_internal_unit_test_actual as (
  select
    "variavel_codigo","mes_referencia","unidade_medida","valor", 'actual' as "actual_or_expected"
  from (
    with __dbt__cte__raw__ibge_ipca as (

-- Fixture for ibge_ipca
select 
    
    cast('2265' as character varying)
 as "variavel_codigo", cast(null as character varying(256)) as "variavel_nome", 
    
    cast('202001' as character varying)
 as "periodo_codigo", cast(null as character varying(256)) as "periodo_nome", cast(null as character varying(256)) as "classificacao_codigo", cast(null as character varying(256)) as "classificacao_nome", 
    
    cast('' as character varying)
 as "unidade_medida", 
    
    cast('...' as character varying)
 as "valor", cast(null as character varying(256)) as "_source_key", cast(null as TIMESTAMP) as "_ingested_at"
union all
select 
    
    cast('2265' as character varying)
 as "variavel_codigo", cast(null as character varying(256)) as "variavel_nome", 
    
    cast('202012' as character varying)
 as "periodo_codigo", cast(null as character varying(256)) as "periodo_nome", cast(null as character varying(256)) as "classificacao_codigo", cast(null as character varying(256)) as "classificacao_nome", 
    
    cast('%' as character varying)
 as "unidade_medida", 
    
    cast('4.52' as character varying)
 as "valor", cast(null as character varying(256)) as "_source_key", cast(null as TIMESTAMP) as "_ingested_at"
) select
    try_cast(variavel_codigo as integer)                                 as variavel_codigo,
    variavel_nome,
    strptime(periodo_codigo || '01', '%Y%m%d')::date                     as mes_referencia,
    nullif(trim(unidade_medida), '')                                     as unidade_medida,
    try_cast(valor as double)                                            as valor
from __dbt__cte__raw__ibge_ipca
  ) _dbt_internal_unit_test_actual
),
-- Build expected result
dbt_internal_unit_test_expected as (
  select
    "variavel_codigo", "mes_referencia", "unidade_medida", "valor", 'expected' as "actual_or_expected"
  from (
    select 
    
    cast(2265 as INTEGER)
 as "variavel_codigo", 
    
    cast('2020-12-01' as DATE)
 as "mes_referencia", 
    
    cast('%' as character varying)
 as "unidade_medida", 
    
    cast(4.52 as DOUBLE)
 as "valor"
union all
select 
    
    cast(2265 as INTEGER)
 as "variavel_codigo", 
    
    cast('2020-01-01' as DATE)
 as "mes_referencia", 
    
    cast(null as character varying(256))
 as "unidade_medida", 
    
    cast(null as DOUBLE)
 as "valor"
  ) _dbt_internal_unit_test_expected
)
-- Union actual and expected results
select * from dbt_internal_unit_test_actual
union all
select * from dbt_internal_unit_test_expected