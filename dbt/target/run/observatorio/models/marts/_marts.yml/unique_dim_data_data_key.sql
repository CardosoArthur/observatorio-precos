
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    data_key as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_data"
where data_key is not null
group by data_key
having count(*) > 1



  
  
      
    ) dbt_internal_test