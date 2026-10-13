-- Every month up to the last IPCA published by IBGE must carry the monthly IPCA.
select mes_referencia, produto, uf
from "observatorio"."marts"."mart_preco_inflacao_mensal"
where mes_referencia <= (select max(mes_referencia) from "observatorio"."staging"."stg_ibge_ipca")
  and ipca_mensal_pct is null