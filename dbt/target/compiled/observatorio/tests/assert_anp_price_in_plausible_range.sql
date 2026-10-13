-- Sanity bounds (R$ per litre / m3): catches shifted decimals or parsing errors.
select * from "observatorio"."staging"."stg_anp_precos"
where valor_venda <= 0 or valor_venda >= 100