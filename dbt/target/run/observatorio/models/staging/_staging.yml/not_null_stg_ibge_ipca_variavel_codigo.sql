
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select variavel_codigo
from "observatorio"."staging"."stg_ibge_ipca"
where variavel_codigo is null



  
  
      
    ) dbt_internal_test