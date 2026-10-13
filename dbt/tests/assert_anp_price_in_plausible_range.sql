-- Sanity bounds (R$ per litre / m3): catches shifted decimals or parsing errors.
select * from {{ ref('stg_anp_precos') }}
where valor_venda <= 0 or valor_venda >= 100
