
    

    create  table
      "observatorio"."marts"."dim_produto__dbt_tmp"
  
    
    as (
      select
    md5(concat_ws('|', produto))    as produto_key,
    produto,
    case
        when produto like 'GASOLINA%' then 'GASOLINA'
        when produto like 'DIESEL%'   then 'DIESEL'
        else produto
    end                                 as familia,
    min(unidade_medida)                 as unidade_medida
from "observatorio"."staging"."stg_anp_precos"
group by produto
    );
    
  