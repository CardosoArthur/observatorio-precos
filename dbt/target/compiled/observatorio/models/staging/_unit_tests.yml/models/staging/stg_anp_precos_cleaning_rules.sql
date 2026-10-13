with  __dbt__cte__raw__anp_precos as (

-- Fixture for anp_precos
select cast(null as character varying(256)) as "regiao_sigla", 
    
    cast('al' as character varying)
 as "estado_sigla", 
    
    cast('rio largo' as character varying)
 as "municipio", cast(null as character varying(256)) as "revenda", 
    
    cast(' 01.600.494/0001-08' as character varying)
 as "cnpj_revenda", cast(null as character varying(256)) as "nome_rua", cast(null as character varying(256)) as "numero_rua", cast(null as character varying(256)) as "complemento", cast(null as character varying(256)) as "bairro", cast(null as character varying(256)) as "cep", 
    
    cast('gnv' as character varying)
 as "produto", 
    
    cast('10/02/2026' as character varying)
 as "data_coleta", 
    
    cast('4,5' as character varying)
 as "valor_venda", cast(null as character varying(256)) as "valor_compra", 
    
    cast('R$ / m³' as character varying)
 as "unidade_medida", 
    
    cast('Vibra Energia' as character varying)
 as "bandeira", cast(null as character varying(256)) as "_source_file", 
    
    cast('semestral' as character varying)
 as "_source_group", 
    
    cast('2026-10-01 10:00:00' as TIMESTAMP)
 as "_ingested_at"
), source as (

    select * from __dbt__cte__raw__anp_precos

),

parsed as (

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
        _ingested_at                                                         as ingested_at,
        case _source_group
            when 'mensal' then 1
            when 'semestral' then 2
            when 'ultimas_4_semanas' then 3
            else 9
        end                                                                  as source_priority
    from source

),



typed as (

    select * from parsed

),



ranked as (

    select
        *,
        min(source_priority) over (
            partition by cnpj_revenda, produto, data_coleta
        ) as best_priority,
        max(ingested_at) over (
            partition by cnpj_revenda, produto, data_coleta
        ) as key_ingested_at
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
    count(*)                                    as n_registros_origem,
    max(key_ingested_at)                        as ingested_at
from best
group by cnpj_revenda, produto, data_coleta