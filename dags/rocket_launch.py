import json
import pathlib

import airflow
import requests
import requests.exceptions as requests_execeptions

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

rocket_launch_etl = DAG(
    dag_id="download_rocket_launches",
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval=None,
)


def get_pictures():
    # Check to ensure directory existis
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)

    # Download all pictures in launches.json
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
        image_urls = [launch["image"] for launch in launches["results"]]

        for image_url in image_urls:
            try:
                response = requests.get(image_url)
                image_filename = image_url.split("/")[-1]
                target_file = f"/tmp/images/{image_filename}"
                with open(target_file, "wb") as f:
                    f.write(response.content)

                print(f"Downloaded {image_url} to {target_file}")

            except requests_execeptions.MissingSchema:
                print(f"{image_url} appears to be an invalid URL.")

            except requests_execeptions.ConnectionError:
                print(f"Could not connect to {image_url}")


download_launches_task = BashOperator(
    task_id="download_launches",
    bash_command="curl -o /tmp/launches.json -L 'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",
    dag=rocket_launch_etl,
)

get_picture_task = PythonOperator(
    task_id="get_picture_task",
    python_callable=get_pictures,
    dag=rocket_launch_etl,
)

notify_task = BashOperator(
    task_id="notify_task",
    bash_command="echo 'There are now $(ls /tmp/images/ | wc -l) images.'",
    dag=rocket_launch_etl,
)

download_launches_task >> get_picture_task >> notify_task # type: ignore
