with deviations as (
    select * from {{ ref('stg_deviations') }}
),

batches as (
    select * from {{ ref('stg_batches') }}
)

select
    batches.product_code,
    deviations.category,
    date_trunc('month', deviations.opened_date) as opened_month,
    count(*) as deviations_opened,
    round(avg(deviations.days_to_close), 1) as avg_days_to_close,
    max(deviations.days_to_close) as max_days_to_close,
    sum(case when deviations.days_to_close > 30 then 1 else 0 end) as overdue_30day_count
from deviations
inner join batches on deviations.batch_id = batches.batch_id
group by 1, 2, 3
order by opened_month, product_code, category
