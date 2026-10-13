
    

    create  table
      "observatorio"."staging"."stg_anp_precos__dbt_tmp"
  
    
    as (
      with source as (

    select * from "observatorio"."raw"."anp_precos"

),

typed as (

    select
        regexp_replace(cnpj_revenda, '[^0-9]', '', 'g')                      as cnpj_revenda,
        upper(trim(produto))                                                 as produto,
        try_strptime(trim(data_coleta), '%d/%m/%Y')::date                    as data_coleta,
        try_cast(replace(trim(valor_venda), ',', '.') as decimal(10, 4))     as valor_venda,
        case
            when trim(unidade_medida) = 'R$ / litro' then 'R$/litro'
            when trim(unidade_medida) in ('R$ / m³', 'R$ / m3') then 'R$/m3'
            else trim(unidade_medida)
        end                                                                  as unidade_medida,
        case
            when upper(trim(bandeira)) = 'VIBRA ENERGIA' then 'VIBRA'
            else upper(trim(bandeira))
        end                                                                  as bandeira,
        trim(revenda)                                                        as revenda,
        upper(trim(regiao_sigla))                                            as regiao_sigla,
        upper(trim(estado_sigla))                                            as uf,
        upper(trim(municipio))                                               as municipio,
        trim(bairro)                                                         as bairro,
        trim(cep)                                                            as cep,
        _source_group                                                        as source_group,
        case _source_group
            when 'mensal' then 1
            when 'semestral' then 2
            when 'ultimas_4_semanas' then 3
            else 9
        end                                                                  as source_priority
    from source

),

ranked as (

    select
        *,
        min(source_priority) over (
            partition by cnpj_revenda, produto, data_coleta
        ) as best_priority
    from typed

),

best as (

    select * from ranked where source_priority = best_priority

)

select
    cnpj_revenda,
    produto,
    data_coleta,
    round(avg(valor_venda), 4)::decimal(10, 4)  as valor_venda,
    min(unidade_medida)                         as unidade_medida,
    min(bandeira)                               as bandeira,
    min(revenda)                                as revenda,
    min(regiao_sigla)                           as regiao_sigla,
    min(uf)                                     as uf,
    min(municipio)                              as municipio,
    min(bairro)                                 as bairro,
    min(cep)                                    as cep,
    min(source_group)                           as source_group,
    count(*)                                    as n_registros_origem
from best
group by cnpj_revenda, produto, data_coleta
    );
    
  