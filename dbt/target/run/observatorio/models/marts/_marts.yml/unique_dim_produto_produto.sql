
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    produto as unique_field,
    count(*) as n_records

from "observatorio"."marts"."dim_produto"
where produto is not null
group by produto
having count(*) > 1



  
  
      
    ) dbt_internal_test