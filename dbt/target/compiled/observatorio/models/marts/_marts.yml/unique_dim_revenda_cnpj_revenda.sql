
    
    

select
    cnpj_revenda as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_revenda"
where cnpj_revenda is not null
group by cnpj_revenda
having count(*) > 1


