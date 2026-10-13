
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select data_key
from "observatorio"."marts"."fact_preco_combustivel"
where data_key is null



  
  
      
    ) dbt_internal_test