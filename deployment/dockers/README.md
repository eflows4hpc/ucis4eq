# Installation guide

### 1- Install software Dependencies

* Docker (Community Edition)
  ```
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```
  Find more installation options in:
  https://docs.docker.com/install/linux/docker-ce/ubuntu/
  
* Docker compose
  ```
  sudo curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  ```
  Find more installation options in:
  https://docs.docker.com/compose/install/

### 2 - Install image on the local host

Due to the image was registered on the GitLab repository, first step is doing login

```
  docker login registry.gitlab.com
```

##### Option 1: Obtain the docker-composer.yml file from the GitLab repository

```
  curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2Fdocker-compose.yml/raw?ref=master' > docker-compose.yml
```

```
  docker-compose up
```

##### Option 2: Get and run the docker conainers manually

1 - Pull the ucis4eq image from the registry
```
  docker pull registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/listener
  docker pull registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/dispatcher
```

2 - Indicate the configuration file of the ucis4eq listener service 
```
  export UCIS4EQ_LISTENER_CONFIG=/local/path/to/config_events.json
```

3 - Start the Docker containers

```
  docker run -ti --net="host" -v "$PWD:/workspace" registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/dispatcher
  docker run -ti --net="host" -v "$UCIS4EQ_LISTENER_CONFIG:/root/services/config.json" -v "$PWD:/workspace" registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/listener
```

# Additional actions

### Generate the ucis4eq-service Docker local image

This steps is just for users who wants to create the Docker image from scratch.


1 - Obtain the Dockerfiles with the Docker images setup
```
  curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-listener/raw?ref=master' > Dockerfile-listener
  curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/deployment%2Fdockers%2FDockerfile-dispatcher/raw?ref=master' > Dockerfile-dispatcher
```

2 - Building the images with the environement for ucis4eq services

```
  docker build -f Dockerfile-listener -t registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/listener .
  docker build -f Dockerfile-dispatcher -t registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/dispatcher .
```

3 - Register the built images
```
  docker push registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/listener
  docker push registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/dispatcher
```
  

### Start container in a terminal

```
  docker run -ti --net="host" -v "$PWD:/workspace" --entrypoint=bash registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/dispatcher
  docker run -ti --net="host" -v "$PWD:/workspace" --entrypoint=bash registry.gitlab.com/juane2rodriguez/cheese_pd1/ucis4eq-services/listener
```
