{#- Grain: (uf, municipio). The same municipality name can exist in different states. -#}
select
    {{ surrogate_key(['uf', 'municipio']) }}    as localidade_key,
    uf,
    municipio,
    min(regiao_sigla)                           as regiao_sigla
from {{ ref('stg_anp_precos') }}
group by uf, municipio
