
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select localidade_key as from_field
    from "observatorio"."marts"."fact_preco_combustivel"
    where localidade_key is not null
),

parent as (
    select localidade_key as to_field
    from "observatorio"."marts"."dim_localidade"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test