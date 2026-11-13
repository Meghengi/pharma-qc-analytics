with source as (
    select * from {{ ref('raw_batches') }}
),

renamed as (
    select
        batch_id,
        product_code,
        batch_size_units,
        cast(manufacture_date as date) as manufacture_date,
        line as production_line
    from source
)

select * from renamed
