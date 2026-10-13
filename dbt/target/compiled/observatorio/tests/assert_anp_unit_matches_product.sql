-- GNV is sold per m3; every other product per litre.
select * from "observatorio"."staging"."stg_anp_precos"
where (produto = 'GNV' and unidade_medida <> 'R$/m3')
   or (produto <> 'GNV' and unidade_medida <> 'R$/litro')