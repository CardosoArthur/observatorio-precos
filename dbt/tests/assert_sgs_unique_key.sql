select serie_codigo, data, count(*) as n
from {{ ref('stg_bcb_sgs') }}
group by 1, 2
having count(*) > 1
