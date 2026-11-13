-- Singular test: a result flagged "Pass" should never actually sit outside
-- its own spec limits, and a result flagged "OOS" should never actually
-- sit inside them. This catches a disagreement between the `status` field
-- and the limits it was supposedly judged against -- exactly the kind of
-- discrepancy a QC data reviewer would flag. dbt fails this test if it
-- returns any rows.

select *
from {{ ref('fct_qc_results') }}
where
    (status = 'Pass' and (
        (lower_spec_limit is not null and result_value < lower_spec_limit)
        or (upper_spec_limit is not null and result_value > upper_spec_limit)
    ))
    or
    (status = 'OOS' and (
        (lower_spec_limit is null or result_value >= lower_spec_limit)
        and (upper_spec_limit is null or result_value <= upper_spec_limit)
    ))
