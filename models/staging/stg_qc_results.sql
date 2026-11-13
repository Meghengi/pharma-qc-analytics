with source as (
    select * from {{ ref('raw_qc_results') }}
),

renamed as (
    select
        result_id,
        batch_id,
        test_name,
        result_value,
        unit,
        cast(test_date as date) as test_date,
        analyst,
        shift,
        instrument_id,
        status,
        case when status = 'OOS' then true else false end as is_oos
    from source
)

select * from renamed
