
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        unidade_medida as value_field,
        count(*) as n_records

    from "observatorio"."staging"."stg_anp_precos"
    group by unidade_medida

)

select *
from all_values
where value_field not in (
    'R$/litro','R$/m3'
)



  
  
      
    ) dbt_internal_test