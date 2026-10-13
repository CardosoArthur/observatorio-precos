select
    cnpj_revenda,
    md5(concat_ws('|', produto))                    as produto_key,
    md5(concat_ws('|', uf, municipio))            as localidade_key,
    cast(strftime(data_coleta, '%Y%m%d') as integer)    as data_key,
    data_coleta,
    valor_venda,
    bandeira,
    source_group,
    n_registros_origem
from "observatorio"."staging"."stg_anp_precos"