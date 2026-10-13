
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- The mart must not lose or invent observations: totals must match the fact table.
select m.total as mart_rows, f.total as fact_rows
from (select sum(n_observacoes) as total from "observatorio"."marts"."mart_preco_inflacao_mensal") as m
cross join (select count(*) as total from "observatorio"."marts"."fact_preco_combustivel") as f
where m.total <> f.total
  
  
      
    ) dbt_internal_test