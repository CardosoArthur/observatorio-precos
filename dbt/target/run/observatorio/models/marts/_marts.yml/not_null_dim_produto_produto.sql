
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select produto
from "observatorio"."marts"."dim_produto"
where produto is null



  
  
      
    ) dbt_internal_test