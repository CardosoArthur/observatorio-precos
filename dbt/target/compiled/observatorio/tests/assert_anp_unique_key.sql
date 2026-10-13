-- Grain of stg_anp_precos: (cnpj_revenda, produto, data_coleta) must be unique.
select cnpj_revenda, produto, data_coleta, count(*) as n
from "observatorio"."staging"."stg_anp_precos"
group by 1, 2, 3
having count(*) > 1