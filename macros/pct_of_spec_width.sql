{% macro pct_of_spec_width(value_col, lsl_col, usl_col) %}
    {#
        For a two-sided spec (both a lower and upper limit), returns where a
        result falls across the acceptance window as a percentage: 0% sits
        exactly at the lower limit, 100% sits exactly at the upper limit,
        and a result can land below 0% or above 100% when it is actually
        out of spec. This gives QC a single comparable "how close to the
        edge" number across tests that use very different units (%, AV,
        mg/mL, ...).

        One-sided specs (only a lower OR only an upper limit) have no
        natural "width" to measure against, so this macro returns null for
        those rows rather than inventing a denominator.
    #}
    case
        when {{ lsl_col }} is not null and {{ usl_col }} is not null and {{ usl_col }} != {{ lsl_col }}
            then round(100.0 * ({{ value_col }} - {{ lsl_col }}) / ({{ usl_col }} - {{ lsl_col }}), 1)
        else null
    end
{% endmacro %}
