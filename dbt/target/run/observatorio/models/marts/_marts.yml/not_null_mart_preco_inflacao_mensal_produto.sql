
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select produto
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where produto is null



  
  
      
    ) dbt_internal_test