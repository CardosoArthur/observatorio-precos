
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mes_referencia
from "observatorio"."staging"."stg_ibge_ipca"
where mes_referencia is null



  
  
      
    ) dbt_internal_test