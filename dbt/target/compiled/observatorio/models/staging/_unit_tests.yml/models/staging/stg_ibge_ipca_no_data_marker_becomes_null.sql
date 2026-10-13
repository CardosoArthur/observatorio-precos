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