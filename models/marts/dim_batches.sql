with batches as (
    select * from {{ ref('stg_batches') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

results as (
    select * from {{ ref('fct_qc_results') }}
),

deviations as (
    select * from {{ ref('stg_deviations') }}
),

result_agg as (
    select
        batch_id,
        count(*) as tests_performed,
        sum(case when is_oos then 1 else 0 end) as oos_test_count,
        max(test_date) as last_test_date
    from results
    group by 1
),

deviation_agg as (
    select
        batch_id,
        count(*) as deviation_count,
        sum(case when impact = 'Batch rejected' then 1 else 0 end) as rejection_flag_count
    from deviations
    group by 1
)

select
    batches.batch_id,
    batches.product_code,
    products.product_name,
    products.dosage_form,
    batches.batch_size_units,
    batches.manufacture_date,
    batches.production_line,
    coalesce(result_agg.tests_performed, 0) as tests_performed,
    coalesce(result_agg.oos_test_count, 0) as oos_test_count,
    date_diff('day', batches.manufacture_date, result_agg.last_test_date) as days_mfg_to_last_test,
    coalesce(deviation_agg.deviation_count, 0) as deviation_count,
    case
        when coalesce(deviation_agg.rejection_flag_count, 0) > 0 then 'Rejected'
        when coalesce(result_agg.oos_test_count, 0) > 0 then 'Released with deviation'
        else 'Released'
    end as release_disposition
from batches
left join products on batches.product_code = products.product_code
left join result_agg on batches.batch_id = result_agg.batch_id
left join deviation_agg on batches.batch_id = deviation_agg.batch_id
