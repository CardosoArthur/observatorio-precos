
    
    

with child as (
    select data_key as from_field
    from "observatorio"."marts"."fact_preco_combustivel"
    where data_key is not null
),

parent as (
    select data_key as to_field
    from "observatorio"."marts"."dim_data"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


