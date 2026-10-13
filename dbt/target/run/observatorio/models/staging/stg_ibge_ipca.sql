
  
  create view "observatorio"."staging"."stg_ibge_ipca__dbt_tmp" as (
    select
    try_cast(variavel_codigo as integer)                                 as variavel_codigo,
    variavel_nome,
    strptime(periodo_codigo || '01', '%Y%m%d')::date                     as mes_referencia,
    nullif(trim(unidade_medida), '')                                     as unidade_medida,
    try_cast(valor as double)                                            as valor
from "observatorio"."raw"."ibge_ipca"
  );
