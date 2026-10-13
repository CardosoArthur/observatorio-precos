
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Staging collapses overlaps and duplicates but must keep every distinct natural key of raw.
with raw_keys as (

    select count(*) as n
    from (
        select distinct
            regexp_replace(cnpj_revenda, '[^0-9]', '', 'g')       as cnpj_revenda,
            upper(trim(produto))                                  as produto,
            try_strptime(trim(data_coleta), '%d/%m/%Y')::date     as data_coleta
        from "observatorio"."raw"."anp_precos"
    )

),

staged as (

    select count(*) as n from "observatorio"."staging"."stg_anp_precos"

)

select raw_keys.n as raw_distinct_keys, staged.n as staged_rows
from raw_keys
cross join staged
where raw_keys.n <> staged.n
  
  
      
    ) dbt_internal_test