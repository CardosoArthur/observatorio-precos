
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select produto
from "observatorio"."staging"."stg_anp_precos"
where produto is null



  
  
      
    ) dbt_internal_test