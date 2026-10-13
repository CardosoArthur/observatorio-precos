select * from {{ ref('stg_anp_precos') }} where length(cnpj_revenda) <> 14
