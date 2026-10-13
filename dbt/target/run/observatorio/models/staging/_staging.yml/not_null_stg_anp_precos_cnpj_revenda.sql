
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select cnpj_revenda
from "observatorio"."staging"."stg_anp_precos"
where cnpj_revenda is null



  
  
      
    ) dbt_internal_test