# UCIS4EQ Instalation 
echo "Welcome to UCIS4EQ instalation"

# Creating the dir structure
echo "Creating the directories structure"
mkdir -p deployment/dockers/ data/

# Downloading files from repository
echo "Downloading files from repository ..."

echo "... for service deployment..."
curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/docker-compose.yml/raw?ref=marta_devel' > docker-compose.yml
#curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-credentials/raw?ref=master' > deployment/dockers/Dockerfile-credentials

echo "... for compute and data repositories setup..."
curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2FDAL.template.json/raw?ref=marta_devel' > data/DAL.json
curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2FSites.template.json/raw?ref=marta_devel' > data/Sites.json
curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2Fresources.xml/raw?ref=marta_devel' > data/resources.xml
curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2Fproject.xml/raw?ref=marta_devel' > data/project.xml

#echo "... and an known event..."
#curl --silent GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2FSAMOS_EQ_Event_DEMO.json/raw?ref=master' > data/SAMOS_EQ_Event_DEMO.json

echo "All DONE!"

echo ""
echo "Now:"
echo " 1- Revise the files data Sites.json and DAL.json to set your own credentials..."
echo " 2- Make sure that docker-compose is on your system ---> 'https://docs.docker.com/compose/install/'"
echo " 3- Login on the Gitlab UCIS4EQ registry:"
echo "    docker login registry.gitlab.com"
echo ' 4- To start runnning: docker-compose up'
#         SSH_PRV="$(cat ~/.ssh/id_rsa)"  docker-compose up'
echo " 5- To stop running services just ctrl+C  (twice)"         
echo " 6- To make an installation clean-up" 
echo "    docker-compose down"
