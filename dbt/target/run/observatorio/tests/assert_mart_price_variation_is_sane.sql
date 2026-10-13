
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- A monthly move above +/-60% points to a data problem (a real fuel shock is far smaller).
select mes_referencia, produto, uf, variacao_preco_mom_pct
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where abs(variacao_preco_mom_pct) > 60
  
  
      
    ) dbt_internal_test