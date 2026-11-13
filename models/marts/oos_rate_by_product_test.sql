with results as (
    select * from {{ ref('fct_qc_results') }}
)

select
    product_code,
    test_name,
    count(*) as total_results,
    sum(case when is_oos then 1 else 0 end) as oos_count,
    round(100.0 * sum(case when is_oos then 1 else 0 end) / count(*), 2) as oos_rate_pct,
    round(avg(pct_of_spec_width_used), 1) as avg_pct_of_spec_width_used
from results
group by 1, 2
order by oos_rate_pct desc
