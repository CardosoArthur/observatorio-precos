
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select usd_brl_venda_medio
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where usd_brl_venda_medio is null



  
  
      
    ) dbt_internal_test