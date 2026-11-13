with source as (
    select * from {{ ref('raw_deviations') }}
),

renamed as (
    select
        deviation_id,
        batch_id,
        -- blank in the CSV for deviations not tied to a single result
        cast(nullif(cast(related_result_id as varchar), '') as integer) as related_result_id,
        category,
        cast(opened_date as date) as opened_date,
        cast(closed_date as date) as closed_date,
        impact,
        date_diff('day', cast(opened_date as date), cast(closed_date as date)) as days_to_close
    from source
)

select * from renamed
