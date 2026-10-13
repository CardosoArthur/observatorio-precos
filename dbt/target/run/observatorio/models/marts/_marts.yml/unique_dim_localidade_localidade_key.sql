
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    localidade_key as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_localidade"
where localidade_key is not null
group by localidade_key
having count(*) > 1



  
  
      
    ) dbt_internal_test