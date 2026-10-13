
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Grain of stg_anp_precos: (cnpj_revenda, produto, data_coleta) must be unique.
select cnpj_revenda, produto, data_coleta, count(*) as n
from "observatorio"."staging"."stg_anp_precos"
group by 1, 2, 3
having count(*) > 1
  
  
      
    ) dbt_internal_test