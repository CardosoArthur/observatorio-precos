
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