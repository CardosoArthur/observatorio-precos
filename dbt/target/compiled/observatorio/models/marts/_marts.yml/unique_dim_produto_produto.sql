
    
    

select
    produto as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_produto"
where produto is not null
group by produto
having count(*) > 1


