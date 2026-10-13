{#- Grain: one price per (cnpj_revenda, produto, data_coleta). -#}
select
    cnpj_revenda,
    {{ surrogate_key(['produto']) }}                    as produto_key,
    {{ surrogate_key(['uf', 'municipio']) }}            as localidade_key,
    cast(strftime(data_coleta, '%Y%m%d') as integer)    as data_key,
    data_coleta,
    valor_venda,
    bandeira,
    source_group,
    n_registros_origem
from {{ ref('stg_anp_precos') }}
