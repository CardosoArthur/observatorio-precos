
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- The most recent load attempt of every source key must have succeeded.
select source, source_file, status, error, loaded_at
from "observatorio"."raw"."_load_metadata"
qualify row_number() over (partition by source, source_file order by loaded_at desc) = 1
   and status <> 'success'
  
  
      
    ) dbt_internal_test