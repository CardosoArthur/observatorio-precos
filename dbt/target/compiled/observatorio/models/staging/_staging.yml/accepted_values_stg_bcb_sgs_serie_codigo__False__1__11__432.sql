
    
    

with all_values as (

    select
        serie_codigo as value_field,
        count(*) as n_records

    from "observatorio"."staging"."stg_bcb_sgs"
    group by serie_codigo

)

select *
from all_values
where value_field not in (
    1,11,432
)


