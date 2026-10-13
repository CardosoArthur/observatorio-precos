select serie_codigo, data, count(*) as n
from "observatorio"."staging"."stg_bcb_sgs"
group by 1, 2
having count(*) > 1