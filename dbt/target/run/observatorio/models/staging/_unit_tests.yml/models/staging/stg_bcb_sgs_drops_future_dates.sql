
    -- Build actual result given inputs
with dbt_internal_unit_test_actual as (
  select
    "serie_codigo","data","valor", 'actual' as "actual_or_expected"
  from (
    with __dbt__cte__raw__bcb_sgs as (

-- Fixture for bcb_sgs
select 
    
    cast('432' as character varying)
 as "serie_codigo", 
    
    cast('selic_meta' as character varying)
 as "serie_nome", 
    
    cast('02/01/2022' as character varying)
 as "data", 
    
    cast('9.25' as character varying)
 as "valor", cast(null as character varying(256)) as "_source_key", cast(null as TIMESTAMP) as "_ingested_at"
union all
select 
    
    cast('432' as character varying)
 as "serie_codigo", 
    
    cast('selic_meta' as character varying)
 as "serie_nome", 
    
    cast('02/01/2999' as character varying)
 as "data", 
    
    cast('9.25' as character varying)
 as "valor", cast(null as character varying(256)) as "_source_key", cast(null as TIMESTAMP) as "_ingested_at"
) select
    try_cast(serie_codigo as integer)                  as serie_codigo,
    serie_nome,
    try_strptime(trim(data), '%d/%m/%Y')::date         as data,
    try_cast(valor as double)                          as valor
from __dbt__cte__raw__bcb_sgs
where try_strptime(trim(data), '%d/%m/%Y')::date <= current_date
  ) _dbt_internal_unit_test_actual
),
-- Build expected result
dbt_internal_unit_test_expected as (
  select
    "serie_codigo", "data", "valor", 'expected' as "actual_or_expected"
  from (
    select 
    
    cast(432 as INTEGER)
 as "serie_codigo", 
    
    cast('2022-01-02' as DATE)
 as "data", 
    
    cast(9.25 as DOUBLE)
 as "valor"
  ) _dbt_internal_unit_test_expected
)
-- Union actual and expected results
select * from dbt_internal_unit_test_actual
union all
select * from dbt_internal_unit_test_expected