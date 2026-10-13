
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