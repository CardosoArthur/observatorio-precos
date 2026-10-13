
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select preco_medio
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where preco_medio is null



  
  
      
    ) dbt_internal_test