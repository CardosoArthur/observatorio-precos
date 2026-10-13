{#- SGS series typed. Future dates are dropped (series 432 can carry them; ADR-006). -#}

select
    try_cast(serie_codigo as integer)                  as serie_codigo,
    serie_nome,
    try_strptime(trim(data), '%d/%m/%Y')::date         as data,
    try_cast(valor as double)                          as valor
from {{ source('raw', 'bcb_sgs') }}
where try_strptime(trim(data), '%d/%m/%Y')::date <= current_date
