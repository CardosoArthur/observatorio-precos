
    
    

with child as (
    select produto_key as from_field
    from "observatorio"."marts"."fact_preco_combustivel"
    where produto_key is not null
),

parent as (
    select produto_key as to_field
    from "observatorio"."marts"."dim_produto"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


