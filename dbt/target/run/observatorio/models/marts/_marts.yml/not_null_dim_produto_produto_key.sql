
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select produto_key
from "observatorio"."marts"."dim_produto"
where produto_key is null



  
  
      
    ) dbt_internal_test