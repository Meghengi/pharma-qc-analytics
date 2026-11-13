with source as (
    select * from {{ ref('raw_products') }}
),

renamed as (
    select
        product_code,
        product_name,
        dosage_form
    from source
)

select * from renamed
