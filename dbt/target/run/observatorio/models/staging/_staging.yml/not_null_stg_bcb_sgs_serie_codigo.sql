
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select serie_codigo
from "observatorio"."staging"."stg_bcb_sgs"
where serie_codigo is null



  
  
      
    ) dbt_internal_test