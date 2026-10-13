
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select selic_meta_aa_media
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where selic_meta_aa_media is null



  
  
      
    ) dbt_internal_test