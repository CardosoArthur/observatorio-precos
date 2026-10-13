
    

    create  table
      "observatorio"."marts"."dim_localidade__dbt_tmp"
  
    
    as (
      select
    md5(concat_ws('|', uf, municipio))    as localidade_key,
    uf,
    municipio,
    min(regiao_sigla)                           as regiao_sigla
from "observatorio"."staging"."stg_anp_precos"
group by uf, municipio
    );
    
  