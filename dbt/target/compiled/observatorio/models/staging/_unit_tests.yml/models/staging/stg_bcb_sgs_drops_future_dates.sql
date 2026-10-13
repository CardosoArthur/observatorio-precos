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