# UCIS4EQ

UCIS4EQ provides the services needed for dealing with an urgent computing
scenario.

## Disclaimer
```

This software solution was developed at the Barcelona Supercomputing
Center (BSC) - Centro Nacional de Supercomputación (CNS), as part of
the ChEESE-COE project. It was later modified within the framework
of the ChEESE-2P and eFlows4HPC projects.

Authors: Josep de la Puente, Juan Esteban Rodríguez, Marisol Monterrubio,
Marta Pienkowska-Cote.
Contributors: Jorge Ejarque, Cedric Bhihe
Contacts:
    marisol.monterrubio@bsc.es
    jorge.ejarque@bsc.es
    cedric.bhihe@bsc.es

This program is free software: you can redistribute it and/or
modify it under the terms of the Modified BSD (3-clause) License,
aka BSD NEW License, aka BSD REVISED License, aka MODIFIED BSD
License as published by the Regents of the University of California.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
LICENSE.md file included in this repository for more details.

You should have received a copy of the Modified BSD License along
with this program. If not, see <https://www.gnu.org/licenses/>.
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
  docker login registry.gitlab.bsc.es
```

For obtaining docker-composer.yml, setup and test files, create a working directory, move there and then:

```
  bash -c "$(curl --request GET --header 'PRIVATE-TOKEN: ER9nSBQo8xsiczs47pAn' 'https://gitlab.bsc.es/api/v4/projects/2703/repository/files/install.sh/raw?ref=migration-fixes')"
```

Follow the instructions

## Manual event triggering

From working directory:

### 1 - Start the UCIS4EQ System
Open a terminal and be sure that both .env and docker-compose.yml are in the such directory. Then, run:

```
> SSH_PRV="$(cat ~/.ssh/<my_id_rsa>)" docker-compose up
```

IMPORTANT: During first deployment, some images will be created for adding user's ssh credentials.

### 2 - Trigger a manual alert
```
curl -X POST -H 'Content-Type: application/json' -d @data/SAMOS_EQ_Event_DEMO.json http://127.0.0.1:5001/PyCOMPSsWM
```

### 3 - Event follow-up in the Dashboard

Open a browser and go to http://127.0.0.1:8050/

## Quickstart tutorial

Independently from the above, this repo contains a quickstart tutorial in PDF format to guide you step by step through basic installation and launch on the BSC infrastructure.
