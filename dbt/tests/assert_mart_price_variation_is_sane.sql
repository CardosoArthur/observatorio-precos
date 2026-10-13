-- A monthly move above +/-60% points to a data problem (a real fuel shock is far smaller).
select mes_referencia, produto, uf, variacao_preco_mom_pct
from {{ ref('mart_preco_inflacao_mensal') }}
where abs(variacao_preco_mom_pct) > 60
