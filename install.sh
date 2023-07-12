#!/usr/bin/bash

# UCIS4EQ Instalation
printf "%s\n" "Welcome to UCIS4EQ instalation"

# Creating the dir structure
printf "%s\n" "Dreating the directories structure ..."
mkdir -p deployment/dockers/ data/

# Downloading files from repository
printf "%s\n" "Downloading files from the https://gitlab.bsc.es/wavephenomenagroup/ucis4eq/ repository"
printf "%s\n" "........ for service deployment..."
printf "%s\n" "(Already existing files in the destination directory will be overwritten.)"

# The PRIVATE-TOKEN provided below gives full programmatic READ access to the code
# repository and to the Docker image registry. The user's scope is assimilated to
# that of a "maintainer". The current Project Access Token (PAT) expires in 2033.08.03.

curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/docker-compose.yml/raw?ref=migration-fixes' >| docker-compose.yml

if ! "$?"; then
    printf "\n\n%s\n" "Installation process aborted. Please check the \`install.sh' script present in your"
    printf "%s\n" "installation directory and make sure:"
    printf "%s\n" " - either that your GitLab instance's \`PRIVATE-TOKEN', i.e. the GitLab Project Access Token"
    printf "%s\n" " (PAT), is still valid to access resources on https://gitlab.bsc.es/wavephenomenagroup/ucis4eq/"
    printf "%s\n\n" " - or that the fetched file resources are available in that same repo."
    exit 1
fi

curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/docker-compose-add-ssh-key-to-docker.yml/raw?ref=migration-fixes' >| docker-compose-add-ssh-key-to-docker.yml
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/deployment%2Fdockers%2FDockerfile-credentials/raw?ref=migration-fixes' >| deployment/dockers/Dockerfile-credentials

printf "%s\n" "........ for compute and data repositories setup..."
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FDAL.template.json/raw?ref=migration-fixes' >| data/DAL.json
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FSites.template.json/raw?ref=migration-fixes' >| data/Sites.json
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2Fresources.xml/raw?ref=migration-fixes' >| data/resources.xml
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2Fproject.xml/raw?ref=migration-fixes' >| data/project.xml

<<<<<<< HEAD
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
=======
printf "%s\n" "........ and a test event..."
curl --silent GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/data%2FMED_SAMOS_IZMIR_IRIS_test.json/raw?ref=migration-fixes' >| data/MED_SAMOS_IZMIR_IRIS_test.json

printf "%s\n\n" "All DONE!"
printf "%s\n" "Now:"
printf "%s\n" " 1- Revise the files data \`Sites.json' and \`DAL.json' to set your own credentials as well"
printf "%s\n" "    paths specific to your installation."
printf "%s\n" " 2- Make sure that \`docker' and \`docker-compose' are installed locally"
printf "%s\n"  "   ---> 'https://docs.docker.com/compose/install/'"
printf "%s\n" " 3- Login to the Gitlab UCIS4EQ registry with:"
printf "%\t\ts\n" "> docker login registry.gitlab.bsc.es"
printf "%s\n" " 4- To start runnning the services, issue either:"
printf "%s\t\t\n" "> docker compose up"
printf "%s\n" "or:"
printf "%s\t\t\n" "> SSH_PRV=$(cat ~/.ssh/your_id_rsa_file)  docker-compose up"
printf "%s\n" " 5- To stop running the services, press: Ctrl+C  (twice)"
printf "%s\n" " 6- To clean-up after running Docker containers:"
printf "%s\t\t\n" "> docker-compose down"
>>>>>>> 45f9372 (updated README.md files and instructions for UCIS4EQ deployment)
