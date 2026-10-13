select variavel_codigo, mes_referencia, count(*) as n
from {{ ref('stg_ibge_ipca') }}
group by 1, 2
having count(*) > 1
