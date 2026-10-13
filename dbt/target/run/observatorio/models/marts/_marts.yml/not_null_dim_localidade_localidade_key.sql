
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select localidade_key
from "observatorio"."marts"."dim_localidade"
where localidade_key is null



  
  
      
    ) dbt_internal_test