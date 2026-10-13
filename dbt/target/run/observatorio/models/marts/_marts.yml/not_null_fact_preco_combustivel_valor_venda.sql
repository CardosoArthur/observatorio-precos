
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select valor_venda
from "observatorio"."marts"."fact_preco_combustivel"
where valor_venda is null



  
  
      
    ) dbt_internal_test