# UCIS4EQ Instalation 
echo "Welcome to UCIS4EQ instalation"

# Creating the dir structure
echo "Creating the directories structure"
mkdir -p data deployment/dockers

# Creating environment file
echo "Creating environment file ..."
echo UCIS4EQ_DAL=$PWD/data/DAL.json > .env
echo UCIS4EQ_DAL=$PWD/data/Sites.json > .env

# Downloading files from repository
echo "Downloading files from repository ..."

echo "... for service deployment..."
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/docker-compose.yml/raw?ref=master' > docker-compose.yml  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-dashboard/raw?ref=master' > deployment/dockers/Dockerfile-dashboard  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-listener/raw?ref=master' > deployment/dockers/Dockerfile-listener  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-microServices/raw?ref=master' > deployment/dockers/Dockerfile-microServices  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-salvusServices/raw?ref=master' > deployment/dockers/Dockerfile-salvusServices  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-slipGen/raw?ref=master' > deployment/dockers/Dockerfile-slipGen  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-workflowManager/raw?ref=master' > deployment/dockers/Dockerfile-workflowManager  /dev/null 2>&1

echo "... for compute and data repositories setup..."
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2F/DAL.json/raw?ref=master' > data/DAL.json  /dev/null 2>&1
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2F/Sites.json/raw?ref=master' > data/Sites.json  /dev/null 2>&1

echo "... and an known event..."
curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2F/SAMOS_EQ_Event_DEMO.json/raw?ref=master' > data/SAMOS_EQ_Event_DEMO.json.json  /dev/null 2>&1

echo "All DONE!"

echo ""
echo "Now:"
echo " 1- Revise the files data Sites.json and DAL.json to set your own credentials..."
echo " 2- Make sure that docker-compose is on your system ---> 'https://docs.docker.com/compose/install/'"
echo " 3- Login on the Gitlab UCIS4EQ registry:"
echo "    docker login registry.gitlab.com"
echo ' 4- To start runnning:
         SSH_PRV="$(cat ~/.ssh/id_rsa)"  docker-compose up'
echo " 5- To stop running services just ctrl+C  (twice)"         
echo " 6- To make an installation clean-up" 
echo "    docker-compose down"

echo ""
echo "Good luck!"
