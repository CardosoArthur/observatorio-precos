
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select data_coleta
from "observatorio"."staging"."stg_anp_precos"
where data_coleta is null



  
  
      
    ) dbt_internal_test