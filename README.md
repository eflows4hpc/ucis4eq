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

### 2 - Deploy UCIS4EQ services

Because the Docker images are registered on the GitLab repository, first step is login on it

```
  docker login registry.gitlab.com
```

For obtaining docker-composer.yml, setup and test files, create a working directory, move there and then:

```
  bash -c "$(curl --request GET --header 'PRIVATE-TOKEN: glpat-8SmAHs1yjVmWq6-q_bkz' 'https://gitlab.com/api/v4/projects/12232768/repository/files/install.sh/raw?ref=master')"
```

Follow the instructions

## Manual event triggering

From working directory:

### 1 - Start the UCIS4EQ System
Open a terminal and be sure that both .env and docker-compose.yml are in the such directory. Then, run:

```
SSH_PRV="$(cat ~/.ssh/id_rsa)" docker-compose up 
```

IMPORTANT: During first deployment, some images will be created for adding user's ssh credentials.

### 2 - Trigger a manual alert
```
curl -X POST -H 'Content-Type: application/json' -d @data/SAMOS_EQ_Event_DEMO.json http://127.0.0.1:5001/PyCOMPSsWM
```

### 3 - Event follow-up in the Dashboard

Open a browser and go to http://127.0.0.1:8050/
