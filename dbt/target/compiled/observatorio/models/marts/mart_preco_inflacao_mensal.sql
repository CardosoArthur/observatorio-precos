with price as (

    select
        d.mes_referencia,
        p.produto,
        l.uf,
        avg(f.valor_venda)                  as preco_medio,
        count(*)                            as n_observacoes,
        count(distinct f.cnpj_revenda)      as n_revendas,
        count(distinct f.data_coleta)       as n_dias_coleta
    from "observatorio"."marts"."fact_preco_combustivel" as f
    inner join "observatorio"."marts"."dim_produto"    as p on f.produto_key = p.produto_key
    inner join "observatorio"."marts"."dim_localidade" as l on f.localidade_key = l.localidade_key
    inner join "observatorio"."marts"."dim_data"       as d on f.data_key = d.data_key
    group by 1, 2, 3

),

ipca as (

    select
        mes_referencia,
        max(valor) filter (where variavel_codigo = 63)   as ipca_mensal_pct,
        max(valor) filter (where variavel_codigo = 69)   as ipca_acum_ano_pct,
        max(valor) filter (where variavel_codigo = 2265) as ipca_12m_pct
    from "observatorio"."staging"."stg_ibge_ipca"
    group by 1

),

sgs as (

    select
        date_trunc('month', data)::date                           as mes_referencia,
        avg(valor) filter (where serie_codigo = 432)              as selic_meta_aa_media,
        avg(valor) filter (where serie_codigo = 1)                as usd_brl_venda_medio
    from "observatorio"."staging"."stg_bcb_sgs"
    group by 1

)

select
    pr.mes_referencia,
    pr.produto,
    pr.uf,
    round(pr.preco_medio, 4)                                                        as preco_medio,
    pr.n_observacoes,
    pr.n_revendas,
    pr.n_dias_coleta,
    round((pr.preco_medio / prev_m.preco_medio - 1) * 100, 4)                       as variacao_preco_mom_pct,
    round((pr.preco_medio / prev_y.preco_medio - 1) * 100, 4)                       as variacao_preco_12m_pct,
    ipca.ipca_mensal_pct,
    ipca.ipca_acum_ano_pct,
    ipca.ipca_12m_pct,
    round(sgs.selic_meta_aa_media, 4)                                               as selic_meta_aa_media,
    round(sgs.usd_brl_venda_medio, 4)                                               as usd_brl_venda_medio
from price as pr
left join price as prev_m
    on  prev_m.produto = pr.produto
    and prev_m.uf = pr.uf
    and prev_m.mes_referencia = (pr.mes_referencia - interval 1 month)::date
left join price as prev_y
    on  prev_y.produto = pr.produto
    and prev_y.uf = pr.uf
    and prev_y.mes_referencia = (pr.mes_referencia - interval 12 month)::date
left join ipca on ipca.mes_referencia = pr.mes_referencia
left join sgs  on sgs.mes_referencia  = pr.mes_referencia