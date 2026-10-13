
    
    

select
    localidade_key as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_localidade"
where localidade_key is not null
group by localidade_key
having count(*) > 1


