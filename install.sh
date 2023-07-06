#!/usr/bin/bash

# UCIS4EQ Instalation
echo "Welcome to UCIS4EQ instalation"

# Creating the dir structure
echo "Creating the directories structure"
mkdir -p deployment/dockers/ data/

# Downloading files from repository
echo "Downloading files from repository ..."

echo "... for service deployment..."
# The PRIVATE-TOKEN provided below gives full programmatic read access to the 
# code repository and to the Docker image registry. The user's scope is 
# assimilated to that of a "maintainer". The Project Access Token (PAT) expires
# in 2033.08.03.

curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/docker-compose.yml/raw?ref=migration-fixes' > docker-compose.yml
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/docker-compose-add-ssh-key-to-docker.yml/raw?ref=migration-fixes' > docker-compose-add-ssh-key-to-docker.yml
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/deployment%2Fdockers%2FDockerfile-credentials/raw?ref=migration-fixes' > deployment/dockers/Dockerfile-credentials

echo "... for compute and data repositories setup..."
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FDAL.template.json/raw?ref=migration-fixes' > data/DAL.json
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FSites.template.json/raw?ref=migration-fixes' > data/Sites.json
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2Fresources.xml/raw?ref=migration-fixes' > data/resources.xml
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2Fproject.xml/raw?ref=migration-fixes' > data/project.xml

echo "... and a test event..."
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FMED_SAMOS_IZMIR_IRIS_test.json/raw?ref=migration-fixes' > data/MED_SAMOS_IZMIR_IRIS_test.json

echo "All DONE!"

echo ""
echo "Now:"
echo " 1- Revise the files data Sites.json and DAL.json to set your own credentials."
echo " 2- Make sure that docker and docker compose are on your system ---> 'https://docs.docker.com/compose/install/'"
echo " 3- Login to the Gitlab UCIS4EQ registry:"
echo "    docker login registry.gitlab.com"
echo ' 4- To start runnning the services: docker compose up'
#         SSH_PRV="$(cat ~/.ssh/id_rsa)"  docker-compose up'
echo " 5- To stop running the services: ctrl+C  (twice)"
echo " 6- To make an installation clean-up" 
echo "    docker-compose down"
