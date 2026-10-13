
    
    

select
    produto_key as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_produto"
where produto_key is not null
group by produto_key
having count(*) > 1


