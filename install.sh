# UCIS4EQ Instalation 
echo "Welcome to UCIS4EQ instalation"

# Creating the dir structure
echo "Creating the directories structure"
mkdir -p deployment/dockers/ data/

# Downloading files from repository
echo "Downloading files from repository ..."

echo "... for service deployment..."
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/docker-compose.yml/raw?ref=marta_devel' > docker-compose.yml
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/docker-compose-add-ssh-key-to-docker.yml/raw?ref=marta_devel' > docker-compose-add-ssh-key-to-docker.yml
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/deployment%2Fdockers%2FDockerfile-credentials/raw?ref=marta_devel' > deployment/dockers/Dockerfile-credentials

echo "... for compute and data repositories setup..."
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/data%2FDAL.template.json/raw?ref=marta_devel' > data/DAL.json
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/data%2FSites.template.json/raw?ref=marta_devel' > data/Sites.json
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/data%2Fresources.xml/raw?ref=marta_devel' > data/resources.xml
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/data%2Fproject.xml/raw?ref=marta_devel' > data/project.xml

echo "... and a test event..."
curl --silent GET --header 'PRIVATE-TOKEN: glpat-75-FV88yWpzpCZJvoKfe' 'https://gitlab.com/api/v4/projects/43953314/repository/files/data%2FMED_SAMOS_IZMIR_IRIS_test.json/raw?ref=marta_devel' > data/MED_SAMOS_IZMIR_IRIS_test.json

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
