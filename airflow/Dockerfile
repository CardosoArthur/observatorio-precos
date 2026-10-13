# Airflow + an isolated virtualenv for the pipeline (ingestion + dbt-duckdb).
FROM apache/airflow:3.3.2

COPY requirements-pipeline.txt /tmp/requirements-pipeline.txt

# The virtualenv keeps dbt/duckdb separate from Airflow's constrained dependencies.
RUN python -m venv /home/airflow/dbt-venv \
    && /home/airflow/dbt-venv/bin/pip install --no-cache-dir -r /tmp/requirements-pipeline.txt

# Created here so the named volume inherits the airflow user's ownership.
RUN mkdir -p /opt/airflow/warehouse
