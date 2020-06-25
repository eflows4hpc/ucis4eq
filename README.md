# UCIS4EQ

The system provides the services needed for dealing with an urgent computing
scenario.

## Disclaimer
```

This software solution was developed under the ChEESE-COE project

Author:  Juan Esteban Rodríguez, Marisol Monterrubio, Josep de la Puente
Contact: juan.rodriguez@bsc.es, marisol.monterrubio@bsc.es, josep.delapuente@bsc.es

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```


## HOW TO:

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

##### Obtain the docker-composer.yml and .env file from the GitLab repository

```
  curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/docker-compose.yml/raw?ref=master' > docker-compose.yml
  curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/.env/raw?ref=master' > .env  
```

## Manual TEST Example

### 1 - Start the UCIS4EQ System
Open a terminal and be sure that both .env and docker-compose.yml are in the such directory. Then, run:

```
docker-compose up 
```

### 2 - Download the event setup
```
curl --request GET --header 'PRIVATE-TOKEN: bZA9JyDsdqyzawJngzzy' 'https://gitlab.com/api/v4/projects/12232768/repository/files/data%2FSISZ_EQEventExample.json/raw?ref=master' > SISZ_EQEventExample.json
```

### 3 - Trigger a manual alert
```
curl -X POST -H 'Content-Type: application/json' -d @SISZ_EQEventExample.json http://127.0.0.1:5001/WMEmulator
```

Notice that .env file and all configuration files should be provided for a right behaviour 
