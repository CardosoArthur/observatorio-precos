
    
    

select
    data as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_data"
where data is not null
group by data
having count(*) > 1


