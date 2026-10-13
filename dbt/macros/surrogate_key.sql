{#- Deterministic surrogate key: md5 of the columns joined by '|' (no external packages). -#}
{% macro surrogate_key(columns) -%}
    md5(concat_ws('|', {{ columns | join(', ') }}))
{%- endmacro %}
