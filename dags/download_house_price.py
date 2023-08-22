import json
import pathlib

import airflow
import requests
import requests.exceptions as requests_execeptions

from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator


download_hdb_resale_data = DAG(
    dag_id="download_hdb_resale_data",
    start_date=airflow.utils.dates.days_ago(1),
    schedule_interval="@daily",
)


def check_last_dag_run_success():
    # Get the last_modified of resource
    with open("/tmp/resale_price_metadata.json") as f:
        metadata = json.load(f)
        last_modified_str = metadata["result"]["last_modified"]
        last_modified_dt = datetime.strptime(last_modified_str.split(".")[0],"%Y-%m-%dT%H:%M:%S")

        if last_modified_dt < datetime.now():
            return "download_new_data"
        else:
            return "skip_dowload_no_new_data"


download_metadata_task = BashOperator(
    task_id="download_metadata",
    bash_command="curl -o /tmp/resale_price_metadata.json -L 'https://data.gov.sg/api/action/resource_show?id=f1765b54-a209-4718-8d38-a39237f502b3'",
    dag=download_hdb_resale_data,
)


branch_download_task = BranchPythonOperator(
    task_id="branch_download_task",
    provide_context=True,
    python_callable=check_last_dag_run_success,
    dag=download_hdb_resale_data,
)

download_new_data_task = EmptyOperator(task_id="download_new_data")

skip_dowload_no_new_data_task = EmptyOperator(task_id="skip_dowload_no_new_data")


skipped_notification_task = BashOperator(
    task_id="skipped_notification_task",
    bash_command="echo 'Skipped download.'",
    dag=download_hdb_resale_data,
)

download_resale_data_task = BashOperator(
    task_id="download_resale_data_task",
    bash_command="curl -o /opt/resale_price_data.json -L 'https://data.gov.sg/api/action/datastore_search?resource_id=f1765b54-a209-4718-8d38-a39237f502b3&limit=1000000'",
    dag=download_hdb_resale_data,
)

download_metadata_task >> branch_download_task >> download_new_data_task >> download_resale_data_task  # type: ignore
branch_download_task >> skip_dowload_no_new_data_task >> skipped_notification_task  # type: ignore
