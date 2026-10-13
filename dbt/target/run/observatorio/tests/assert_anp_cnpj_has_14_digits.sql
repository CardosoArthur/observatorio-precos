
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select * from "observatorio"."staging"."stg_anp_precos" where length(cnpj_revenda) <> 14
  
  
      
    ) dbt_internal_test