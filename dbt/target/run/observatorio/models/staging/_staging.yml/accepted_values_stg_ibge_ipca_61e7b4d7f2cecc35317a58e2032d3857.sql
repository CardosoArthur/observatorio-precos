
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        variavel_codigo as value_field,
        count(*) as n_records

    from "observatorio"."staging"."stg_ibge_ipca"
    group by variavel_codigo

)

select *
from all_values
where value_field not in (
    63,66,69,2265
)



  
  
      
    ) dbt_internal_test