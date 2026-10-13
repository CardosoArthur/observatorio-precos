
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select cnpj_revenda, produto_key, data_key, count(*) as n
from "observatorio"."marts"."fact_preco_combustivel"
group by 1, 2, 3
having count(*) > 1
  
  
      
    ) dbt_internal_test