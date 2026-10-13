"""Daily ELT pipeline of the Observatório de Preços e Inflação.

    ingest_sgs -> ingest_sidra -> ingest_anp -> dbt_build -> export_marts -> dbt_freshness

Everything runs sequentially on purpose: DuckDB accepts one writer at a time, so the DAG
allows a single active task and a single active run. Each step is idempotent, so a retry or
a re-run never duplicates data.

ANP CSVs are dropped by hand in data/raw/anp (no public API); `ingest_anp` skips unchanged
files. Paths and binaries come from environment variables set in docker-compose.yaml.
"""
from __future__ import annotations

import os
from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT_DIR = os.getenv("PROJECT_DIR", "/opt/airflow/project")
PYTHON = os.getenv("PIPELINE_PYTHON", "/opt/dbt-venv/bin/python")
DBT = os.getenv("PIPELINE_DBT", "/opt/dbt-venv/bin/dbt")
DBT_ARGS = "--project-dir dbt --profiles-dir dbt"

default_args = {
    "owner": "data-engineering",
    "retries": 0,
}

with DAG(
    dag_id="observatorio_pipeline",
    description="ANP + IBGE + BCB -> DuckDB raw -> dbt staging/marts -> Parquet exports",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,  # DuckDB is single-writer
    dagrun_timeout=timedelta(hours=2),
    default_args=default_args,
    tags=["observatorio", "elt", "duckdb", "dbt"],
    doc_md=__doc__,
) as dag:
    ingest_sgs = BashOperator(
        task_id="ingest_sgs",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m ingestion sgs",
        retries=2,  # public API: transient network errors are expected
        retry_delay=timedelta(minutes=5),
    )
    ingest_sidra = BashOperator(
        task_id="ingest_sidra",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m ingestion sidra",
        retries=2,
        retry_delay=timedelta(minutes=5),
    )
    ingest_anp = BashOperator(
        task_id="ingest_anp",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m ingestion anp",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT_DIR} && {DBT} build {DBT_ARGS}",
    )
    export_marts = BashOperator(
        task_id="export_marts",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m ingestion export",
    )
    dbt_freshness = BashOperator(
        task_id="dbt_freshness",
        bash_command=f"cd {PROJECT_DIR} && {DBT} source freshness {DBT_ARGS}",
    )

    ingest_sgs >> ingest_sidra >> ingest_anp >> dbt_build >> export_marts >> dbt_freshness
