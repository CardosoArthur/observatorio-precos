
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        source_group as value_field,
        count(*) as n_records

    from "observatorio"."staging"."stg_anp_precos"
    group by source_group

)

select *
from all_values
where value_field not in (
    'mensal','semestral','ultimas_4_semanas'
)



  
  
      
    ) dbt_internal_test