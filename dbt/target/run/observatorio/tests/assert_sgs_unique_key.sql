
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select serie_codigo, data, count(*) as n
from "observatorio"."staging"."stg_bcb_sgs"
group by 1, 2
having count(*) > 1
  
  
      
    ) dbt_internal_test