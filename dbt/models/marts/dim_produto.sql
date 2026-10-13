select
    {{ surrogate_key(['produto']) }}    as produto_key,
    produto,
    case
        when produto like 'GASOLINA%' then 'GASOLINA'
        when produto like 'DIESEL%'   then 'DIESEL'
        else produto
    end                                 as familia,
    min(unidade_medida)                 as unidade_medida
from {{ ref('stg_anp_precos') }}
group by produto
