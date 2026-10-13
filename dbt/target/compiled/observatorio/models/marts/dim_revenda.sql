select
    cnpj_revenda,
    arg_max(revenda, data_coleta)   as revenda,
    arg_max(bandeira, data_coleta)  as bandeira_atual,
    arg_max(uf, data_coleta)        as uf,
    arg_max(municipio, data_coleta) as municipio,
    arg_max(bairro, data_coleta)    as bairro,
    arg_max(cep, data_coleta)       as cep,
    min(data_coleta)                as primeira_coleta,
    max(data_coleta)                as ultima_coleta,
    count(*)                        as n_registros
from "observatorio"."staging"."stg_anp_precos"
group by cnpj_revenda