
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select mes_referencia, produto, uf, count(*) as n
from "observatorio"."marts"."mart_preco_inflacao_mensal"
group by 1, 2, 3
having count(*) > 1
  
  
      
    ) dbt_internal_test