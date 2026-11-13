with source as (
    select * from {{ ref('raw_specifications') }}
),

renamed as (
    select
        spec_id,
        product_code,
        test_name,
        cast(nullif(cast(lower_spec_limit as varchar), '') as double) as lower_spec_limit,
        cast(nullif(cast(upper_spec_limit as varchar), '') as double) as upper_spec_limit,
        unit
    from source
)

select * from renamed
