### Initialise Airflow

docker-compose up airflow-init

### Start Airflow services

docker-compose up

### Export environmental variables

echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env

### Enter into docker container

docker exec -it <container_name> bash

### Tear down all containers and images

docker-compose down --volumes --rmi all
