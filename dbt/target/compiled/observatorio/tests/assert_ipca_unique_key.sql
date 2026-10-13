select variavel_codigo, mes_referencia, count(*) as n
from "observatorio"."staging"."stg_ibge_ipca"
group by 1, 2
having count(*) > 1