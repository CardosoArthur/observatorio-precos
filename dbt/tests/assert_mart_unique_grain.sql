select mes_referencia, produto, uf, count(*) as n
from {{ ref('mart_preco_inflacao_mensal') }}
group by 1, 2, 3
having count(*) > 1
