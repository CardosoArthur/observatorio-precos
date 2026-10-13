
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select variavel_codigo, mes_referencia, count(*) as n
from "observatorio"."staging"."stg_ibge_ipca"
group by 1, 2
having count(*) > 1
  
  
      
    ) dbt_internal_test