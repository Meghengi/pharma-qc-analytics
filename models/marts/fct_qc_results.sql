{{
    config(
        materialized='table'
    )
}}

with results as (
    select * from {{ ref('stg_qc_results') }}
),

batches as (
    select * from {{ ref('stg_batches') }}
),

specs as (
    select * from {{ ref('stg_specifications') }}
)

select
    results.result_id,
    results.batch_id,
    batches.product_code,
    batches.manufacture_date,
    batches.production_line,
    results.test_name,
    results.result_value,
    results.unit,
    specs.lower_spec_limit,
    specs.upper_spec_limit,
    results.test_date,
    date_diff('day', batches.manufacture_date, results.test_date) as days_mfg_to_test,
    results.analyst,
    results.shift,
    results.instrument_id,
    results.status,
    results.is_oos,
    {{ pct_of_spec_width('results.result_value', 'specs.lower_spec_limit', 'specs.upper_spec_limit') }} as pct_of_spec_width_used
from results
inner join batches on results.batch_id = batches.batch_id
left join specs
    on batches.product_code = specs.product_code
    and results.test_name = specs.test_name
