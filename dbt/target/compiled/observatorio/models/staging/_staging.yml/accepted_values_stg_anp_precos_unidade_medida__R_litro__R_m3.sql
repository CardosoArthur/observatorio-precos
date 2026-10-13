
    
    

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


