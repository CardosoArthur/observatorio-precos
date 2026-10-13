
  
  create view "observatorio"."staging"."stg_bcb_sgs__dbt_tmp" as (
    select
    try_cast(serie_codigo as integer)                  as serie_codigo,
    serie_nome,
    try_strptime(trim(data), '%d/%m/%Y')::date         as data,
    try_cast(valor as double)                          as valor
from "observatorio"."raw"."bcb_sgs"
where try_strptime(trim(data), '%d/%m/%Y')::date <= current_date
  );
