
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Wide sanity bounds that still catch scale errors (e.g. a rate in percent vs fraction).
select mes_referencia, produto, uf, ipca_mensal_pct, ipca_12m_pct, selic_meta_aa_media, usd_brl_venda_medio
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where selic_meta_aa_media not between 0 and 40
   or usd_brl_venda_medio not between 1 and 15
   or ipca_mensal_pct not between -3 and 5
   or ipca_12m_pct not between -3 and 25
  
  
      
    ) dbt_internal_test