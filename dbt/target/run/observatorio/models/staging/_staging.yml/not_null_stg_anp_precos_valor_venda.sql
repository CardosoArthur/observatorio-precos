
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select valor_venda
from "observatorio"."staging"."stg_anp_precos"
where valor_venda is null



  
  
      
    ) dbt_internal_test