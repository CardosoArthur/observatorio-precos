
    

    create  table
      "observatorio"."marts"."dim_data__dbt_tmp"
  
    
    as (
      with bounds as (

    select min(data_coleta) as first_day, max(data_coleta) as last_day
    from "observatorio"."staging"."stg_anp_precos"

),

spine as (

    select unnest(generate_series(first_day, last_day, interval 1 day))::date as data
    from bounds

)

select
    cast(strftime(data, '%Y%m%d') as integer)   as data_key,
    data,
    year(data)                                  as ano,
    month(data)                                 as mes,
    date_trunc('month', data)::date             as mes_referencia,
    quarter(data)                               as trimestre,
    isodow(data)                                as dia_semana_iso,
    isodow(data) >= 6                           as is_fim_de_semana
from spine
    );
    
  